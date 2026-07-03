"""
Deterministic, rule-based differential-diagnosis engine.

NOT artificial intelligence: no model, no randomness, no external calls.
Pure weighted scoring over the admin-editable knowledge base — the same
inputs ALWAYS produce the same ranked output (there is a test asserting
this). Output is clinical decision support only and is always labelled
"Provisional Diagnosis" — the doctor confirms or rejects it.

Scoring (documented constants below):

    history_bucket     = Σ weights of matched WORKING complaints
                         + Σ deltas of matched history-modifier rules
    presenting_bucket  = Σ weights of matched PRESENTING symptoms

    score = HISTORY_WEIGHT * history_bucket + PRESENTING_WEIGHT * presenting_bucket

History + working complaints carry ~70% of the total score weight;
presenting symptoms carry the remaining 30%. Ties are broken
alphabetically by ICD-10 code, then name — never arbitrarily.
"""
from decimal import Decimal, ROUND_HALF_UP

from .models import Condition, DifferentialResult, HistoryModifierRule, Symptom

ENGINE_VERSION = '1.0'

# ── Fixed, documented scoring constants ──────────────────────────────────────
HISTORY_WEIGHT    = Decimal('0.70')   # history + working complaints share
PRESENTING_WEIGHT = Decimal('0.30')   # presenting symptoms share
TOP_N             = 10                # size of the returned differential
MIN_INPUTS        = 3                 # below this, prompt the doctor for more data

# Likelihood bands from fixed absolute score thresholds (weights are 1–10).
BAND_HIGH   = Decimal('6.0')
BAND_MEDIUM = Decimal('3.0')

OUTPUT_TITLE = 'Provisional Diagnosis'   # never "Final"


def _q(value):
    """Quantise to 2 decimal places, deterministic rounding."""
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _band(score):
    if score >= BAND_HIGH:
        return 'High'
    if score >= BAND_MEDIUM:
        return 'Medium'
    return 'Low'


def _age_in_band(age, match_value):
    """match_value like '0-5' or '50-120' (inclusive)."""
    try:
        lo, hi = match_value.split('-')
        return int(lo) <= age <= int(hi)
    except (ValueError, AttributeError):
        return False


def match_history_rule(rule, patient, prior_condition_codes):
    """Return True if a HistoryModifierRule matches this patient's stored
    history. Every factor type is an explicit, documented comparison."""
    if rule.factor == 'age_band':
        return _age_in_band(patient.get_age(), rule.match_value)
    if rule.factor == 'sex':
        return patient.gender == (rule.match_value or '').strip().upper()[:1]
    if rule.factor == 'chronic':
        needle = (rule.match_value or '').strip().lower()
        return bool(needle) and any(needle in c.lower() for c in patient.chronic_list())
    if rule.factor == 'prior_episode':
        return rule.condition.icd10_code in prior_condition_codes
    if rule.factor == 'smoking':
        return (patient.smoking_status or '') == rule.match_value
    if rule.factor == 'alcohol':
        return (patient.alcohol_use or '') == rule.match_value
    return False


def prior_icd10_codes(patient):
    """Set of ICD-10 codes recorded on the patient's past consultations."""
    codes = set()
    for consult in patient.consultations.all():
        for entry in consult.icd10_codes_list:
            code = (entry.get('code') or '').strip()
            if code:
                codes.add(code)
    return codes


def first_occurrence_flags(patient, symptom_ids, exclude_consultation=None):
    """General first-occurrence rule: a symptom is flagged if it has never
    been recorded for this patient before — neither in a prior structured
    engine run nor mentioned in a prior consultation's narrative fields.
    """
    symptoms = Symptom.objects.filter(id__in=symptom_ids)

    prior_runs = DifferentialResult.objects.filter(patient=patient)
    if exclude_consultation is not None:
        prior_runs = prior_runs.exclude(consultation=exclude_consultation)
    seen_ids = set()
    for run in prior_runs:
        seen_ids.update(run.inputs.get('presenting_symptom_ids', []))
        seen_ids.update(run.inputs.get('working_symptom_ids', []))

    consults = patient.consultations.all()
    if exclude_consultation is not None:
        consults = consults.exclude(pk=exclude_consultation.pk)
    narrative = ' '.join(
        ' '.join(filter(None, [c.chief_complaint, c.subjective, c.assessment, c.differential_diagnosis]))
        for c in consults
    ).lower()

    flags = []
    for s in symptoms.order_by('name'):
        if s.id in seen_ids:
            continue
        names = [s.name] + [x.strip() for x in (s.synonyms or '').split(',') if x.strip()]
        if any(n.lower() in narrative for n in names):
            continue
        flags.append({'symptom_id': s.id, 'symptom': s.name,
                      'message': f'First recorded {s.name.lower()} for this patient.'})
    return flags


def run_differential(patient, presenting_symptom_ids, working_symptom_ids, notes=''):
    """Score every active condition against the captured symptoms + stored
    history and return the ranked top-{TOP_N} provisional-diagnosis list.

    Deterministic: querysets are explicitly ordered, arithmetic is Decimal,
    and ties break on (ICD-10 code, name).
    """
    presenting_ids = sorted(set(int(i) for i in presenting_symptom_ids))
    working_ids    = sorted(set(int(i) for i in working_symptom_ids) - set(presenting_ids))

    symptom_names = dict(Symptom.objects.filter(
        id__in=presenting_ids + working_ids).values_list('id', 'name'))
    prior_codes = prior_icd10_codes(patient)

    results = []
    conditions = (Condition.objects.filter(active=True)
                  .prefetch_related('symptom_links__symptom', 'history_rules')
                  .order_by('icd10_code', 'name'))

    for condition in conditions:
        links = {l.symptom_id: l for l in condition.symptom_links.all()}

        presenting_matches = [
            {'symptom': symptom_names[sid], 'weight': links[sid].weight}
            for sid in presenting_ids if sid in links
        ]
        working_matches = [
            {'symptom': symptom_names[sid], 'weight': links[sid].weight}
            for sid in working_ids if sid in links
        ]

        history_factors = []
        for rule in sorted(condition.history_rules.all(), key=lambda r: (r.factor, r.match_value, r.id)):
            if not rule.active:
                continue
            if match_history_rule(rule, patient, prior_codes):
                history_factors.append({
                    'factor': rule.get_factor_display().split(' (')[0],
                    'match': rule.match_value,
                    'delta': rule.delta,
                    'kind': 'confirming' if rule.delta >= 0 else 'contradicting',
                    'note': rule.note or '',
                })

        presenting_raw = sum(m['weight'] for m in presenting_matches)
        working_raw    = sum(m['weight'] for m in working_matches)
        history_delta  = sum(f['delta'] for f in history_factors)

        if not presenting_matches and not working_matches:
            continue   # condition has no symptom evidence at all

        history_bucket    = Decimal(working_raw + history_delta)
        presenting_bucket = Decimal(presenting_raw)
        score = _q(HISTORY_WEIGHT * history_bucket + PRESENTING_WEIGHT * presenting_bucket)
        if score <= 0:
            continue

        why_parts = []
        if presenting_matches:
            why_parts.append('presenting: ' + ', '.join(
                f"{m['symptom']} (+{m['weight']})" for m in presenting_matches))
        if working_matches:
            why_parts.append('working/history complaints: ' + ', '.join(
                f"{m['symptom']} (+{m['weight']})" for m in working_matches))
        for f in history_factors:
            sign = '+' if f['delta'] >= 0 else ''
            why_parts.append(f"{f['kind']} history factor: {f['note'] or f['factor']} ({sign}{f['delta']})")

        results.append({
            'condition_id': condition.id,
            'condition': condition.name,
            'icd10_code': condition.icd10_code,
            'score': str(score),
            'band': _band(score),
            'why': '; '.join(why_parts),
            'breakdown': {
                'presenting_matches': presenting_matches,
                'working_matches': working_matches,
                'history_factors': history_factors,
                'presenting_raw': presenting_raw,
                'working_raw': working_raw,
                'history_delta': history_delta,
                'formula': (
                    f'{HISTORY_WEIGHT} × (working {working_raw} + history {history_delta}) '
                    f'+ {PRESENTING_WEIGHT} × presenting {presenting_raw} = {score}'
                ),
            },
        })

    results.sort(key=lambda r: (-Decimal(r['score']), r['icd10_code'], r['condition']))
    ranked = results[:TOP_N]
    for i, r in enumerate(ranked, start=1):
        r['rank'] = i

    total_inputs = len(presenting_ids) + len(working_ids)
    return {
        'title': OUTPUT_TITLE,
        'engine_version': ENGINE_VERSION,
        'constants': {
            'history_weight': str(HISTORY_WEIGHT),
            'presenting_weight': str(PRESENTING_WEIGHT),
            'band_high': str(BAND_HIGH),
            'band_medium': str(BAND_MEDIUM),
        },
        'needs_more_data': total_inputs < MIN_INPUTS,
        'input_count': total_inputs,
        'results': ranked,
        'notes': notes or '',
    }


def suggest_more_symptoms(output, presenting_ids, working_ids, limit=8):
    """Deterministic 'ask for more data' helper: for the current top
    candidates, list their highest-weighted knowledge-base symptoms not yet
    captured — the discriminating questions worth asking next."""
    selected = set(presenting_ids) | set(working_ids)
    top_condition_ids = [r['condition_id'] for r in output['results'][:5]]
    if not top_condition_ids:
        return []
    from .models import SymptomConditionLink
    links = (SymptomConditionLink.objects
             .filter(condition_id__in=top_condition_ids, symptom__active=True)
             .exclude(symptom_id__in=selected)
             .select_related('symptom', 'condition')
             .order_by('-weight', 'symptom__name', 'condition__icd10_code'))
    seen, suggestions = set(), []
    for link in links:
        if link.symptom_id in seen:
            continue
        seen.add(link.symptom_id)
        suggestions.append({
            'symptom_id': link.symptom_id,
            'symptom': link.symptom.name,
            'hint': f'would support {link.condition.name} (weight {link.weight})',
        })
        if len(suggestions) >= limit:
            break
    return suggestions
