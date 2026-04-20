"""
Google Authenticator QR Code Key Extractor
==========================================
Extracts secret keys from Google Authenticator migration QR codes.

Usage: python extract_keys.py <image_file>
"""

import sys
import base64
import urllib.parse
import cv2  # OpenCV for QR reading
from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor_pb2 import FileDescriptorProto, FieldDescriptorProto


def define_proto():
    """Programmatic definition of Google Auth Protobuf schema."""
    file_desc = FileDescriptorProto()
    file_desc.name = "google_auth.proto"
    file_desc.package = ""
    
    # 1. Message: MigrationPayload
    msg_payload = file_desc.message_type.add()
    msg_payload.name = "MigrationPayload"
    
    # Field: otp_parameters (repeated OtpParameters)
    field = msg_payload.field.add()
    field.name = "otp_parameters"
    field.number = 1
    field.label = FieldDescriptorProto.LABEL_REPEATED
    field.type = FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = "OtpParameters"

    # 2. Message: OtpParameters
    msg_otp = file_desc.message_type.add()
    msg_otp.name = "OtpParameters"
    
    # Field: secret (bytes)
    field = msg_otp.field.add()
    field.name = "secret"
    field.number = 1
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_BYTES
    
    # Field: name (string)
    field = msg_otp.field.add()
    field.name = "name"
    field.number = 2
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_STRING
    
    # Field: issuer (string)
    field = msg_otp.field.add()
    field.name = "issuer"
    field.number = 3
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_STRING
    
    # Field: algorithm (int)
    field = msg_otp.field.add()
    field.name = "algorithm"
    field.number = 4
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_INT32
    
    # Field: digits (int)
    field = msg_otp.field.add()
    field.name = "digits"
    field.number = 5
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_INT32
    
    # Field: type (int)
    field = msg_otp.field.add()
    field.name = "type"
    field.number = 6
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_INT32
    
    # Field: counter (int64)
    field = msg_otp.field.add()
    field.name = "counter"
    field.number = 7
    field.label = FieldDescriptorProto.LABEL_OPTIONAL
    field.type = FieldDescriptorProto.TYPE_INT64

    # Register
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_desc)
    factory = message_factory.MessageFactory(pool)
    return factory.GetPrototype(pool.FindMessageTypeByName('MigrationPayload'))


# Get the class
MigrationPayload = define_proto()


def extract_secret(image_path):
    print(f"📸 Reading image: {image_path}")
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            print("❌ Error: Could not read image file.")
            return

        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(img)
        
        if not data:
            print("❌ No QR code detected by OpenCV.")
            return

        if "otpauth-migration" not in data:
            print(f"❌ Found QR code but it contains: {data[:50]}...")
            print("This is not a Google Authenticator export QR code.")
            return

        print(f"✅ Found Migration URL")
        
        parsed = urllib.parse.urlparse(data)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        if "data" not in query_params:
             print("❌ URL missing 'data' parameter.")
             return
             
        data_b64 = query_params["data"][0]
        
        # Decode
        data_bytes = base64.b64decode(data_b64)
        payload = MigrationPayload()
        try:
            payload.ParseFromString(data_bytes)
        except Exception as pb_err:
             print(f"❌ Protobuf Parse Error: {pb_err}")
             return
        
        print("\n🔑 EXTRACTED KEYS:")
        print("="*40)
        
        for otp in payload.otp_parameters:
            secret_b32 = base64.b32encode(otp.secret).decode("utf-8").replace("=", "")
            name = otp.name
            issuer = otp.issuer
            
            print(f"Name:   {name}")
            print(f"Issuer: {issuer}")
            print(f"Secret: {secret_b32}")
            print("-" * 40)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_keys.py <image_file>")
    else:
        extract_secret(sys.argv[1])
