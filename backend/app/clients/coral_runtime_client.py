import httpx

from app.core.config import settings


class CoralRuntimeClient:
    def __init__(self) -> None:
        self.base_url = settings.coral_runtime_base_url

    async def query(self, sql: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.post("/query", json={"sql": sql})
            response.raise_for_status()
            return response.json()
