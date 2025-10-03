# utils/cookies.py
from django.conf import settings
from rest_framework.response import Response

def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    """
    Set HTTP-only cookies for access and refresh tokens
    """
    # Access token cookie
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'],
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']
    )
    
    # Refresh token cookie  
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
        domain=settings.SIMPLE_JWT['AUTH_COOKIE_DOMAIN']
    )
    
    return response

def clear_auth_cookies(response: Response) -> Response:
    """
    Clear authentication cookies on logout
    """
    response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'])
    response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
    return response