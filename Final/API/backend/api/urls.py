from django.urls import path
from .views import UploadJSONView

urlpatterns = [
    path('process/', UploadJSONView.as_view(), name='process-json'),
]
