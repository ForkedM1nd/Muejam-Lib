from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.core.decorators import async_api_view
from .serializers import OnboardingProgressSerializer, OnboardingStepUpdateSerializer
from .service import OnboardingService


class OnboardingProgressView(APIView):
    """Get current onboarding progress"""
    permission_classes = [IsAuthenticated]
    
    @async_api_view
    async def get(self, request):
        user_id = request.user_profile_id
        
        progress = await OnboardingService.get_or_create_progress(user_id)
        serializer = OnboardingProgressSerializer(progress)
        
        return Response(serializer.data)


class OnboardingStepView(APIView):
    """Update onboarding step"""
    permission_classes = [IsAuthenticated]
    
    @async_api_view
    async def post(self, request):
        user_id = request.user_profile_id
        
        serializer = OnboardingStepUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        step = serializer.validated_data['step']
        progress = await OnboardingService.update_step(user_id, step)
        
        response_serializer = OnboardingProgressSerializer(progress)
        return Response(response_serializer.data)


class OnboardingSkipView(APIView):
    """Skip onboarding"""
    permission_classes = [IsAuthenticated]
    
    @async_api_view
    async def post(self, request):
        user_id = request.user_profile_id

        progress = await OnboardingService.skip_onboarding(user_id)
        serializer = OnboardingProgressSerializer(progress)

        return Response(serializer.data)


class OnboardingCompleteView(APIView):
    """Mark onboarding as complete"""
    permission_classes = [IsAuthenticated]

    @async_api_view
    async def post(self, request):
        user_id = request.user_profile_id

        progress = await OnboardingService.skip_onboarding(user_id)
        serializer = OnboardingProgressSerializer(progress)

        return Response(serializer.data)
