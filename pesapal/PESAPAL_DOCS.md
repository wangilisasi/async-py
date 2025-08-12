# Pesapal API v3.0 Documentation

Welcome to the Pesapal API v3.0. This guide provides all the information you need to integrate Pesapal's payment services into your application. Our RESTful API uses standard HTTP verbs, accepts JSON-encoded requests, and returns JSON-encoded responses.

## Getting Started: The Integration Flow

Integrating with Pesapal follows these five core steps:

1.  **Authentication:** Obtain an access token using your merchant credentials.
2.  **Register IPN URL:** Register your Instant Payment Notification (IPN) endpoint to receive real-time transaction updates.
3.  **Submit Order:** Send the transaction details to Pesapal to generate a payment redirection link.
4.  **Handle Callback & IPN:** Process the information Pesapal sends to your `callback_url` and `ipn_url` after a payment attempt.
5.  **Get Transaction Status:** Securely query the final status of the transaction using the `OrderTrackingId`.

---

## Core Concepts

### Environments

Pesapal provides two distinct environments. Use the Sandbox for development and testing before going live.

| Environment | Base URL                               |
| :---------- | :------------------------------------- |
| **Sandbox** | `https://cybqa.pesapal.com/pesapalv3`    |
| **Live**    | `https://pay.pesapal.com/v3`             |

### Authentication

All API endpoints, except for `Auth/RequestToken`, require a Bearer Token for authentication. This token is obtained from the authentication endpoint and is valid for **5 minutes**. You must include it in the `Authorization` header of your requests.

**Header Example:** `Authorization: Bearer <YOUR_ACCESS_TOKEN>`

### Standard Headers

All `POST` requests must include the following headers:

```
Accept: application/json
Content-Type: application/json
```

### Error Handling

If an API call results in an error, Pesapal will return a standard error object with a `4xx` or `5xx` status code.

**Error Object Structure:**

```json
{
  "error": {
    "type": "error_type",
    "code": "response_code",
    "message": "A detailed error message goes here."
  }
}
```

---

## Step 1: Authentication

### `POST /api/Auth/RequestToken`

This endpoint generates an access token required to authorize subsequent API calls.

#### Request Body

| Parameter         | Type   | Required | Description                               |
| :---------------- | :----- | :------- | :---------------------------------------- |
| `consumer_key`    | String | Yes      | Your Pesapal merchant consumer key.       |
| `consumer_secret` | String | Yes      | Your Pesapal merchant consumer secret.    |

#### Sample Request

```json
{
  "consumer_key": "YOUR_CONSUMER_KEY",
  "consumer_secret": "YOUR_CONSUMER_SECRET"
}
```

#### Sample Response (`200 OK`)

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiryDate": "2025-08-12T10:05:30.517Z",
  "error": null,
  "status": "200",
  "message": "Request processed successfully"
}
```

---

## Step 2: IPN URL Management

An Instant Payment Notification (IPN) URL is a crucial endpoint on your server that Pesapal calls to notify you of transaction status changes in real-time. **You must register at least one IPN URL before submitting orders.**

### Register an IPN URL

#### `POST /api/URLSetup/RegisterIPN`

Registers a new IPN URL and returns a unique `ipn_id` for use in order submissions.

#### Request Body

| Parameter               | Type   | Required | Description                                                              |
| :---------------------- | :----- | :------- | :----------------------------------------------------------------------- |
| `url`                   | String | Yes      | The publicly accessible URL for receiving notifications.                 |
| `ipn_notification_type` | String | Yes      | The HTTP method Pesapal will use: `GET` or `POST`.                       |

#### Sample Request

```json
{
  "url": "https://www.myapplication.com/ipn-handler",
  "ipn_notification_type": "GET"
}
```

#### Sample Response (`200 OK`)

```json
{
  "url": "https://www.myapplication.com/ipn-handler",
  "created_date": "2025-08-12T10:02:22.282Z",
  "ipn_id": "84740ab4-3cd9-47da-8a4f-dd1db53494b5",
  "ipn_notification_type_description": "GET",
  "ipn_status_description": "Active",
  "error": null,
  "status": "200"
}
```

### Get Registered IPN URLs

#### `GET /api/URLSetup/GetIpnList`

Fetches a list of all IPN URLs registered to your merchant account.

#### Sample Response (`200 OK`)

```json
[
  {
    "url": "https://www.myapplication.com/ipn-handler",
    "created_date": "2025-08-12T10:02:22.282Z",
    "ipn_id": "84740ab4-3cd9-47da-8a4f-dd1db53494b5",
    "error": null,
    "status": "200"
  }
]
```

---

## Step 3: Submit an Order Request

### `POST /api/Transactions/SubmitOrderRequest`

Creates a transaction and generates a `redirect_url` for the customer to complete payment.

#### Request Body

| Parameter         | Type   | Required | Description                                                              |
| :---------------- | :----- | :------- | :----------------------------------------------------------------------- |
| `id`              | String | Yes      | A unique order ID generated by your system (max 50 chars). **Must be unique for every transaction.** |
| `currency`        | String | Yes      | ISO currency code (e.g., `KES`, `UGX`, `USD`).                         |
| `amount`          | Float  | Yes      | The total amount to be charged.                                         |
| `description`     | String | Yes      | A brief description of the order (max 100 chars).                      |
| `callback_url`    | String | Yes      | The URL where the customer is redirected after the payment attempt.    |
| `notification_id` | String | Yes      | The `ipn_id` obtained from the IPN registration step.                  |
| `billing_address` | Object | Yes      | An object containing the customer's billing information. See details below. |
| `cancellation_url`| String | Optional | A URL to redirect the customer to if they cancel the payment.          |
| `redirect_mode`   | String | Optional | Defines how the `callback_url` is loaded. `TOP_WINDOW` (default) or `PARENT_WINDOW`. |
| `branch`          | String | Optional | The name of the store or branch associated with the payment.            |

#### `billing_address` Object

| Parameter       | Type   | Required                               | Description                               |
| :-------------- | :----- | :------------------------------------- | :---------------------------------------- |
| `email_address` | String | Yes (if `phone_number` is not provided) | Customer's email address.                 |
| `phone_number`  | String | Yes (if `email_address` is not provided) | Customer's phone number.                  |
| `country_code`  | String | Optional                               | 2-letter ISO 3166-1 country code (e.g., `KE`). |
| `first_name`    | String | Optional                               | Customer's first name.                    |
| `last_name`     | String | Optional                               | Customer's last name.                     |

#### Sample Request

```json
{
  "id": "ORD-2025-12345",
  "currency": "KES",
  "amount": 1500.5,
  "description": "Payment for Invoice #INV-089",
  "callback_url": "https://www.myapplication.com/payment-complete",
  "notification_id": "84740ab4-3cd9-47da-8a4f-dd1db53494b5",
  "billing_address": {
    "email_address": "john.doe@example.com",
    "phone_number": "0723000111",
    "country_code": "KE",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### Sample Response (`200 OK`)

```json
{
  "order_tracking_id": "b945e4af-80a5-4ec1-8706-e03f8332fb04",
  "merchant_reference": "ORD-2025-12345",
  "redirect_url": "https://cybqa.pesapal.com/pesapaliframe/PesapalIframe3/Index/?OrderTrackingId=b945e4af-80a5-4ec1-8706-e03f8332fb04",
  "error": null,
  "status": "200"
}
```

---

## Step 4: Handle Callback and IPN

After the customer attempts a payment, Pesapal will send notifications to your `callback_url` and your registered `ipn_url`.

**Security Warning:** Neither the callback nor the IPN request contains the final payment status. They are simply notifications that a transaction's state has changed. You **must** use the `GetTransactionStatus` endpoint (Step 5) to get the definitive transaction result.

### Callback Request

The customer's browser is redirected to your `callback_url` with the following query parameters:

| Parameter                | Description                                          |
| :----------------------- | :--------------------------------------------------- |
| `OrderTrackingId`        | The unique ID generated by Pesapal for this order.   |
| `OrderMerchantReference` | Your unique order ID (`id`) from the order request.  |
| `OrderNotificationType`  | Always `CALLBACKURL`.                                |

**Sample Callback URL:**
`https://www.myapplication.com/payment-complete?OrderTrackingId=...&OrderMerchantReference=...&OrderNotificationType=CALLBACKURL`

### IPN Request

Simultaneously, Pesapal sends a request to your registered `ipn_url`.

| Parameter                | Description                                          |
| :----------------------- | :--------------------------------------------------- |
| `OrderTrackingId`        | The unique ID generated by Pesapal for this order.   |
| `OrderMerchantReference` | Your unique order ID (`id`) from the order request.  |
| `OrderNotificationType`  | Always `IPNCHANGE`.                                  |

**Sample IPN `GET` Request:**
`https://www.myapplication.com/ipn-handler?OrderTrackingId=...&OrderMerchantReference=...&OrderNotificationType=IPNCHANGE`

---

## Step 5: Get Transaction Status

### `GET /api/Transactions/GetTransactionStatus`

Use this endpoint to securely fetch the final status and details of a transaction. You should call this endpoint whenever your `callback_url` or `ipn_url` is hit.

#### Request

The `orderTrackingId` is passed as a query parameter in the URL.

**URL Format:** `/api/Transactions/GetTransactionStatus?orderTrackingId=<OrderTrackingId>`

#### Response Parameters

| Parameter                    | Type   | Description                                                              |
| :--------------------------- | :----- | :----------------------------------------------------------------------- |
| `payment_method`             | String | The method used for payment (e.g., `Visa`, `Mpesa`).                   |
| `amount`                     | Float  | The amount paid by the customer.                                        |
| `payment_status_description` | String | The final status of the transaction: `COMPLETED`, `FAILED`, `REVERSED`, or `INVALID`. |
| `confirmation_code`          | String | The unique confirmation code from the payment provider.                 |
| `merchant_reference`         | String | Your unique order ID.                                                   |
| `status_code`                | Int    | A numerical code for the status: `1` (COMPLETED), `2` (FAILED), `3` (REVERSED), `0` (INVALID). |

#### Sample Response (`200 OK` - Completed)

```json
{
  "payment_method": "Visa",
  "amount": 1500.5,
  "created_date": "2025-08-12T10:11:09.763Z",
  "confirmation_code": "PSPL-CONFIRM-XYZ123",
  "payment_status_description": "Completed",
  "description": "Transaction processed successfully.",
  "message": "Request processed successfully",
  "payment_account": "476173******0010",
  "call_back_url": "https://www.myapplication.com/payment-complete?OrderTrackingId=...",
  "status_code": 1,
  "merchant_reference": "ORD-2025-12345",
  "currency": "KES",
  "status": "200"
}
```

---

## Final Step: Responding to the IPN

After you have received the IPN, processed it, and queried the transaction status, your server **must** respond to Pesapal's IPN request with a specific JSON object to acknowledge receipt.

#### IPN Acknowledgement Response

Your IPN endpoint must output a JSON string with the following structure. Failure to do so may result in Pesapal re-sending the IPN notification.

```json
{
  "orderNotificationType": "IPNCHANGE",
  "orderTrackingId": "THE_ID_YOU_RECEIVED",
  "orderMerchantReference": "YOUR_ORDER_ID",
  "status": 200
}
```

-   **`status: 200`**: Confirms that you received and successfully processed the notification.
-   **`status: 500`**: Informs Pesapal that you received the notification but encountered an error on your end. Pesapal may attempt to resend the notification.

---

## Summary

This documentation provides a complete guide to integrating with Pesapal API v3.0. The five-step process ensures secure payment processing with proper notification handling. Remember to always verify transaction status using the dedicated endpoint rather than relying solely on callback or IPN notifications for security reasons.

For additional support or questions about the integration process, please refer to the official Pesapal developer resources or contact their technical support team.
