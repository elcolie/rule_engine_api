from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase

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
                    "value": 18
                }
            ],
            "is_active": True
        }
        res = client.post(url, data=payload, format="json")
        first_rule = Rule.objects.first()
        self.assertTrue(status.HTTP_200_OK, res.status_code)
        self.assertTrue(first_rule.name, "Age over 18")
        self.assertTrue(first_rule.condition, [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 18
                }
            ])
        self.assertTrue(first_rule.is_active, True)
        self.assertTrue(first_rule.created_by, self.admin)

    def test_admin_list(self) -> None:
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-list")
        res = client.get(url)
        self.assertTrue(status.HTTP_200_OK, res.status_code)
        self.assertEqual(0, len(res.data))

    def test_admin_get(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-detail", kwargs={"pk": first_rule.pk})
        res = client.get(url)
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertEqual(first_rule.name, res.data["name"])
        self.assertEqual(first_rule.condition, res.data["condition"])
        self.assertEqual(first_rule.is_active, res.data["is_active"])

    def test_admin_update(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin
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
                    "value": 40
                }
            ],
            "is_active": False
        }
        res = client.put(url, data=payload, format="json")
        self.assertTrue(status.HTTP_200_OK, res.status_code)

        first_rule.refresh_from_db()
        self.assertTrue(first_rule.name, "Age over 40")
        self.assertTrue(first_rule.condition, [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 40
                }
            ])
        self.assertFalse(first_rule.is_active)

    def test_admin_delete(self) -> None:
        first_rule = Rule.objects.create(
            name="Age over 18",
            condition=[],
            created_by=self.admin
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("api:rules-detail", kwargs={"pk": first_rule.pk})
        res = client.delete(url)
        self.assertTrue(status.HTTP_204_NO_CONTENT, res.status_code)

    def test_anonymous_post(self) -> None:
        client = APIClient()
        url = reverse("api:rules-list")
        payload = {
            "name": "Age over 40",
            "condition": [
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 40
                }
            ],
            "is_active": False
        }
        res = client.post(url, data=payload, format="json")
        self.assertTrue(status.HTTP_401_UNAUTHORIZED, res.status_code)


    def test_anonymous_list(self) -> None:
        client = APIClient()
        url = reverse("api:rules-list")
        res = client.get(url)
        self.assertTrue(status.HTTP_401_UNAUTHORIZED, res.status_code)

class RuleEngineTest(UserSetupTestCase):

    def test_evaluate_condition_happy_path(self) -> None:
        condition = {
          "field": "age",
          "operator": ">=",
          "value": 18
        }
        payload = {
            "age": 21
        }
        # No error raises
        evaluate_condition(condition, payload)

    def test_evaluate_condition_sad_path(self) -> None:
        condition = {
          "field": "age",
          "operator": ">=",
          "value": 18
        }
        payload = {
            "age": 8
        }
        # No error raises
        res = evaluate_condition(condition, payload)
        self.assertFalse(res)

    def test_multiple_rules_happy_path(self) -> None:
        Rule.objects.create(
            name="Minimum Age Check",
            condition=
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 18
                },
            created_by=self.admin
        )
        Rule.objects.create(
            name="Country Check",
            condition={
                "field": "country",
                "operator": "==",
                "value": "Thailand"
            },
            created_by=self.admin
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("evaluate")
        payload = {
            "rules": ["Minimum Age Check", "Country Check"],
            "payload": {
                "age": 21,
                "country": "Thailand"
            }
        }
        res = client.post(url, data=payload, format="json")
        self.assertTrue(status.HTTP_200_OK, res.status_code)
        self.assertEqual("APPROVED", res.data["result"])
        self.assertEqual(2, len(res.data["passed_rules"]))
        self.assertEqual(0, len(res.data["failed_rules"]))

    def test_multiple_rules_sad_path(self) -> None:
        Rule.objects.create(
            name="Minimum Age Check",
            condition=
                {
                    "field": "age",
                    "operator": ">=",
                    "value": 18
                },
            created_by=self.admin
        )
        Rule.objects.create(
            name="Country Check",
            condition={
                "field": "country",
                "operator": "==",
                "value": "Vietnam"
            },
            created_by=self.admin
        )
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("evaluate")
        payload = {
            "rules": ["Minimum Age Check", "Country Check"],
            "payload": {
                "age": 21,
                "country": "Thailand"
            }
        }
        res = client.post(url, data=payload, format="json")
        self.assertTrue(status.HTTP_200_OK, res.status_code)
        self.assertEqual("REJECTED", res.data["result"])
        self.assertEqual(1, len(res.data["passed_rules"]))
        self.assertEqual(1, len(res.data["failed_rules"]))
