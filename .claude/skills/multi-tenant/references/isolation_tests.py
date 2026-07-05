"""Isolation test template — adapt model/URL names, keep every category.

The suite proves a user in tenant A can never reach tenant B's records via
ORM, views/API, admin, background context, or public tokens. A red test here
blocks shipping, full stop.
"""
from django.contrib.auth.models import User
from django.test import TestCase

# from tenancy import tenant_context, TenantContextMissing
# from tenancy.models import Tenant, TenantMembership
# from patients.models import Patient


class IsolationTests(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Clinic A', subdomain='clinica')
        self.tenant_b = Tenant.objects.create(name='Clinic B', subdomain='clinicb')

        with tenant_context(self.tenant_a):
            self.user_a = User.objects.create_user('doc_a', password='pw')
            TenantMembership.objects.create(user=self.user_a, tenant=self.tenant_a, role='doctor')
            self.patient_a = Patient.objects.create(first_name='Ann', last_name='A', ...)

        with tenant_context(self.tenant_b):
            self.user_b = User.objects.create_user('doc_b', password='pw')
            TenantMembership.objects.create(user=self.user_b, tenant=self.tenant_b, role='doctor')
            self.patient_b = Patient.objects.create(first_name='Ben', last_name='B', ...)

    # ── ORM ──────────────────────────────────────────────────────────────
    def test_orm_scoping(self):
        with tenant_context(self.tenant_a):
            self.assertEqual(Patient.objects.count(), 1)
            self.assertFalse(Patient.objects.filter(pk=self.patient_b.pk).exists())
            with self.assertRaises(Patient.DoesNotExist):
                Patient.objects.get(pk=self.patient_b.pk)

    def test_no_context_raises_never_leaks(self):
        with self.assertRaises(TenantContextMissing):
            list(Patient.objects.all())

    # ── Views / API — 404, not 403: don't confirm the record exists ──────
    def test_cross_tenant_view_is_404(self):
        self.client.force_login(self.user_a)
        response = self.client.get(
            f'/patients/{self.patient_b.pk}/', HTTP_HOST='clinica.gpcrm.test')
        self.assertEqual(response.status_code, 404)

    def test_cross_tenant_json_endpoint_is_404(self):
        self.client.force_login(self.user_a)
        response = self.client.get(
            f'/diagnosis/patients/appointments/?patient_id={self.patient_b.pk}',
            HTTP_HOST='clinica.gpcrm.test')
        self.assertEqual(response.status_code, 404)

    def test_search_endpoints_exclude_other_tenant(self):
        self.client.force_login(self.user_a)
        data = self.client.get('/diagnosis/patients/search/?q=Ben',
                               HTTP_HOST='clinica.gpcrm.test').json()
        self.assertEqual(data['results'], [])

    # ── Admin ─────────────────────────────────────────────────────────────
    def test_admin_queryset_scoped(self):
        self.user_a.is_staff = True
        self.user_a.save()
        self.client.force_login(self.user_a)
        response = self.client.get('/admin/patients/patient/', HTTP_HOST='clinica.gpcrm.test')
        self.assertNotContains(response, 'Ben')

    # ── Public token surfaces ─────────────────────────────────────────────
    def test_token_bound_to_its_tenant_host(self):
        with tenant_context(self.tenant_a):
            token = make_checkin_token(self.patient_a)     # adapt to real helper
        response = self.client.get(f'/appointments/checkin/{token}/',
                                   HTTP_HOST='clinicb.gpcrm.test')
        self.assertEqual(response.status_code, 404)

    # ── Role × tenant composition ─────────────────────────────────────────
    def test_role_is_per_tenant(self):
        """doctor at A is nobody at B — doctor-only views 403/404 on B's host."""
        self.client.force_login(self.user_a)
        response = self.client.get('/consultations/', HTTP_HOST='clinicb.gpcrm.test')
        self.assertIn(response.status_code, (403, 404))
