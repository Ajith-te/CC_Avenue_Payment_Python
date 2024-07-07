import os
from dotenv import load_dotenv

from ccavenue.utils import generate_order_id

load_dotenv()

# PostgreSQL server
SECRET_KEY = os.environ.get('SECRET_KEY')
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')


# Dictionary to map Product IDs to environment variables; if adding the new Profile here, and also update the .env
profile_credentials = {
    'network_manager_NET001'   : {'ACCESS_CODE': 'NET_ACC_CODE', 'WORKING_KEY': 'NET_WOR_KEY'},
    'finvesta_FIN001'          : {'ACCESS_CODE': 'FIN_ACC_CODE', 'WORKING_KEY': 'FIN_WOR_KEY'},
    'fiaglobal_FIA001'         : {'ACCESS_CODE': 'FIA_ACC_CODE', 'WORKING_KEY': 'FIA_WOR_KEY'},
    'localhost_LH001'          : {'ACCESS_CODE': 'LOC_ACC_CODE', 'WORKING_KEY': 'LOC_WOR_KEY'},
    'netext_NE001'             : {'ACCESS_CODE': 'EXT_ACC_CODE', 'WORKING_KEY': 'EXT_WOR_KEY'}
}


# is used to get response data for encrypt format, and WORKING_KEYS is used to decrypt after that, get all the deta.
WORKING_KEYS = [os.environ.get('NET_WOR_KEY'), os.environ.get('FIN_WOR_KEY'), os.environ.get('FIA_WOR_KEY'), os.environ.get('LOC_WOR_KEY'), os.environ.get('EXT_WOR_KEY')]


# Function to retrieve credentials based on profile ID
def get_credentials(profile_id):
    try:
        # Check if the profile ID is valid
        if profile_id not in profile_credentials:
            return {'error': 'Invalid profile ID'}, 400

        # Retrieve credentials from environment variables
        credentials = {}
        for key, value in profile_credentials[profile_id].items():
            credentials[key] = os.environ.get(value)

        return credentials, 200

    except Exception as e:
        return {'error': str(e)}, 500


def prepare_invoice_data(data):
    order_id = generate_order_id()
    # valid type --- minutes/hours/days/month/year
    # bill_delivery_type --- EMAIL/SMS/BOTH
    return {
            "customer_name":data['customer_name'],
            "bill_delivery_type":data["bill_delivery_type"],
            "customer_mobile_no":data["customer_mobile_no"],
            "customer_email_id":data["customer_email_id"],
            "customer_email_subject":data["customer_email_subject"],
            "invoice_description":data["invoice_description"],
            "currency":"INR",
            "valid_for":data["valid_for"],
            "valid_type":data["valid_type"],
            "amount":data['amount'],
            "sub_acc_id":"sub1",
            "terms_and_conditions":"terms and condition",
            "sms_content":"Pls call 022-2121212121topayyourLegalEntity_Namebill# Invoice_IDforInvoice_CurrencyInvoice_AmountorpayonlineatPay_Link.",
            "files": [{
                "name": "Test.doc",
                "content": "77u/SGVsbG8gaW5kaWEK"
                }],
            "merchant_reference_no": order_id,
            "merchant_reference_no1": order_id,
        }

