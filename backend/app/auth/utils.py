from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
from .config import auth_settings

class AuthError(Exception):
    def __init__(self, error, status_code):
        super().__init__()
        self.error = error
        self.status_code = status_code

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

        if not credentials.scheme == "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme.")

        try:
            payload = await verify_token(credentials.credentials)
        except Exception as e:
            raise HTTPException(status_code=403, detail=str(e))

        return payload

async def verify_token(token: str):
    try:
        jwks_url = f'https://{auth_settings.AUTH0_DOMAIN}/.well-known/jwks.json'
        jwks_response = requests.get(jwks_url)
        jwks = jwks_response.json()

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}

        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key),
                    algorithms=auth_settings.ALGORITHMS,
                    audience=auth_settings.AUTH0_API_AUDIENCE,
                    issuer=f"https://{auth_settings.AUTH0_DOMAIN}/"
                )
                return payload

            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired", "description": "Token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims", "description": "Incorrect claims, please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication token."}, 401)

        raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)

    except Exception as e:
        raise AuthError({"code": "invalid_header", "description": str(e)}, 401)
