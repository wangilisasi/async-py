# Pesapal FastAPI Backend

A comprehensive FastAPI backend implementation for integrating with Pesapal API 3.0 payment gateway. This backend provides all the essential functionality for processing one-time payments through Pesapal.

## Features

- ✅ **Authentication**: Automatic token management with refresh
- ✅ **IPN Management**: Register and manage Instant Payment Notification URLs
- ✅ **Payment Processing**: Submit payment orders and get redirect URLs
- ✅ **Transaction Status**: Check payment status and get transaction details
- ✅ **Callback Handling**: Handle payment callbacks and IPN notifications
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Type Safety**: Full Pydantic model validation
- ✅ **Async Support**: Built with async/await for high performance

## API Endpoints

### Authentication
- `POST /pesapal/auth` - Get access token

### IPN Management
- `POST /pesapal/register-ipn` - Register IPN URL
- `GET /pesapal/ipns` - Get registered IPN URLs

### Payment Processing
- `POST /pesapal/submit-order` - Submit payment order
- `GET /pesapal/transaction-status/{order_tracking_id}` - Check transaction status

### Callback Handling
- `GET /pesapal/callback` - Handle payment callbacks
- `POST|GET /pesapal/ipn` - Handle IPN notifications

### Utility
- `GET /health` - Health check
- `GET /pesapal/config` - Get API configuration

## Quick Start

### 1. Installation

```bash
# Clone or download the files
# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the environment example file and configure your credentials:

```bash
cp env_example.txt .env
```

Edit `.env` file with your Pesapal credentials:

```env
PESAPAL_CONSUMER_KEY=your_actual_consumer_key
PESAPAL_CONSUMER_SECRET=your_actual_consumer_secret
PESAPAL_ENVIRONMENT=sandbox  # or production
APP_BASE_URL=http://localhost:8000
```

### 3. Start the Server

```bash
python pesapal_api.py
```

The server will start on `http://localhost:8000`

### 4. Test the API

Run the example script:

```bash
python example_usage.py
```

Or visit the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Basic Payment Flow

```python
import aiohttp
import asyncio

async def create_payment():
    async with aiohttp.ClientSession() as session:
        # Submit payment order
        payment_data = {
            "id": "ORDER-123456",
            "currency": "KES",
            "amount": 1000.00,
            "description": "Test payment",
            "billing_address": {
                "email_address": "customer@example.com",
                "phone_number": "0723456789",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
        
        async with session.post(
            "http://localhost:8000/pesapal/submit-order",
            json=payment_data
        ) as response:
            result = await response.json()
            
            if result.get("redirect_url"):
                print(f"Payment URL: {result['redirect_url']}")
                return result["order_tracking_id"]

# Run the example
asyncio.run(create_payment())
```

### Check Payment Status

```python
async def check_status(order_tracking_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/pesapal/transaction-status/{order_tracking_id}"
        ) as response:
            status = await response.json()
            print(f"Payment Status: {status.get('payment_status_description')}")
            return status
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PESAPAL_CONSUMER_KEY` | Your Pesapal consumer key | - | Yes |
| `PESAPAL_CONSUMER_SECRET` | Your Pesapal consumer secret | - | Yes |
| `PESAPAL_ENVIRONMENT` | Environment (sandbox/production) | sandbox | No |
| `APP_BASE_URL` | Your application base URL | http://localhost:8000 | No |
| `PESAPAL_IPN_ID` | IPN ID after registration | - | No |

### Pesapal Credentials

#### Sandbox/Test Credentials
- Get test credentials from: [Pesapal Sandbox](https://cybqa.pesapal.com)
- Download test credentials from the documentation

#### Production Credentials
- Create a business account at: [Pesapal Business](https://pay.pesapal.com)
- Your live credentials will be sent to your merchant email

## Payment Flow

1. **Authentication**: Backend automatically gets and manages access tokens
2. **IPN Registration**: Register your IPN URL to receive payment notifications
3. **Order Submission**: Submit payment order with customer details
4. **Customer Payment**: Redirect customer to Pesapal payment page
5. **Payment Processing**: Customer completes payment on Pesapal
6. **Callback**: Customer is redirected back to your application
7. **IPN Notification**: Pesapal sends payment status to your IPN URL
8. **Status Check**: Verify payment status using transaction status API

## Payment Status Codes

| Status Code | Description |
|-------------|-------------|
| 0 | INVALID |
| 1 | COMPLETED |
| 2 | FAILED |
| 3 | REVERSED |

## Error Handling

The API includes comprehensive error handling:

- **Authentication Errors**: Invalid credentials, expired tokens
- **Validation Errors**: Invalid request data, missing fields
- **Network Errors**: Connection issues, timeouts
- **Pesapal API Errors**: Upstream API errors with detailed messages

All errors are logged and returned in a consistent format:

```json
{
  "error": {
    "error_type": "authentication_error",
    "code": "401",
    "message": "Invalid credentials"
  },
  "status": "401",
  "message": "Authentication failed"
}
```

## Security Considerations

1. **Environment Variables**: Never commit credentials to version control
2. **HTTPS**: Use HTTPS in production for all endpoints
3. **IPN Security**: Verify IPN calls are from Pesapal domains
4. **Token Management**: Tokens are automatically refreshed and cached
5. **Input Validation**: All inputs are validated using Pydantic models

## Production Deployment

### 1. Environment Setup
```bash
# Set production environment
export PESAPAL_ENVIRONMENT=production
export PESAPAL_CONSUMER_KEY=your_production_key
export PESAPAL_CONSUMER_SECRET=your_production_secret
export APP_BASE_URL=https://yourdomain.com
```

### 2. HTTPS Configuration
Ensure your application is served over HTTPS in production.

### 3. IPN URL Requirements
- IPN URL must be publicly accessible
- Must respond to Pesapal's domain calls
- Should return status 200 for successful processing

### 4. Logging
Configure appropriate logging levels for production:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your consumer key and secret
   - Ensure you're using the correct environment (sandbox/production)

2. **IPN Registration Failed**
   - Ensure your IPN URL is publicly accessible
   - Check that the URL responds correctly

3. **Payment Order Failed**
   - Verify all required fields are provided
   - Check that your IPN is registered and active

4. **Network Errors**
   - Check internet connectivity
   - Verify Pesapal API endpoints are accessible

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing with Postman

Import the Pesapal Postman collection:
- URL: https://documenter.getpostman.com/view/6715320/UyxepTv1

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

For Pesapal API support:
- Documentation: [Pesapal API 3.0 Docs](https://developer.pesapal.com)
- Support: Contact Pesapal support team

For this implementation:
- Check the example usage script
- Review the API documentation
- Enable debug logging for detailed error information

## License

This implementation is provided as-is for educational and integration purposes. Please ensure compliance with Pesapal's terms of service and your local regulations.
