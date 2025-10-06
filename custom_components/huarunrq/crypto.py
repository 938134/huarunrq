import time, random, base64, json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from .const import BIZ_H5_PUBLIC_KEY_PEM

def encrypt_param() -> str:
    public_key = serialization.load_pem_public_key(
        BIZ_H5_PUBLIC_KEY_PEM.encode(), backend=default_backend()
    )
    plain = f"e5b871c278a84defa8817d22afc34338#{int(time.time() * 1000)}#{random.randint(1000, 9999)}"
    encrypted = public_key.encrypt(plain.encode(), padding.PKCS1v15())
    return base64.urlsafe_b64encode(encrypted).decode()