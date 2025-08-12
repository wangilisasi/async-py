# Pesapal API - Synchronous Implementation

This directory contains both **asynchronous** and **synchronous** implementations of the Pesapal API FastAPI backend.

## Synchronous Files

- **`pesapal_api_sync.py`** - Main synchronous FastAPI backend
- **`example_usage_sync.py`** - Example client using requests library
- **`SYNC_VS_ASYNC_COMPARISON.md`** - Detailed comparison between both versions

## Quick Start (Synchronous Version)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Copy and configure your environment:
```bash
cp env_example.txt .env
# Edit .env with your Pesapal credentials
```

### 3. Start the Synchronous Server
```bash
python pesapal_api_sync.py
```

The server will start on `http://localhost:8000`

### 4. Test the API
In a new terminal, run the example:
```bash
python example_usage_sync.py
```

## API Endpoints (Same for Both Versions)

- `GET /health` - Health check
- `POST /pesapal/auth` - Get access token
- `POST /pesapal/register-ipn` - Register IPN URL
- `GET /pesapal/ipns` - Get registered IPNs
- `POST /pesapal/submit-order` - Submit payment order
- `GET /pesapal/transaction-status/{id}` - Check transaction status
- `GET /pesapal/callback` - Payment callback handler
- `POST/GET /pesapal/ipn` - IPN notification handler
- `GET /pesapal/config` - Get configuration

## Key Differences from Async Version

### Synchronous Implementation:
- Uses `requests` library instead of `aiohttp`
- No `async`/`await` keywords
- Simpler error handling
- Linear code execution
- Easier to debug and understand
- Better for learning and prototyping

### Performance Trade-offs:
- **Pros**: Lower latency for single requests, simpler code
- **Cons**: Cannot handle as many concurrent requests

## When to Use Synchronous Version

Choose the synchronous version when:
- 🎓 **Learning**: You're new to FastAPI or async programming
- 🚀 **Prototyping**: Building MVPs or proof of concepts
- 📊 **Low Traffic**: Handling < 100 concurrent users
- 🔧 **Debugging**: Need easier troubleshooting
- 🏢 **Legacy Systems**: Integrating with existing sync code

## Example Usage

```python
import requests

# Make a payment request
response = requests.post("http://localhost:8000/pesapal/submit-order", json={
    "id": "ORDER-123",
    "currency": "KES", 
    "amount": 100.00,
    "description": "Test payment",
    "billing_address": {
        "email_address": "customer@example.com",
        "phone_number": "0723456789",
        "country_code": "KE",
        "first_name": "John",
        "last_name": "Doe"
    }
})

payment_data = response.json()
print(f"Payment URL: {payment_data['redirect_url']}")
```

## Migration Between Versions

Both versions use the same:
- ✅ Pydantic models
- ✅ API endpoints and paths  
- ✅ Environment configuration
- ✅ Business logic

You can easily switch between versions by changing the import and removing/adding `async`/`await` keywords.

## Support

For questions about:
- **Async Version**: See `README.md` and `pesapal_api.py`
- **Sync Version**: See this file and `pesapal_api_sync.py`
- **Comparison**: See `SYNC_VS_ASYNC_COMPARISON.md`
- **Pesapal API**: See `PESAPAL_DOCS.md`
