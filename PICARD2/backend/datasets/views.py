import os

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from datasets.models import PRIVATE, PUBLIC
from experiments.models import CSVDataset


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

#TODO add a view all datasets (personal or public)