import os

from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from datasets.models import PRIVATE, PUBLIC
from scripts.models import Script

# 1. GET: List all experiments for the logged-in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_scripts(request):
    # Logic: Show scripts I own OR scripts that are marked public
    scripts = Script.objects.filter(
        Q(user=request.user) | Q(access_level=PUBLIC)
    ).values('id', 'name', 'access_level', 'user_id', 'created_at')

    return JsonResponse(list(scripts), safe=False)

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
