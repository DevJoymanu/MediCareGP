"""Fallback adapter for schemes with no direct API: the claim is recorded
and queued for manual submission via the scheme's portal/email, so the rest
of the system behaves exactly as it does for API-connected schemes."""
from medaid.gateway import (ClaimResult, EligibilityResult, MedicalAidGateway,
                            MemberDetails, RemittanceResult)


class ManualAdapter(MedicalAidGateway):

    def _portal_hint(self):
        if self.config.endpoint_url:
            return f'Submit via the scheme portal: {self.config.endpoint_url}'
        return 'No direct API — submit via the scheme portal or contact the scheme.'

    def verify_member(self, member_number, id_number=''):
        return MemberDetails(
            verified=False,
            scheme_name=self.config.scheme_name,
            member_number=member_number,
            message=f'{self.config.scheme_name} has no direct API. '
                    f'Verify membership telephonically or on the portal. {self._portal_hint()}',
        )

    def check_eligibility(self, member_number, service_date):
        return EligibilityResult(
            eligible=False,
            scheme_name=self.config.scheme_name,
            message=f'Eligibility cannot be checked automatically. {self._portal_hint()}',
        )

    def submit_claim(self, claim_payload):
        """Record the claim on the invoice as pending manual submission."""
        from billing.models import ClaimSubmission, Invoice

        invoice = Invoice.objects.get(invoice_number=claim_payload['claim']['invoice_number'])
        reference = f"MANUAL-{claim_payload['claim']['invoice_number']}"
        ClaimSubmission.objects.get_or_create(
            invoice=invoice,
            scheme_name=self.config.scheme_name,
            submission_reference=reference,
            defaults={'status': 'Submitted',
                      'resubmission_notes': 'Queued for manual portal submission (no direct API).'},
        )
        return ClaimResult(
            submitted=True,
            scheme_name=self.config.scheme_name,
            reference=reference,
            requires_manual_action=True,
            message=f'Claim recorded for manual submission. {self._portal_hint()}',
        )

    def get_remittance(self, reference):
        return RemittanceResult(
            found=False,
            scheme_name=self.config.scheme_name,
            message='Remittances arrive by email/portal for this scheme — capture them via ERA import.',
        )
