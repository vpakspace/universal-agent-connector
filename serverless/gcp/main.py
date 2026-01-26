"""
GCP Cloud Functions entry point
"""
from cloud_function_handler import cloud_function_handler

# Export handler for Cloud Functions
main = cloud_function_handler

