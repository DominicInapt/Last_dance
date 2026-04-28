import os

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
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
