"""URL configuration for legal app."""
from django.urls import path
from . import views

urlpatterns = [
    path('documents/<str:document_type>', views.get_legal_document, name='get_legal_document'),
    path('consent/status', views.get_consent_status, name='get_consent_status'),
    path('consent', views.record_consent, name='record_consent'),
    path('cookie-consent', views.update_cookie_consent, name='update_cookie_consent'),
    path('verify-age', views.verify_age, name='verify_age'),
    path('dmca/submit', views.submit_dmca_takedown, name='submit_dmca_takedown'),
    path('dmca/requests', views.get_dmca_requests, name='get_dmca_requests'),
    path('dmca/requests/<str:request_id>/review', views.review_dmca_request, name='review_dmca_request'),
]
