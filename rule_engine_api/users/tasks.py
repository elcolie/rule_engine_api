import typing as typ
from celery import shared_task

from .models import User
from ..rules.rule_engine import evaluate_condition


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()

@shared_task()
def async_evaluate_condition(
    condition: typ.Dict[str, typ.Any],
    payload: typ.Dict[str, typ.Any],
):
    return evaluate_condition(condition, payload)
