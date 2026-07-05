"""Scheme simulator scaffolding — same contract as a real adapter.

Copy to medicaregp/medaid/adapters/simulator.py, subclass per scheme if
their behaviors diverge, and gate injection in get_gateway() behind
settings.MEDAID_SIMULATE (with the production startup guard).
"""
from medaid.gateway import (ClaimResult, EligibilityResult, MedicalAidGateway,
                            MemberDetails, RemittanceResult)

# Member-number prefixes reception/QA can type to force each path.
SCENARIO_PREFIXES = {
    'SIM-OK':      'approved',
    'SIM-DENY':    'denied',
    'SIM-NOMEM':   'member_not_found',
    'SIM-INEL':    'ineligible',
    'SIM-PARTIAL': 'partial_cover',
    'SIM-SLOW':    'upstream_timeout',
    'SIM-500':     'malformed_response',
}


class SchemeSimulator(MedicalAidGateway):
    """Deterministic fake: outcome derives from the member number prefix,
    or from a forced `scenario` passed at construction (tests)."""

    def __init__(self, config=None, scenario=None):
        self.config = config
        self.forced_scenario = scenario

    def _scenario(self, member_number):
        if self.forced_scenario:
            return self.forced_scenario
        for prefix, scenario in SCENARIO_PREFIXES.items():
            if str(member_number).upper().startswith(prefix):
                return scenario
        return 'approved'    # unprefixed synthetic members behave normally

    # ── Contract implementation ───────────────────────────────────────────

    def verify_member(self, member_number, id_number=''):
        scenario = self._scenario(member_number)
        if scenario == 'member_not_found':
            return MemberDetails(found=False, status='member_not_found',
                                 message='[SIM] Member number not recognised.')
        if scenario == 'upstream_timeout':
            return MemberDetails(found=False, status='upstream_down',
                                 message='[SIM] Scheme not responding.')
        if scenario == 'malformed_response':
            return MemberDetails(found=False, status='malformed_response',
                                 message='[SIM] Scheme returned an unreadable response.')
        return MemberDetails(found=True, status='active',
                             member_number=member_number,
                             first_name='Sim', last_name='Member',
                             plan='Simulated Plan')

    def check_eligibility(self, member_number, service_date):
        scenario = self._scenario(member_number)
        table = {
            'approved':      ('eligible',        '[SIM] Fully covered.'),
            'partial_cover': ('partial',         '[SIM] 60% covered; balance to patient.'),
            'ineligible':    ('ineligible',      '[SIM] Benefit exhausted for this year.'),
            'member_not_found': ('member_not_found', '[SIM] Member number not recognised.'),
            'denied':        ('eligible',        '[SIM] Eligible (claim will deny).'),
            'upstream_timeout': ('upstream_down', '[SIM] Scheme not responding.'),
            'malformed_response': ('malformed_response', '[SIM] Unreadable response.'),
        }
        status, message = table[scenario]
        return EligibilityResult(status=status, message=message)

    def submit_claim(self, claim_payload):
        member = (claim_payload.get('patient') or {}).get('member_number', '')
        scenario = self._scenario(member)
        if scenario == 'denied':
            return ClaimResult(status='denied', reference='',
                               message='[SIM] Denied: service code not covered on this option.')
        if scenario == 'upstream_timeout':
            return ClaimResult(status='upstream_down', reference='',
                               message='[SIM] Scheme unreachable — queue manually.')
        if scenario == 'malformed_response':
            return ClaimResult(status='malformed_response', reference='',
                               message='[SIM] Unreadable scheme response.')
        reference = 'SIMREF-' + str(claim_payload.get('claim_number', ''))[-8:]
        return ClaimResult(status='accepted', reference=reference,
                           message='[SIM] Claim accepted.')

    def get_remittance(self, reference):
        return RemittanceResult(status='paid', reference=reference,
                                message='[SIM] Paid in full.')


# ── Factory injection (in medaid/adapters/__init__.py) ─────────────────────
#
# def get_gateway(scheme_name):
#     if getattr(settings, 'MEDAID_SIMULATE', False):
#         return SchemeSimulator()
#     ...existing resolution...
#
# ── Production guard (system check) ────────────────────────────────────────
#
# @register()
# def simulation_not_in_prod(app_configs, **kwargs):
#     if getattr(settings, 'MEDAID_SIMULATE', False) and not settings.DEBUG \
#             and os.getenv('RAILWAY_ENVIRONMENT'):
#         return [Error('MEDAID_SIMULATE is on in production.', id='medaid.E001')]
#     return []
