from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from rest_framework.fields import HiddenField

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


class EvaluateRulesRequestSerializer(serializers.Serializer):
    rules = serializers.ListField(child=serializers.CharField())
    payload = serializers.DictField()

    def validate_rules(self, value: str) -> str:
        # Get all rules
        valid_names = set(Rule.objects.values_list("name", flat=True))
        # Find invalid rules
        invalid = [name for name in value if name not in valid_names]
        if invalid:
            raise serializers.ValidationError(f"Invalid rule names: {invalid}")  # noqa: TRY003, EM102
        return value


class EvaluateRulesResponseSerializer(serializers.Serializer):
    result = serializers.CharField()
    passed_rules = serializers.ListField(child=serializers.CharField())
    failed_rules = serializers.ListField(child=serializers.CharField())
