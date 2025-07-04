from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from rule_engine_api.rules.api.serializers import EvaluateRulesRequestSerializer
from rule_engine_api.rules.api.serializers import EvaluateRulesResponseSerializer
from rule_engine_api.rules.api.serializers import RuleSerializer
from rule_engine_api.rules.models import Rule
from rule_engine_api.rules.rule_engine import evaluate_condition

User = get_user_model()


class RulePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.user_role == User.RoleChoice.ADMIN.value


class EvaluatePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.user_role in [
            User.RoleChoice.ADMIN.value,
            User.RoleChoice.CLIENT.value,
        ]


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [RulePermission]


# ChatGPT solution.
class EvaluateRulesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [EvaluatePermission]

    @extend_schema(
        request=EvaluateRulesRequestSerializer,
        responses=EvaluateRulesResponseSerializer,
        tags=["Rules"],
    )
    def post(self, request):
        serializer = EvaluateRulesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule_names = serializer.validated_data["rules"]
        payload = serializer.validated_data["payload"]

        passed_rules = []
        failed_rules = []

        for rule in Rule.objects.filter(name__in=rule_names, is_active=True):
            try:
                if evaluate_condition(rule.condition, payload):
                    passed_rules.append(rule.name)
                else:
                    failed_rules.append(rule.name)
            except Exception:  # noqa: BLE001
                failed_rules.append(rule.name)

        result = "APPROVED" if not failed_rules else "REJECTED"

        return Response(
            {
                "result": result,
                "passed_rules": passed_rules,
                "failed_rules": failed_rules,
            },
        )
