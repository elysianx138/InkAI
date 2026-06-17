class AppException(Exception):
    """所有业务异常处理的基类"""
    def __init__(self,code:str,message:str,status:int=400):
        self.code = code
        self.message = message
        self.status = status

class NotFoundError(AppException):
    def __init__(self,message:str = "资源不存在"):
        super().__init__(code="NOT_FOUND",message=message,status=404)

class UnauthorizeError(AppException):
    def __init__(self,message:str = "未登录或者登录已过期"):
        super().__init__(code="UNAUTHORIZED",message=message,status=401)

class ConflictError(AppException):
    def __init__(self,message:str = "资源已存在"):
        super().__init__(code="CONFLICT",message=message,status=409)

class TooManyRequestsError(AppException):
    def __init__(self,message:str = "请求过于频繁"):
        super().__init__(code="TOO_MANY_REQUESTS",message=message,status=429)