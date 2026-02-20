from django.urls import path
from .views import OnboardingProgressView, OnboardingStepView, OnboardingSkipView, OnboardingCompleteView

urlpatterns = [
    path('progress/', OnboardingProgressView.as_view(), name='onboarding-progress'),
    path('step/', OnboardingStepView.as_view(), name='onboarding-step'),
    path('skip/', OnboardingSkipView.as_view(), name='onboarding-skip'),
    path('complete/', OnboardingCompleteView.as_view(), name='onboarding-complete'),
]
