"""
MedicalAidGateway — the single internal interface for talking DIRECTLY to
medical aid schemes (no third-party claims switch).

Calling code (billing views, front office) only ever sees this interface and
its result dataclasses. Everything scheme-specific — protocol (REST / SOAP /
X12 EDI / portal-only), payload mapping, auth — lives inside one adapter per
scheme (medaid/adapters/). Adding a new medical aid means writing ONE new
adapter class + a SchemeConfig row; no calling code changes.

Privacy: adapters receive claims exclusively from ClaimBuilder
(medaid/claim_builder.py), which whitelists non-clinical billing fields.
Clinical notes can never reach a scheme because they never enter the
gateway boundary.
"""
from dataclasses import dataclass, field


@dataclass
class MemberDetails:
    verified: bool
    scheme_name: str
    member_number: str = ''
    plan: str = ''
    dependant_code: str = ''
    message: str = ''


@dataclass
class EligibilityResult:
    eligible: bool
    scheme_name: str
    message: str = ''
    benefits: dict = field(default_factory=dict)


@dataclass
class ClaimResult:
    submitted: bool
    scheme_name: str
    reference: str = ''
    message: str = ''
    requires_manual_action: bool = False


@dataclass
class RemittanceResult:
    found: bool
    scheme_name: str
    status: str = ''
    amount_paid: str = ''
    message: str = ''


class MedicalAidGateway:
    """Interface every scheme adapter implements."""

    def __init__(self, config):
        self.config = config   # SchemeConfig — credentials resolved from env at call time

    def verify_member(self, member_number, id_number=''):
        raise NotImplementedError

    def check_eligibility(self, member_number, service_date):
        raise NotImplementedError

    def submit_claim(self, claim_payload):
        """claim_payload MUST come from ClaimBuilder.build() — never build
        payloads by hand."""
        raise NotImplementedError

    def get_remittance(self, reference):
        raise NotImplementedError
