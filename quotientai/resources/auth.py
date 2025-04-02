import asyncio
class AuthResource:
    def __init__(self, client):
        self._client = client

    def authenticate(self):
        """
        A call to GET /auth/profile to initially authenticate the user.
        """
        response = self._client._get("/auth/profile")
        return response
    
class AsyncAuthResource:
    def __init__(self, client):
        self._client = client

    def authenticate(self):
        """
        A synchronous wrapper for an async auth call to be used during initialization.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Create the task
            task = loop.create_task(self._client._get("/auth/profile"))
            # Run the task to completion
            result = loop.run_until_complete(task)
            return result
        finally:
            loop.close()


