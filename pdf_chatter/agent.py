from __future__ import annotations

import openai
from openai import OpenAI
from typing import Generator, Literal
from enum import Enum
import os


import pdb


class Role(str, Enum):
    system = "system"
    assistant = "assistant"
    user = "user"
    tool = "tool"
    function = "function"


class Message(dict):
    """Message format for communicating with the OpenAI API."""

    def __init__(self, role: Role, content: str):
        super().__init__(role=role.value, content=content)


class Agent:
    def __init__(self, model: Literal['gpt-4', 'gpt-4-turbo-preview'], timeout=None):
        self.model = model
        self.timeout = timeout

    def oneshot_sync(self, prompt: str, query: str) -> str:
        return self.multishot_sync([
            Message(role=Role.system, content=prompt),
            Message(role=Role.user, content=query)
        ])

    def oneshot_streaming(self, prompt: str, query: str) -> Generator[str, None, None]:
        return self.multishot_streaming([
            Message(role=Role.system, content=prompt),
            Message(role=Role.user, content=query)
        ])

    def multishot_sync(self, messages: list[Message]) -> str:
        # use the streaming version so that timeout is on a per chunk basis
        gen = self.multishot_streaming(messages)
        return ''.join([*gen])

    def multishot_streaming(self, messages: list[Message]) -> Generator[str, None, None]:
        client = OpenAI()
        # TODO: type hint this since it doesn't know that it's the streaming version
        gen = client.chat.completions.create(
            model=self.model,
            messages=messages,
            timeout=self.timeout,
            stream=True
        )
        for chunk in gen:
            try:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            except:
                pass


def set_openai_key(api_key: str | None = None):
    # check that an api key was given, and set it
    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY', None)
    if not api_key:
        raise Exception(
            "No OpenAI API key given. Please set the OPENAI_API_KEY environment variable or pass the api_key argument to set_openai_key()")
    openai.api_key = api_key
