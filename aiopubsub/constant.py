class PubsubRole(object):
    PUB = "pub"
    SUB = "sub"

    def __init__(self, role=None):
        self.role = role

    def clear(self):
        self.role = None

    def set(self, role):
        if self.role is None:
            self.role = role
        elif self.role != role:
            raise ValueError(f"role is already set {self.role}")
