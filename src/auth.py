import os

class AuthService:
    def __init__(self):
        self.secret = os.getenv("JWT_SECRET")

    def login(self, username, password):
        user = self.find_user(username)
        if not user:
            return None
        return self.generate_token(user)

    def generate_token(self, user):
        pass

    def find_user(self, username):
        pass


class JwtMiddleware:
    def validate_token(self, token):
        pass

    def decode_token(self, token):
        pass