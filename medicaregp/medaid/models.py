"""Per-scheme gateway configuration.

SECURITY: this table stores the NAMES of environment variables, never the
credential values themselves. Actual secrets live only in the environment
(Railway variables / local shell) — they are absent from the repo, the
database, logs and reprs. There is a test asserting resolved secrets never
leak through __str__/__repr__.
"""
import os

from django.db import models


class SchemeConfig(models.Model):
    ADAPTER_CHOICES = [
        ('manual', 'Manual / portal fallback (no direct API)'),
        # Real per-scheme adapters register here as they are built, e.g.:
        # ('discovery_rest', 'Discovery Health REST API'),
        # ('gems_edi',       'GEMS X12 EDI'),
    ]

    scheme_name  = models.CharField(max_length=100, unique=True,
                                    help_text='Must match Patient.medical_aid_name (case-insensitive).')
    adapter      = models.CharField(max_length=40, choices=ADAPTER_CHOICES, default='manual')
    endpoint_url = models.URLField(blank=True, default='',
                                   help_text='Scheme API base URL (or portal URL for the manual adapter).')
    # Names of env vars holding this scheme's credentials — NOT the values.
    username_env = models.CharField(max_length=100, blank=True, default='',
                                    help_text='Name of the env var holding the API username/client id.')
    password_env = models.CharField(max_length=100, blank=True, default='',
                                    help_text='Name of the env var holding the API password/secret.')
    api_key_env  = models.CharField(max_length=100, blank=True, default='',
                                    help_text='Name of the env var holding an API key/token, if used.')
    active       = models.BooleanField(default=True)
    notes        = models.TextField(blank=True, null=True,
                                    help_text='Onboarding contacts, portal instructions, etc. Never paste secrets here.')

    class Meta:
        ordering = ['scheme_name']
        verbose_name = 'Medical aid scheme config'

    def __str__(self):
        # Deliberately excludes anything credential-related.
        return f'{self.scheme_name} ({self.get_adapter_display()})'

    def credentials(self):
        """Resolve credentials from the environment at call time. Values are
        returned to the adapter only — never store, log or render them."""
        return {
            'username': os.environ.get(self.username_env, '') if self.username_env else '',
            'password': os.environ.get(self.password_env, '') if self.password_env else '',
            'api_key':  os.environ.get(self.api_key_env, '') if self.api_key_env else '',
        }
