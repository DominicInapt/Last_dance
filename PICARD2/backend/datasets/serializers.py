import os

from rest_framework import serializers
from .models import CSVDataset

class CSVDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVDataset
        # We exclude 'user' because we'll inject it from the request
        fields = ['id', 'name', 'file', 'access_modifier', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    def validate_file(self, value):
        """
        Check that the uploaded file is a .csv
        """
        ext = os.path.splitext(value.name)[1]  # Get file extension
        if ext.lower() != '.csv':
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value