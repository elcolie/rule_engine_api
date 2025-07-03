from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

class UserSetupTestCase(TestCase):
    def setUp(self) -> None:
        self.admin: User = User.objects.create(username="David", email="david@gmail.com", user_role=User.RoleChoice.ADMIN)
        self.client: User = User.objects.create(username="Jones", email="jones@gmail.com", user_role=User.RoleChoice.CLIENT)

class RuleTestCase(UserSetupTestCase):

    def test_admin(self) -> None:
        assert self.admin.user_role == User.RoleChoice.ADMIN

    def test_client(self) -> None:
        assert self.client.user_role == User.RoleChoice.CLIENT
