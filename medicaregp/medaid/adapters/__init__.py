"""Adapter registry: scheme name → gateway adapter.

Adding a new medical aid:
  1. Write ONE adapter class implementing MedicalAidGateway
     (see manual.py for the shape) in this package.
  2. Register it in ADAPTERS below and in SchemeConfig.ADAPTER_CHOICES.
  3. Create a SchemeConfig row in admin (endpoint + env-var NAMES for creds).
No calling code changes.
"""
from medaid.models import SchemeConfig

from .manual import ManualAdapter

ADAPTERS = {
    'manual': ManualAdapter,
}


def get_gateway(scheme_name):
    """Gateway for a scheme. Unknown/unconfigured schemes fall back to a
    manual adapter with an unsaved default config, so calling code always
    gets a working gateway."""
    config = None
    if scheme_name:
        config = SchemeConfig.objects.filter(
            scheme_name__iexact=scheme_name.strip(), active=True).first()
    if config is None:
        config = SchemeConfig(scheme_name=scheme_name or 'Unknown scheme', adapter='manual')
    adapter_cls = ADAPTERS.get(config.adapter, ManualAdapter)
    return adapter_cls(config)
