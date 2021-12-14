from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from API.endpoints.views import EndpointViewSet
from API.endpoints.views import MLAlgorithmViewSet
from API.endpoints.views import MLAlgorithmStatusViewSet
from API.endpoints.views import MLRequestViewSet
from API.endpoints.views import PredictView # import PredictView

router = DefaultRouter(trailing_slash=False)
router.register(r"endpoints", EndpointViewSet, basename="endpoints")
router.register(r"mlalgorithms", MLAlgorithmViewSet, basename="mlalgorithms")
router.register(r"mlalgorithmstatuses", MLAlgorithmStatusViewSet, basename="mlalgorithmstatuses")
router.register(r"mlrequests", MLRequestViewSet, basename="mlrequests")

urlpatterns = [
    re_path(r"^api/v1/", include(router.urls)),

    re_path(r"^api/v1/(?P<endpoint_name>.+)/predict$", PredictView.as_view(), name="predict"),
]

