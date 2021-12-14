from django.test import TestCase
import inspect
from API.ml.registry import MLRegistry
from API.ml.metadata.suggestions import Recommendations

class MLTests(TestCase):
    
    def test_metadata_algorithm(self):
        input_data = {"course_id":377}
        my_alg = Recommendations()
        response = my_alg.predict_recommendations(input_data)
        self.assertEqual('Success', response['status'])
        self.assertEqual(0, response['error'])
        #self.assertEqual('<=50K', response['label'])
    
    def test_registry(self):
        registry = MLRegistry()
        self.assertEqual(len(registry.endpoints), 0)
        endpoint_name = "metadata_recommender"
        algorithm_object = Recommendations()
        algorithm_name = "metadata_based_recommendation"
        algorithm_status = "production"
        algorithm_version = "0.0.1"
        algorithm_owner = "Rituparna"
        algorithm_description = "Metadata based recommendation system"
        algorithm_code = inspect.getsource(Recommendations)
        # add to registry
        registry.add_algorithm(endpoint_name, algorithm_object, algorithm_name,
                    algorithm_status, algorithm_version, algorithm_owner,
                    algorithm_description, algorithm_code)
        # there should be one endpoint available
        self.assertEqual(len(registry.endpoints), 1)

        

        