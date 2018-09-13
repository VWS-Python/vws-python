class Success(Exception):
    def __init__(self, response) -> None:
        self.response = response


class TargetCreated(Exception):
    def __init__(self, response) -> None:
        self.response = response


class AuthenticationFailure(Exception):
    def __init__(self, response) -> None:
        self.response = response


class RequestTimeTooSkewed(Exception):
    def __init__(self, response) -> None:
        self.response = response


class TargetNameExist(Exception):
    def __init__(self, response) -> None:
        self.response = response


class UnknownTarget(Exception):
    def __init__(self, response) -> None:
        self.response = response


class BadImage(Exception):
    def __init__(self, response) -> None:
        self.response = response


class ImageTooLarge(Exception):
    def __init__(self, response) -> None:
        self.response = response


class MetadataTooLarge(Exception):
    def __init__(self, response) -> None:
        self.response = response


class DateRangeError(Exception):
    def __init__(self, response) -> None:
        self.response = response


class Fail(Exception):
    def __init__(self, response) -> None:
        self.response = response


class TargetStatusProcessing(Exception):
    def __init__(self, response) -> None:
        self.response = response


class RequestQuotaReached(Exception):
    def __init__(self, response) -> None:
        self.response = response


class TargetStatusNotSuccess(Exception):
    def __init__(self, response) -> None:
        self.response = response


class ProjectInactive(Exception):
    def __init__(self, response) -> None:
        self.response = response


class InactiveProject(Exception):
    def __init__(self, response) -> None:
        self.response = response
