import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def encrypt_session_id(public_key_string, session_id):
    """
    Encrypt the session ID using the public key for API authentication
    
    Args:
        public_key_string (str): The public key string from OpenAPI
        session_id (str): The session ID received from the initial API call
    
    Returns:
        str: Base64 encoded encrypted session ID
    """
    
    try:
        print("Encrypting Session ID...")
        print(f"Session ID to encrypt: {session_id}")
        
        # Step 1: Decode the public key from Base64
        print("Step 1: Decoding Public Key from Base64...")
        public_key_bytes = base64.b64decode(public_key_string)
        
        # Step 2: Load the RSA public key
        print("Step 2: Loading RSA public key...")
        public_key = serialization.load_der_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        
        # Step 3: Encrypt the session ID
        print("Step 3: Encrypting session ID with RSA...")
        
        # Convert session ID to bytes
        session_id_bytes = session_id.encode('utf-8')
        
        # Encrypt using RSA with PKCS1v15 padding
        encrypted_session_id = public_key.encrypt(
            session_id_bytes,
            padding.PKCS1v15()
        )
        
        # Step 4: Convert to Base64 string format
        print("Step 4: Converting to Base64 format...")
        encrypted_session_id_b64 = base64.b64encode(encrypted_session_id).decode('utf-8')
        
        print("✅ Session ID encrypted successfully!")
        return encrypted_session_id_b64
        
    except Exception as e:
        print(f"❌ Error encrypting session ID: {str(e)}")
        return None

def encrypt_session_id_oaep(public_key_string, session_id):
    """
    Alternative version using OAEP padding (if PKCS1v15 doesn't work)
    """
    try:
        # Decode and load public key
        public_key_bytes = base64.b64decode(public_key_string)
        public_key = serialization.load_der_public_key(public_key_bytes, backend=default_backend())
        
        # Encrypt with OAEP padding
        encrypted_session_id = public_key.encrypt(
            session_id.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted_session_id).decode('utf-8')
        
    except Exception as e:
        print(f"❌ Error with OAEP encryption: {str(e)}")
        return None

def main():
    """
    Main function to encrypt your session ID
    """
    
    # Your session ID from the API response
    SESSION_ID = "e2f8992444594c85bed03d144c4318a0"
    
    # Your public key from OpenAPI (replace with actual key)
    PUBLIC_KEY = """
    MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEArv9yxA69XQKBo24BaF/D+fvlqmGdYjqLQ5WtNBb5tquqGvAvG3WMFETVUSow/LizQalxj2ElMVrUmzu5mGGkxK08bWEXF7a1DEvtVJs6nppIlFJc2SnrU14AOrIrB28ogm58JjAl5BOQawOXD5dfSk7MaAA82pVHoIqEu0FxA8BOKU+RGTihRU+ptw1j4bsAJYiPbSX6i71gfPvwHPYamM0bfI4CmlsUUR3KvCG24rB6FNPcRBhM3jDuv8ae2kC33w9hEq8qNB55uw51vK7hyXoAa+U7IqP1y6nBdlN25gkxEA8yrsl1678cspeXr+3ciRyqoRgj9RD/ONbJhhxFvt1cLBh+qwK2eqISfBb06eRnNeC71oBokDm3zyCnkOtMDGl7IvnMfZfEPFCfg5QgJVk1msPpRvQxmEsrX9MQRyFVzgy2CWNIb7c+jPapyrNwoUbANlN8adU1m6yOuoX7F49x+OjiG2se0EJ6nafeKUXw/+hiJZvELUYgzKUtMAZVTNZfT8jjb58j8GVtuS+6TM2AutbejaCV84ZK58E2CRJqhmjQibEUO6KPdD7oTlEkFy52Y1uOOBXgYpqMzufNPmfdqqqSM4dU70PO8ogyKGiLAIxCetMjjm6FCMEA3Kc8K0Ig7/XtFm9By6VxTJK1Mg36TlHaZKP6VzVLXMtesJECAwEAAQ==
    """
    
    print("Session ID Encryption Tool")
    print("=" * 50)
    print(f"Session ID from API: {SESSION_ID}")
    print()
    
    # Validate inputs
    if "REPLACE_WITH" in PUBLIC_KEY:
        print("⚠️  Please replace the placeholder with your actual Public Key from OpenAPI")
        return
    
    # Encrypt the session ID
    encrypted_session_id = encrypt_session_id(PUBLIC_KEY.strip(), SESSION_ID)
    
    if encrypted_session_id:
        print("\n" + "=" * 50)
        print("🔐 ENCRYPTED SESSION ID:")
        print("-" * 50)
        print(encrypted_session_id)
        print("-" * 50)
        print("\nUse this encrypted session ID in your subsequent API calls")
        print("(typically in the Authorization header or request body)")
        
        # Show example usage
        print("\n📋 Example usage in API calls:")
        print("Authorization: Bearer " + encrypted_session_id)
        print("OR")
        print("X-SECURITY-TOKEN: " + encrypted_session_id)
        
    else:
        print("\n❌ Failed to encrypt session ID. Please check your public key.")

# Quick function for immediate use
def quick_encrypt(public_key_pem, session_id):
    """
    Quick encryption function - just pass your values directly
    
    Usage:
    encrypted = quick_encrypt("YOUR_PUBLIC_KEY", "e2f8092444594ce85be20d14ca4318ad")
    """
    return encrypt_session_id(public_key_pem, session_id)

if __name__ == "__main__":
    main()

# For immediate use with your session ID:
# Replace YOUR_PUBLIC_KEY with your actual public key
# encrypted_id = quick_encrypt("YOUR_PUBLIC_KEY", "e2f8092444594ce85be20d14ca4318ad")
# print(f"Encrypted Session ID: {encrypted_id}")