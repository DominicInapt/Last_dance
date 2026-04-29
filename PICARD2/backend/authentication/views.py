import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


from authentication.serializers import UserSerializer

#1. POST: Sign a user into the database.
@api_view(['POST'])
@permission_classes([AllowAny]) # Allows anyone to access the signup page
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return JsonResponse({
            "message": "User created successfully",
            "user": {
                "username": user.username,
                "email": user.email
            }
        }, status=201)

    return JsonResponse(serializer.errors, status=400)


#2. POST: Log a user into the system.
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        return JsonResponse({"status": "login success"}, status=200)
    return JsonResponse({"status": "login failed"}, status=401)

def _get_frontend_target(frontend_origin=None):
    if frontend_origin:
        normalized_origin = frontend_origin.rstrip('/')
        for target_name, config in settings.GITHUB_OAUTH_APPS.items():
            if config.get('frontend_url') == normalized_origin:
                return target_name, config

    local_config = settings.GITHUB_OAUTH_APPS['local']
    if local_config.get('frontend_url'):
        return 'local', local_config

    raise ValueError('No GitHub OAuth frontend URL has been configured.')

def _build_frontend_redirect(target_config, status, reason=''):
    base_url = target_config.get('frontend_url', '').rstrip('/')
    query = {'auth': status}
    if reason:
        query['reason'] = reason
    return f"{base_url}/?{urlencode(query)}"

def _build_github_username(profile):
    login_name = (profile.get('login') or '').strip()
    if login_name:
        return f"github_{login_name}"[:150]
    return f"github_{profile['id']}"

def _clear_auth_cookies(response):
    cookie_options = {
        'path': settings.SESSION_COOKIE_PATH,
        'domain': settings.SESSION_COOKIE_DOMAIN,
        'samesite': settings.SESSION_COOKIE_SAMESITE,
    }
    if settings.SESSION_COOKIE_SECURE:
        cookie_options['secure'] = True

    response.delete_cookie(settings.SESSION_COOKIE_NAME, **cookie_options)

    csrf_cookie_options = {
        'path': settings.CSRF_COOKIE_PATH,
        'domain': settings.CSRF_COOKIE_DOMAIN,
        'samesite': settings.CSRF_COOKIE_SAMESITE,
    }
    if settings.CSRF_COOKIE_SECURE:
        csrf_cookie_options['secure'] = True

    response.delete_cookie(settings.CSRF_COOKIE_NAME, **csrf_cookie_options)
    return response

def _upsert_github_user(profile, email):
    username = _build_github_username(profile)
    defaults = {
        'email': email or '',
        'first_name': (profile.get('name') or '')[:150],
    }

    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
        return user

    updated_fields = []
    if email and user.email != email:
        user.email = email
        updated_fields.append('email')
    full_name = (profile.get('name') or '')[:150]
    if full_name and user.first_name != full_name:
        user.first_name = full_name
        updated_fields.append('first_name')
    if updated_fields:
        user.save(update_fields=updated_fields)
    return user

@api_view(['GET'])
@permission_classes([AllowAny])
def github_login(request):
    frontend_origin = request.GET.get('origin', '').rstrip('/')
    try:
        target_name, target_config = _get_frontend_target(frontend_origin)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    client_id = target_config.get('client_id')
    client_secret = target_config.get('client_secret')
    if not client_id or not client_secret:
        return JsonResponse(
            {'error': f'GitHub OAuth is not configured for the {target_name} app.'},
            status=500,
        )

    state = secrets.token_urlsafe(32)
    request.session['github_oauth_state'] = state
    request.session['github_oauth_target'] = target_name

    params = {
        'client_id': client_id,
        'redirect_uri': request.build_absolute_uri('/auth/github/callback/'),
        'scope': settings.GITHUB_OAUTH_SCOPE,
        'state': state,
    }
    return HttpResponseRedirect(f"{settings.GITHUB_AUTHORIZE_URL}?{urlencode(params)}")

@api_view(['GET'])
@permission_classes([AllowAny])
def github_callback(request):
    target_name = request.session.get('github_oauth_target', 'local')
    target_config = settings.GITHUB_OAUTH_APPS.get(target_name, settings.GITHUB_OAUTH_APPS['local'])
    expected_state = request.session.get('github_oauth_state')
    returned_state = request.GET.get('state')

    if not expected_state or expected_state != returned_state:
        return HttpResponseRedirect(_build_frontend_redirect(target_config, 'error', 'state_mismatch'))

    error = request.GET.get('error')
    if error:
        return HttpResponseRedirect(_build_frontend_redirect(target_config, 'error', error))

    code = request.GET.get('code')
    if not code:
        return HttpResponseRedirect(_build_frontend_redirect(target_config, 'error', 'missing_code'))

    client_id = target_config.get('client_id')
    client_secret = target_config.get('client_secret')

    token_response = requests.post(
        settings.GITHUB_TOKEN_URL,
        headers={'Accept': 'application/json'},
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': request.build_absolute_uri('/auth/github/callback/'),
            'state': returned_state,
        },
        timeout=15,
    )
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    if not token_response.ok or not access_token:
        return HttpResponseRedirect(_build_frontend_redirect(target_config, 'error', 'token_exchange_failed'))

    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    profile_response = requests.get(settings.GITHUB_USER_API_URL, headers=headers, timeout=15)
    if not profile_response.ok:
        return HttpResponseRedirect(_build_frontend_redirect(target_config, 'error', 'profile_fetch_failed'))
    profile = profile_response.json()

    email = profile.get('email')
    if not email:
        emails_response = requests.get(settings.GITHUB_EMAILS_API_URL, headers=headers, timeout=15)
        if emails_response.ok:
            emails = emails_response.json()
            primary_email = next((item for item in emails if item.get('primary')), None)
            verified_email = next((item for item in emails if item.get('verified')), None)
            email = (primary_email or verified_email or {}).get('email')

    user = _upsert_github_user(profile, email)
    login(request, user)
    request.session['github_profile'] = {
        'login': profile.get('login', ''),
        'name': profile.get('name', ''),
        'avatar_url': profile.get('avatar_url', ''),
        'profile_url': profile.get('html_url', ''),
        'email': email or '',
    }
    request.session.pop('github_oauth_state', None)
    request.session.pop('github_oauth_target', None)

    return HttpResponseRedirect(_build_frontend_redirect(target_config, 'success'))

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_session(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=200)

    github_profile = request.session.get('github_profile', {})
    return JsonResponse(
        {
            'authenticated': True,
            'user': {
                'username': request.user.username,
                'email': request.user.email,
                'name': github_profile.get('name') or request.user.first_name,
                'github_login': github_profile.get('login', ''),
                'avatar_url': github_profile.get('avatar_url', ''),
                'profile_url': github_profile.get('profile_url', ''),
            },
        },
        status=200,
    )

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_logout(request):
    logout(request)
    response = JsonResponse({'authenticated': False}, status=200)
    return _clear_auth_cookies(response)