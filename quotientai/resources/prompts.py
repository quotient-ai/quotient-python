from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import traceback

from quotientai.exceptions import logger


@dataclass
class Prompt:
    id: str
    name: str
    version: int
    user_prompt: str

    created_at: datetime
    updated_at: datetime

    system_prompt: Optional[str] = None

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "name", self.name
        yield "system_prompt", self.system_prompt
        yield "user_prompt", self.user_prompt

    @property
    def messages(self) -> List[str]:
        messages = []
        if self.system_prompt is not None:
            messages.append({"role": "system", "content": self.system_prompt})

        messages.append({"role": "user", "content": self.user_prompt})
        return messages


class PromptsResource:
    """
    A resource for interacting with prompts in the QuotientAI API.
    """

    def __init__(self, client):
        self._client = client

    def list(self) -> List[Prompt]:
        response = self._client._get("/prompts")
        prompts = []
        for prompt in response:
            prompt["created_at"] = datetime.fromisoformat(prompt["created_at"])
            prompt["updated_at"] = datetime.fromisoformat(prompt["updated_at"])
            prompts.append(
                Prompt(
                    id=prompt["id"],
                    name=prompt["name"],
                    version=prompt["version"],
                    system_prompt=prompt["system_prompt"],
                    user_prompt=prompt["user_prompt"],
                    created_at=prompt["created_at"],
                    updated_at=prompt["updated_at"],
                )
            )

        return prompts

    def get(self, id: str, version: Optional[str] = None) -> Prompt:
        path = f"/prompts/{id}"
        if version is not None:
            path += f"/versions/{version}"

        prompts = self._client._get(path)
        if not prompts:
            logger.error(f"Prompt with id {id} not found.\n{traceback.format_exc()}")
            return None
        response = prompts[0]
        response["created_at"] = datetime.fromisoformat(response["created_at"])
        response["updated_at"] = datetime.fromisoformat(response["updated_at"])

        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    def create(
        self,
        name: str,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
    ) -> Prompt:
        data = {
            "name": name,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
        response = self._client._post("/prompts", data=data)
        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    def update(
        self,
        prompt: Prompt,
    ) -> Prompt:
        data = {
            "id": prompt.id,
            "name": prompt.name,
            "system_prompt": prompt.system_prompt,
            "user_prompt": prompt.user_prompt,
        }
        response = self._client._patch(f"/prompts/{prompt.id}", data=data)
        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    def delete(self, prompt: Prompt) -> Optional[None]:
        data = {
            "id": prompt.id,
            "name": prompt.name,
            "system_prompt": prompt.system_prompt,
            "user_prompt": prompt.user_prompt,
            # soft delete
            "is_deleted": True,
        }

        self._client._patch(f"/prompts/{prompt.id}", data=data)
        return None


class AsyncPromptsResource:
    """
    An asynchronous resource for interacting with prompts in the QuotientAI API.
    """

    def __init__(self, client):
        self._client = client

    async def list(self) -> List[Prompt]:
        response = await self._client._get("/prompts")
        prompts = []
        for prompt in response:
            prompt["created_at"] = datetime.fromisoformat(prompt["created_at"])
            prompt["updated_at"] = datetime.fromisoformat(prompt["updated_at"])
            prompts.append(
                Prompt(
                    id=prompt["id"],
                    name=prompt["name"],
                    version=prompt["version"],
                    system_prompt=prompt["system_prompt"],
                    user_prompt=prompt["user_prompt"],
                    created_at=prompt["created_at"],
                    updated_at=prompt["updated_at"],
                )
            )

        return prompts

    async def get(self, id: str, version: Optional[str] = None) -> Prompt:
        path = f"/prompts/{id}"
        if version is not None:
            path += f"/versions/{version}"

        prompts = await self._client._get(path)
        if not prompts:
            logger.error(f"Prompt with id {id} not found.\n{traceback.format_exc()}")
            return None

        response = prompts[0]
        response["created_at"] = datetime.fromisoformat(response["created_at"])
        response["updated_at"] = datetime.fromisoformat(response["updated_at"])

        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    async def create(
        self,
        name: str,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
    ) -> Prompt:
        data = {
            "name": name,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
        response = await self._client._post("/prompts", data=data)
        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    async def update(
        self,
        prompt: Prompt,
    ) -> Prompt:
        data = {
            "id": prompt.id,
            "name": prompt.name,
            "system_prompt": prompt.system_prompt,
            "user_prompt": prompt.user_prompt,
        }
        response = await self._client._patch(f"/prompts/{prompt.id}", data=data)
        prompt = Prompt(
            id=response["id"],
            name=response["name"],
            version=response["version"],
            system_prompt=response["system_prompt"],
            user_prompt=response["user_prompt"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
        )
        return prompt

    async def delete(self, prompt: Prompt) -> Optional[None]:
        data = {
            "id": prompt.id,
            "name": prompt.name,
            "system_prompt": prompt.system_prompt,
            "user_prompt": prompt.user_prompt,
            # soft delete
            "is_deleted": True,
        }

        await self._client._patch(f"/prompts/{prompt.id}", data=data)
        return None
