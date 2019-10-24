
class SQLiteRxError(Exception):
    pass


class InvalidAuthConfig(SQLiteRxError):
    pass


class ZAPSetupError(SQLiteRxError):
    pass


class MissingServerCurveKeyID(SQLiteRxError):
    pass


class InvalidRequest(SQLiteRxError):
    pass


class RequestSendError(SQLiteRxError):
    pass


class SerializationError(SQLiteRxError):
    pass


class RequestCompressionError(SQLiteRxError):
    pass
