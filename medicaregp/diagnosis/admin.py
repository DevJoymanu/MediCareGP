"""Admin for the diagnosis knowledge base — this is where the doctor tunes
conditions, symptom weights and history rules without a redeploy."""
from django.contrib import admin

from .models import (Condition, DifferentialResult, HistoryModifierRule,
                     Symptom, SymptomConditionLink)


class SymptomLinkInline(admin.TabularInline):
    model = SymptomConditionLink
    extra = 1
    autocomplete_fields = ['symptom']


class HistoryRuleInline(admin.TabularInline):
    model = HistoryModifierRule
    extra = 0


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'icd10_code', 'active']
    list_filter = ['active']
    search_fields = ['name', 'icd10_code']
    inlines = [SymptomLinkInline, HistoryRuleInline]


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'synonyms', 'active']
    list_filter = ['kind', 'active']
    search_fields = ['name', 'synonyms']


@admin.register(SymptomConditionLink)
class SymptomConditionLinkAdmin(admin.ModelAdmin):
    list_display = ['symptom', 'condition', 'weight', 'note']
    list_editable = ['weight']
    list_filter = ['condition']
    search_fields = ['symptom__name', 'condition__name']
    autocomplete_fields = ['symptom', 'condition']


@admin.register(HistoryModifierRule)
class HistoryModifierRuleAdmin(admin.ModelAdmin):
    list_display = ['condition', 'factor', 'match_value', 'delta', 'active', 'note']
    list_editable = ['delta', 'active']
    list_filter = ['factor', 'active']
    search_fields = ['condition__name']
    autocomplete_fields = ['condition']


@admin.register(DifferentialResult)
class DifferentialResultAdmin(admin.ModelAdmin):
    """Read-only audit trail of engine runs."""
    list_display = ['patient', 'consultation', 'engine_version', 'created_by', 'created_at']
    readonly_fields = ['consultation', 'patient', 'created_by', 'engine_version',
                       'inputs', 'output', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
