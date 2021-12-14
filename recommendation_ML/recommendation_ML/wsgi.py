"""
WSGI config for recommendation_ML project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
application = get_wsgi_application()

# ML registry
import inspect
from API.ml.registry import MLRegistry
from API.ml.metadata.suggestions import Recommendations

try:
    registry = MLRegistry() # create ML registry
    # Random Forest classifier
    rf = Recommendations()
    # add to ML registry
    registry.add_algorithm(endpoint_name="metadata",
                            algorithm_object=rf,
                            algorithm_name="metadata_based_recommendation",
                            algorithm_status="production",
                            algorithm_version="0.0.1",
                            owner="Rituparna",
                            algorithm_description="Metadata based recommendation system",
                            algorithm_code=inspect.getsource(Recommendations))

except Exception as e:
    print("Exception while loading the algorithms to the registry,", str(e))
