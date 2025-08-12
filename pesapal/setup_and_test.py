"""
Pesapal FastAPI Backend Setup and Test Script

This script helps you set up and test the Pesapal FastAPI backend.
It will:
1. Check if dependencies are installed
2. Help you configure environment variables
3. Test the API endpoints
4. Provide next steps

Run this script after setting up your environment variables.
"""

import subprocess
import sys
import os
import asyncio
import aiohttp
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'aiohttp',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    print("✅ All dependencies are already installed!")
    return True

def check_environment():
    """Check environment configuration"""
    print("\n" + "="*50)
    print("CHECKING ENVIRONMENT CONFIGURATION")
    print("="*50)
    
    env_vars = {
        'PESAPAL_CONSUMER_KEY': 'Your Pesapal consumer key',
        'PESAPAL_CONSUMER_SECRET': 'Your Pesapal consumer secret',
        'PESAPAL_ENVIRONMENT': 'sandbox or production (optional)',
        'APP_BASE_URL': 'Your app base URL (optional)'
    }
    
    missing_vars = []
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if var in ['PESAPAL_CONSUMER_KEY', 'PESAPAL_CONSUMER_SECRET']:
            if not value or value == f"your_{var.lower()}_here":
                missing_vars.append(var)
                print(f"❌ {var}: Not set - {description}")
            else:
                print(f"✅ {var}: Set (***hidden***)")
        else:
            if value:
                print(f"✅ {var}: {value}")
            else:
                print(f"⚠️  {var}: Using default - {description}")
    
    if missing_vars:
        print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("\n📝 To fix this:")
        print("1. Copy env_example.txt to .env")
        print("2. Edit .env with your actual Pesapal credentials")
        print("3. Set environment variables or use python-dotenv")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

async def test_api_endpoints():
    """Test the API endpoints"""
    print("\n" + "="*50)
    print("TESTING API ENDPOINTS")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("✅ Health check: API is running")
                else:
                    print(f"❌ Health check failed: Status {response.status}")
                    return False
        except aiohttp.ClientConnectorError:
            print("❌ Cannot connect to API. Make sure the server is running on localhost:8000")
            print("   Start the server with: python pesapal_api.py")
            return False
        
        # Test config endpoint
        try:
            async with session.get(f"{base_url}/pesapal/config") as response:
                if response.status == 200:
                    config = await response.json()
                    print("✅ Configuration endpoint: Working")
                    print(f"   Environment: {config.get('environment')}")
                    print(f"   Consumer key set: {config.get('consumer_key_set')}")
                    print(f"   Consumer secret set: {config.get('consumer_secret_set')}")
                else:
                    print(f"❌ Configuration endpoint failed: Status {response.status}")
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
        
        # Test authentication
        try:
            async with session.post(f"{base_url}/pesapal/auth") as response:
                auth_result = await response.json()
                if response.status == 200 and auth_result.get('status') == '200':
                    print("✅ Authentication: Working")
                else:
                    print(f"❌ Authentication failed: {auth_result.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
    
    return True

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    
    print("🎉 Your Pesapal FastAPI backend is ready!")
    print("\n📋 What you can do now:")
    print("1. 📖 Read the README.md for detailed documentation")
    print("2. 🧪 Run the example: python example_usage.py")
    print("3. 🌐 Visit API docs: http://localhost:8000/docs")
    print("4. 🔧 Test endpoints using the interactive docs")
    
    print("\n💳 To process a payment:")
    print("1. Register your IPN URL: POST /pesapal/register-ipn")
    print("2. Submit payment order: POST /pesapal/submit-order")
    print("3. Redirect customer to the returned payment URL")
    print("4. Handle callback and check transaction status")
    
    print("\n📚 Useful endpoints:")
    print("- Health check: GET /health")
    print("- API config: GET /pesapal/config")
    print("- Authentication: POST /pesapal/auth")
    print("- Submit order: POST /pesapal/submit-order")
    print("- Check status: GET /pesapal/transaction-status/{id}")
    
    print("\n🆘 Need help?")
    print("- Check the example_usage.py script")
    print("- Review the comprehensive README.md")
    print("- Enable debug logging for detailed error info")

async def main():
    """Main setup and test function"""
    print("🚀 Pesapal FastAPI Backend Setup & Test")
    print("="*50)
    
    # Step 1: Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        print("❌ Please install dependencies and try again")
        return
    
    # Step 2: Check environment
    if not check_environment():
        print("❌ Please configure environment variables and try again")
        return
    
    # Step 3: Test API (if server is running)
    print("\n🧪 Testing API endpoints...")
    print("Note: Make sure the server is running with: python pesapal_api.py")
    
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
        print("   This is normal if the server isn't running yet")
    
    # Step 4: Show next steps
    show_next_steps()
    
    print("\n✨ Setup complete! Happy coding! 🎉")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
