# experiments/views.py
import os

from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SparkExperiment, Script, CSVDataset, PRIVATE, PUBLIC
from .tasks import run_db_script
from .serializers import CSVDatasetSerializer, UserSerializer


# 1. GET: List all experiments for the logged-in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scripts(request):
    # Logic: Show scripts I own OR scripts that are marked public
    scripts = Script.objects.filter(
        Q(user=request.user) | Q(access_level=PUBLIC)
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
    access = request.data.get('access_level', PRIVATE)
    main_class = request.data.get('main_class') # Will be None if not provided

    _, extension = os.path.splitext(file.name)
    file_type = extension.lstrip('.').lower()  # Remove the dot and normalize to lowercase

    script = Script.objects.create(
        user=request.user,
        name=file.name,
        file_type=file_type,
        content=file.read(),
        access_level=access,
        main_class = main_class
    )
    return JsonResponse({"script_id": script.id, "access_level": script.access_level})

# 6. POST: Trigger a Spark run on the fly using a Script ID and Dataset ID
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_script(request, script_id):
    # Get dataset_id from POST data
    dataset_id = request.data.get('dataset_id')

    try:
        # Check permissions: script must be mine OR public
        script = Script.objects.get(
            Q(id=script_id) & (Q(user=request.user) | Q(access_level=PUBLIC))
        )

        # Validate Dataset permissions (Mine OR Public)
        dataset = CSVDataset.objects.get(
            Q(id=dataset_id) & (Q(user=request.user) | Q(access_modifier=PUBLIC))
        )

        # Create the experiment on the fly
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

#7. POST: Upload a dataset to the backend.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    # 1. Get the file and optional access modifier from the request
    uploaded_file = request.FILES.get('file') # Make sure your frontend sends it as 'file'
    access_modifier = request.data.get('access_modifier', PRIVATE)

    if not uploaded_file:
        return JsonResponse({
            'status': 'error',
            'errors': {'file': ['No file was submitted.']}
        }, status=400)

    try:
        # 2. Save the database record first to generate the primary key (ID)
        dataset = CSVDataset.objects.create(
            user=request.user,
            access_modifier=access_modifier
        )

        # 3. Ensure the 'data/' directory exists
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)

        # 4. Generate the path dynamically: data/<ID>.csv
        file_path = dataset.get_file_path()

        # 5. Write the file to disk manually in chunks (to prevent memory bloat with large CSVs)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return JsonResponse({
            'status': 'success',
            'message': 'File uploaded successfully',
            'data': {
                'id': dataset.id,
                'path': file_path,
                'access_modifier': dataset.access_modifier
            }
        }, status=201)

    except Exception as e:
        # If writing the file fails, consider deleting the database record so it doesn't get orphaned
        if 'dataset' in locals():
            dataset.delete()
        return JsonResponse({
            'status': 'error',
            'errors': str(e)
        }, status=500)


# 8. GET: List all experiments for the logged-in user
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


# 9. POST: Construct a new experiment without immediately running it
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
                Q(id=dataset_id) & (Q(user=request.user) | Q(access_modifier=PUBLIC))
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


# 10. POST: Queue an already existing Experiment
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