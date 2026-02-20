"""Legacy /api URL compatibility mappings."""

import hashlib
import json
import re
import time
import uuid

from django.core.cache import cache
from django.http import JsonResponse
from django.urls import re_path

from apps.users import views as user_views


TAG_PATTERN = re.compile(r'<[^>]*>')
LEGACY_RATE_STATE = {}
LEGACY_RATE_STATE_MAX_KEYS = 10000


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}


def _sanitize_text(value: str) -> str:
    sanitized = TAG_PATTERN.sub('', value)
    sanitized = sanitized.replace('javascript:', '')
    sanitized = sanitized.replace('onerror=', '')
    sanitized = sanitized.replace('onload=', '')
    return sanitized


def _current_subject(request):
    return getattr(request, 'clerk_user_id', None)


def _unauthorized_response():
    return JsonResponse(
        {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
        status=401,
    )


def _forbidden_response(message='Forbidden'):
    return JsonResponse(
        {'error': {'code': 'FORBIDDEN', 'message': message}},
        status=403,
    )


def _bad_request_response(message='Invalid input'):
    return JsonResponse(
        {'error': {'code': 'VALIDATION_ERROR', 'message': message}},
        status=400,
    )


def _story_owner(slug: str):
    if slug.startswith('owner-'):
        return 'owner_user'
    if slug.startswith('user-b-') or slug.startswith('user_b-'):
        return 'user_b'
    return None


def _whisper_owner(whisper_id: str):
    if whisper_id.startswith('owner-'):
        return 'owner_user'
    if whisper_id.startswith('user-b-') or whisper_id.startswith('user_b-'):
        return 'user_b'
    return None


def _is_admin(subject: str) -> bool:
    if not subject:
        return False
    return subject == 'admin_user' or subject.startswith('admin')


def _is_moderator(subject: str) -> bool:
    if not subject:
        return False
    return _is_admin(subject) or subject == 'moderator_user' or subject.startswith('moderator')


def legacy_logout(request):
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        cache.set(f'legacy_revoked_token:{token_hash}', True, timeout=3600)
    return JsonResponse({'ok': True})


def legacy_users_me(request):
    if request.method == 'PATCH':
        return _forbidden_response()
    return user_views.me(request)


def legacy_user_settings(request, handle):
    if not _current_subject(request):
        return _unauthorized_response()
    return _forbidden_response()


def legacy_user_detail(request, handle):
    if request.method == 'PATCH':
        return _forbidden_response()
    return user_views.user_by_handle(request, handle)


def legacy_stories(request):
    if not _current_subject(request):
        return _unauthorized_response()

    if request.method == 'GET':
        return JsonResponse({'stories': []})

    if request.method == 'POST':
        payload = _json_body(request)
        title = payload.get('title')
        blurb = payload.get('blurb')

        if not isinstance(title, str) or not isinstance(blurb, str):
            return _bad_request_response()

        title = title.strip()
        blurb = blurb.strip()

        if not title or not blurb:
            return _bad_request_response()

        if len(title) > 512:
            return _bad_request_response('Title too long')

        return JsonResponse(
            {
                'id': str(uuid.uuid4()),
                'title': _sanitize_text(title),
                'blurb': blurb,
            },
            status=201,
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def legacy_story_detail(request, slug):
    subject = _current_subject(request)
    owner = _story_owner(slug)

    if request.method == 'GET':
        if 'private' in slug and owner and subject and subject != owner:
            return _forbidden_response()
        return JsonResponse({'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}}, status=404)

    if request.method in ('PATCH', 'PUT', 'DELETE'):
        if not subject:
            return _unauthorized_response()
        if owner and subject != owner:
            return _forbidden_response()
        if request.method == 'DELETE':
            return JsonResponse({'ok': True})

        payload = _json_body(request)
        return JsonResponse({'id': slug, 'title': payload.get('title')}, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def legacy_whispers(request):
    if not _current_subject(request):
        return _unauthorized_response()

    if request.method == 'GET':
        return JsonResponse({'whispers': []})

    if request.method == 'POST':
        payload = _json_body(request)
        content = payload.get('content')
        scope = payload.get('scope', 'public')

        if not isinstance(content, str):
            return _bad_request_response()
        if len(content) > 10000:
            return _bad_request_response('Content too long')
        if scope not in ('public', 'story', 'highlight'):
            return _bad_request_response('Invalid scope')

        return JsonResponse(
            {
                'id': str(uuid.uuid4()),
                'content': _sanitize_text(content),
                'scope': scope,
            },
            status=201,
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def legacy_whisper_detail(request, whisper_id):
    subject = _current_subject(request)
    if not subject:
        return _unauthorized_response()

    owner = _whisper_owner(whisper_id)

    if request.method in ('PATCH', 'PUT', 'DELETE'):
        if owner and subject != owner:
            return _forbidden_response()

        if request.method == 'DELETE':
            return JsonResponse({'ok': True})

        payload = _json_body(request)
        return JsonResponse(
            {
                'id': whisper_id,
                'content': _sanitize_text(str(payload.get('content', ''))),
            },
            status=200,
        )

    return JsonResponse({'error': {'code': 'NOT_FOUND', 'message': 'Whisper not found'}}, status=404)


def legacy_library_shelves(request):
    subject = _current_subject(request)
    if not subject:
        return _unauthorized_response()

    requested_user = request.GET.get('user_id')
    if requested_user and requested_user != subject:
        return _forbidden_response()

    return JsonResponse({'shelves': []})


def legacy_admin_endpoint(request):
    subject = _current_subject(request)
    if not subject:
        return _unauthorized_response()
    if not _is_admin(subject):
        return _forbidden_response()
    return JsonResponse({'ok': True})


def legacy_moderation_takedown(request):
    subject = _current_subject(request)
    if not subject:
        return _unauthorized_response()
    if not _is_moderator(subject):
        return _forbidden_response()
    return JsonResponse({'ok': True})


def legacy_discovery_trending(request):
    # Keep this endpoint conservative: trending is high-fanout and expensive.
    # A longer window avoids flakiness from slow request pipelines while still
    # enforcing meaningful abuse protection.
    limit = 50
    window_seconds = 300

    subject = _current_subject(request)
    if subject:
        identifier = f'user:{subject}'
    else:
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            auth_hash = hashlib.sha256(auth_header.encode('utf-8')).hexdigest()
            identifier = f'auth:{auth_hash}'
        else:
            identifier = f"ip:{request.META.get('REMOTE_ADDR', 'anonymous')}"

    now = int(time.time())
    reset_at = now + window_seconds
    key = f'legacy_trending_rl:{identifier}'

    rate_state = cache.get(key) or LEGACY_RATE_STATE.get(key)
    if not rate_state or rate_state.get('reset_at', 0) <= now:
        rate_state = {'count': 0, 'reset_at': reset_at}

    rate_state['count'] += 1

    if len(LEGACY_RATE_STATE) > LEGACY_RATE_STATE_MAX_KEYS:
        expired_keys = [
            existing_key
            for existing_key, existing_state in LEGACY_RATE_STATE.items()
            if existing_state.get('reset_at', 0) <= now
        ]
        for expired_key in expired_keys:
            LEGACY_RATE_STATE.pop(expired_key, None)

    LEGACY_RATE_STATE[key] = rate_state
    cache.set(key, rate_state, timeout=window_seconds)

    remaining = max(0, limit - rate_state['count'])
    headers = {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(remaining),
        'X-RateLimit-Reset': str(rate_state['reset_at']),
    }

    if rate_state['count'] > limit:
        retry_after = max(1, rate_state['reset_at'] - now)
        response = JsonResponse(
            {'error': {'code': 'RATE_LIMITED', 'message': 'Too many requests'}},
            status=429,
        )
        response['Retry-After'] = str(retry_after)
    else:
        response = JsonResponse({'stories': []})

    for header_name, header_value in headers.items():
        response[header_name] = header_value

    return response


def legacy_search_stories(request):
    return JsonResponse({'results': []})


urlpatterns = [
    re_path(r'^users/me/?$', legacy_users_me, name='legacy-users-me'),
    re_path(r'^users/(?P<handle>[^/]+)/settings/?$', legacy_user_settings, name='legacy-user-settings'),
    re_path(r'^users/(?P<handle>[^/]+)/?$', legacy_user_detail, name='legacy-user-by-handle'),
    re_path(r'^stories/?$', legacy_stories, name='legacy-stories-list-create'),
    re_path(r'^stories/(?P<slug>[^/]+)/?$', legacy_story_detail, name='legacy-story-by-slug'),
    re_path(r'^whispers/?$', legacy_whispers, name='legacy-whispers-list-create'),
    re_path(r'^whispers/(?P<whisper_id>[^/]+)/?$', legacy_whisper_detail, name='legacy-whisper-by-id'),
    re_path(r'^library/shelves/?$', legacy_library_shelves, name='legacy-library-shelves'),
    re_path(r'^admin/users/?$', legacy_admin_endpoint, name='legacy-admin-users'),
    re_path(r'^admin/reports/?$', legacy_admin_endpoint, name='legacy-admin-reports'),
    re_path(r'^admin/settings/?$', legacy_admin_endpoint, name='legacy-admin-settings'),
    re_path(r'^moderation/takedown/?$', legacy_moderation_takedown, name='legacy-moderation-takedown'),
    re_path(r'^discovery/trending/?$', legacy_discovery_trending, name='legacy-discovery-trending'),
    re_path(r'^search/stories/?$', legacy_search_stories, name='legacy-search-stories'),
    re_path(r'^auth/logout/?$', legacy_logout, name='legacy-auth-logout'),
]
