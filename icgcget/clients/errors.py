class SubprocessError(BaseException):
    def __init__(self, code, message):
        self.message = message
        self.code = code


class ApiError(BaseException):
    def __init__(self, request_string, message, code=None):
        self.message = message
        self.request_string = request_string
        self.code = code
