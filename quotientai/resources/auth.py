import asyncio


class AuthResource:
    def __init__(self, client):
        self._client = client

    def authenticate(self):
        """
        A call to GET /auth/profile to initially authenticate the user.
        """
        response = self._client._get("/auth/profile")

        # Set the user_id if successful
        if response and isinstance(response, dict) and "user_id" in response:
            self._client._user = response["user_id"]

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

            # Set the user_id if successful
            if result and isinstance(result, dict) and "user_id" in result:
                self._client._user = result["user_id"]

            return result
        finally:
            loop.close()
