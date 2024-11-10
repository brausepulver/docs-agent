import os
import requests
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

# Fetch the JWKS from Auth0
def get_jwks():
    try:
        response = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        response.raise_for_status()
        return response.json()["keys"]
    except requests.RequestException as e:
        print(f"Error fetching JWKS: {e}")
        return None

def get_public_key(token):
    unverified_header = jwt.get_unverified_header(token)
    jwks = get_jwks()

    rsa_key = {}
    for key in jwks:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break
    return rsa_key

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        rsa_key = get_public_key(token)
        if not rsa_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public key not found")

        # Since email is not in the access token, fetch it from the userinfo endpoint
        try:
            userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(userinfo_url, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            user_email = user_info.get("email")

            if not user_email:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email not found in user info"
                )

            return user_email

        except Exception as e:
            print(f"Error fetching user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not fetch user info"
            )

    except JWTError as e:
        print(f"JWT error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token"
        )
