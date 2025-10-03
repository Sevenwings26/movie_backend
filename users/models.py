from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator



# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email Field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.email


class Movie(models.Model):
    GENRE_CHOICES = [
        ('Action', 'Action'),
        ('Comedy', 'Comedy'),
        ('Drama', 'Drama'),
        ('Horror', 'Horror'),
        ('Sci-Fi', 'Sci-Fi'),
        ('Romance', 'Romance'),
        ('Thriller', 'Thriller'),
        ('Fantasy', 'Fantasy'),
        ('Documentary', 'Documentary'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    release_year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='movies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Denormalized fields for performance
    ratings_count = models.IntegerField(default=0)
    ratings_avg = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['title', 'release_year']  # Prevent duplicates
    
    def __str__(self):
        return f"{self.title} ({self.release_year})"
    
    def update_ratings_stats(self):
        """Update denormalized rating statistics"""
        ratings = self.ratings.all()
        self.ratings_count = ratings.count()
        if self.ratings_count > 0:
            self.ratings_avg = sum(r.rating for r in ratings) / self.ratings_count
        else:
            self.ratings_avg = 0.0
        self.save()

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['movie', 'user']  # One rating per user per movie
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}: {self.rating}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update movie ratings stats when a rating is saved
        self.movie.update_ratings_stats()
    
    def delete(self, *args, **kwargs):
        movie = self.movie
        super().delete(*args, **kwargs)
        # Update movie ratings stats when a rating is deleted
        movie.update_ratings_stats()

