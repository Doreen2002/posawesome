# import qrcode
# import base64
# from io import BytesIO
# import frappe
# import requests
# from frappe import _

# @frappe.whitelist()
# def generate_payment_qr(provider, amount, invoice):
#     # Simulate provider-specific QR data
#     qr_data_map = {
#         "eSewa": f"https://esewa.com.np/pay?invoice={invoice}&amount={amount}",
#         "Khalti": f"https://khalti.com/pay?invoice={invoice}&amount={amount}",
#         "FonePay": f"https://fonepay.com/qr/{invoice}?amt={amount}",
#         "NepalPay": f"https://nepalpay.com/qr?inv={invoice}&amt={amount}",
#     }

#     qr_data = qr_data_map.get(provider, f"Invalid Provider")
#     img = qrcode.make(qr_data)
#     buffered = BytesIO()
#     img.save(buffered, format="PNG")
#     img_str = base64.b64encode(buffered.getvalue()).decode()
#     return f"data:image/png;base64,{img_str}"

# @frappe.whitelist()
# def get_qr_code_providers(company):
#     return frappe.get_all("Mode of Payment",
#         filters={
#             'company': company,
#             'type': 'QR Code',
#         },
#         fields=['name'],
#         pluck='name'
#     )

# @frappe.whitelist()
# def get_qr_code(gateway, amount, pos_invoice):
#     qr_code_url = None
#     transaction_id = None

#     if gateway == 'Sample':
#         # Skip DB fetch for dummy provider
#         try:
#             qr_data = f"Sample Payment | Invoice: {pos_invoice} | Amount: {amount}"
#             qr = qrcode.make(qr_data)
#             buffer = BytesIO()
#             qr.save(buffer, format="PNG")
#             img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
#             qr_code_url = f"data:image/png;base64,{img_base64}"
#             transaction_id = frappe.generate_hash(length=10)
#         except Exception as e:
#             frappe.throw(_('Failed to generate Sample QR code: ') + str(e))

#     else:
#         # Fetch real Payment Gateway Account only for real gateways
#         try:
#             payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
#         except frappe.DoesNotExistError:
#             frappe.throw(_(f"Payment Gateway Account not found for: {gateway}"))

#         if gateway == 'Khalti':
#             try:
#                 response = requests.post(
#                     'https://khalti.com/api/v2/payment/qr/',
#                     headers={'Authorization': f'Key {payment_gateway.api_key}'},
#                     json={
#                         'amount': float(amount) * 100,
#                         'order_id': pos_invoice,
#                         'merchant_id': payment_gateway.merchant_id
#                     }
#                 )
#                 response_data = response.json()
#                 qr_code_url = response_data.get('qr_code')
#                 transaction_id = response_data.get('transaction_id')
#             except Exception as e:
#                 frappe.throw(_('Failed to generate Khalti QR code: ') + str(e))
#         elif gateway == 'eSewa':
#             try:
#                 response = requests.post(
#                     'https://esewa.com.np/api/v1/payment/qr/',  # hypothetical URL
#                     headers={'Authorization': f'Bearer {payment_gateway.api_key}'},
#                     json={
#                         'amount': float(amount),
#                         'order_id': pos_invoice,
#                         'merchant_id': payment_gateway.merchant_id
#                     }
#                 )
#                 response_data = response.json()
#                 qr_code_url = response_data.get('qr_code_url')
#                 transaction_id = response_data.get('transaction_id')
#             except Exception as e:
#                 frappe.throw(_('Failed to generate eSewa QR code: ') + str(e))

#         elif gateway == 'Fonepay':
#             try:
#                 response = requests.post(
#                     'https://fonepay.com/api/merchant/qr',
#                     headers={'Authorization': f'Bearer {payment_gateway.api_key}'},
#                     json={
#                         'amount': float(amount),
#                         'order_id': pos_invoice,
#                         'merchant_id': payment_gateway.merchant_id
#                     }
#                 )
#                 response_data = response.json()
#                 qr_code_url = response_data.get('qr_code_url')
#                 transaction_id = response_data.get('transaction_id')
#             except Exception as e:
#                 frappe.throw(_('Failed to generate Fonepay QR code: ') + str(e))

#         elif gateway == 'NepalPay':
#             qr_code_url = payment_gateway.get('qr_code_url')  # Static QR
#             transaction_id = frappe.generate_hash(length=10)

#         else:
#             frappe.throw(_('Unsupported payment gateway: ') + gateway)

#     return {
#         'qr_code_url': qr_code_url,
#         'transaction_id': transaction_id
#     }



# @frappe.whitelist()
# def check_payment_status(gateway, transaction_id):
#     status = 'pending'
#     if gateway == 'Khalti':
#         try:
#             response = requests.get(
#                 f'https://khalti.com/api/v2/payment/status/{transaction_id}',
#                 headers={'Authorization': f'Key {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
#             )
#             status = response.json().get('status', 'pending')
#         except Exception as e:
#             frappe.log_error(_('Khalti payment status check failed: ') + str(e))

#     elif gateway == 'Fonepay':
#         try:
#             response = requests.get(
#                 f'https://fonepay.com/api/merchant/status/{transaction_id}',
#                 headers={'Authorization': f'Bearer {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
#             )
#             status = response.json().get('status', 'pending')
#         except Exception as e:
#             frappe.log_error(_('Fonepay payment status check failed: ') + str(e))
#     elif gateway == 'eSewa':
#         try:
#             response = requests.get(
#                 f'https://esewa.com.np/api/v1/payment/status/{transaction_id}',  # hypothetical URL
#                 headers={'Authorization': f'Bearer {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
#             )
#             status = response.json().get('status', 'pending')
#         except Exception as e:
#             frappe.log_error(_('eSewa payment status check failed: ') + str(e))

#     elif gateway == 'NepalPay':
#         status = 'pending'  # Placeholder; implement bank-specific API call

#     return {'status': status}


import qrcode
import base64
from io import BytesIO
import frappe
import requests
import hmac
import hashlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import websocket
import json
import threading
from frappe import _

# Helper function to generate HMAC-SHA512 Data Validation (DV) token
def generate_hmac_sha512(secret_key, message):
    try:
        byte_key = secret_key.encode('utf-8')
        byte_message = message.encode('utf-8')
        hmac_obj = hmac.new(byte_key, byte_message, hashlib.sha512)
        return hmac_obj.hexdigest()
    except Exception as e:
        frappe.log_error(f"HMAC-SHA512 generation failed: {str(e)}")
        frappe.throw(_("Failed to generate HMAC-SHA512: ") + str(e))

# Helper function to get or refresh eSewa access token (unchanged)
def get_esewa_access_token(payment_gateway, refresh_token=None):
    try:
        frappe.msgprint(_("Starting eSewa access token retrieval..."))
        client_id = "JB0BBQ4aD0UqIThFJwAKBgAXEUkEGQUBBAwdOgABHD4DChwUAB0R"
        client_secret = "BhwIWQQADhIYSxILExMcAgFXFhcOBwAKBgAXEQ=="
        username = "9806800001"
        password = base64.b64encode("Nepal@123".encode()).decode()
        base_url = "https://uat.esewa.com.np/api/v1"

        frappe.msgprint(_("Prepared credentials and base URL."))
        auth_url = f"{base_url}/access-token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "client_id": client_id,
            "client_secret": client_secret
        }

        if refresh_token:
            payload.update({"grant_type": "refresh_token", "refresh_token": refresh_token})
            frappe.msgprint(_("Using refresh token for access token retrieval."))
        else:
            payload.update({"grant_type": "password", "username": username, "password": password})
            frappe.msgprint(_("Using username/password for access token retrieval."))

        frappe.msgprint(_("Sending request to eSewa API..."))
        response = requests.post(auth_url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        frappe.msgprint(_("Response received from eSewa API: {0}").format(response_data))

        access_token = response_data.get("access_token")
        refresh_token = response_data.get("refresh_token")
        expires_in = response_data.get("expires_in")
        refresh_expires_in = response_data.get("refresh_expires_in")

        if not access_token:
            frappe.throw(_("Failed to obtain eSewa access token: No access token in response"))

        frappe.db.set_value("Payment Gateway Account", payment_gateway.name, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_token_expires_in": expires_in,
            "refresh_token_expires_in": refresh_expires_in
        })
        frappe.db.commit()
        frappe.msgprint(_("Access token stored successfully."))
        return access_token
    except Exception as e:
        frappe.log_error(f"eSewa access token retrieval failed: {str(e)}")
        frappe.throw(_("Failed to obtain eSewa access token: ") + str(e))

@frappe.whitelist()
def generate_payment_qr(provider, amount, invoice):
    qr_data_map = {
        "eSewa": f"https://fonepay.com/qr/{invoice}?amt={amount}",
        "FonePay": f"https://fonepay.com/qr/{invoice}?amt={amount}",
    }
    qr_data = qr_data_map.get(provider, f"Invalid Provider")
    img = qrcode.make(qr_data)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@frappe.whitelist()
def get_qr_code_providers(company):
    return frappe.get_all("Mode of Payment",
        filters={'company': company, 'type': 'QR Code'},
        fields=['name'],
        pluck='name'
    )

# WebSocket handler for FonePay
def on_fonepay_ws_message(ws, message):
    try:
        data = json.loads(message)
        frappe.msgprint(_("FonePay WebSocket message received: {0}").format(data))
        
        # Parse transactionStatus JSON string
        transaction_status = json.loads(data.get("transactionStatus", "{}"))
        merchant_id = data.get("merchantId")
        device_id = data.get("deviceId")
        qr_verified = transaction_status.get("qrVerified", False)
        payment_success = transaction_status.get("paymentSuccess")
        product_number = transaction_status.get("productNumber")
        amount = transaction_status.get("amount")
        transaction_date = transaction_status.get("transactionDate")
        message = transaction_status.get("message")
        
        # Determine status based on WebSocket message
        if qr_verified:
            status = "VERIFIED"
        elif payment_success is True:
            status = "SUCCESS"
        elif payment_success is False:
            status = "FAILED"
        else:
            status = "PENDING"
        
        # Store transaction details
        frappe.db.set_value("Payment Gateway Account", {"payment_gateway": "FonePay"}, {
            "last_request_id": product_number,
            "last_amount": float(amount) if amount else 0.0,
            "last_transaction_date": transaction_date,
            "last_status": status,
            "last_message": message
        })
        frappe.db.commit()
        
        # Trigger status check if productNumber is available
        if product_number:
            check_payment_status("FonePay", product_number)
            
    except Exception as e:
        frappe.log_error(f"FonePay WebSocket message handling failed: {str(e)}")

def on_fonepay_ws_error(ws, error):
    frappe.log_error(f"FonePay WebSocket error: {str(error)}")

def on_fonepay_ws_close(ws, close_status_code, close_msg):
    frappe.msgprint(_("FonePay WebSocket connection closed: {0}").format(close_msg))

def on_fonepay_ws_open(ws):
    frappe.msgprint(_("FonePay WebSocket connection opened"))

def start_fonepay_websocket(websocket_url):
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=on_fonepay_ws_message,
        on_error=on_fonepay_ws_error,
        on_close=on_fonepay_ws_close,
        on_open=on_fonepay_ws_open
    )
    # Run WebSocket in a separate thread
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

@frappe.whitelist()
def get_qr_code(gateway, amount, pos_invoice, mobile_number=None, package_id=None):
    """
    Main function to generate QR code and transaction code for a payment gateway.
    """
    if gateway == 'Sample':
        return generate_sample_qr(amount, pos_invoice)
    elif gateway == 'eSewa':
        return generate_esewa_qr(amount, pos_invoice, mobile_number, package_id)
    elif gateway == 'FonePay':
        return generate_fonepay_qr(amount, pos_invoice, gateway)
    else:
        frappe.throw(_('Unsupported payment gateway: ') + gateway)

def generate_sample_qr(amount, pos_invoice):
    """
    Generate QR code for Sample payment gateway.
    """
    try:
        qr_data = f"Sample Payment | Invoice: {pos_invoice} | Amount: {amount}"
        qr_code_url = create_qr_code(qr_data)
        transaction_code = frappe.generate_hash(length=10)
        return {'qr_code_url': qr_code_url, 'transaction_code': transaction_code}
    except Exception as e:
        frappe.throw(_('Failed to generate Sample QR code: ') + str(e))

def generate_esewa_qr(amount, pos_invoice, mobile_number=None, package_id=None):
    """
    Generate QR code for eSewa payment gateway.
    """
    try:
        payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': 'eSewa'})
        access_token = payment_gateway.get("access_token")
        if not access_token:
            access_token = get_esewa_access_token(payment_gateway)
        else:
            try:
                refresh_token = payment_gateway.get("refresh_token")
                access_token = get_esewa_access_token(payment_gateway, refresh_token)
            except Exception:
                access_token = get_esewa_access_token(payment_gateway)

        base_url = payment_gateway.get("base_url", "https://uat.esewa.com.np/api/v1")
        merchant_id = payment_gateway.get("merchant_id", "EPAYTEST")
        inquiry_url = f"{base_url}/inquiry/{pos_invoice}"
        if mobile_number:
            inquiry_url += f"/{mobile_number}"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        inquiry_response = requests.get(inquiry_url, headers=headers)
        inquiry_response.raise_for_status()
        inquiry_data = inquiry_response.json()

        if inquiry_data.get("response_code") != 0:
            frappe.throw(_("eSewa inquiry failed: ") + inquiry_data.get("response_message", "Unknown error"))

        if float(inquiry_data.get("amount")) != float(amount):
            frappe.throw(_("Amount mismatch in eSewa inquiry response"))

        transaction_code = frappe.generate_hash(length=10)
        payment_url = f"{base_url}/payment"
        payment_payload = {
            "request_id": pos_invoice,
            "amount": float(amount),
            "transaction_code": transaction_code,
            "merchant_id": merchant_id
        }
        if package_id:
            payment_payload["package_id"] = package_id

        payment_response = requests.post(payment_url, headers=headers, json=payment_payload)
        payment_response.raise_for_status()
        payment_data = payment_response.json()

        if payment_data.get("response_code") != 0:
            frappe.throw(_("eSewa payment failed: ") + payment_data.get("response_message", "Unknown error"))

        frappe.db.set_value("Payment Gateway Account", payment_gateway.name, {
            "last_request_id": pos_invoice,
            "last_amount": float(amount)
        })
        frappe.db.commit()

        reference_code = payment_data.get("reference_code")
        qr_data = f"{base_url}/pay?request_id={pos_invoice}&amount={amount}&reference_code={reference_code}&merchant_id={merchant_id}"
        qr_code_url = create_qr_code(qr_data)
        return {'qr_code_url': qr_code_url, 'transaction_code': transaction_code}
    except Exception as e:
        frappe.log_error(f"eSewa QR code generation failed: {str(e)}", title=f"eSewa QR Error (Invoice: {pos_invoice})")
        frappe.throw(_("Failed to generate eSewa QR code: ") + str(e))

def generate_fonepay_qr(amount, pos_invoice, gateway):
    """
    Generate QR code for FonePay payment gateway with retry logic for 502 errors.
    """
    try:
        payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
        base_url = "https://dev-merchantapi.fonepay.com/convergent-merchant-web"
        secret_key = "a7e3512f5032480a83137793cb2021dc"
        merchant_code = "NBQM"
        username = "ashok@raindropinc.com"
        password = "Admin@123"
        remarks1 = "test1"
        remarks2 = "test2"

        prn = pos_invoice

        # Generate HMAC-SHA512 for QR request
        message = f"{amount},{prn},{merchant_code},{remarks1},{remarks2}"
        tax_amount = payment_gateway.get("tax_amount", None)
        tax_refund = payment_gateway.get("tax_refund", None)
        if tax_amount and tax_refund:
            message += f",{tax_amount},{tax_refund}"
        data_validation = generate_hmac_sha512(secret_key, message)

        # Prepare QR request payload
        qr_url = f"{base_url}/api/merchant/merchantDetailsForThirdParty/thirdPartyDynamicQrDownload"
        payload = {
            "amount": str(amount),
            "remarks1": remarks1,
            "remarks2": remarks2,
            "prn": prn,
            "merchantCode": merchant_code,
            "dataValidation": data_validation,
            "username": username,
            "password": password
        }
        if tax_amount and tax_refund:
            payload.update({"taxAmount": str(tax_amount), "taxRefund": str(tax_refund)})

        headers = {"Content-Type": "application/json"}
        
        frappe.msgprint(f"""
            <b>🔹 FonePay QR Request Debug</b><br>
            <b>URL:</b> {qr_url}<br>
            <b>Headers:</b> {headers}<br>
            <b>Payload:</b> {frappe.as_json(payload, indent=2)}
            """)

        # Add retry logic for 502, 503, 504 errors
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.post(qr_url, headers=headers, json=payload)

        frappe.msgprint(f"""
            <b>🔹 FonePay QR Response Debug</b><br>
            <b>Status Code:</b> {response.status_code}<br>
            <b>Response:</b> {response.text}
            """)

        response.raise_for_status()
        response_data = response.json()

        frappe.msgprint(f"""
            <b>🔹 FonePay QR Response Data</b><br>
            <b>Status Data:</b> {response_data}<br>
            """)

        if not response_data.get("success") or response_data.get("statusCode") != 201:
            frappe.throw(_("FonePay QR request failed: ") + response_data.get("message", "Unknown error"))

        # Extract QR message, WebSocket URL, and trace ID
        qr_message = response_data.get("qrMessage")
        websocket_url = response_data.get("thirdpartyQrWebSocketUrl")
        fonepay_trace_id = response_data.get("fonepayTraceId")
        transaction_code = prn

        # Generate QR code
        qr_code_url = create_qr_code(qr_message)

        # Store transaction details in QR Transaction Detail table
        qr_transaction = frappe.get_doc({
            "doctype": "QR Transaction Detail",
            "prn": prn,
            "amount": float(amount),
            "transaction_code": transaction_code,
            "websocket_url": websocket_url,
            "fonepay_trace_id": fonepay_trace_id,
            "payment_gateway": payment_gateway.name,
            "created_at": frappe.utils.now(),
            "created_by": frappe.session.user
        })
        qr_transaction.insert(ignore_permissions=True)
        frappe.db.commit()

        # Start WebSocket connection
        start_fonepay_websocket(websocket_url)

        return {'qr_code_url': qr_code_url, 'transaction_code': transaction_code}
    except Exception as e:
        frappe.log_error(f"FonePay QR code generation failed: {str(e)}\nPayload: {payload}\nURL: {qr_url}", title=f"FonePay QR Error (Invoice: {pos_invoice})")
        frappe.throw(_("Failed to generate FonePay QR code: ") + str(e))

def create_qr_code(qr_data):
    """
    Utility function to generate a base64-encoded QR code from provided data.
    """
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
    return qr_code_url

@frappe.whitelist()
def check_payment_status(gateway, transaction_code):
    """
    Check payment status for the specified gateway and transaction code.
    Dispatches to gateway-specific functions.
    """
    status = 'PENDING'
    if gateway == 'eSewa':
        status = check_esewa_status(transaction_code)
    elif gateway == 'FonePay':
        status = check_fonepay_status(transaction_code)
    
    return {'status': status}

def check_esewa_status(transaction_code):
    """
    Check payment status for eSewa gateway.
    """
    try:
        payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': 'eSewa'})
        access_token = payment_gateway.get("access_token")
        if not access_token:
            access_token = get_esewa_access_token(payment_gateway)
        else:
            try:
                refresh_token = payment_gateway.get("refresh_token")
                access_token = get_esewa_access_token(payment_gateway, refresh_token)
            except Exception:
                access_token = get_esewa_access_token(payment_gateway)

        base_url = payment_gateway.get("base_url", "https://uat.esewa.com.np/api/v1")
        status_url = f"{base_url}/status"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        status_payload = {
            "request_id": payment_gateway.get("last_request_id"),
            "amount": float(payment_gateway.get("last_amount", 0)),
            "transaction_code": transaction_code
        }

        response = requests.post(status_url, headers=headers, json=status_payload)
        response.raise_for_status()
        status_data = response.json()

        if status_data.get("response_code") == 0:
            return status_data.get("status", "SUCCESS")
        else:
            frappe.log_error(f"eSewa payment status check failed: {status_data.get('response_message', 'Unknown error')}")
            return status_data.get("status", "FAILED")
    except Exception as e:
        frappe.log_error(f"eSewa payment status check failed: {str(e)}")
        return 'PENDING'

def check_fonepay_status(transaction_code):
    """
    Check payment status for FonePay gateway with retry logic for transient errors.
    """
    try:

        payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': 'FonePay'})
        base_url = payment_gateway.get("base_url", "https://dev-merchantapi.fonepay.com/convergent-merchant-web")
        secret_key = payment_gateway.get("secret_key", "a7e3512f5032480a83137793cb2021dc")
        merchant_code = payment_gateway.get("merchant_code", "NBQM")
        username = payment_gateway.get("username", "ashok@raindropinc.com")
        password = payment_gateway.get("password", "Admin@123")
        prn = transaction_code

        frappe.msgprint(_("Param, url:{0}, key: {1}, code: {2}, name: {3}").format(base_url,secret_key,merchant_code,username))

        # Generate HMAC-SHA512 for status check
        message = f"{prn},{merchant_code}"
        data_validation = generate_hmac_sha512(secret_key, message)

        # Prepare status check request
        status_url = f"{base_url}/api/merchant/merchantDetailsForThirdParty/thirdPartyDynamicQrGetStatus"
        payload = {
            "prn": prn,
            "merchantCode": merchant_code,
            "dataValidation": data_validation,
            "username": username,
            "password": password
        }
        headers = {"Content-Type": "application/json"}

        # Set up retry logic for 502/503/504 errors
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))

        frappe.msgprint(_("FonePay Status Request: {0}").format({k: v if k != "password" else "****" for k, v in payload.items()}))

        # Make request with retry and timeout
        response = session.post(status_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        status_data = response.json()

        # Map FonePay status to internal status
        fonepay_status = status_data.get("paymentStatus", "pending").upper()
        status = {
            "SUCCESS": "SUCCESS",
            "FAILED": "FAILED",
            "PENDING": "PENDING"
        }.get(fonepay_status, "PENDING")

        # Store trace ID for tax refund
        fonepay_trace_id = status_data.get("fonepayTraceId")
        if fonepay_trace_id:
            frappe.db.set_value("Payment Gateway Account", payment_gateway.name, {
                "fonepay_trace_id": fonepay_trace_id
            })
            frappe.db.commit()

        if status == "SUCCESS":
            frappe.msgprint(_("Payment successful. Schedule tax refund API call for the next day."))

        return status

    except Exception as e:
        frappe.log_error(f"FonePay payment status check failed: {str(e)}\nResponse: {response.text if 'response' in locals() else 'No response'}", title="FonePay Status Error")
        return 'PENDING'

@frappe.whitelist()
def post_tax_refund(gateway, fonepay_trace_id, merchant_prn, invoice_number, invoice_date, transaction_amount):
    if gateway != 'FonePay':
        frappe.throw(_('Tax refund API is only supported for FonePay'))

    try:
        payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
        base_url = payment_gateway.get("base_url", "https://dev-merchantapi.fonepay.com/convergent-merchant-web")
        secret_key = payment_gateway.get("secret_key", "a7e3512f5032480a83137793cb2021dc")
        merchant_code = payment_gateway.get("merchant_code", "NBQM")
        username = payment_gateway.get("username", "9861101076")
        password = payment_gateway.get("password", "admin123456")

        # Generate HMAC-SHA512 for tax refund
        message = f"{fonepay_trace_id},{merchant_prn},{invoice_number},{invoice_date},{transaction_amount},{merchant_code}"
        data_validation = generate_hmac_sha512(secret_key, message)

        # Prepare tax refund request
        tax_refund_url = f"{base_url}/api/merchant/merchantDetailsForThirdParty/thirdPartyPostTaxRefund"
        payload = {
            "fonepayTraceId": str(fonepay_trace_id),
            "merchantPRN": merchant_prn,
            "invoiceNumber": invoice_number,
            "invoiceDate": invoice_date,
            "transactionAmount": str(transaction_amount),
            "merchantCode": merchant_code,
            "dataValidation": data_validation,
            "username": username,
            "password": password
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(tax_refund_url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        if not response_data.get("success"):
            frappe.throw(_("FonePay tax refund request failed: ") + response_data.get("message", "Unknown error"))

        frappe.msgprint(_("Tax refund request successful: {0}").format(response_data.get("message")))
        return {
            "fonepayTraceId": response_data.get("fonepayTraceId"),
            "message": response_data.get("message"),
            "success": response_data.get("success")
        }

    except Exception as e:
        frappe.log_error(f"FonePay tax refund request failed: {str(e)}")
        frappe.throw(_("Failed to process FonePay tax refund: ") + str(e))