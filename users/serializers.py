from rest_framework import serializers
from . import models
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# serializers.py

# ... (other imports and UserLoginSerializer)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password1", "password2")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords don’t match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password1")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid Credentials")
        if not user.is_active:
            raise serializers.ValidationError("Account is not active. Please verify your email.")

        data['user'] = user
        return data


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ('id', 'username', 'email')
        

class MovieSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = models.Movie
        fields = [
            'id', 'title', 'genre', 'release_year', 'description',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
            'ratings_count', 'ratings_avg'
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at', 'ratings_count', 'ratings_avg']


class RatingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    
    class Meta:
        model = models.Rating
        fields = [
            'id', 'movie', 'movie_title', 'user', 'user_username',
            'rating', 'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'user_username', 'movie_title', 'created_at', 'updated_at']


class MovieDetailSerializer(MovieSerializer):
    """Extended movie serializer with recent ratings"""
    recent_ratings = serializers.SerializerMethodField()
    
    class Meta(MovieSerializer.Meta):
        fields = MovieSerializer.Meta.fields + ['recent_ratings']
    
    def get_recent_ratings(self, obj):
        recent_ratings = obj.ratings.select_related('user').order_by('-created_at')[:5]
        return RatingSerializer(recent_ratings, many=True).data

        