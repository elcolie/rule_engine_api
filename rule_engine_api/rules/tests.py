from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from rule_engine_api.rules.models import Rule
from rule_engine_api.rules.rule_engine import evaluate_condition
from rule_engine_api.users.tests.test_user_roles import UserSetupTestCase


class RuleViewSetTest(UserSetupTestCase):
    def test_admin_post(self) -> None:
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-list")
        payload = {
            "name": "Age over 18",
            "condition": [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 18,
                },
            ],
            "is_active": True,
        }
        res = client.post(url, data=payload, format="json")
        first_rule = Rule.objects.first()
        assert res.status_code == status.HTTP_201_CREATED
        assert first_rule.name == "Age over 18"
        assert first_rule.condition == [
            {
                "field": "age",
                "operator": ">=",
                "value": 18,
            },
        ]
        assert first_rule.is_active is True
        assert first_rule.created_by == self.admin

    def test_admin_list_empty_list(self) -> None:
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-list")
        res = client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 0

    def test_admin_list_non_empty_list(self) -> None:
        Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin,
        )
        Rule.objects.create(
            name="Age not over 50",
            condition=[],
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-list")
        res = client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 2  # noqa: PLR2004

    def test_admin_get(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-detail", kwargs={"pk": first_rule.pk})
        res = client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert first_rule.name == res.data["name"]
        assert first_rule.condition == res.data["condition"]
        assert first_rule.is_active == res.data["is_active"]

    def test_admin_update(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-detail", kwargs={"pk": first_rule.pk})
        payload = {
            "name": "Age over 40",
            "condition": [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 40,
                },
            ],
            "is_active": False,
        }
        res = client.put(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK

        first_rule.refresh_from_db()
        assert first_rule.name == "Age over 40"
        assert first_rule.condition == [
            {
                "field": "age",
                "operator": ">=",
                "value": 40,
            },
        ]
        assert not first_rule.is_active

    def test_admin_delete(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-detail", kwargs={"pk": first_rule.pk})
        res = client.delete(url)
        assert res.status_code == status.HTTP_204_NO_CONTENT

    def test_anonymous_post(self) -> None:
        client = APIClient()
        url = reverse("api:rules-list")
        payload = {
            "name": "Age over 40",
            "condition": [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 40,
                },
            ],
            "is_active": False,
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_anonymous_list(self) -> None:
        client = APIClient()
        url = reverse("api:rules-list")
        res = client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class RuleEngineTest(UserSetupTestCase):
    def test_evaluate_condition_happy_path(self) -> None:
        condition = {
            "field": "age",
            "operator": ">=",
            "value": 18,
        }
        payload = {
            "age": 21,
        }
        # No error raises
        evaluate_condition(condition, payload)

    def test_evaluate_condition_sad_path(self) -> None:
        condition = {
            "field": "age",
            "operator": ">=",
            "value": 18,
        }
        payload = {
            "age": 8,
        }
        # No error raises
        res = evaluate_condition(condition, payload)
        assert not res

    def test_multiple_rules_happy_path(self) -> None:
        Rule.objects.create(
            name="Minimum Age Check",
            condition={
                "field": "age",
                "operator": ">=",
                "value": 18,
            },
            created_by=self.admin,
        )
        Rule.objects.create(
            name="Country Check",
            condition={
                "field": "country",
                "operator": "==",
                "value": "Thailand",
            },
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("evaluate")
        payload = {
            "rules": ["Minimum Age Check", "Country Check"],
            "payload": {
                "age": 21,
                "country": "Thailand",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "APPROVED"
        assert len(res.data["passed_rules"]) == 2  # noqa: PLR2004
        assert len(res.data["failed_rules"]) == 0

    def test_multiple_rules_sad_path(self) -> None:
        Rule.objects.create(
            name="Minimum Age Check",
            condition={
                "field": "age",
                "operator": ">=",
                "value": 18,
            },
            created_by=self.admin,
        )
        Rule.objects.create(
            name="Country Check",
            condition={
                "field": "country",
                "operator": "==",
                "value": "Vietnam",
            },
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("evaluate")
        payload = {
            "rules": ["Minimum Age Check", "Country Check"],
            "payload": {
                "age": 21,
                "country": "Thailand",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "REJECTED"
        assert len(res.data["passed_rules"]) == 1
        assert len(res.data["failed_rules"]) == 1

    def test_multiple_rules_invalid_rule_name_sad_path(self) -> None:
        """If the error raises at serializer level use DRF exception handler."""
        Rule.objects.create(
            name="Minimum Age Check",
            condition={
                "field": "age",
                "operator": ">=",
                "value": 18,
            },
            created_by=self.admin,
        )
        Rule.objects.create(
            name="Country Check",
            condition={
                "field": "country",
                "operator": "==",
                "value": "Vietnam",
            },
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("evaluate")
        payload = {
            "rules": ["Minimum Age Check XXX", "Country Check XXX"],
            "payload": {
                "age": 21,
                "country": "Thailand",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            str(res.data["rules"][0])
            == "Invalid rule names: ['Minimum Age Check XXX', 'Country Check XXX']"
        )


class RuleViewSetClientTest(UserSetupTestCase):
    def test_client_post(self) -> None:
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("api:rules-list")
        payload = {
            "name": "Weight in between 60-80 kg",
            "condition": [
                {"field": "weight", "operator": ">=", "value": 60},
                {"field": "weight", "operator": "<=", "value": 80},
            ],
            "is_active": True,
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def _create_age_under_18_rule(self) -> Rule:
        return Rule.objects.create(
            name="Age under 18",
            condition={},
            created_by=self.admin,
        )

    def test_client_get_detail(self) -> None:
        rule1 = self._create_age_under_18_rule()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("api:rules-detail", {"pk": rule1.id})
        res = client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_client_get_list(self) -> None:
        self._create_age_under_18_rule()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("api:rules-list")
        res = client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_client_put(self) -> None:
        rule1 = Rule.objects.create(
            name="Age under 18",
            condition={},
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("api:rules-detail", {"pk": rule1.id})
        data = {
            "name": "Age under 25",
            "condition": {},
            "is_active": False,
        }
        res = client.put(url, data=data, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_client_delete(self) -> None:
        rule1 = Rule.objects.create(
            name="Age under 18",
            condition={},
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("api:rules-detail", {"pk": rule1.id})
        res = client.delete(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def _create_weight_between_60_to_80(self):
        Rule.objects.create(
            name="Weight in between 60-80 kg",
            condition={
                "AND": [
                    {"field": "weight", "operator": ">=", "value": 60},
                    {"field": "weight", "operator": "<=", "value": 80},
                ],
            },
            is_active=True,
            created_by=self.admin,
        )

    def test_client_evaluate_single_rule_happy_path_multiple_condition_happy_path(
        self,
    ) -> None:
        self._create_weight_between_60_to_80()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Weight in between 60-80 kg"],
            "payload": {
                "weight": 70,
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "APPROVED"
        assert res.data["passed_rules"] == ["Weight in between 60-80 kg"]
        assert res.data["failed_rules"] == []

    def test_client_evaluate_single_rule_multiple_condition_sad_path(
        self,
    ) -> None:
        self._create_weight_between_60_to_80()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Weight in between 60-80 kg"],
            "payload": {
                "weight": 90,
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "REJECTED"
        assert res.data["failed_rules"] == ["Weight in between 60-80 kg"]
        assert res.data["passed_rules"] == []

    def _create_dog_or_cat_rule(self):
        Rule.objects.create(
            name="Accept only Dog or Cat",
            condition={
                "OR": [
                    {"field": "pet", "operator": "==", "value": "dog"},
                    {"field": "pet", "operator": "==", "value": "cat"},
                ],
            },
            is_active=True,
            created_by=self.admin,
        )

    def test_client_evaluate_single_rule_or_condition_happy_path(self) -> None:
        self._create_dog_or_cat_rule()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Accept only Dog or Cat"],
            "payload": {
                "pet": "dog",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "APPROVED"
        assert res.data["failed_rules"] == []
        assert res.data["passed_rules"] == ["Accept only Dog or Cat"]

    def test_client_evaluate_single_rule_or_condition_sad_path(self) -> None:
        self._create_dog_or_cat_rule()
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Accept only Dog or Cat"],
            "payload": {
                "pet": "camel",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "REJECTED"
        assert res.data["failed_rules"] == ["Accept only Dog or Cat"]
        assert res.data["passed_rules"] == []

    def test_man_and_between_30_to_60_happy_path(self) -> None:
        Rule.objects.create(
            name="Man age 30-60 yr",
            condition={
                "AND": [
                    {"field": "age", "operator": ">=", "value": 30},
                    {"field": "age", "operator": "<=", "value": 60},
                    {
                        "field": "gender",
                        "operator": "==",
                        "value": "male",
                    },
                ],
            },
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Man age 30-60 yr"],
            "payload": {
                "age": 34,
                "gender": "male",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "APPROVED"
        assert res.data["failed_rules"] == []
        assert res.data["passed_rules"] == ["Man age 30-60 yr"]

    def test_apple_or_durian_happy_path(self) -> None:
        Rule.objects.create(
            name="Apple or Durian",
            condition={
                "OR": [
                    {
                        "field": "fruit",
                        "operator": "==",
                        "value": "apple",
                    },
                    {
                        "field": "fruit",
                        "operator": "==",
                        "value": "durian",
                    },
                ],
            },
            is_active=True,
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Apple or Durian"],
            "payload": {
                "fruit": "apple",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "APPROVED"
        assert res.data["failed_rules"] == []
        assert res.data["passed_rules"] == ["Apple or Durian"]

    def test_apple_or_durian_sad_path(self) -> None:
        Rule.objects.create(
            name="Apple or Durian",
            condition={
                "OR": [
                    {
                        "field": "fruit",
                        "operator": "==",
                        "value": "apple",
                    },
                    {
                        "field": "fruit",
                        "operator": "==",
                        "value": "durian",
                    },
                ],
            },
            is_active=True,
            created_by=self.admin,
        )
        client = APIClient()
        client.force_authenticate(user=self.client)
        url = reverse("evaluate")
        payload = {
            "rules": ["Apple or Durian"],
            "payload": {
                "fruit": "mango",
            },
        }
        res = client.post(url, data=payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["result"] == "REJECTED"
        assert res.data["failed_rules"] == ["Apple or Durian"]
        assert res.data["passed_rules"] == []
