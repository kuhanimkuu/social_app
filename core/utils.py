import requests
from django.conf import settings

API_BASE_URL = 'http://127.0.0.1:8000/api/'  

def get_auth_headers(request):
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')
    headers = {}
    print("Access token:", access_token)
    print("Refresh token:", refresh_token)
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

        # Verify the token
        verify_response = requests.post(
            f"{API_BASE_URL}token/verify/", json={"token": access_token}
        )

        if verify_response.status_code == 401 and refresh_token:
            # Try refreshing the access token
            refresh_response = requests.post(
                f"{API_BASE_URL}token/refresh/", json={"refresh": refresh_token}
            )

            if refresh_response.status_code == 200:
                new_access_token = refresh_response.json().get("access")
                request.session["access_token"] = new_access_token
                headers["Authorization"] = f"Bearer {new_access_token}"
            else:
                print(" Refresh token is also invalid or expired.")
                # Optionally clear tokens and force login
                request.session.pop('access_token', None)
                request.session.pop('refresh_token', None)
                headers = {}  # Unauthenticated
    
    return headers
