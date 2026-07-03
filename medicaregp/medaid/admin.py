from django.contrib import admin

from .models import SchemeConfig


@admin.register(SchemeConfig)
class SchemeConfigAdmin(admin.ModelAdmin):
    list_display = ['scheme_name', 'adapter', 'endpoint_url', 'active']
    list_filter = ['adapter', 'active']
    search_fields = ['scheme_name']
    fieldsets = [
        (None, {'fields': ['scheme_name', 'adapter', 'endpoint_url', 'active', 'notes']}),
        ('Credential environment variables (names only — values live in the environment)', {
            'fields': ['username_env', 'password_env', 'api_key_env'],
        }),
    ]
