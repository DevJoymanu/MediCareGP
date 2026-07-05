---
name: integration-simulators
description: Deterministic simulators and contract tests for the GP CRM's medical-aid and comms integrations — build and QA scheme flows without live endpoints (schemes rarely offer sandboxes). Load this when writing integration tests for medaid, building or modifying a simulator/fake/mock for a scheme (CIMAS, PSMAS, First Mutual…), forcing failure scenarios (denied, timeout, member-not-found), or wiring the real-vs-simulated toggle. Companion to the api-integrations skill.
---

# Integration Simulators

The dev/test counterpart to `api-integrations`. Real scheme endpoints are scarce, slow, and stateful; the whole eligibility/claim UI must still be buildable and testable. The answer is **simulators that implement the exact same contract as real adapters**, driven by explicit scenarios.

## Core design

A simulator is just another adapter class — it implements `MedicalAidGateway` (`verify_member`, `check_eligibility`, `submit_claim`, `get_remittance`) and returns the same dataclasses (`MemberDetails`, `EligibilityResult`, `ClaimResult`, `RemittanceResult`). Because calling code only knows the interface, nothing upstream can tell it's fake — which is exactly what makes the tests honest.

Scaffolding to copy: `assets/simulator.py`.

## Scenario selection — deterministic, two channels

1. **Member-number convention** (best for manual QA — reception can type these):
   the member number's prefix picks the outcome. `SIM-OK-…` → approved, `SIM-DENY-…` → denied, `SIM-NOMEM-…` → member-not-found, `SIM-PARTIAL-…` → partial cover, `SIM-SLOW-…` → simulated timeout, `SIM-500-…` → malformed/5xx. Same input, same outcome, every time — no hidden state.
2. **Env/fixture override** (for tests that need a specific path regardless of input): `MEDAID_SIM_SCENARIO=denied` forces every call down one path; individual tests instantiate the simulator with `scenario='upstream_timeout'` directly.

Every scenario from the `api-integrations` error taxonomy must be reachable: approved, denied, member-not-found, ineligible, partial cover, upstream timeout, malformed/5xx. If the taxonomy grows, the simulator grows in the same PR.

## Real-vs-simulated toggle (nothing simulated ever ships)

Injection happens at the existing factory, `medaid/adapters/get_gateway()` — the single choke point:

- Setting: `MEDAID_SIMULATE` env var → `settings.MEDAID_SIMULATE` (default off). When on, `get_gateway()` returns the scheme's simulator regardless of `SchemeConfig`.
- **Production guard**: if simulation is on while `RAILWAY_ENVIRONMENT`/production settings are active, raise at startup (a Django system check is ideal). A clinic submitting pretend claims is a silent-disaster mode; make it impossible, not discouraged.
- The UI shows a visible banner when simulation is active ("SIMULATED SCHEME RESPONSES") so a QA session can never be mistaken for a live one.

## Contract tests — one assertion set, two targets

The drift killer: a single test class parameterized over the gateway. Run it against the simulator always; against the real endpoint when creds exist (skip otherwise):

```python
class GatewayContractMixin:
    """Same assertions for sim and real — shapes, statuses, invariants."""
    def test_verify_known_member_shape(self):
        result = self.gateway.verify_member(self.known_member)
        self.assertIsInstance(result, MemberDetails)
        self.assertIn(result.status, KNOWN_STATUSES)
    def test_unknown_member_maps_to_member_not_found(self): ...
    def test_claim_result_carries_reference_on_accept(self): ...

class SimulatorContractTests(GatewayContractMixin, TestCase):
    gateway = CimasSimulator(scenario_from='member_number')
    known_member = 'SIM-OK-001'

@skipUnless(os.getenv('CIMAS_API_KEY'), 'no live creds')
class LiveCimasContractTests(GatewayContractMixin, TestCase):
    gateway = get_gateway('CIMAS')          # real adapter
    known_member = os.getenv('CIMAS_TEST_MEMBER')
```

When the live run fails but the simulator passes, the **simulator is wrong** — update it to match reality, then fix whatever the change breaks. That's the feedback loop working.

These contract tests join the regression suite (`python manage.py test`) and run in CI like everything else — every scheme feature lands with its scenario tests.

## Record/replay (optional, use with care)

VCR-style cassettes are allowed for capturing real response *shapes*, with a hard rule: **scrub before saving** — member numbers, names, DOBs, addresses replaced with synthetic values by an allowlist scrubber (keep only fields you explicitly name). A cassette with real PHI in the repo is a breach, not a fixture. If scrubbing is uncertain, hand-write the fixture from the API docs instead.

## Fixture data

Synthetic only, always: invented names, `SIM-` member numbers, impossible-but-valid ID numbers. Never paste real patient records into fixtures, cassettes, or test assertions — test data lives in the repo and CI logs forever.
