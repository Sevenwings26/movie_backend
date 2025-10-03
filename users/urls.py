from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', views.health_check, name="health"),
    path('auth/register/', views.register_user, name="register"),
    path('auth/login/', views.login_user, name="login"),
    path('auth/logout/', views.logout_user, name="logout"),

    # SimpleJWT endpoints for raw token management
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Movies endpoints
    path('movies/add/', views.create_movie, name='create_movie'),  # POST - create movie
    path('movies/', views.list_movies, name='list_movies'),  # GET - list movies
    path('movies/<int:movie_id>/', views.get_movie_detail, name='movie_detail'),  # GET - movie details
    path('movies/<int:movie_id>/', views.delete_movie, name='delete_movie'),  # DELETE - delete movie
    
    # Rating endpoints
    path('movies/<int:movie_id>/ratings/', views.rate_movie, name='rate_movie'),  # POST - rate movie
    path('movies/<int:movie_id>/ratings/', views.get_movie_ratings, name='get_movie_ratings'),  # GET - movie ratings    
    path('user/ratings/', views.get_user_ratings, name='user_ratings'),  # GET - current user's ratings
    # path('users/<int:user_id>/ratings/', views.get_user_ratings_by_id, name='user_ratings_by_id'),  # GET - specific user's ratings]
]

    # password reset 
    # path("password-reset/", views.password_reset_request, name="password-reset"),
    # path("password-reset/<uid64>/<token>/", views.password_reset_confirm, name="password-reset-confirm"),
