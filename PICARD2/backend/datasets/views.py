import os

from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import CSVDataset, PRIVATE, PUBLIC
from .serializers import CSVDatasetSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    serializer = CSVDatasetSerializer(data=request.data)
    uploaded_file = request.FILES.get('file')

    if not uploaded_file:
        return JsonResponse({
            'status': 'error',
            'errors': {'file': ['A CSV file is required.']}
        }, status=400)

    if serializer.is_valid():
        # Fallback: if 'name' isn't explicitly sent in the form data, use the filename
        dataset_name = request.data.get('name', uploaded_file.name)

        # Save the dataset to the DB and disk simultaneously
        serializer.save(user=request.user, name=dataset_name)

        return JsonResponse({
            'status': 'success',
            'message': 'File uploaded successfully',
            'data': serializer.data
        }, status=201)

    return JsonResponse({
        'status': 'error',
        'errors': serializer.errors
    }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_datasets(request):
    """
    Returns a list of datasets that are either owned by the user or marked as public.
    """
    # Use Q objects to perform an OR query: (My Datasets) OR (Public Datasets)
    datasets = CSVDataset.objects.filter(
        Q(user=request.user) | Q(access_level=PUBLIC)
    ).order_by('-uploaded_at') # Order by newest first

    # Construct a simple list containing just the requested data
    dataset_data = []
    for ds in datasets:
        dataset_data.append({
            "id": ds.id,
            "name": ds.name,
            "file_name": os.path.basename(ds.file.name),
            "access_level": ds.access_level,
            "owner": ds.user.username,
            "uploaded_at": ds.uploaded_at,
        })

    return JsonResponse(dataset_data, safe=False, status=200)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_dataset(request, dataset_id):
    try:
        dataset = CSVDataset.objects.get(id=dataset_id, user=request.user)
    except CSVDataset.DoesNotExist:
        return JsonResponse({"error": "Dataset not found or access denied"}, status=404)

    dataset.file.delete(save=False)
    dataset.delete()
    return JsonResponse({"message": "Dataset deleted successfully"}, status=200)