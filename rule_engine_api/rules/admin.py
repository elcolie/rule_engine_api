from django.contrib import admin

from rule_engine_api.rules.models import Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    __fields = [
        "name",
        "condition",
        "is_active",
        "created_by",
        "created_at",
        "updated_at",
    ]
    list_display = ["id", *__fields]
