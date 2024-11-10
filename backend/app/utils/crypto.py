from cryptography.fernet import Fernet
import os

key = os.getenv("ENCRYPTION_KEY")

def encrypt_token(token: str) -> str:
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()
