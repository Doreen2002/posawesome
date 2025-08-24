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
from frappe import _

# Helper function to get or refresh eSewa access token
# Helper function to get or refresh eSewa access token
def get_esewa_access_token(payment_gateway, refresh_token=None):
    try:
        frappe.msgprint(_("Starting eSewa access token retrieval..."))

        # Fetch credentials from Payment Gateway Account
        client_id = "JB0BBQ4aD0UqIThFJwAKBgAXEUkEGQUBBAwdOgABHD4DChwUAB0R"
        client_secret = "BhwIWQQADhIYSxILExMcAgFXFhcOBwAKBgAXEQ=="
        username = "9806800001"  # Default test eSewa ID
        password = base64.b64encode("Nepal@123".encode()).decode()  # Base64-encoded test password
        base_url = "https://uat.esewa.com.np/api/v1"  # Replace with actual sandbox URL

        frappe.msgprint(_("Prepared credentials and base URL."))

        # Prepare request for access token
        auth_url = f"{base_url}/access-token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "client_id": client_id,
            "client_secret": client_secret
        }

        if refresh_token:
            payload.update({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            })
            frappe.msgprint(_("Using refresh token for access token retrieval."))
        else:
            payload.update({
                "grant_type": "password",
                "username": username,
                "password": password
            })
            frappe.msgprint(_("Using username/password for access token retrieval."))

        # Make request to get access token
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

        # Store tokens and expiry in Payment Gateway Account
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
        frappe.msgprint(_("Failed to obtain eSewa access token: {0}").format(str(e)))
        frappe.throw(_("Failed to obtain eSewa access token: ") + str(e))


@frappe.whitelist()
def generate_payment_qr(provider, amount, invoice):
    # Simulate provider-specific QR data
    qr_data_map = {
        "eSewa": f"https://uat.esewa.com.np/pay?invoice={invoice}&amount={amount}",  # Update with actual payment URL
        "Khalti": f"https://khalti.com/pay?invoice={invoice}&amount={amount}",
        "FonePay": f"https://fonepay.com/qr/{invoice}?amt={amount}",
        "NepalPay": f"https://nepalpay.com/qr?inv={invoice}&amt={amount}",
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
        filters={
            'company': company,
            'type': 'QR Code',
        },
        fields=['name'],
        pluck='name'
    )

@frappe.whitelist()
def get_qr_code(gateway, amount, pos_invoice, mobile_number=None, package_id=None):
    qr_code_url = None
    transaction_code = None

    if gateway == 'Sample':
        try:
            qr_data = f"Sample Payment | Invoice: {pos_invoice} | Amount: {amount}"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            qr_code_url = f"data:image/png;base64,{img_base64}"
            transaction_code = frappe.generate_hash(length=10)
        except Exception as e:
            frappe.throw(_('Failed to generate Sample QR code: ') + str(e))

    else:
        try:
            payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
        except frappe.DoesNotExistError:
            frappe.throw(_(f"Payment Gateway Account not found for: {gateway}"))

        if gateway == 'eSewa':
            try:
                # Step 1: Get or refresh access token
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

                # Step 2: Inquiry API
                inquiry_url = f"{base_url}/inquiry/{pos_invoice}"
                if mobile_number:
                    inquiry_url += f"/{mobile_number}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                inquiry_response = requests.get(inquiry_url, headers=headers)
                inquiry_response.raise_for_status()
                inquiry_data = inquiry_response.json()

                if inquiry_data.get("response_code") != 0:
                    frappe.throw(_("eSewa inquiry failed: ") + inquiry_data.get("response_message", "Unknown error"))

                # Validate amount
                if float(inquiry_data.get("amount")) != float(amount):
                    frappe.throw(_("Amount mismatch in eSewa inquiry response"))

                # Step 3: Payment API
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

                # Store transaction details for status check
                frappe.db.set_value("Payment Gateway Account", payment_gateway.name, {
                    "last_request_id": pos_invoice,
                    "last_amount": float(amount)
                })
                frappe.db.commit()

                # Generate QR code from reference_code
                reference_code = payment_data.get("reference_code")
                qr_data = f"{base_url}/pay?request_id={pos_invoice}&amount={amount}&reference_code={reference_code}&merchant_id={merchant_id}"
                qr = qrcode.make(qr_data)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

            except Exception as e:
                frappe.log_error(f"eSewa QR code generation failed: {str(e)}")
                frappe.throw(_("Failed to generate eSewa QR code: ") + str(e))

        elif gateway == 'Khalti':
            try:
                response = requests.post(
                    'https://khalti.com/api/v2/payment/qr/',
                    headers={'Authorization': f'Key {payment_gateway.api_key}'},
                    json={
                        'amount': float(amount) * 100,
                        'order_id': pos_invoice,
                        'merchant_id': payment_gateway.merchant_id
                    }
                )
                response_data = response.json()
                qr_code_url = response_data.get('qr_code')
                transaction_code = response_data.get('transaction_id')
            except Exception as e:
                frappe.throw(_('Failed to generate Khalti QR code: ') + str(e))

        elif gateway == 'Fonepay':
            try:
                response = requests.post(
                    'https://fonepay.com/api/merchant/qr',
                    headers={'Authorization': f'Bearer {payment_gateway.api_key}'},
                    json={
                        'amount': float(amount),
                        'order_id': pos_invoice,
                        'merchant_id': payment_gateway.merchant_id
                    }
                )
                response_data = response.json()
                qr_code_url = response_data.get('qr_code_url')
                transaction_code = response_data.get('transaction_id')
            except Exception as e:
                frappe.throw(_('Failed to generate Fonepay QR code: ') + str(e))

        elif gateway == 'NepalPay':
            qr_code_url = payment_gateway.get('qr_code_url')  # Static QR
            transaction_code = frappe.generate_hash(length=10)

        else:
            frappe.throw(_('Unsupported payment gateway: ') + gateway)

    return {
        'qr_code_url': qr_code_url,
        'transaction_code': transaction_code
    }

@frappe.whitelist()
def check_payment_status(gateway, transaction_code):
    status = 'pending'

    if gateway == 'eSewa':
        try:
            payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
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
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            status_payload = {
                "request_id": payment_gateway.get("last_request_id"),
                "amount": float(payment_gateway.get("last_amount", 0)),
                "transaction_code": transaction_code
            }
            response = requests.post(status_url, headers=headers, json=status_payload)
            response.raise_for_status()
            status_data = response.json()

            if status_data.get("response_code") == 0:
                status = status_data.get("status", "SUCCESS")
            else:
                status = status_data.get("status", "FAILED")
                frappe.log_error(f"eSewa payment status check failed: {status_data.get('response_message', 'Unknown error')}")
        except Exception as e:
            frappe.log_error(f"eSewa payment status check failed: {str(e)}")
            status = 'pending'

    elif gateway == 'Khalti':
        try:
            response = requests.get(
                f'https://khalti.com/api/v2/payment/status/{transaction_code}',
                headers={'Authorization': f'Key {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
            )
            status = response.json().get('status', 'pending')
        except Exception as e:
            frappe.log_error(_('Khalti payment status check failed: ') + str(e))

    elif gateway == 'Fonepay':
        try:
            response = requests.get(
                f'https://fonepay.com/api/merchant/status/{transaction_code}',
                headers={'Authorization': f'Bearer {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
            )
            status = response.json().get('status', 'pending')
        except Exception as e:
            frappe.log_error(_('Fonepay payment status check failed: ') + str(e))

    elif gateway == 'NepalPay':
        status = 'pending'  # Placeholder; implement bank-specific API call

    return {'status': status}