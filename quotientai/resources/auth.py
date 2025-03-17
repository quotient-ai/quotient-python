class AuthResource:
    def __init__(self, client):
        self._client = client

    def authenticate(self):
        response = self._client._get("/auth/profile")
        return response

