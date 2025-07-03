from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import JSONField

User = get_user_model()

class Rule(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_query_name="rule", related_name="rules")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, unique=True, blank=False)
    condition = JSONField(blank=False)
    is_active = models.BooleanField(default=True)
