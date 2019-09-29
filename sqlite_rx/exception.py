
class Error(Exception):
    pass


class InvalidAuthConfig(Error):
    pass


class ZAPSetupError(Error):
    pass


class MissingServerCurveKeyID(Error):
    pass


class InvalidRequest(Error):
    pass

