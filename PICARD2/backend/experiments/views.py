# experiments/views.py
import os

from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SparkExperiment, Script, CSVDataset
from .tasks import run_db_script
from .serializers import CSVDatasetSerializer, UserSerializer


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
def run_experiment(request, script_id):
    # Get dataset_id from POST data
    dataset_id = request.data.get('dataset_id')

    if not dataset_id:
        return JsonResponse({"error": "dataset_id is required"}, status=400)

    try:
        # Check permissions: script must be mine OR public
        script = Script.objects.get(
            Q(id=script_id) & (Q(user=request.user) | Q(access_level=Script.PUBLIC))
        )

        # Validate Dataset permissions (Mine OR Public)
        dataset = CSVDataset.objects.get(
            Q(id=dataset_id) & (Q(user=request.user) | Q(access_modifier='public'))
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
    except Script.DoesNotExist:
        return JsonResponse({"error": "Script not found"}, status=404)

#7. POST: Upload a dataset to the backend.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    # DRF's request.data handles both POST and FILES together
    serializer = CSVDatasetSerializer(data=request.data)

    if serializer.is_valid():
        # Pass the user manually during the save process
        serializer.save(user=request.user)

        return JsonResponse({
            'status': 'success',
            'message': 'File uploaded successfully',
            'data': serializer.data
        }, status=201)

    # If validation fails, serializer.errors returns a structured error JSON
    return JsonResponse({
        'status': 'error',
        'errors': serializer.errors
    }, status=400)
