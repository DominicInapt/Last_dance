import os

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import CSVDataset

class CSVDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVDataset
        # We exclude 'user' because we'll inject it from the request
        fields = ['id', 'file', 'access_modifier', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    def validate_file(self, value):
        """
        Check that the uploaded file is a .csv
        """
        ext = os.path.splitext(value.name)[1]  # Get file extension
        if ext.lower() != '.csv':
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} # Password won't be returned in JSON

    def create(self, validated_data):
        # Use create_user to hash the password automatically
        return User.objects.create_user(**validated_data)
