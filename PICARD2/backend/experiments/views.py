# experiments/views.py

from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SparkExperiment, Script, CSVDataset, PRIVATE, PUBLIC
from .tasks import run_db_script

# 1. GET: Allows for the frontend to watch an experiments results
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

# 2. POST: Trigger a Spark run on the fly using a Script ID and Dataset ID
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