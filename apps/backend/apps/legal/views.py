"""Views for legal compliance system."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from .serializers import (
    LegalDocumentSerializer,
    ConsentStatusSerializer,
    ConsentCreateSerializer,
    CookieConsentUpdateSerializer,
    CookieConsentSerializer,
    AgeVerificationSerializer
)
import asyncio


def _run_async(coro):
    """Run async code from sync legal views."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}
    error = {}

    def _runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            error['value'] = exc

    import threading

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()

    if 'value' in error:
        raise error['value']

    return result.get('value')


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['GET'])
@permission_classes([AllowAny])
def get_legal_document(request, document_type):
    """
    Get the current active legal document by type.
    
    Path Parameters:
        - document_type: Type of document ('TOS', 'PRIVACY', 'CONTENT_POLICY', 'DMCA')
        
    Returns:
        Legal document data
        
    Requirements:
        - 1.1: Display Terms of Service
        - 1.2: Display Privacy Policy compliant with GDPR and CCPA
        - 1.3: Provide DMCA takedown request process
        - 1.5: Display Content Policy
        - 1.9: Make all legal documents accessible from footer
    """
    # Map common aliases to actual document types
    type_mapping = {
        'terms': 'TOS',
        'tos': 'TOS',
        'privacy': 'PRIVACY',
        'content-policy': 'CONTENT_POLICY',
        'content_policy': 'CONTENT_POLICY',
        'dmca': 'DMCA'
    }
    
    # Normalize document type
    document_type_lower = document_type.lower()
    document_type_upper = type_mapping.get(document_type_lower, document_type.upper())
    
    # Validate document type
    valid_types = ['TOS', 'PRIVACY', 'CONTENT_POLICY', 'DMCA']
    
    if document_type_upper not in valid_types:
        return Response(
            {'error': f'Invalid document type. Must be one of: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        document_data = _run_async(
            fetch_legal_document(document_type_upper)
        )
        
        if document_data is None:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(document_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve document'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_legal_document(document_type):
    """
    Fetch the active legal document from database.
    
    Args:
        document_type: Type of document to fetch
        
    Returns:
        Document data dictionary or None if not found
        
    Requirements:
        - 1.1: Display Terms of Service
        - 1.2: Display Privacy Policy
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find the active document of the specified type
        document = await db.legaldocument.find_first(
            where={
                'document_type': document_type,
                'is_active': True
            },
            order={'effective_date': 'desc'}
        )
        
        if not document:
            return None
        
        return {
            'id': document.id,
            'document_type': document.document_type,
            'version': document.version,
            'content': document.content,
            'effective_date': document.effective_date.isoformat(),
            'created_at': document.created_at.isoformat(),
            'is_active': document.is_active
        }
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consent_status(request):
    """
    Get user's consent status for all legal documents.
    
    Returns:
        List of consent status for each document type
        
    Requirements:
        - 1.7: Store user consent records with timestamps
    """
    user_id = request.user_profile.id
    
    try:
        consent_status = _run_async(
            fetch_consent_status(user_id)
        )
        
        return Response(consent_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve consent status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_consent_status(user_id):
    """
    Fetch user's consent status for all document types.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of consent status dictionaries
        
    Requirements:
        - 1.7: Store user consent records with timestamps
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Get all active documents
        documents = await db.legaldocument.find_many(
            where={'is_active': True}
        )
        
        # Get user's consents
        consents = await db.userconsent.find_many(
            where={'user_id': user_id},
            include={'document': True}
        )
        
        # Create a map of document_id to consent
        consent_map = {consent.document_id: consent for consent in consents}
        
        # Build status for each document type
        status_list = []
        for document in documents:
            consent = consent_map.get(document.id)
            status_list.append({
                'document_type': document.document_type,
                'version': document.version,
                'consented': consent is not None,
                'consented_at': consent.consented_at.isoformat() if consent else None
            })
        
        return status_list
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_consent(request):
    """
    Record user consent for a legal document.
    
    Request Body:
        - document_id: ID of the legal document
        
    Returns:
        Created consent record
        
    Requirements:
        - 1.7: Store user consent records with timestamps
        - 1.8: Record consent changes with timestamp
    """
    # Validate request data
    serializer = ConsentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    document_id = validated_data['document_id']
    
    # Get user info
    user_id = request.user_profile.id
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        consent_data = _run_async(
            create_consent(user_id, document_id, ip_address, user_agent)
        )
        
        if consent_data is None:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(consent_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to record consent'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def create_consent(user_id, document_id, ip_address, user_agent):
    """
    Create a consent record in the database.
    
    Args:
        user_id: ID of the user
        document_id: ID of the legal document
        ip_address: IP address of the user
        user_agent: User agent string
        
    Returns:
        Consent data dictionary or None if document not found
        
    Requirements:
        - 1.7: Store user consent records with timestamps
        - 1.8: Record consent changes with timestamp
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Verify document exists
        document = await db.legaldocument.find_unique(
            where={'id': document_id}
        )
        
        if not document:
            return None
        
        # Check if consent already exists
        existing_consent = await db.userconsent.find_first(
            where={
                'user_id': user_id,
                'document_id': document_id
            }
        )
        
        if existing_consent:
            # Update existing consent (new timestamp)
            consent = await db.userconsent.update(
                where={'id': existing_consent.id},
                data={
                    'consented_at': datetime.now(),
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )
        else:
            # Create new consent
            consent = await db.userconsent.create(
                data={
                    'user_id': user_id,
                    'document_id': document_id,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )
        
        return {
            'id': consent.id,
            'user_id': consent.user_id,
            'document_id': consent.document_id,
            'consented_at': consent.consented_at.isoformat(),
            'ip_address': consent.ip_address,
            'user_agent': consent.user_agent
        }
        
    finally:
        await db.disconnect()


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_cookie_consent(request):
    """
    Update cookie consent preferences.
    
    Request Body:
        - analytics: Boolean for analytics cookies consent
        - marketing: Boolean for marketing cookies consent
        
    Returns:
        Updated cookie consent record
        
    Requirements:
        - 1.6: Display Cookie Consent banner with granular consent options
        - 1.8: Record consent changes with timestamp
    """
    # Validate request data
    serializer = CookieConsentUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    analytics = validated_data['analytics']
    marketing = validated_data['marketing']
    
    # Get user info (may be None for anonymous users)
    user_id = None
    if hasattr(request, 'user_profile') and request.user_profile is not None:
        user_id = request.user_profile.id
    session_id = request.session.session_key or 'anonymous'
    
    try:
        consent_data = _run_async(
            update_cookie_consent_record(user_id, session_id, analytics, marketing)
        )
        
        return Response(consent_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to update cookie consent'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_cookie_consent_record(user_id, session_id, analytics, marketing):
    """
    Update or create cookie consent record.
    
    Args:
        user_id: ID of the user (may be None for anonymous)
        session_id: Session ID
        analytics: Analytics consent
        marketing: Marketing consent
        
    Returns:
        Cookie consent data dictionary
        
    Requirements:
        - 1.6: Display Cookie Consent banner with granular consent options
        - 1.8: Record consent changes with timestamp
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find existing consent by user_id or session_id
        where_clause = {}
        if user_id:
            where_clause['user_id'] = user_id
        else:
            where_clause['session_id'] = session_id
        
        existing_consent = await db.cookieconsent.find_first(
            where=where_clause
        )
        
        if existing_consent:
            # Update existing consent
            consent = await db.cookieconsent.update(
                where={'id': existing_consent.id},
                data={
                    'analytics': analytics,
                    'marketing': marketing,
                    'consented_at': datetime.now()
                }
            )
        else:
            # Create new consent
            consent = await db.cookieconsent.create(
                data={
                    'user_id': user_id,
                    'session_id': session_id,
                    'essential': True,  # Always true
                    'analytics': analytics,
                    'marketing': marketing
                }
            )
        
        return {
            'id': consent.id,
            'user_id': consent.user_id,
            'session_id': consent.session_id,
            'essential': consent.essential,
            'analytics': consent.analytics,
            'marketing': consent.marketing,
            'consented_at': consent.consented_at.isoformat()
        }
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_age(request):
    """
    Verify user's age for COPPA compliance.
    
    Request Body:
        - age: User's age in years (must be >= 13)
        
    Returns:
        Success message with age verification status
        
    Requirements:
        - 1.4: Implement age verification requiring users to confirm they are 13 years or older
    """
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request data
    serializer = AgeVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    age = validated_data['age']
    
    # Get user info
    user_id = request.user_profile.id
    
    try:
        result = _run_async(
            update_age_verification(user_id, age)
        )
        
        if result is None:
            return Response(
                {'error': 'Failed to update age verification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {
                'message': 'Age verification successful',
                'age_verified': True,
                'age_verified_at': result['age_verified_at']
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': 'Failed to verify age'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_age_verification(user_id, age):
    """
    Update user's age verification status.
    
    Args:
        user_id: ID of the user
        age: User's age (already validated to be >= 13)
        
    Returns:
        Updated user data or None if update fails
        
    Requirements:
        - 1.4: Store age verification status
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Update user profile with age verification
        updated_profile = await db.userprofile.update(
            where={'id': user_id},
            data={
                'age_verified': True,
                'age_verified_at': datetime.now()
            }
        )
        
        return {
            'age_verified': updated_profile.age_verified,
            'age_verified_at': updated_profile.age_verified_at.isoformat()
        }
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_dmca_takedown(request):
    """
    Submit a DMCA takedown request.
    
    Request Body:
        - copyright_holder: Name of the copyright holder
        - contact_info: Contact information
        - copyrighted_work_description: Description of copyrighted work
        - infringing_url: URL of infringing content
        - good_faith_statement: Confirmation of good faith belief
        - signature: Electronic signature
        
    Returns:
        Created DMCA takedown request
        
    Requirements:
        - 31.1: Provide DMCA takedown request form
        - 31.2: Require specific fields in DMCA requests
        - 31.3: Require electronic signature
        - 31.4: Send confirmation email to requester
        - 31.5: Notify designated DMCA agent
    """
    from .serializers import DMCATakedownSerializer, DMCATakedownResponseSerializer
    from .email_service import LegalEmailService
    
    # Validate request data
    serializer = DMCATakedownSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    
    try:
        takedown_data = _run_async(
            create_dmca_takedown(validated_data)
        )
        
        # Send confirmation email to requester (Requirement 31.4)
        email_service = LegalEmailService()
        # Extract email from contact_info (assuming it contains email)
        contact_info = validated_data['contact_info']
        # Simple email extraction - in production, this should be more robust
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', contact_info)
        if email_match:
            requester_email = email_match.group(0)
            _run_async(email_service.send_dmca_confirmation(requester_email, takedown_data['id']))
        
        # Notify designated DMCA agent (Requirement 31.5)
        _run_async(email_service.send_dmca_agent_notification(takedown_data))
        
        return Response(takedown_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to submit DMCA takedown request'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def create_dmca_takedown(data):
    """
    Create a DMCA takedown request in the database.
    
    Args:
        data: Validated DMCA takedown data
        
    Returns:
        DMCA takedown data dictionary
        
    Requirements:
        - 31.1: Store DMCA takedown requests
        - 31.2: Store all required fields
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Create DMCA takedown request
        takedown = await db.dmcatakedown.create(
            data={
                'copyright_holder': data['copyright_holder'],
                'contact_info': data['contact_info'],
                'copyrighted_work_description': data['copyrighted_work_description'],
                'infringing_url': data['infringing_url'],
                'good_faith_statement': data['good_faith_statement'],
                'signature': data['signature'],
                'status': 'PENDING'
            }
        )
        
        return {
            'id': takedown.id,
            'copyright_holder': takedown.copyright_holder,
            'contact_info': takedown.contact_info,
            'copyrighted_work_description': takedown.copyrighted_work_description,
            'infringing_url': takedown.infringing_url,
            'good_faith_statement': takedown.good_faith_statement,
            'signature': takedown.signature,
            'status': takedown.status,
            'submitted_at': takedown.submitted_at.isoformat(),
            'reviewed_at': None,
            'reviewed_by': None
        }
        
    finally:
        await db.disconnect()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dmca_requests(request):
    """
    Get all DMCA takedown requests for the dashboard.
    
    Query Parameters:
        - status: Filter by status (PENDING, APPROVED, REJECTED)
        
    Returns:
        List of DMCA takedown requests
        
    Requirements:
        - 31.6: Provide DMCA agent dashboard for reviewing requests
    """
    from .permissions import IsDMCAAgent
    from .serializers import DMCATakedownResponseSerializer
    
    # Check DMCA agent permission
    permission = IsDMCAAgent()
    if not permission.has_permission(request, None):
        return Response(
            {'error': 'You do not have permission to access the DMCA dashboard'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get status filter from query params
    status_filter = request.GET.get('status', None)
    
    try:
        requests_data = _run_async(
            fetch_dmca_requests(status_filter)
        )
        
        return Response(requests_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve DMCA requests'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_dmca_requests(status_filter=None):
    """
    Fetch DMCA takedown requests from database.
    
    Args:
        status_filter: Optional status to filter by
        
    Returns:
        List of DMCA request dictionaries
        
    Requirements:
        - 31.6: Provide DMCA agent dashboard
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Build where clause
        where_clause = {}
        if status_filter:
            where_clause['status'] = status_filter
        
        # Fetch requests ordered by submission date (newest first)
        requests = await db.dmcatakedown.find_many(
            where=where_clause,
            order={'submitted_at': 'desc'}
        )
        
        # Convert to dictionaries
        requests_data = []
        for req in requests:
            requests_data.append({
                'id': req.id,
                'copyright_holder': req.copyright_holder,
                'contact_info': req.contact_info,
                'copyrighted_work_description': req.copyrighted_work_description,
                'infringing_url': req.infringing_url,
                'good_faith_statement': req.good_faith_statement,
                'signature': req.signature,
                'status': req.status,
                'submitted_at': req.submitted_at.isoformat(),
                'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
                'reviewed_by': req.reviewed_by
            })
        
        return requests_data
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_dmca_request(request, request_id):
    """
    Review a DMCA takedown request (approve or reject).
    
    Path Parameters:
        - request_id: ID of the DMCA request
        
    Request Body:
        - action: 'approve' or 'reject'
        - reason: Optional reason for rejection
        
    Returns:
        Updated DMCA request
        
    Requirements:
        - 31.6: Provide DMCA agent dashboard
        - 31.7: Implement content takedown on approval
        - 31.8: Notify content author
    """
    from .permissions import IsDMCAAgent
    from .email_service import LegalEmailService
    
    # Check DMCA agent permission
    permission = IsDMCAAgent()
    if not permission.has_permission(request, None):
        return Response(
            {'error': 'You do not have permission to review DMCA requests'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate action
    action = request.data.get('action')
    if action not in ['approve', 'reject']:
        return Response(
            {'error': 'Action must be either "approve" or "reject"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reason = request.data.get('reason', '')
    reviewer_id = request.user_profile.id
    
    try:
        # Update the DMCA request
        updated_request = _run_async(
            update_dmca_request_status(request_id, action, reviewer_id, reason)
        )
        
        if updated_request is None:
            return Response(
                {'error': 'DMCA request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # If approved, take down the content (Requirement 31.7)
        if action == 'approve':
            content_taken_down = _run_async(
                takedown_content(updated_request['infringing_url'])
            )
            
            if content_taken_down:
                # Send notification to content author (Requirement 31.8)
                email_service = LegalEmailService()
                author_email = content_taken_down.get('author_email')
                if author_email:
                    _run_async(
                        email_service.send_dmca_takedown_notification(
                            author_email,
                            updated_request['infringing_url'],
                            updated_request['copyrighted_work_description']
                        )
                    )
        
        return Response(updated_request, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to review DMCA request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_dmca_request_status(request_id, action, reviewer_id, reason):
    """
    Update DMCA request status.
    
    Args:
        request_id: ID of the DMCA request
        action: 'approve' or 'reject'
        reviewer_id: ID of the reviewer
        reason: Optional reason for rejection
        
    Returns:
        Updated DMCA request dictionary or None if not found
        
    Requirements:
        - 31.6: Update DMCA request status
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if request exists
        dmca_request = await db.dmcatakedown.find_unique(
            where={'id': request_id}
        )
        
        if not dmca_request:
            return None
        
        # Update status
        new_status = 'APPROVED' if action == 'approve' else 'REJECTED'
        
        updated_request = await db.dmcatakedown.update(
            where={'id': request_id},
            data={
                'status': new_status,
                'reviewed_at': datetime.now(),
                'reviewed_by': reviewer_id
            }
        )
        
        return {
            'id': updated_request.id,
            'copyright_holder': updated_request.copyright_holder,
            'contact_info': updated_request.contact_info,
            'copyrighted_work_description': updated_request.copyrighted_work_description,
            'infringing_url': updated_request.infringing_url,
            'good_faith_statement': updated_request.good_faith_statement,
            'signature': updated_request.signature,
            'status': updated_request.status,
            'submitted_at': updated_request.submitted_at.isoformat(),
            'reviewed_at': updated_request.reviewed_at.isoformat() if updated_request.reviewed_at else None,
            'reviewed_by': updated_request.reviewed_by
        }
        
    finally:
        await db.disconnect()


async def takedown_content(infringing_url):
    """
    Take down content by marking it as deleted.
    
    Args:
        infringing_url: URL of the infringing content
        
    Returns:
        Dictionary with author_email if successful, None otherwise
        
    Requirements:
        - 31.7: Implement content takedown on approval
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Parse the URL to determine content type and ID
        # Expected formats:
        # - /stories/{slug}
        # - /stories/{slug}/chapters/{chapter_number}
        # - /whispers/{id}
        
        import re
        
        # Try to match story URL
        story_match = re.search(r'/stories/([^/]+)(?:/chapters/(\d+))?', infringing_url)
        whisper_match = re.search(r'/whispers/([^/]+)', infringing_url)
        
        author_email = None
        
        if story_match:
            slug = story_match.group(1)
            chapter_number = story_match.group(2)
            
            if chapter_number:
                # Take down specific chapter
                story = await db.story.find_unique(
                    where={'slug': slug},
                    include={'author': True}
                )
                
                if story:
                    chapter = await db.chapter.find_first(
                        where={
                            'story_id': story.id,
                            'chapter_number': int(chapter_number)
                        }
                    )
                    
                    if chapter:
                        await db.chapter.update(
                            where={'id': chapter.id},
                            data={'deleted_at': datetime.now()}
                        )
                        
                        # Get author email from Clerk (simplified - would need Clerk API)
                        author_email = f"{story.author.handle}@example.com"  # Placeholder
            else:
                # Take down entire story
                story = await db.story.find_unique(
                    where={'slug': slug},
                    include={'author': True}
                )
                
                if story:
                    await db.story.update(
                        where={'id': story.id},
                        data={'deleted_at': datetime.now()}
                    )
                    
                    # Get author email from Clerk (simplified - would need Clerk API)
                    author_email = f"{story.author.handle}@example.com"  # Placeholder
        
        elif whisper_match:
            whisper_id = whisper_match.group(1)
            
            # Take down whisper
            whisper = await db.whisper.find_unique(
                where={'id': whisper_id},
                include={'author': True}
            )
            
            if whisper:
                await db.whisper.update(
                    where={'id': whisper_id},
                    data={'deleted_at': datetime.now()}
                )
                
                # Get author email from Clerk (simplified - would need Clerk API)
                author_email = f"{whisper.author.handle}@example.com"  # Placeholder
        
        if author_email:
            return {'author_email': author_email}
        
        return None
        
    finally:
        await db.disconnect()
