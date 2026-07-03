"""Pluggable biometric identification for front-office check-in.

A BiometricProvider turns a device-supplied sample into an enrolment
template hash (enrol) or a matched patient (identify). The default
HashBiometricProvider is a SIMULATOR: it hashes the sample string exactly,
so any scanner (or a typed test string) whose SDK emits a stable template
works out of the box. When real fingerprint hardware is chosen, implement
this interface around its SDK and point settings.BIOMETRIC_PROVIDER at it —
nothing else in the system changes.

Privacy: only a one-way SHA-256 hash is ever stored (BiometricTemplate);
a successful match releases MEDICAL-AID FIELDS ONLY (medicaregp.roles
.MEDICAL_AID_FIELDS) — never clinical data.
"""
import hashlib

from django.conf import settings
from django.utils.module_loading import import_string

from .models import BiometricTemplate


class BiometricProvider:
    """Interface every biometric backend must implement."""

    def make_template_hash(self, sample):
        raise NotImplementedError

    def enrol(self, patient, sample):
        """Store (or replace) the patient's template. Returns the record."""
        template_hash = self.make_template_hash(sample)
        record, _ = BiometricTemplate.objects.update_or_create(
            patient=patient, defaults={'template_hash': template_hash})
        return record

    def identify(self, sample):
        """Return the matched Patient or None."""
        template_hash = self.make_template_hash(sample)
        record = (BiometricTemplate.objects
                  .filter(template_hash=template_hash)
                  .select_related('patient').first())
        return record.patient if record else None


class HashBiometricProvider(BiometricProvider):
    """Simulator / exact-template backend: SHA-256 of the sample string."""

    def make_template_hash(self, sample):
        return hashlib.sha256(sample.strip().encode('utf-8')).hexdigest()


def get_provider():
    path = getattr(settings, 'BIOMETRIC_PROVIDER',
                   'patients.biometrics.HashBiometricProvider')
    return import_string(path)()
