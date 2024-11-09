from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str  # Remove the default value
    ALGORITHMS: list = ["RS256"]

    class Config:
        env_file = ".env"

auth_settings = AuthSettings()
