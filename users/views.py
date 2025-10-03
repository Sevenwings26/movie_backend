from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings

from .serializers import UserRegistrationSerializer, UserLoginSerializer, MovieSerializer, RatingSerializer, MovieDetailSerializer, UserDataSerializer
# from .utils.cookies import set_auth_cookies, clear_auth_cookies
from .utils import set_auth_cookies, clear_auth_cookies
from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Movie, Rating


User = get_user_model()


@extend_schema(
        tags=["System"],
        summary="Health Check", 
        description="Basic liveness probe", 
        responses={200:dict}
)
@api_view(['GET'])
def health_check(request):
    return Response({'Status':"Ok"}, status=status.HTTP_200_OK)


# register  
@extend_schema(
    tags=["Authentication"],
    summary="Register a new user", 
    description="Creates a new user account and sets HTTP-only auth cookies",
    request=UserRegistrationSerializer,
    responses={
        status.HTTP_201_CREATED: {"description": "User created successfully."},
        status.HTTP_400_BAD_REQUEST: {"description": "Validation error"},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Serialize the user data for the response body
        user_data = UserDataSerializer(user).data
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Create response and set cookies
        response = Response(
            {
                "message": "User registered successfully", 
                "user": user_data,
                "access": access_token, 
                "refresh": refresh_token
            }, 
            status=status.HTTP_201_CREATED
        )
        # return set_auth_cookies(response, access_token, refresh_token)
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# login  
@extend_schema(
    tags=["Authentication"],
    summary="Login a user",
    description="Authenticate user credentials and set HTTP-only auth cookies",
    request=UserLoginSerializer,
    responses={
        status.HTTP_200_OK: {"description": "User successfully logged in."},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid credentials."},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    print("RAW REQUEST DATA:", request.data)
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        print("AUTH USER:", user)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Serialize user data
        user_data = UserDataSerializer(user).data

        # Return tokens + user data
        response = Response(
            {
                "message": "User logged in successfully",
                "user": user_data,
                "access": access_token,
                "refresh": refresh_token,
            },
            status=status.HTTP_200_OK
        )

        # You can still set cookies if you want dual auth (optional)
        return set_auth_cookies(response, access_token, refresh_token)

    else:
        print("SERIALIZER ERRORS:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# logout  
@extend_schema(
    tags=["Authentication"],
    summary="Logout a user", 
    description="Blacklist refresh token and clear auth cookies",
    request=None,
    responses={
        status.HTTP_200_OK: {"description": "User successfully logged out."},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid or missing token."},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_user(request):
    response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    return clear_auth_cookies(response)


# Create movies 
@extend_schema(
    tags=["Movies"],
    summary="Create a new movie",
    description="Create a new movie entry (protected - requires authentication)",
    request=MovieSerializer,
    responses={
        201: MovieSerializer,
        400: {"description": "Validation error"},
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_movie(request):
    serializer = MovieSerializer(data=request.data)
    if serializer.is_valid():
        # Set the created_by field to the current user
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Rate movies 
@extend_schema(
    tags=["Movies"],
    summary="Rate a movie",
    description="Rate or update rating for a specific movie (protected - requires authentication)",
    request=RatingSerializer,
    responses={
        201: RatingSerializer,
        200: RatingSerializer,
        400: {"description": "Validation error"},
        404: {"description": "Movie not found"},
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response(
            {"error": "Movie not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user already rated this movie
    try:
        rating = Rating.objects.get(movie=movie, user=request.user)
        # Update existing rating
        serializer = RatingSerializer(rating, data=request.data, partial=True)
        status_code = status.HTTP_200_OK
    except Rating.DoesNotExist:
        # Create new rating
        serializer = RatingSerializer(data=request.data)
        status_code = status.HTTP_201_CREATED
    
    if serializer.is_valid():
        # Ensure the rating belongs to the current user and movie
        serializer.save(movie=movie, user=request.user)
        
        # Return rating along with updated movie stats
        response_data = {
            "rating": serializer.data,
            "movie": {
                "id": movie.id,
                "title": movie.title,
                "ratings_count": movie.ratings_count,
                "ratings_avg": round(movie.ratings_avg, 2)
            }
        }
        return Response(response_data, status=status_code)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get all movies 
@extend_schema(
    tags=["Movies"],
    summary="List movies",
    description="Get paginated list of movies with filtering and search",
    parameters=[
        OpenApiParameter(name='page', description='Page number', type=int),
        OpenApiParameter(name='limit', description='Items per page', type=int),
        OpenApiParameter(name='genre', description='Filter by genre', type=str),
        OpenApiParameter(name='search', description='Search in title and description', type=str),
        OpenApiParameter(name='min_rating', description='Minimum average rating', type=float),
    ],
    responses={200: MovieSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def list_movies(request):
    # Get query parameters
    page = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    genre = request.GET.get('genre', '')
    search = request.GET.get('search', '')
    min_rating = request.GET.get('min_rating', '')
    
    # Base queryset
    movies = Movie.objects.select_related('created_by').prefetch_related('ratings')
    
    # Apply filters
    if genre:
        movies = movies.filter(genre__iexact=genre)
    
    if search:
        movies = movies.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if min_rating:
        try:
            min_rating_float = float(min_rating)
            movies = movies.filter(ratings_avg__gte=min_rating_float)
        except ValueError:
            pass
    
    # Order by highest rated first, then newest
    movies = movies.order_by('-ratings_avg', '-created_at')
    
    # Pagination
    try:
        limit = min(int(limit), 50)  # Cap at 50 items per page
    except ValueError:
        limit = 10
    
    paginator = Paginator(movies, limit)
    
    try:
        movies_page = paginator.page(page)
    except PageNotAnInteger:
        movies_page = paginator.page(1)
    except EmptyPage:
        movies_page = paginator.page(paginator.num_pages)
    
    # Serialize data
    serializer = MovieSerializer(movies_page, many=True)
    
    # Return paginated response
    return Response({
        "items": serializer.data,
        "page": movies_page.number,
        "limit": limit,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
        "has_next": movies_page.has_next(),
        "has_previous": movies_page.has_previous(),
    })


@extend_schema(
    tags=["Movies"],
    summary="Get movie details",
    description="Get detailed information about a specific movie",
    responses={200: MovieDetailSerializer, 404: {"description": "Movie not found"}},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_movie_detail(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
        serializer = MovieDetailSerializer(movie)
        return Response(serializer.data)
    except Movie.DoesNotExist:
        return Response(
            {"error": "Movie not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=["Ratings"],
    summary="Get user's ratings",
    description="Get all ratings by the authenticated user",
    responses={200: RatingSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_ratings(request):
    ratings = Rating.objects.filter(user=request.user).select_related('movie')
    serializer = RatingSerializer(ratings, many=True)
    return Response(serializer.data)

@extend_schema(
    tags=["Movies"],
    summary="Delete a movie",
    description="Delete a movie (protected - only the user who created it can delete)",
    responses={
        204: {"description": "Movie deleted successfully"},
        403: {"description": "Permission denied"},
        404: {"description": "Movie not found"},
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_movie(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response(
            {"error": "Movie not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Only allow the user who created the movie to delete it
    if movie.created_by != request.user:
        return Response(
            {"error": "You don't have permission to delete this movie"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    movie.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    tags=["Ratings"],
    summary="Get movie ratings",
    description="Get paginated list of ratings for a specific movie",
    parameters=[
        OpenApiParameter(name='page', description='Page number', type=int),
        OpenApiParameter(name='limit', description='Items per page', type=int),
    ],
    responses={200: RatingSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_movie_ratings(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response(
            {"error": "Movie not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get query parameters
    page = request.GET.get('page', 1)
    limit = request.GET.get('limit', 10)
    
    # Get ratings for this movie
    ratings = Rating.objects.filter(movie=movie).select_related('user').order_by('-created_at')
    
    # Pagination
    try:
        limit = min(int(limit), 50)  # Cap at 50 items per page
    except ValueError:
        limit = 10
    
    paginator = Paginator(ratings, limit)
    
    try:
        ratings_page = paginator.page(page)
    except PageNotAnInteger:
        ratings_page = paginator.page(1)
    except EmptyPage:
        ratings_page = paginator.page(paginator.num_pages)
    
    # Serialize data
    serializer = RatingSerializer(ratings_page, many=True)
    
    # Return paginated response
    return Response({
        "movie": {
            "id": movie.id,
            "title": movie.title,
            "ratings_count": movie.ratings_count,
            "ratings_avg": round(movie.ratings_avg, 2)
        },
        "items": serializer.data,
        "page": ratings_page.number,
        "limit": limit,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
        "has_next": ratings_page.has_next(),
        "has_previous": ratings_page.has_previous(),
    })


# # views.py
# @extend_schema(
#     tags=["Users"],
#     summary="Get user's ratings by user ID",
#     description="Get all ratings by a specific user",
#     responses={200: RatingSerializer(many=True)},
# )
# @api_view(["GET"])
# @permission_classes([AllowAny])
# def get_user_ratings_by_id(request, user_id):
#     try:
#         user = CustomUser.objects.get(id=user_id)
#     except CustomUser.DoesNotExist:
#         return Response(
#             {"error": "User not found"}, 
#             status=status.HTTP_404_NOT_FOUND
#         )
    
#     ratings = Rating.objects.filter(user=user).select_related('movie')
#     serializer = RatingSerializer(ratings, many=True)
#     return Response(serializer.data)
