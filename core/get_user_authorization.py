from fastapi import Header

from core.exceptions import UnauthorizeError, MissingAuthorizationHeader
from core.security import decode_token

def get_user_authorization(authorization: str = Header(None)) -> dict:
    if not authorization or " " not in authorization:
        raise MissingAuthorizationHeader()
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise UnauthorizeError()
    return payload