"""Multi-tenant enforcement scaffolding for the GP CRM.

Model-independent pieces: request-scoped tenant context, loud-failure
manager, middleware, and the membership model. Under django-tenants the
schema handles row scoping and the manager's job reduces to the
loud-failure guard; under shared-schema the manager also filters.
"""
import contextvars

from django.db import models
from django.http import Http404

# ── Request-scoped tenant context ─────────────────────────────────────────────
# contextvars (not a module global) because gunicorn runs threaded (--threads 8):
# a plain global would bleed tenants across concurrently-handled requests.
_current_tenant = contextvars.ContextVar('current_tenant', default=None)


class TenantContextMissing(Exception):
    """Raised when tenant-owned data is touched with no tenant in context.
    This is the loud-failure guard: a crash here is a bug to fix, but a
    silent unscoped query is a cross-clinic PHI leak."""


def get_current_tenant():
    tenant = _current_tenant.get()
    if tenant is None:
        raise TenantContextMissing(
            'No tenant in context. Views get one from middleware; background '
            'jobs and shell code must use tenant_context(tenant).')
    return tenant


class tenant_context:
    """Explicit context manager for jobs, shell, and per-tenant iteration:

        for tenant in Tenant.objects.filter(active=True):
            with tenant_context(tenant):
                send_follow_up_reminders()
    """
    def __init__(self, tenant):
        self.tenant = tenant

    def __enter__(self):
        self._token = _current_tenant.set(self.tenant)
        return self.tenant

    def __exit__(self, *exc):
        _current_tenant.reset(self._token)


# ── Middleware: resolve tenant from subdomain before anything else ────────────
class TenantResolutionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import Tenant  # adjust import to where Tenant lives
        subdomain = request.get_host().split(':')[0].split('.')[0].lower()
        tenant = Tenant.objects.filter(subdomain=subdomain, active=True).first()
        if tenant is None:
            raise Http404('Unknown clinic.')   # never fall back to a default tenant
        token = _current_tenant.set(tenant)
        try:
            request.tenant = tenant
            return self.get_response(request)
        finally:
            _current_tenant.reset(token)


# ── Scoped manager for tenant-owned models (shared-schema variant) ────────────
class TenantManager(models.Manager):
    """Every queryset on a tenant-owned model goes through here. Under
    schema-per-tenant, drop the .filter() and keep the get_current_tenant()
    call purely as the loud-failure guard."""
    def get_queryset(self):
        tenant = get_current_tenant()          # raises if context is missing
        return super().get_queryset().filter(tenant=tenant)

    def unscoped(self):
        """Deliberate escape hatch for operations code. Grep-able; every use
        needs a comment justifying it."""
        return super().get_queryset()


class TenantOwnedModel(models.Model):
    """Abstract base: FK + scoped default manager + auto-stamp on save."""
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, editable=False)

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.tenant_id is None:
            self.tenant = get_current_tenant()
        super().save(*args, **kwargs)


# ── Tenancy × RBAC ─────────────────────────────────────────────────────────────
class TenantMembership(models.Model):
    """A user belongs to a tenant AND holds a role within it. Replaces global
    Doctor/Reception groups when multi-tenancy lands: medicaregp/roles.py
    is_doctor()/is_reception() switch to checking membership for
    request.tenant instead of user.groups."""
    ROLE_CHOICES = [('doctor', 'Doctor'), ('reception', 'Reception')]

    user   = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='tenant_memberships')
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='memberships')
    role   = models.CharField(max_length=20, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('user', 'tenant')]
