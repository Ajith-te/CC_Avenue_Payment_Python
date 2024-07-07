import json
import logging
import os
from flask import Blueprint, abort, jsonify, request
import requests

from ccavenue.database import RefundDetails, db
from ccavenue.log.log import log_data
from ccavenue.utils import current_time, decrypt, encrypt
from config import get_credentials

# Create a Blueprint instance
refund_bp = Blueprint('refund', __name__)


@refund_bp.route('/request/refund', methods=['POST'])
def request_refund():
    try:
        profile_id = request.headers.get('Profile')
        if not profile_id:
            return jsonify({'error': 'Profile ID not provided in headers'}), 400
        
        refund_data = request.json
        if not refund_data.get('reference_no') or not refund_data.get('refund_amount'):
            return jsonify({'error': 'Order ID and Refund amount must be provided'}), 400

        profile_data, status_code = get_credentials(profile_id)
        if status_code != 200:
            return jsonify({'error': 'Failed to retrieve credentials for the profile'}), 500
        
        ACCESS_CODE = profile_data['ACCESS_CODE']
        WORKING_KEY = profile_data['WORKING_KEY']


        request_data = {
            "reference_no": refund_data['reference_no'],
            "refund_amount": refund_data['refund_amount'],
            "refund_ref_no": refund_data['refund_ref_no']
        }  
        
        request_data_str = json.dumps(request_data)
        enc_request = encrypt(request_data_str, WORKING_KEY)

        params = {
            'enc_request':enc_request,
            'access_code':ACCESS_CODE,
            'request_type':'JSON',
            'response_type':'JSON',
            'command':'refundOrder',
            'version':'1.1'
        }
        api_url = os.environ.get('CC_PRO_API_URL')
        if not api_url:
            return jsonify({'error': 'API URL not configured'}), 500

        response = requests.post(api_url, data=params)  
        response_data = response.content.decode('utf-8').strip()
        response_params = dict(item.split('=') for item in response_data.split('&'))
       

        if response.status_code == 200:
            if response_params.get('status') == '0':
                enc_response = response_params.get('enc_response')
                decrypted_response = decrypt(enc_response)
                decrypted_json = json.loads(decrypted_response)

                if decrypted_json.get('refund_status')== '0':
                    decrypted_response_json = {
                        "reason": decrypted_response.get("reason", ""),
                        "error_code": decrypted_response.get("error_code", ""),
                        "refund_status": decrypted_response.get("refund_status", ""),
                        "reference_no": request_data["reference_no"],
                        "refund_amount": request_data["refund_amount"],
                        "refund_ref_no": request_data["refund_ref_no"],
                        "refund_request_time": current_time(),
                    }
                    new_refund = RefundDetails(**decrypted_response_json)

                    try:
                        db.session.add(new_refund)
                        db.session.commit()

                    except Exception as db_error:
                        log_data(message={'Database error': str(db_error)}, event_type='/request/refund', log_level=logging.ERROR)
                        return jsonify({'error': 'Database error occurred', 'details': str(db_error)}), 500
                     
                    log_data(message="Received the refund status", event_type='/request/refund', log_level=logging.INFO,
                            additional_context={'response_data': decrypted_json})
                    
                    return jsonify({"Decrypted Response": decrypted_json})
                
                log_data(message="Received Error in refund response", event_type='/request/refund', log_level=logging.INFO,
                            additional_context={'response_data': decrypted_json})
                return jsonify({"Error": decrypted_json})
                 
            else:
                log_data(message="Error in refund response", event_type='/request/refund', log_level=logging.ERROR,
                         additional_context={'response_params': response_params})
                return jsonify({"Error": response_params})
        
        else:
            log_data(message=f"HTTP Error {response.status_code}", event_type='/request/refund', log_level=logging.ERROR)
            return jsonify({"HTTP Error": response.status_code})
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data provided'}), 400

    except Exception as e:
        log_data(message= str(e) , event_type='/request/refund', log_level=logging.ERROR)
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500


# Refund AMount check the status
@refund_bp.route('/refund/status', methods=['POST'])
def refund_status():
    try:
        profile_id = request.headers.get('Profile')
        if not profile_id:
            return jsonify({'error': 'Profile ID not provided in headers'}), 400
        
        request_data = request.json
        if not request_data or not request_data.get('reference_no'):
            return jsonify({'error': 'Reference No must be provided'}), 400

        reference_no = request_data.get('reference_no')

        profile_data, status_code = get_credentials(profile_id)
        if status_code != 200:
            return jsonify({'error': 'Failed to retrieve credentials for the profile'}), 500
        
        ACCESS_CODE = profile_data['ACCESS_CODE']
        WORKING_KEY = profile_data['WORKING_KEY']  

        request_data_str = json.dumps({'reference_no': reference_no})
        enc_request = encrypt(request_data_str, WORKING_KEY)

        params = {
            'enc_request':enc_request,
            'access_code':ACCESS_CODE,
            'command':'getRefundDetails',
            'request_type':'JSON',
            'response_type':'JSON',
            'version':'1.1'
        }

        response = requests.post(os.environ.get('CC_PRO_API_URL'), data=params)
        response_data = response.content.decode('utf-8').strip()

        if response.status_code == 200:
            response_params = dict(item.split('=') for item in response_data.split('&'))

            if response_params.get('status') == '0':
                enc_response = response_params.get('enc_response')
                decrypted_response = decrypt(enc_response)
                decrypted_json = json.loads(decrypted_response)

                log_data(message="Received the response 200", event_type='/refund/status', log_level=logging.INFO,
                         additional_context={'response_data': decrypted_json})
                
                return jsonify({"Decrypted Response": decrypted_json})        
            
            else:
                log_data(message="Error in refund status response", event_type='/refund/status', log_level=logging.ERROR,
                         additional_context={'response_params': response_params})
                return jsonify({"Error": response_params})
        
        else:
            
            log_data(message=f"HTTP Error{response.status_code}", event_type='/refund/status', log_level=logging.ERROR,
                  additional_context={'response_data': response_params, 'reference_no':request_data['reference_no']})
            
            return jsonify({"HTTP Error": response.status_code})
    
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON data provided'}), 400

    except Exception as e:
        log_data(message={'Unexpected error': str(e)}, event_type='/refund/status', log_level=logging.ERROR)
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500
