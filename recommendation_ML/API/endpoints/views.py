from django.db import transaction
from rest_framework.exceptions import APIException

from rest_framework import viewsets
from rest_framework import mixins

from API.endpoints.models import Endpoint
from API.endpoints.serializers import EndpointSerializer

from API.endpoints.models import MLAlgorithm
from API.endpoints.serializers import MLAlgorithmSerializer

from API.endpoints.models import MLAlgorithmStatus
from API.endpoints.serializers import MLAlgorithmStatusSerializer

from API.endpoints.models import MLRequest
from API.endpoints.serializers import MLRequestSerializer

import json
import requests
from numpy.random import rand
from rest_framework import views, status
from rest_framework.response import Response
from API.ml.registry import MLRegistry
from recommendation_ML.wsgi import registry
from API.ml.metadata.suggestions import Recommendations


class EndpointViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EndpointSerializer
    queryset = Endpoint.objects.all()


class MLAlgorithmViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MLAlgorithmSerializer
    queryset = MLAlgorithm.objects.all()


def deactivate_other_statuses(instance):
    old_statuses = MLAlgorithmStatus.objects.filter(parent_mlalgorithm = instance.parent_mlalgorithm,
                                                        created_at__lt = instance.created_at,
                                                        active = True)
    for i in range(len(old_statuses)):
        old_statuses[i].active = False

    MLAlgorithmStatus.objects.bulk_update(old_statuses, ["active"])

class MLAlgorithmStatusViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)

        except Exception as e:
            raise APIException(str(e))

class MLRequestViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet, mixins.UpdateModelMixin):
    serializer_class = MLRequestSerializer
    queryset = MLRequest.objects.all()

class PredictView(views.APIView):
    
    def post(self, request, endpoint_name, format=None):

        token = self.request.headers["Authorization"]
        access_code = token.split()[1]
        response = requests.get('https://eustard-customers.herokuapp.com/api/auth/profile', headers = {'Authorization' : 'Bearer %s' % access_code})
        data = response.json()
        if data['statusCode'] != 200 :
            return {"message": "Unauthenticated",
                    "error": "Invalid Access Token.",
                    "statusCode": 401}
        else:
            algorithm_status = self.request.query_params.get("status", "production")
            algorithm_version = self.request.query_params.get("version")
            algs = MLAlgorithm.objects.filter(parent_endpoint__name = endpoint_name, status__status = algorithm_status, status__active=True)
                  
            if algorithm_version is not None:
                algs = algs.filter(version = algorithm_version).first()
            
            if len(algs) == 0:
                return Response(
                    {"status": "Error", "message": "ML algorithm is not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(algs) != 1 and algorithm_status != "ab_testing":
                return Response(
                    {"status": "Error", "message": "ML algorithm selection is ambiguous. Please specify algorithm version."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            alg_index = 0
            if algorithm_status == "ab_testing":
                alg_index = 0 if rand() < 0.5 else 1
            
            algorithm_object = registry.endpoints[algs[alg_index].id]
            #algorithm_object = Recommendations()
            prediction = algorithm_object.predict_recommendations(request.data)
                    
            ml_request = MLRequest(
                input_data = json.dumps(request.data),
                full_response = prediction,
                #response=label,
                feedback = "",
                parent_mlalgorithm = algs[alg_index],
                
            )
            ml_request.save()
                    
            return Response(prediction)
        
