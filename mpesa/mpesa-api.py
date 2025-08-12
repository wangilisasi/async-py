import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def generate_session_key(public_key_string, api_key):
    """
    Generate encrypted session key for OpenAPI authentication
    
    Args:
        public_key_string (str): The public key string from OpenAPI
        api_key (str): Your API key from step 4
    
    Returns:
        str: Base64 encoded encrypted API key (your session key)
    """
    
    try:
        # Step 6: Generate a decoded Base64 string from the Public Key
        print("Step 6: Decoding Public Key from Base64...")
        public_key_bytes = base64.b64decode(public_key_string)
        
        # Step 7: Generate an instance of an RSA cipher and use the Base64 string as the input
        print("Step 7: Creating RSA cipher instance...")
        public_key = serialization.load_der_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        
        # Step 8: Encode the API Key with the RSA cipher and digest as Base64 string format
        print("Step 8: Encrypting API Key with RSA cipher...")
        
        # Convert API key to bytes
        api_key_bytes = api_key.encode('utf-8')
        
        # Encrypt using RSA with PKCS1v15 padding (commonly used for API key encryption)
        encrypted_api_key = public_key.encrypt(
            api_key_bytes,
            padding.PKCS1v15()
        )
        
        # Step 9: Convert result to Base64 string format (your encrypted API Key/Session Key)
        print("Step 9: Converting to Base64 format...")
        encrypted_session_key = base64.b64encode(encrypted_api_key).decode('utf-8')
        
        return encrypted_session_key
        
    except Exception as e:
        print(f"Error generating session key: {str(e)}")
        return None

def main():
    """
    Main function to demonstrate usage
    Replace these values with your actual Public Key and API Key
    """
    
    # Step 5: Copy the Public Key from OpenAPI (replace with actual key)
    PUBLIC_KEY = """
   MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEArv9yxA69XQKBo24BaF/D+fvlqmGdYjqLQ5WtNBb5tquqGvAvG3WMFETVUSow/LizQalxj2ElMVrUmzu5mGGkxK08bWEXF7a1DEvtVJs6nppIlFJc2SnrU14AOrIrB28ogm58JjAl5BOQawOXD5dfSk7MaAA82pVHoIqEu0FxA8BOKU+RGTihRU+ptw1j4bsAJYiPbSX6i71gfPvwHPYamM0bfI4CmlsUUR3KvCG24rB6FNPcRBhM3jDuv8ae2kC33w9hEq8qNB55uw51vK7hyXoAa+U7IqP1y6nBdlN25gkxEA8yrsl1678cspeXr+3ciRyqoRgj9RD/ONbJhhxFvt1cLBh+qwK2eqISfBb06eRnNeC71oBokDm3zyCnkOtMDGl7IvnMfZfEPFCfg5QgJVk1msPpRvQxmEsrX9MQRyFVzgy2CWNIb7c+jPapyrNwoUbANlN8adU1m6yOuoX7F49x+OjiG2se0EJ6nafeKUXw/+hiJZvELUYgzKUtMAZVTNZfT8jjb58j8GVtuS+6TM2AutbejaCV84ZK58E2CRJqhmjQibEUO6KPdD7oTlEkFy52Y1uOOBXgYpqMzufNPmfdqqqSM4dU70PO8ogyKGiLAIxCetMjjm6FCMEA3Kc8K0Ig7/XtFm9By6VxTJK1Mg36TlHaZKP6VzVLXMtesJECAwEAAQ==
    """
    
    # Your API Key from step 4 (replace with actual key)
    API_KEY = "5RZGYp5XRZBsESMSp6NV6PqY3HZa7E5h"
    
    print("OpenAPI Session Key Generator")
    print("=" * 40)
    
    # Validate inputs
    if "REPLACE_WITH" in PUBLIC_KEY or "REPLACE_WITH" in API_KEY:
        print("⚠️  Please replace the placeholder values with your actual:")
        print("   - Public Key from OpenAPI")
        print("   - API Key from step 4")
        return
    
    # Generate the encrypted session key
    session_key = generate_session_key(PUBLIC_KEY.strip(), API_KEY)
    
    if session_key:
        print("\n✅ Session Key Generated Successfully!")
        print("-" * 40)
        print("Your Encrypted Session Key:")
        print(session_key)
        print("-" * 40)
        print("This is your encrypted API Key that you can use for authentication.")
    else:
        print("\n❌ Failed to generate session key. Please check your inputs.")

# Alternative function if you want to use OAEP padding instead of PKCS1v15
def generate_session_key_oaep(public_key_string, api_key):
    """
    Alternative version using OAEP padding (more secure but less commonly used for API keys)
    """
    try:
        # Decode the public key
        public_key_bytes = base64.b64decode(public_key_string)
        public_key = serialization.load_der_public_key(public_key_bytes, backend=default_backend())
        
        # Encrypt with OAEP padding
        encrypted_api_key = public_key.encrypt(
            api_key.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted_api_key).decode('utf-8')
        
    except Exception as e:
        print(f"Error with OAEP encryption: {str(e)}")
        return None

if __name__ == "__main__":
    main()

# Example usage with your actual keys:
#session_key = generate_session_key(your_public_key, your_api_key)
#print(f"Your Session Key: {session_key}")