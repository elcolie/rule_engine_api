from rest_framework import serializers
from rest_framework.fields import HiddenField, CurrentUserDefault

from rule_engine_api.rules.models import Rule


class RuleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    condition = serializers.JSONField(required=True)
    is_active = serializers.BooleanField(required=True)
    created_by = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Rule
        fields = (
            "name",
            "condition",
            "is_active",
            "created_by",
        )
