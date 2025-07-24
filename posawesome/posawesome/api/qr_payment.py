import qrcode
import base64
from io import BytesIO
import frappe
import requests
from frappe import _

@frappe.whitelist()
def generate_payment_qr(provider, amount, invoice):
    # Simulate provider-specific QR data
    qr_data_map = {
        "Khalti": f"https://khalti.com/pay?invoice={invoice}&amount={amount}",
        "FonePay": f"https://fonepay.com/qr/{invoice}?amt={amount}",
        "NepalPay": f"https://nepalpay.com/qr?inv={invoice}&amt={amount}"
    }

    qr_data = qr_data_map.get(provider, f"Invalid Provider")
    img = qrcode.make(qr_data)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"



@frappe.whitelist()
def get_qr_code(gateway, amount, pos_invoice):
    qr_code_url = None
    transaction_id = None

    if gateway == 'Sample':
        # Skip DB fetch for dummy provider
        try:
            qr_data = f"Sample Payment | Invoice: {pos_invoice} | Amount: {amount}"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            qr_code_url = f"data:image/png;base64,{img_base64}"
            transaction_id = frappe.generate_hash(length=10)
        except Exception as e:
            frappe.throw(_('Failed to generate Sample QR code: ') + str(e))

    else:
        # Fetch real Payment Gateway Account only for real gateways
        try:
            payment_gateway = frappe.get_doc('Payment Gateway Account', {'payment_gateway': gateway})
        except frappe.DoesNotExistError:
            frappe.throw(_(f"Payment Gateway Account not found for: {gateway}"))

        if gateway == 'Khalti':
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
                transaction_id = response_data.get('transaction_id')
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
                transaction_id = response_data.get('transaction_id')
            except Exception as e:
                frappe.throw(_('Failed to generate Fonepay QR code: ') + str(e))

        elif gateway == 'NepalPay':
            qr_code_url = payment_gateway.get('qr_code_url')  # Static QR
            transaction_id = frappe.generate_hash(length=10)

        else:
            frappe.throw(_('Unsupported payment gateway: ') + gateway)

    return {
        'qr_code_url': qr_code_url,
        'transaction_id': transaction_id
    }



@frappe.whitelist()
def check_payment_status(gateway, transaction_id):
    status = 'pending'
    if gateway == 'Khalti':
        try:
            response = requests.get(
                f'https://khalti.com/api/v2/payment/status/{transaction_id}',
                headers={'Authorization': f'Key {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
            )
            status = response.json().get('status', 'pending')
        except Exception as e:
            frappe.log_error(_('Khalti payment status check failed: ') + str(e))

    elif gateway == 'Fonepay':
        try:
            response = requests.get(
                f'https://fonepay.com/api/merchant/status/{transaction_id}',
                headers={'Authorization': f'Bearer {frappe.get_value("Payment Gateway Account", {"payment_gateway": gateway}, "api_key")}'}
            )
            status = response.json().get('status', 'pending')
        except Exception as e:
            frappe.log_error(_('Fonepay payment status check failed: ') + str(e))

    elif gateway == 'NepalPay':
        status = 'pending'  # Placeholder; implement bank-specific API call

    return {'status': status}