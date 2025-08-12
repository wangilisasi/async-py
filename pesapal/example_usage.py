"""
Example usage of the Pesapal FastAPI backend

This script demonstrates how to interact with the Pesapal API backend
to process payments, check transaction status, and handle callbacks.

Make sure to:
1. Install dependencies: pip install -r requirements.txt
2. Set up your environment variables (copy env_example.txt to .env)
3. Start the FastAPI server: python pesapal_api.py
4. Run this example script: python example_usage.py
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Base URL for your FastAPI backend
BASE_URL = "http://localhost:8000"

class PesapalExample:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: dict = None):
        """Make HTTP request to the API"""
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, json=data) as response:
                result = await response.json()
                print(f"\n{method} {endpoint}")
                print(f"Status: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    async def test_authentication(self):
        """Test Pesapal authentication"""
        print("\n" + "="*50)
        print("TESTING AUTHENTICATION")
        print("="*50)
        
        result = await self.make_request("POST", "/pesapal/auth")
        return result

    async def register_ipn_url(self):
        """Register IPN URL with Pesapal"""
        print("\n" + "="*50)
        print("REGISTERING IPN URL")
        print("="*50)
        
        ipn_data = {
            "url": f"{BASE_URL}/pesapal/ipn",
            "ipn_notification_type": "POST"
        }
        
        result = await self.make_request("POST", "/pesapal/register-ipn", ipn_data)
        return result

    async def get_registered_ipns(self):
        """Get all registered IPN URLs"""
        print("\n" + "="*50)
        print("GETTING REGISTERED IPNS")
        print("="*50)
        
        result = await self.make_request("GET", "/pesapal/ipns")
        return result

    async def submit_payment_order(self):
        """Submit a payment order"""
        print("\n" + "="*50)
        print("SUBMITTING PAYMENT ORDER")
        print("="*50)
        
        # Generate unique merchant reference
        merchant_ref = f"ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        payment_data = {
            "id": merchant_ref,
            "currency": "KES",
            "amount": 100.00,
            "description": "Test payment for Pesapal integration",
            "callback_url": f"{BASE_URL}/pesapal/callback",
            "redirect_mode": "TOP_WINDOW",
            "branch": "Main Store",
            "billing_address": {
                "email_address": "customer@example.com",
                "phone_number": "0723456789",
                "country_code": "KE",
                "first_name": "John",
                "middle_name": "",
                "last_name": "Doe",
                "line_1": "123 Test Street",
                "line_2": "Test Building",
                "city": "Nairobi",
                "state": "NBI",
                "postal_code": "00100",
                "zip_code": "00100"
            }
        }
        
        result = await self.make_request("POST", "/pesapal/submit-order", payment_data)
        
        if result and result.get("redirect_url"):
            print(f"\n🔗 Payment URL: {result['redirect_url']}")
            print("💡 Open this URL in your browser to complete the payment")
            
        return result

    async def check_transaction_status(self, order_tracking_id: str):
        """Check transaction status"""
        print("\n" + "="*50)
        print("CHECKING TRANSACTION STATUS")
        print("="*50)
        
        result = await self.make_request("GET", f"/pesapal/transaction-status/{order_tracking_id}")
        return result

    async def get_api_config(self):
        """Get API configuration"""
        print("\n" + "="*50)
        print("API CONFIGURATION")
        print("="*50)
        
        result = await self.make_request("GET", "/pesapal/config")
        return result

    async def run_complete_example(self):
        """Run a complete payment flow example"""
        print("🚀 Starting Pesapal API Example")
        print("Make sure your FastAPI server is running on http://localhost:8000")
        
        try:
            # 1. Check API configuration
            await self.get_api_config()
            
            # 2. Test authentication
            auth_result = await self.test_authentication()
            if not auth_result or auth_result.get("status") != "200":
                print("❌ Authentication failed. Check your credentials.")
                return
            
            # 3. Register IPN URL (optional, may already be registered)
            print("\n📡 Registering IPN URL...")
            await self.register_ipn_url()
            
            # 4. Get registered IPNs
            await self.get_registered_ipns()
            
            # 5. Submit payment order
            payment_result = await self.submit_payment_order()
            
            if payment_result and payment_result.get("order_tracking_id"):
                order_id = payment_result["order_tracking_id"]
                
                # 6. Check transaction status
                await asyncio.sleep(2)  # Wait a bit
                await self.check_transaction_status(order_id)
                
                print(f"\n✅ Payment flow completed!")
                print(f"📋 Order Tracking ID: {order_id}")
                print(f"🔗 Payment URL: {payment_result.get('redirect_url', 'N/A')}")
                
            else:
                print("❌ Payment order submission failed")
                
        except Exception as e:
            print(f"❌ Error running example: {e}")
        
        finally:
            await self.close_session()

async def main():
    """Main function to run the example"""
    example = PesapalExample()
    await example.run_complete_example()

if __name__ == "__main__":
    print("Pesapal FastAPI Backend Example")
    print("=" * 50)
    print("This example demonstrates the Pesapal payment flow:")
    print("1. Authentication")
    print("2. IPN URL registration")
    print("3. Payment order submission")
    print("4. Transaction status checking")
    print("\nMake sure your FastAPI server is running first!")
    print("Start server with: python pesapal_api.py")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    
    try:
        input()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Example cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
