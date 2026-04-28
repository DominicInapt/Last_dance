from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}} # Password won't be returned in JSON

    def create(self, validated_data):
        # Use create_user to hash the password automatically
        return User.objects.create_user(**validated_data)
