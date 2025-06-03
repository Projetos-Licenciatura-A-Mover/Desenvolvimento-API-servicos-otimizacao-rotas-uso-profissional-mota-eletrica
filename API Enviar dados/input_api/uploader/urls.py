from django.urls import path
from .views import UploadInputView

urlpatterns = [
    path('upload/', UploadInputView.as_view(), name='upload-input'),
]
