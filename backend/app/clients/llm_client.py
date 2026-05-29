from typing import Protocol


class LLMClientError(Exception):
    pass


class PlannerLLMClient(Protocol):
    @property
    def enabled(self) -> bool: ...

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict: ...
