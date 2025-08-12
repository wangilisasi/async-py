"""
Pesapal API 3.0 FastAPI Backend Implementation (Synchronous Version)

This module provides a synchronous FastAPI backend for integrating with Pesapal payment gateway.
It implements all the core functionality for one-time payments including:
- Authentication and token management
- IPN URL registration
- Order submission and payment processing
- Transaction status checking
- Callback and IPN handling

Based on Pesapal API 3.0 documentation.
Uses requests library for synchronous HTTP operations.
"""

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
class PesapalConfig:
    def __init__(self):
        # Pesapal API Configuration
        self.consumer_key = os.getenv("PESAPAL_CONSUMER_KEY", "your_consumer_key_here")
        self.consumer_secret = os.getenv("PESAPAL_CONSUMER_SECRET", "your_consumer_secret_here")
        
        # Environment URLs
        self.is_sandbox = os.getenv("PESAPAL_ENVIRONMENT", "sandbox").lower() == "sandbox"
        
        if self.is_sandbox:
            self.base_url = "https://cybqa.pesapal.com/pesapalv3"
        else:
            self.base_url = "https://pay.pesapal.com/v3"
        
        # API Endpoints
        self.auth_url = f"{self.base_url}/api/Auth/RequestToken"
        self.register_ipn_url = f"{self.base_url}/api/URLSetup/RegisterIPN"
        self.get_ipns_url = f"{self.base_url}/api/URLSetup/GetIpnList"
        self.submit_order_url = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        self.transaction_status_url = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        
        # Application URLs
        self.app_base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        self.ipn_url = f"{self.app_base_url}/pesapal/ipn"
        self.callback_url = f"{self.app_base_url}/pesapal/callback"

config = PesapalConfig()

# Pydantic Models
class BillingAddress(BaseModel):
    """Customer billing address information"""
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2, description="2-character ISO country code")
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    line_1: Optional[str] = None
    line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=3)
    postal_code: Optional[str] = None
    zip_code: Optional[str] = None

class PaymentRequest(BaseModel):
    """Payment request model"""
    id: str = Field(..., max_length=50, description="Unique merchant reference")
    currency: str = Field(..., description="ISO currency code (e.g., KES, USD)")
    amount: float = Field(..., gt=0, description="Payment amount")
    description: str = Field(..., max_length=100, description="Payment description")
    callback_url: Optional[str] = None
    cancellation_url: Optional[str] = None
    redirect_mode: Optional[str] = Field("TOP_WINDOW", description="TOP_WINDOW or PARENT_WINDOW")
    branch: Optional[str] = None
    billing_address: BillingAddress

class AuthRequest(BaseModel):
    """Authentication request model"""
    consumer_key: str
    consumer_secret: str

class IPNRegistration(BaseModel):
    """IPN URL registration model"""
    url: str
    ipn_notification_type: str = Field(..., description="GET or POST")

class PesapalError(BaseModel):
    """Pesapal error response model"""
    error_type: Optional[str] = None
    code: Optional[str] = None
    message: Optional[str] = None
    call_back_url: Optional[str] = None

class AuthResponse(BaseModel):
    """Authentication response model"""
    token: Optional[str] = None
    expiryDate: Optional[str] = None
    error: Optional[PesapalError] = None
    status: str
    message: str

class PaymentResponse(BaseModel):
    """Payment response model"""
    order_tracking_id: Optional[str] = None
    merchant_reference: Optional[str] = None
    redirect_url: Optional[str] = None
    error: Optional[PesapalError] = None
    status: str
    message: Optional[str] = None

class TransactionStatus(BaseModel):
    """Transaction status response model"""
    payment_method: Optional[str] = None
    amount: Optional[float] = None
    created_date: Optional[str] = None
    confirmation_code: Optional[str] = None
    payment_status_description: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None
    payment_account: Optional[str] = None
    call_back_url: Optional[str] = None
    status_code: Optional[int] = None
    merchant_reference: Optional[str] = None
    currency: Optional[str] = None
    error: Optional[PesapalError] = None
    status: str

# Global variables for token management
current_token: Optional[str] = None
token_expiry: Optional[datetime] = None

class PesapalClient:
    """Pesapal API client for making HTTP requests using requests library"""
    
    def __init__(self):
        self.session = requests.Session()
        # Set default timeout for all requests
        self.session.timeout = 30
    
    def make_request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict] = None, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers or {},
                json=json_data,
                params=params,
                timeout=30
            )
            
            # Log request details
            logger.info(f"{method} {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                logger.error(f"API Error {response.status_code}: {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Pesapal API error: {error_text}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP Client Error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Network error: {str(e)}"
            )
    
    def close_session(self):
        """Close requests session"""
        if self.session:
            self.session.close()

# Initialize client
pesapal_client = PesapalClient()

def get_access_token() -> str:
    """Get or refresh Pesapal access token"""
    global current_token, token_expiry
    
    # Check if current token is still valid (with 1 minute buffer)
    if current_token and token_expiry and datetime.utcnow() < (token_expiry - timedelta(minutes=1)):
        return current_token
    
    logger.info("Requesting new access token from Pesapal")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    auth_data = {
        "consumer_key": config.consumer_key,
        "consumer_secret": config.consumer_secret
    }
    
    try:
        response = pesapal_client.make_request(
            method="POST",
            url=config.auth_url,
            headers=headers,
            json_data=auth_data
        )
        
        if response.get("status") == "200" and response.get("token"):
            current_token = response["token"]
            
            # Parse expiry date
            if response.get("expiryDate"):
                token_expiry = datetime.fromisoformat(
                    response["expiryDate"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
            else:
                # Default to 5 minutes from now if no expiry provided
                token_expiry = datetime.utcnow() + timedelta(minutes=5)
            
            logger.info(f"New token obtained, expires at: {token_expiry}")
            return current_token
        else:
            error_msg = response.get("message", "Unknown authentication error")
            logger.error(f"Authentication failed: {error_msg}")
            raise HTTPException(status_code=401, detail=f"Authentication failed: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

def get_auth_headers() -> Dict[str, str]:
    """Get headers with Bearer token for authenticated requests"""
    token = get_access_token()
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

# FastAPI app
app = FastAPI(
    title="Pesapal API Backend (Sync)",
    description="Synchronous FastAPI backend for Pesapal payment gateway integration",
    version="1.0.0"
)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Authentication endpoints
@app.post("/pesapal/auth", response_model=AuthResponse)
def authenticate():
    """
    Get Pesapal access token
    
    This endpoint authenticates with Pesapal and returns an access token
    that's valid for 5 minutes. The token is cached automatically.
    """
    try:
        token = get_access_token()
        return AuthResponse(
            token=token,
            expiryDate=token_expiry.isoformat() + "Z" if token_expiry else None,
            error=None,
            status="200",
            message="Authentication successful"
        )
    except HTTPException as e:
        return AuthResponse(
            token=None,
            expiryDate=None,
            error=PesapalError(
                error_type="authentication_error",
                code=str(e.status_code),
                message=e.detail
            ),
            status=str(e.status_code),
            message=e.detail
        )

# IPN Management endpoints
@app.post("/pesapal/register-ipn")
def register_ipn(ipn_data: IPNRegistration):
    """
    Register IPN URL with Pesapal
    
    This endpoint registers your IPN (Instant Payment Notification) URL
    with Pesapal. The IPN URL will receive payment status notifications.
    """
    try:
        headers = get_auth_headers()
        
        response = pesapal_client.make_request(
            method="POST",
            url=config.register_ipn_url,
            headers=headers,
            json_data=ipn_data.dict()
        )
        
        logger.info(f"IPN registered successfully: {response}")
        return response
        
    except HTTPException as e:
        logger.error(f"IPN registration failed: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in IPN registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"IPN registration error: {str(e)}")

@app.get("/pesapal/ipns")
def get_registered_ipns():
    """
    Get all registered IPN URLs
    
    This endpoint retrieves all IPN URLs registered for your merchant account.
    """
    try:
        headers = get_auth_headers()
        
        response = pesapal_client.make_request(
            method="GET",
            url=config.get_ipns_url,
            headers=headers
        )
        
        return response
        
    except HTTPException as e:
        logger.error(f"Failed to get IPNs: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error getting IPNs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting IPNs: {str(e)}")

# Payment endpoints
@app.post("/pesapal/submit-order", response_model=PaymentResponse)
def submit_order(payment_request: PaymentRequest):
    """
    Submit payment order to Pesapal
    
    This endpoint creates a payment order and returns a redirect URL
    where the customer can complete the payment.
    """
    try:
        headers = get_auth_headers()
        
        # Prepare the order data
        order_data = payment_request.dict()
        
        # Set default callback URL if not provided
        if not order_data.get("callback_url"):
            order_data["callback_url"] = config.callback_url
        
        # For demo purposes, we'll use a default notification_id
        # In production, you should register your IPN first and use the returned ID
        order_data["notification_id"] = os.getenv("PESAPAL_IPN_ID", "your-ipn-id-here")
        
        logger.info(f"Submitting order: {payment_request.id}")
        
        response = pesapal_client.make_request(
            method="POST",
            url=config.submit_order_url,
            headers=headers,
            json_data=order_data
        )
        
        logger.info(f"Order submitted successfully: {response}")
        
        return PaymentResponse(
            order_tracking_id=response.get("order_tracking_id"),
            merchant_reference=response.get("merchant_reference"),
            redirect_url=response.get("redirect_url"),
            error=None,
            status=response.get("status", "200"),
            message=response.get("message")
        )
        
    except HTTPException as e:
        logger.error(f"Order submission failed: {e.detail}")
        return PaymentResponse(
            order_tracking_id=None,
            merchant_reference=payment_request.id,
            redirect_url=None,
            error=PesapalError(
                error_type="order_submission_error",
                code=str(e.status_code),
                message=e.detail
            ),
            status=str(e.status_code),
            message=e.detail
        )
    except Exception as e:
        logger.error(f"Unexpected error in order submission: {str(e)}")
        return PaymentResponse(
            order_tracking_id=None,
            merchant_reference=payment_request.id,
            redirect_url=None,
            error=PesapalError(
                error_type="internal_error",
                code="500",
                message=str(e)
            ),
            status="500",
            message=f"Internal error: {str(e)}"
        )

@app.get("/pesapal/transaction-status/{order_tracking_id}", response_model=TransactionStatus)
def get_transaction_status(order_tracking_id: str):
    """
    Get payment transaction status
    
    This endpoint checks the status of a payment transaction using
    the order tracking ID returned from the submit order endpoint.
    """
    try:
        headers = get_auth_headers()
        
        params = {"orderTrackingId": order_tracking_id}
        
        response = pesapal_client.make_request(
            method="GET",
            url=config.transaction_status_url,
            headers=headers,
            params=params
        )
        
        logger.info(f"Transaction status retrieved for {order_tracking_id}: {response.get('payment_status_description')}")
        
        return TransactionStatus(**response)
        
    except HTTPException as e:
        logger.error(f"Failed to get transaction status: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error getting transaction status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transaction status: {str(e)}")

# Callback and IPN handling endpoints
@app.get("/pesapal/callback")
def payment_callback(
    request: Request,
    OrderTrackingId: Optional[str] = None,
    OrderMerchantReference: Optional[str] = None,
    OrderNotificationType: Optional[str] = None
):
    """
    Handle payment callback from Pesapal
    
    This endpoint is called by Pesapal after a customer completes
    or cancels a payment. It should redirect the customer to an
    appropriate page on your application.
    """
    logger.info(f"Payment callback received: {OrderTrackingId}, {OrderMerchantReference}, {OrderNotificationType}")
    
    callback_data = {
        "order_tracking_id": OrderTrackingId,
        "merchant_reference": OrderMerchantReference,
        "notification_type": OrderNotificationType,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # In a real application, you would:
    # 1. Get the transaction status using OrderTrackingId
    # 2. Update your database with the payment status
    # 3. Redirect the customer to a success/failure page
    
    if OrderTrackingId:
        try:
            # Get the actual transaction status
            transaction_status = get_transaction_status(OrderTrackingId)
            callback_data["transaction_status"] = transaction_status.dict()
        except Exception as e:
            logger.error(f"Error getting transaction status in callback: {str(e)}")
            callback_data["error"] = str(e)
    
    return JSONResponse(
        content={
            "message": "Payment callback processed",
            "data": callback_data
        }
    )

@app.post("/pesapal/ipn")
@app.get("/pesapal/ipn")
def payment_ipn(request: Request):
    """
    Handle IPN (Instant Payment Notification) from Pesapal
    
    This endpoint receives payment status notifications from Pesapal.
    It should process the notification and respond with status 200.
    """
    try:
        # Handle both GET and POST IPN notifications
        if request.method == "GET":
            # GET parameters
            query_params = dict(request.query_params)
            order_tracking_id = query_params.get("OrderTrackingId")
            merchant_reference = query_params.get("OrderMerchantReference")
            notification_type = query_params.get("OrderNotificationType")
        else:
            # For POST requests, we need to handle this differently in sync context
            # This is a simplified version - in production you'd need proper request body parsing
            order_tracking_id = request.query_params.get("OrderTrackingId")
            merchant_reference = request.query_params.get("OrderMerchantReference")
            notification_type = request.query_params.get("OrderNotificationType")
        
        logger.info(f"IPN received: {order_tracking_id}, {merchant_reference}, {notification_type}")
        
        # Process the IPN notification
        if order_tracking_id and notification_type == "IPNCHANGE":
            try:
                # Get the actual transaction status
                transaction_status = get_transaction_status(order_tracking_id)
                
                # Here you would typically:
                # 1. Update your database with the payment status
                # 2. Send notifications to relevant parties
                # 3. Trigger any business logic based on payment status
                
                logger.info(f"IPN processed successfully for {order_tracking_id}: {transaction_status.payment_status_description}")
                
                # Respond to Pesapal confirming receipt
                return JSONResponse(
                    content={
                        "orderNotificationType": notification_type,
                        "orderTrackingId": order_tracking_id,
                        "orderMerchantReference": merchant_reference,
                        "status": 200
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing IPN: {str(e)}")
                return JSONResponse(
                    content={
                        "orderNotificationType": notification_type,
                        "orderTrackingId": order_tracking_id,
                        "orderMerchantReference": merchant_reference,
                        "status": 500,
                        "error": str(e)
                    }
                )
        else:
            logger.warning(f"Invalid IPN notification: {order_tracking_id}, {notification_type}")
            return JSONResponse(
                content={
                    "status": 400,
                    "error": "Invalid IPN notification"
                }
            )
            
    except Exception as e:
        logger.error(f"Error handling IPN: {str(e)}")
        return JSONResponse(
            content={
                "status": 500,
                "error": f"IPN processing error: {str(e)}"
            }
        )

# Utility endpoints
@app.get("/pesapal/config")
def get_config():
    """Get current Pesapal configuration (for debugging)"""
    return {
        "environment": "sandbox" if config.is_sandbox else "production",
        "base_url": config.base_url,
        "app_base_url": config.app_base_url,
        "ipn_url": config.ipn_url,
        "callback_url": config.callback_url,
        "consumer_key_set": bool(config.consumer_key and config.consumer_key != "your_consumer_key_here"),
        "consumer_secret_set": bool(config.consumer_secret and config.consumer_secret != "your_consumer_secret_here")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pesapal_api_sync:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
