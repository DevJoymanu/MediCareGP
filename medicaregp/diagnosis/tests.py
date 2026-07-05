"""Tests for the provisional-diagnosis engine and its RBAC boundary."""
import json
import re
from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from consultations.icd10_data import ICD10_CODES
from consultations.models import Consultation
from patients.models import Patient

from diagnosis import engine
from diagnosis.models import Condition, DifferentialResult, Symptom
from diagnosis.seed_data import CONDITIONS


def make_patient(**overrides):
    defaults = dict(
        first_name='Thabo', last_name='Mokoena', date_of_birth=date(1980, 5, 10),
        gender='M', id_number='8005105800085', phone='0821234567',
        chronic_conditions='Hypertension', smoking_status='Current',
    )
    defaults.update(overrides)
    return Patient.objects.create(**defaults)


def make_doctor():
    user = User.objects.create_user('doc', password='pw')
    user.groups.add(Group.objects.get(name='Doctor'))
    return user


def make_receptionist():
    user = User.objects.create_user('reception', password='pw')
    user.groups.add(Group.objects.get(name='Reception'))
    return user


class KnowledgeBaseSeedTests(TestCase):
    def test_seed_loaded(self):
        self.assertGreaterEqual(Condition.objects.count(), 40)
        self.assertGreater(Symptom.objects.count(), 50)

    def test_every_condition_has_valid_icd10(self):
        """Acceptance: each suggestion carries a valid ICD-10 code."""
        valid_codes = {code for code, _ in ICD10_CODES}
        icd10_shape = re.compile(r'^[A-Z]\d{2}(\.\d{1,2})?$')
        for condition in Condition.objects.all():
            self.assertRegex(condition.icd10_code, icd10_shape)
            self.assertIn(condition.icd10_code, valid_codes,
                          f'{condition.name}: {condition.icd10_code} not in ICD10_CODES')

    def test_seed_data_matches_db(self):
        self.assertEqual(Condition.objects.count(), len(CONDITIONS))


class EngineTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.fever = Symptom.objects.get(name='Fever').id
        self.cough = Symptom.objects.get(name='Cough').id
        self.sob = Symptom.objects.get(name='Shortness of breath').id
        self.wheeze = Symptom.objects.get(name='Wheeze').id

    def test_deterministic_identical_inputs_identical_ranking(self):
        """Acceptance: same inputs ALWAYS give the same ranked output."""
        run1 = engine.run_differential(self.patient, [self.fever, self.cough], [self.sob])
        run2 = engine.run_differential(self.patient, [self.fever, self.cough], [self.sob])
        self.assertEqual(run1, run2)
        # Order of ids within a bucket must not matter either
        run3 = engine.run_differential(self.patient, [self.cough, self.fever], [self.sob])
        self.assertEqual(run1, run3)

    def test_output_titled_provisional_never_final(self):
        out = engine.run_differential(self.patient, [self.fever], [])
        self.assertEqual(out['title'], 'Provisional Diagnosis')
        self.assertNotIn('final', str(out).lower())

    def test_top_10_limit(self):
        all_ids = list(Symptom.objects.values_list('id', flat=True))
        out = engine.run_differential(self.patient, all_ids, [])
        self.assertLessEqual(len(out['results']), 10)

    def test_constants_visible_in_output(self):
        """Acceptance: 70/30 weighting is a named constant, visible in output."""
        out = engine.run_differential(self.patient, [self.fever], [])
        self.assertEqual(out['constants']['history_weight'], '0.70')
        self.assertEqual(out['constants']['presenting_weight'], '0.30')
        self.assertEqual(str(engine.HISTORY_WEIGHT), '0.70')

    def test_history_bucket_weighs_more(self):
        """The same symptom scores higher as a working complaint (70%) than
        as a presenting symptom (30%)."""
        as_presenting = engine.run_differential(self.patient, [self.wheeze], [])
        as_working = engine.run_differential(self.patient, [], [self.wheeze])
        top_p = next(r for r in as_presenting['results'] if r['icd10_code'] == 'J45.9')
        top_w = next(r for r in as_working['results'] if r['icd10_code'] == 'J45.9')
        self.assertGreater(float(top_w['score']), float(top_p['score']))

    def test_history_modifiers_confirm_and_contradict(self):
        """Smoker vs never-smoker changes COPD score via explicit rules; the
        factors are labelled confirming/contradicting in the breakdown."""
        smoker = self.patient  # Current smoker, 45yrs
        never = make_patient(id_number='9001015800086', smoking_status='Never',
                             date_of_birth=date(1990, 1, 1), chronic_conditions='')
        out_smoker = engine.run_differential(smoker, [self.sob, self.wheeze], [])
        out_never = engine.run_differential(never, [self.sob, self.wheeze], [])
        copd_smoker = next(r for r in out_smoker['results'] if r['icd10_code'] == 'J44.9')
        copd_never = next((r for r in out_never['results'] if r['icd10_code'] == 'J44.9'), None)
        if copd_never is not None:
            self.assertGreater(float(copd_smoker['score']), float(copd_never['score']))
        kinds = {f['kind'] for f in copd_smoker['breakdown']['history_factors']}
        self.assertIn('confirming', kinds)

    def test_contradicting_factor_reported(self):
        """A male patient's dysmenorrhoea is suppressed by the sex=M rule."""
        painful_periods = Symptom.objects.get(name='Painful periods').id
        out = engine.run_differential(self.patient, [painful_periods], [painful_periods])
        codes = [r['icd10_code'] for r in out['results']]
        self.assertNotIn('N94.6', codes)  # score driven <= 0 by -10 contradiction

    def test_needs_more_data_flag(self):
        out = engine.run_differential(self.patient, [self.fever], [])
        self.assertTrue(out['needs_more_data'])
        out = engine.run_differential(self.patient, [self.fever, self.cough], [self.sob])
        self.assertFalse(out['needs_more_data'])

    def test_every_result_has_score_breakdown(self):
        out = engine.run_differential(self.patient, [self.fever, self.cough], [self.sob])
        for r in out['results']:
            self.assertTrue(r['why'])
            self.assertIn('formula', r['breakdown'])
            self.assertIn(str(engine.HISTORY_WEIGHT), r['breakdown']['formula'])


class FirstOccurrenceTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.headache = Symptom.objects.get(name='Headache')

    def test_new_symptom_flagged(self):
        flags = engine.first_occurrence_flags(self.patient, [self.headache.id])
        self.assertEqual(len(flags), 1)
        self.assertIn('First recorded headache', flags[0]['message'])

    def test_symptom_in_prior_narrative_not_flagged(self):
        Consultation.objects.create(patient=self.patient, chief_complaint='Recurring headache for 2 weeks')
        flags = engine.first_occurrence_flags(self.patient, [self.headache.id])
        self.assertEqual(flags, [])

    def test_symptom_in_prior_engine_run_not_flagged(self):
        consult = Consultation.objects.create(patient=self.patient)
        DifferentialResult.objects.create(
            consultation=consult, patient=self.patient, engine_version='1.0',
            inputs={'presenting_symptom_ids': [self.headache.id], 'working_symptom_ids': []},
            output={})
        flags = engine.first_occurrence_flags(self.patient, [self.headache.id])
        self.assertEqual(flags, [])


class DiagnosisRBACTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.consultation = Consultation.objects.create(patient=self.patient)
        self.doctor = make_doctor()
        self.receptionist = make_receptionist()
        self.capture_url = reverse('differential_capture', args=[self.consultation.pk])

    def test_receptionist_gets_403(self):
        """Acceptance: receptionist hitting a diagnosis endpoint gets 403."""
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(self.capture_url).status_code, 403)
        result = DifferentialResult.objects.create(
            consultation=self.consultation, patient=self.patient,
            engine_version='1.0', inputs={}, output={'results': []})
        self.assertEqual(self.client.get(reverse('differential_result', args=[result.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('differential_confirm', args=[result.pk])).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.capture_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_doctor_can_capture_and_confirm(self):
        self.client.force_login(self.doctor)
        self.assertEqual(self.client.get(self.capture_url).status_code, 200)

        fever = Symptom.objects.get(name='Fever').id
        cough = Symptom.objects.get(name='Cough').id
        sob = Symptom.objects.get(name='Shortness of breath').id
        response = self.client.post(self.capture_url, {'presenting': [fever, cough], 'working': [sob]})
        self.assertEqual(response.status_code, 302)
        result = DifferentialResult.objects.latest('created_at')

        page = self.client.get(reverse('differential_result', args=[result.pk]))
        self.assertContains(page, 'Likely Diagnoses')  # Simplified UI title
        self.assertNotContains(page, 'Final Diagnosis')

        top = result.output['results'][0]
        self.client.post(reverse('differential_confirm', args=[result.pk]),
                         {'confirm': [top['condition_id']]})
        self.consultation.refresh_from_db()
        codes = [e['code'] for e in self.consultation.icd10_codes_list]
        self.assertIn(top['icd10_code'], codes)


class WorkspaceTests(TestCase):
    """The single-screen consultation workspace + its JSON endpoints."""

    def setUp(self):
        self.patient = make_patient()
        self.consultation = Consultation.objects.create(patient=self.patient)
        self.doctor = make_doctor()
        self.receptionist = make_receptionist()
        self.ws_url      = reverse('diagnosis_workspace', args=[self.consultation.pk])
        self.run_url     = reverse('workspace_run', args=[self.consultation.pk])
        self.confirm_url = reverse('workspace_confirm', args=[self.consultation.pk])
        self.notes_url   = reverse('workspace_save_notes', args=[self.consultation.pk])
        self.icd_url     = reverse('icd10_search')

    def _post_json(self, url, payload):
        return self.client.post(url, json.dumps(payload), content_type='application/json')

    # ── RBAC ──────────────────────────────────────────────────────────────
    def test_receptionist_gets_403_everywhere(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(self.ws_url).status_code, 403)
        self.assertEqual(self._post_json(self.run_url, {'presenting': []}).status_code, 403)
        self.assertEqual(self._post_json(self.confirm_url, {'promoted': []}).status_code, 403)
        self.assertEqual(self._post_json(self.notes_url, {}).status_code, 403)
        self.assertEqual(self.client.get(self.icd_url + '?q=asthma').status_code, 403)

    def test_anonymous_redirected(self):
        response = self.client.get(self.ws_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    # ── Workspace page ────────────────────────────────────────────────────
    def test_workspace_renders_for_doctor(self):
        self.client.force_login(self.doctor)
        page = self.client.get(self.ws_url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Thabo')
        self.assertContains(page, 'kb-symptoms')          # knowledge base shipped to client
        self.assertContains(page, 'Confirm provisional')  # never "final"
        self.assertNotContains(page, 'Final Diagnosis')

    # ── Run endpoint ──────────────────────────────────────────────────────
    def test_run_creates_audit_result_and_returns_output(self):
        self.client.force_login(self.doctor)
        fever = Symptom.objects.get(name='Fever').id
        cough = Symptom.objects.get(name='Cough').id
        response = self._post_json(self.run_url, {
            'presenting': [fever, cough], 'working': [], 'notes': 'workspace run'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('result_id', data)
        self.assertEqual(data['output']['title'], 'Provisional Diagnosis')
        result = DifferentialResult.objects.get(pk=data['result_id'])
        self.assertEqual(result.consultation, self.consultation)
        self.assertEqual(result.inputs['notes'], 'workspace run')
        self.assertIsNone(result.confirmed_at)   # runs are unconfirmed by default

    def test_run_with_no_symptoms_is_400(self):
        self.client.force_login(self.doctor)
        response = self._post_json(self.run_url, {'presenting': [], 'working': []})
        self.assertEqual(response.status_code, 400)

    # ── Confirm endpoint: frozen snapshot ─────────────────────────────────
    def _make_run(self):
        self.client.force_login(self.doctor)
        wheeze = Symptom.objects.get(name='Wheeze').id
        sob = Symptom.objects.get(name='Shortness of breath').id
        data = self._post_json(self.run_url, {'presenting': [wheeze, sob], 'working': []}).json()
        return data

    def test_confirm_engine_dx_freezes_snapshot_and_writes_codes(self):
        run = self._make_run()
        top = run['output']['results'][0]
        response = self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': top['icd10_code'], 'name': top['condition'], 'source': 'engine'}],
        })
        self.assertEqual(response.status_code, 200)
        self.consultation.refresh_from_db()
        codes = [e['code'] for e in self.consultation.icd10_codes_list]
        self.assertIn(top['icd10_code'], codes)

        result = DifferentialResult.objects.get(pk=run['result_id'])
        self.assertIsNotNone(result.confirmed_at)
        self.assertEqual(result.confirmed_dx[0]['code'], top['icd10_code'])
        # Snapshot output untouched by confirmation (frozen).
        self.assertEqual(result.output, run['output'])

    def test_confirm_offlist_manual_code(self):
        run = self._make_run()
        response = self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': 'A01.0', 'name': '', 'source': 'manual'}],
        })
        self.assertEqual(response.status_code, 200)
        self.consultation.refresh_from_db()
        entry = next(e for e in self.consultation.icd10_codes_list if e['code'] == 'A01.0')
        self.assertEqual(entry['description'], 'Typhoid fever')   # name from ICD10_CODES
        result = DifferentialResult.objects.get(pk=run['result_id'])
        self.assertEqual(result.confirmed_dx[0]['source'], 'manual')

    def test_confirm_rejects_unknown_manual_code(self):
        run = self._make_run()
        response = self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': 'ZZ99.9', 'name': 'Made up', 'source': 'manual'}],
        })
        self.assertEqual(response.status_code, 400)

    def test_confirm_rejects_engine_code_not_in_run(self):
        run = self._make_run()
        response = self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': 'A01.0', 'name': 'Typhoid', 'source': 'engine'}],
        })
        self.assertEqual(response.status_code, 400)

    def test_confirm_requires_promoted(self):
        run = self._make_run()
        response = self._post_json(self.confirm_url, {'result_id': run['result_id'], 'promoted': []})
        self.assertEqual(response.status_code, 400)

    # ── Details view renders the frozen snapshot ──────────────────────────
    def test_detail_shows_reasoning_snapshot(self):
        run = self._make_run()
        top = run['output']['results'][0]
        self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': top['icd10_code'], 'name': top['condition'], 'source': 'engine'}],
        })
        page = self.client.get(reverse('consultation_detail', args=[self.consultation.pk]))
        self.assertContains(page, 'Diagnosis reasoning')
        self.assertContains(page, 'frozen snapshot')
        self.assertContains(page, top['icd10_code'])

    # ── Notes save ────────────────────────────────────────────────────────
    def test_notes_save_updates_fields(self):
        self.client.force_login(self.doctor)
        response = self._post_json(self.notes_url, {
            'chief_complaint': 'Wheezy chest', 'subjective': 'Two days of wheeze', 'plan': 'Salbutamol'})
        self.assertEqual(response.status_code, 200)
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.chief_complaint, 'Wheezy chest')
        self.assertEqual(self.consultation.plan, 'Salbutamol')

    # ── ICD-10 search ─────────────────────────────────────────────────────
    def test_icd10_search(self):
        self.client.force_login(self.doctor)
        data = self.client.get(self.icd_url + '?q=a01').json()
        self.assertTrue(any(r['code'] == 'A01.0' for r in data['results']))
        data = self.client.get(self.icd_url + '?q=typhoid').json()
        self.assertTrue(any('Typhoid' in r['description'] for r in data['results']))
        self.assertEqual(self.client.get(self.icd_url + '?q=a').json()['results'], [])

    # ── Body regions seeded ───────────────────────────────────────────────
    def test_body_regions_assigned(self):
        self.assertEqual(Symptom.objects.get(name='Headache').body_region, 'head')
        self.assertEqual(Symptom.objects.get(name='Wheeze').body_region, 'chest')
        self.assertEqual(Symptom.objects.get(name='Fever').body_region, 'general')
        self.assertFalse(Symptom.objects.filter(body_region='').exists())

    # ── Create-flow integration ───────────────────────────────────────────
    def test_confirm_completes_linked_appointment(self):
        from datetime import time as dtime
        from appointments.models import Appointment
        from django.utils import timezone
        apt = Appointment.objects.create(
            patient=self.patient, date=timezone.localdate(), time=dtime(10, 0),
            reason='Wheeze', status='With Doctor')
        self.consultation.appointment = apt
        self.consultation.save()

        run = self._make_run()
        top = run['output']['results'][0]
        self._post_json(self.confirm_url, {
            'result_id': run['result_id'],
            'promoted': [{'code': top['icd10_code'], 'name': top['condition'], 'source': 'engine'}],
        })
        apt.refresh_from_db()
        self.assertEqual(apt.status, 'Completed')

    def test_notes_save_includes_vitals(self):
        self.client.force_login(self.doctor)
        response = self._post_json(self.notes_url, {'bp_reading': '120/80', 'weight_kg': '72.5'})
        self.assertEqual(response.status_code, 200)
        self.consultation.refresh_from_db()
        self.assertEqual(self.consultation.bp_reading, '120/80')
        self.assertEqual(str(self.consultation.weight_kg), '72.5')

    def test_notes_save_rejects_bad_weight(self):
        self.client.force_login(self.doctor)
        response = self._post_json(self.notes_url, {'weight_kg': 'heavy'})
        self.assertEqual(response.status_code, 400)
