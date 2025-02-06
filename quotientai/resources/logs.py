from typing import List
import asyncio
import httpx


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client

    async def create(
        self,
        model_input: str,
        model_output: str,
        documents: List[str],
        contexts: List[str] = None,
        tags: List[str] = None,
        hallucination_analysis: bool = False,
        environment: str = None,
    ):
        data = {
            "model_input": model_input,
            "model_output": model_output,
            "documents": documents,
            "contexts": contexts,
            "tags": tags,
            "hallucination_analysis": hallucination_analysis,
            "environment": environment,
        }

        try:
            # Temporary longer timeout to avoid throwing timeout error will be fixed with new endpoint
            # TODO: Remove timeout once new endpoint is ready and implement new endpoint /logs
            response = await asyncio.to_thread(
                self._client._post, "/rca/metadata", data, timeout=500
            )
            return response
        except httpx.ReadTimeout:
            # Temporary: Silently handle the timeout error until we have a new endpoint
            pass
        except Exception as e:
            raise e

    def background_create(
        self,
        model_input: str,
        model_output: str,
        documents: List[str],
        contexts: List[str] = None,
        tags: List[str] = None,
        hallucination_analysis: bool = False,
        environment: str = None,
    ):
        asyncio.run(
            self.create(
                model_input=model_input,
                model_output=model_output,
                documents=documents,
                contexts=contexts,
                tags=tags,
                hallucination_analysis=hallucination_analysis,
                environment=environment,
            )
        )
