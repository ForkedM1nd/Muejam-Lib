"""Security URL configuration."""
from django.urls import path
from . import views

urlpatterns = [
    # Certificate pinning endpoints
    path('certificate/fingerprints', views.get_certificate_fingerprints, name='certificate_fingerprints'),
    path('certificate/verify', views.verify_certificate_fingerprint, name='verify_certificate_fingerprint'),
]
