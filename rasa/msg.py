import json


class Msg(object):

    def __init__(self, code=0, msg="", success=True):
        self.code = code
        self.msg = msg
        self.success = success
        self.data = None

    @classmethod
    def success(cls, data):
        self = cls()
        self.data = data
        return self.__dict__()

    def __dict__(self):
        return {"code": self.code, "msg": self.msg, "success": self.success, "data": self.data}

