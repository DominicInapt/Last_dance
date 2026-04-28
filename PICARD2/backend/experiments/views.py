# experiments/views.py
import os
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from datasets.models import CSVDataset
from scripts.models import Script
from .models import SparkExperiment, PUBLIC
from .tasks import run_db_script
from .serializers import CSVDatasetSerializer, UserSerializer


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


# 1. GET: List all experiments for the logged-in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scripts(request):
    # Logic: Show scripts I own OR scripts that are marked public
    scripts = Script.objects.filter(
        Q(user=request.user) | Q(access_level=Script.PUBLIC)
    ).values('id', 'name', 'access_level', 'user_id', 'created_at')

    return JsonResponse(list(scripts), safe=False)

# 2. GET: Allows for the frontend to watch an experiments results
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_experiment_detail(request, experiment_id):
    try:
        exp = SparkExperiment.objects.get(id=experiment_id, user=request.user)
        return JsonResponse({
            "id": exp.id,
            "status": exp.status,
            "output": exp.output
        })
    except SparkExperiment.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

#3. POST: Sign a user into the database.
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
#4. POST: Log a user into the system.
@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)
        request.session['github_profile'] = {}
        return JsonResponse({"status": "login success"}, status=200)
    return JsonResponse({"status": "login failed"}, status=401)

# 5. POST: Upload and save script to DB
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_script(request):
    file = request.FILES.get('script')
    # User can optionally pass access_level in the request
    access = request.data.get('access_level', Script.PRIVATE)
    main_class = request.data.get('main_class') # Will be None if not provided

    _, extension = os.path.splitext(file.name)
    file_type = extension.lstrip('.').lower()  # Remove the dot and normalize to lowercase

    script = Script.objects.create(
        user=request.user,
        name=file.name,
        file_type=file_type,
        content=file.read().encode('utf-8'),
        access_level=access,
        main_class = main_class
    )
    return JsonResponse({"script_id": script.id, "access_level": script.access_level})

# 6. POST: Trigger the Spark run for an existing ID
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_script(request, script_id):
    # Get dataset_id from POST data
    dataset_id = request.data.get('dataset_id')

    if not dataset_id:
        return JsonResponse({"error": "dataset_id is required"}, status=400)

    try:
        # Check permissions: script must be mine OR public
        script = Script.objects.get(
            Q(id=script_id) & (Q(user=request.user) | Q(access_level=PUBLIC))
        )

        # Validate Dataset permissions (Mine OR Public)
        dataset = CSVDataset.objects.get(
            Q(id=dataset_id) & (Q(user=request.user) | Q(access_level=PUBLIC))
        )

        experiment = SparkExperiment.objects.create(
            user=request.user,
            script=script,
            dataset=dataset,
            status='Queued'
        )
        # Pass the experiment ID to the worker
        run_db_script.delay(experiment.id)

        return JsonResponse({"experiment_id": experiment.id, "status": "Queued"})
    except Script.DoesNotExist:
        return JsonResponse({"error": "Script not found or access denied"}, status=404)
    except CSVDataset.DoesNotExist:
        return JsonResponse({"error": "Dataset not found or access denied"}, status=404)

# 3. GET: List all experiments for the logged-in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_experiments(request):
    # Fetch experiments belonging to the user, newest first
    experiments = SparkExperiment.objects.filter(user=request.user).order_by('-created_at')

    # Format the data for the frontend
    experiment_data = []
    for exp in experiments:
        experiment_data.append({
            "id": exp.id,
            "script_name": exp.script.name,
            "dataset_name": exp.dataset.file.name,
            "status": exp.status,
            "created_at": exp.created_at
        })

    return JsonResponse(experiment_data, safe=False)


# 4. POST: Construct a new experiment without immediately running it
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_experiment(request):
    script_id = request.data.get('script_id')
    dataset_id = request.data.get('dataset_id')

    if not script_id or not dataset_id:
        return JsonResponse({"error": "Both script_id and dataset_id are required"}, status=400)

    try:
        # Check permissions: script must be mine OR public
        script = Script.objects.get(
            Q(id=script_id) & (Q(user=request.user) | Q(access_level=PUBLIC))
        )

        dataset = None
        if dataset_id:
            dataset = CSVDataset.objects.get(
                Q(id=dataset_id) & (Q(user=request.user) | Q(access_level=PUBLIC))
            )

        # Construct the experiment
        experiment = SparkExperiment.objects.create(
            user=request.user,
            script=script,
            dataset=dataset,
            status='Pending'
        )

        return JsonResponse({
            "message": "Experiment created successfully",
            "experiment_id": experiment.id,
            "status": experiment.status
        }, status=201)

    except Script.DoesNotExist:
        return JsonResponse({"error": "Script not found or access denied"}, status=404)
    except CSVDataset.DoesNotExist:
        return JsonResponse({"error": "Dataset not found or access denied"}, status=404)


# 5. POST: Queue an already existing Experiment
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_experiment(request, experiment_id):  # <-- New Method
    try:
        # Get the experiment, ensuring it belongs to the logged-in user
        experiment = SparkExperiment.objects.get(id=experiment_id, user=request.user)

        # Reset output and status, then save
        experiment.status = 'Queued'
        experiment.output = ""
        experiment.save(update_fields=['status', 'output'])

        # Pass the experiment ID to the worker
        run_db_script.delay(experiment.id)

        return JsonResponse(
            {"experiment_id": experiment.id, "status": "Queued", "message": "Experiment added to queue"})
    except SparkExperiment.DoesNotExist:
        return JsonResponse({"error": "Experiment not found or access denied"}, status=404)