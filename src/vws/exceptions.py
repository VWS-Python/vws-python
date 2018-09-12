

class Fail(Exception):
    def __init__(self, response) -> None:
        self.response = response
