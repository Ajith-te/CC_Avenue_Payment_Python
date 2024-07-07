import hashlib
import uuid

from Crypto.Cipher import AES
from binascii import unhexlify
from datetime import datetime


def current_time():
    time = datetime.now().strftime('%Y-%m-%d %I:%M %p')    
    return time


# Generate state code
def generate_order_id():
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    uuid_int = int(uuid.uuid4().int)
    combined_number = int(current_time) + uuid_int
    unique_number_str = str(combined_number)[-8:]
    return unique_number_str


# PKCS7 Padding
def pad(data):
    pad_length = 16 - len(data) % 16
    return data + chr(pad_length) * pad_length


def unpad(data):
    pad_length = ord(data[-1])
    return data[:-pad_length]


# Encrypt the merchant data
def encrypt(plainText, workingKey):
    iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
    plainText = pad(plainText)

    encDigest = hashlib.md5()
    encDigest.update(workingKey.encode())

    enc_cipher = AES.new(encDigest.digest(), AES.MODE_CBC, iv)
    encryptedText = enc_cipher.encrypt(plainText.encode()).hex()

    return encryptedText


# Decrypt the response data 
def decrypt(cipherText):
    from config import WORKING_KEYS

    iv = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
    # Iterate through each working key
    for working_key in WORKING_KEYS:
        if working_key is None:
            continue
        
        decDigest = hashlib.md5()
        decDigest.update(working_key.encode('utf-8'))

        encryptedText = bytes.fromhex(cipherText)
        dec_cipher = AES.new(decDigest.digest(), AES.MODE_CBC, iv)
        
        try:
            decryptedText = dec_cipher.decrypt(encryptedText)
            decryptedText = unpad(decryptedText.decode('utf-8'))
            return decryptedText
        
        except Exception as e:
            continue
    
    return None
