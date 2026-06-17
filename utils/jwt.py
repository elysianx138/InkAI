import hashlib
import hmac
import base64
import json,time

def base64_bencode(data:bytes) -> str:
    # 二进制数据转ASCII
    encode_b64 = base64.b64encode(data).replace(b"=",b"").replace(b"+",b"-").replace(b"/",b"_")
    return encode_b64.decode("utf-8")

def base64_bdecode(data:str) -> bytes:
    # ASCII转二进制
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    decode_b64 = base64.b64decode(data.replace("-","+").replace("_","/"))
    return decode_b64

# signature
def sign(header_b64:str,payload_b64:str,secret:str) -> str:
    msg = header_b64 + "." + payload_b64
    sign = hmac.new(secret.encode("utf-8"),msg.encode("utf-8"),hashlib.sha256).hexdigest()
    return base64_bencode(sign.encode("utf-8"))

def encode(payload:dict,secret:str) -> str:
    header = {"alg":"HS256","typ":"JWT"}
    header_b64 = base64_bencode(json.dumps(header).encode("utf-8"))
    payload_b64 = base64_bencode(json.dumps(payload).encode("utf-8"))
    signature = sign(header_b64,payload_b64,secret)
    return header_b64 + "." + payload_b64 + "." + signature

def decode(jwt:str,secret:str) -> dict:
    header_b64,payload_b64,signature_b64 = jwt.split(".")
    signature = sign(header_b64,payload_b64,secret)
    if signature != signature_b64:
        return None
    payload = json.loads(base64_bdecode(payload_b64))

    exp = payload.get("exp")
    if exp and exp<time.time():
        return None
    return payload



    