import os
import json
import logging
import requests

from flask import Blueprint, jsonify, request

from ccavenue.database import PaymentDetails, PaymentInvoice, db
from ccavenue.log.log import log_data
from config import get_credentials, prepare_invoice_data
from ccavenue.utils import current_time, decrypt, encrypt

invo_bp = Blueprint('quick_invoice', __name__)


# Invoice for Quick CC payments
@invo_bp.route('/generate/invoice', methods=['POST'])
def quick_invoice_request():
    try:
        profile_id = request.headers.get('Profile')
        if not profile_id:
            return jsonify({'error': 'Profile ID not provided in headers'}), 400
     
        data = request.json
        if not data:
            return jsonify({'error': 'Invoice data not provided'}), 400

        profile_data, status_code = get_credentials(profile_id)
        if status_code != 200:
            return jsonify({'error': 'Failed to retrieve credentials for the profile'}), 500
        
        ACCESS_CODE = profile_data['ACCESS_CODE']
        WORKING_KEY = profile_data['WORKING_KEY']

        invoice_data = prepare_invoice_data(data)        
        request_data_str = json.dumps(invoice_data)
        enc_request = encrypt(request_data_str, WORKING_KEY)
        
        params = {
            'enc_request':enc_request,
            'access_code':ACCESS_CODE,
            'command':'generateQuickInvoice',
            'request_type':'JSON',
            'response_type':'JSON',
            'version':'1.2'
        }

        api_url = os.environ.get('CC_PRO_API_URL')
        if not api_url:
            return jsonify({'error': 'API URL not configured'}), 500

        response = requests.post(api_url, data=params)  
        response_data = response.content.decode('utf-8').strip()
       
        if response.status_code == 200:
            response_params = dict(item.split('=') for item in response_data.split('&'))
           
            if response_params.get('status') == '1':
                log_data(message="Received the status 1", event_type='/generate/invoice', log_level=logging.ERROR, 
                         additional_context={"Error": response_params})
                return jsonify({"Error": response_params})
            
            enc_response = response_params.get('enc_response')
            decrypted_response = decrypt(enc_response)
            decrypted_json = json.loads(decrypted_response)

            if  decrypted_json.get("invoice_status")  == 0:
                decrypted_data = {
                    "error_desc": decrypted_json.get("error_desc", ""),
                    "invoice_id": decrypted_json.get("invoice_id", ""),
                    "tiny_url": decrypted_json.get("tiny_url", ""),
                    "invoice_status": decrypted_json.get("invoice_status", 0),
                    "error_code": decrypted_json.get("error_code", ""),
                    "merchant_reference_no": decrypted_json.get("merchant_reference_no", ""),
                    "customer_name":invoice_data.get("customer_name"),
                    "customer_email_id":invoice_data.get("customer_email_id"),
                    "customer_mobile_no":invoice_data.get("customer_mobile_no"),
                    "invoice_generate_time": current_time(),
                }

                new_invoice = PaymentInvoice(**decrypted_data)

                try:
                    db.session.add(new_invoice)
                    db.session.commit()

                except Exception as db_error:
                    log_data(message={'Database error': str(db_error)}, event_type='/generate/invoice', log_level=logging.ERROR)
                    return jsonify({'error': 'Database error occurred', 'details': str(db_error)}), 500
                

                log_data(message="Received the response 200", event_type='/generate/invoice', log_level=logging.INFO)
                return jsonify(decrypted_json)
            
            else:
                log_data(message="Invoice status is error zero", event_type='/generate/invoice', log_level=logging.ERROR)
                return jsonify({"Error": decrypted_json})

        else:
            log_data(message="Received an error response",event_type='/generate/invoice',log_level=logging.ERROR,
                     additional_context={'status_code': response.status_code})
            return jsonify({"HTTP Error": response.status_code})
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data provided'}), 400

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
    


@invo_bp.route('/payment/details', methods=['POST'])
def view_payment_details():
    try:
        request_data = request.form.to_dict()

        order_status = request_data.get('order_status')
        order_amount = request_data.get('order_amount')
        order_no = request_data.get('order_no')
        reference_no = request_data.get('reference_no')
        order_bill_name = request_data.get('order_bill_name')
        order_date_time = request_data.get('order_date_time')
        
        query = PaymentDetails.query
        
        if order_status:
            query = query.filter(PaymentDetails.order_status == order_status)
        if order_amount:
            query = query.filter(PaymentDetails.order_amount == order_amount)
        if order_no:
            query = query.filter(PaymentDetails.order_no == order_no)
        if reference_no:
            query = query.filter(PaymentDetails.reference_no == reference_no)
        if order_bill_name:
            query = query.filter(PaymentDetails.order_bill_name == order_bill_name)
        if order_date_time:
            query = query.filter(PaymentDetails.invoice_generate_time == order_date_time)
        
        # Execute the query
        payment_details = query.all()
        
        payment_details_list = [detail.to_dict() for detail in payment_details]
        return jsonify(payment_details_list)
    
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500



# Invoice for Quick CC payments
@invo_bp.route('/status/order_no', methods=['POST'])
def order_no_status():
    try:
        profile_id = request.headers.get('Profile')
        if not profile_id:
            return jsonify({'error': 'Profile ID not provided in headers'}), 400
     
        data = request.json
        if not data:
            return jsonify({'error': 'Invoice data not provided'}), 400

        profile_data, status_code = get_credentials(profile_id)
        if status_code != 200:
            return jsonify({'error': 'Failed to retrieve credentials for the profile'}), 500
        
        ACCESS_CODE = profile_data['ACCESS_CODE']
        WORKING_KEY = profile_data['WORKING_KEY']

        request_data = {
            "from_date": data["from_date"],
            "order_no": data["order_no"],
            "page_number": data['page_number']
        }

        request_data_str = json.dumps(request_data)
        enc_request = encrypt(request_data_str, WORKING_KEY)
        
        params = {
            'enc_request':enc_request,
            'access_code':ACCESS_CODE,
            'command':'orderLookup',
            'request_type':'JSON',
            'response_type':'JSON',
            'version':'1.1'
        }

        api_url = os.environ.get('CC_PRO_API_URL')
        if not api_url:
            return jsonify({'error': 'API URL not configured'}), 500
        
        response = requests.post(api_url, data=params)  
        response_data = response.content.decode('utf-8').strip()
        
        if response.status_code == 200:
            response_params = dict(item.split('=') for item in response_data.split('&'))
           
            if response_params.get('status') == '1':
                log_data(message="Received Error status 1", event_type='/status/order_no', log_level=logging.ERROR)
                return jsonify({"Error": response_params})
            
            decrypted_response = decrypt(response_params.get('enc_response'))
            decrypted_json = json.loads(decrypted_response)
        
            if decrypted_json.get('total_records')== 0:
                log_data(message="No record found for given criteria.", event_type='/status/order_no', log_level=logging.ERROR, 
                         additional_context={"Error": decrypted_json})
                return jsonify({"Error": decrypted_json})            
            
            order_Status_List = decrypted_json.get("order_Status_List", [])
            if isinstance(order_Status_List, list) and order_Status_List:
                order_Status_Details = order_Status_List[-1]
            else:
                order_Status_Details = {}
            
            decrypted_data = {
                "order_status": order_Status_Details.get("order_status", ""),
                "order_amount": order_Status_Details.get("order_amt", ""),
                "order_no": order_Status_Details.get("order_no", ""),
                "reference_no": order_Status_Details.get("reference_no", ""),
                "order_bill_name": order_Status_Details.get("order_bill_name", ""),
                "order_date_time": order_Status_Details.get("order_date_time", ""),
                "payment_details": decrypted_json,
                "data_request_time": current_time()
            }

            existing_payment_details = PaymentDetails.query.filter_by(order_no=decrypted_data['order_no']).first()

            if existing_payment_details:
                for key, value in decrypted_data.items():
                    setattr(existing_payment_details, key, value)
            else:
                new_payment_details = PaymentDetails(**decrypted_data)
                db.session.add(new_payment_details)

            try:
                db.session.commit()
            except Exception as db_error:
                log_data(message={'Database error': str(db_error)}, event_type='/status/order_no', log_level=logging.ERROR)
                return jsonify({'error': 'Database error occurred', 'details': str(db_error)}), 500
                
            log_data(message="Received order status",event_type='/status/order_no',log_level=logging.INFO,
                     additional_context={"Order status": order_Status_Details.get("order_status")}) 

            return jsonify({"Order status": order_Status_Details.get("order_status"), 'Order data': order_Status_Details})


        else:
            log_data(message="Received error response",event_type='/status/order_no',log_level=logging.ERROR,
                     additional_context={'order_status': decrypted_json.get("order_status"), 'status_code': response.status_code})
             
            return jsonify({"HTTP Error": response.status_code, 'response_data': response_data})
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data provided'}), 400

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

