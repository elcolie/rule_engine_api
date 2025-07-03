from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from rule_engine_api.rules.api.viewsets import RuleViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# router.register("users", UserViewSet)
router.register("rules", RuleViewSet, basename="rules")

app_name = "api"
urlpatterns = router.urls
