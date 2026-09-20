from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from .const import (
    CHAT_ENDPOINT,
    CHAT_TYPE,
    CONVERSATIONS_ENDPOINT,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class OneMinAIError(Exception):
    """Base error for 1min.ai API."""


class OneMinAIAuthError(OneMinAIError):
    """Authentication error (invalid API key)."""


class OneMinAIClient:
    """Minimal async client wrapping the Chat with AI endpoint."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "API-KEY": self._api_key,
        }

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with async_timeout.timeout(TIMEOUT):
                resp = await self._session.post(
                    url, json=payload, headers=self._headers
                )
        except aiohttp.ClientError as err:
            raise OneMinAIError(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise OneMinAIError("Timeout talking to 1min.ai") from err

        if resp.status in (401, 403):
            raise OneMinAIAuthError("Invalid API key")
        if resp.status >= 400:
            body = await resp.text()
            raise OneMinAIError(f"HTTP {resp.status}: {body[:300]}")

        try:
            return await resp.json(content_type=None)
        except ValueError as err:
            raise OneMinAIError("Invalid JSON response from 1min.ai") from err

    async def validate(self, model: str) -> None:
        """Validate the API key with a tiny non-streaming request."""
        await self.chat(prompt="ping", model=model)

    async def create_conversation(self, title: str) -> str | None:
        """Create a UNIFY_CHAT_WITH_AI conversation, return its uuid."""
        payload = {"title": title, "type": CHAT_TYPE}
        try:
            data = await self._post(CONVERSATIONS_ENDPOINT, payload)
        except OneMinAIError as err:
            _LOGGER.warning("Could not create 1min.ai conversation: %s", err)
            return None

        conversation = data.get("conversation", data)
        uuid = conversation.get("uuid") or conversation.get("id")
        if not uuid:
            _LOGGER.warning("No uuid in conversation response: %s", data)
        return uuid

    async def chat(
        self,
        prompt: str,
        model: str,
        conversation_id: str | None = None,
        web_search: bool = False,
        num_of_site: int = 3,
        max_word: int = 1000,
        history_limit: int = 10,
        images: list[str] | None = None,
    ) -> str:
        """Send a non-streaming chat request and return the answer text."""
        prompt_object: dict[str, Any] = {"prompt": prompt}

        settings: dict[str, Any] = {}
        if web_search:
            settings["webSearchSettings"] = {
                "webSearch": True,
                "numOfSite": num_of_site,
                "maxWord": max_word,
            }
        if conversation_id:
            prompt_object["conversationId"] = conversation_id
            settings["historySettings"] = {
                "isMixed": False,
                "historyMessageLimit": history_limit,
            }
        if settings:
            prompt_object["settings"] = settings
        if images:
            prompt_object["attachments"] = {"images": images}

        payload = {
            "type": CHAT_TYPE,
            "model": model,
            "promptObject": prompt_object,
        }

        data = await self._post(CHAT_ENDPOINT, payload)
        return self._extract_answer(data)

    @staticmethod
    def _extract_answer(data: dict[str, Any]) -> str:
        """Extract the assistant text from an aiRecord response, defensively."""
        record = data.get("aiRecord", data)

        detail = record.get("aiRecordDetail") or {}
        result = (
            detail.get("resultObject")
            or record.get("resultObject")
            or record.get("result")
        )

        if isinstance(result, list):
            return "\n".join(str(item) for item in result if item)
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            for key in ("text", "content", "answer", "message"):
                if isinstance(result.get(key), str):
                    return result[key]

        _LOGGER.debug("Unrecognized 1min.ai response shape: %s", data)
        raise OneMinAIError("Could not extract answer from 1min.ai response")