class MetricsResource:
    def __init__(self, client) -> None:
        self._client = client

    def list(self):
        response = self._client._get("/runs/metrics")
        return response["data"]


class AsyncMetricsResource:
    def __init__(self, client) -> None:
        self._client = client

    async def list(self):
        response = await self._client._get("/runs/metrics")
        return response["data"]
