from rest_framework.response import Response

def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    # Access token
    response.set_cookie(
        key="access",
        value=access_token,
        httponly=True,
        secure=False,  # change to True in production (HTTPS)
        samesite="Lax",
        max_age=60 * 15,  # 15 minutes
    )
    # Refresh token
    response.set_cookie(
        key="refresh",
        value=refresh_token,
        httponly=True,
        secure=False,  # change to True in production
        samesite="Lax",
        max_age=60 * 60 * 24 * 7,  # 1 week
    )
    return response


def clear_auth_cookies(response: Response) -> Response:
    response.delete_cookie("access")
    response.delete_cookie("refresh")
    return response
