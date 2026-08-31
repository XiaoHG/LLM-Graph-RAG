"""Report generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os

import requests

from schemas import ReportInput, ReportResult


ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "prompt"


@dataclass(frozen=True)
class DeepSeekSettings:
    api_key: str
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    timeout: float = 60.0


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    return path.read_text(encoding="utf-8").strip()


def _build_messages(input_data: ReportInput) -> list[dict[str, str]]:
    payload = json.dumps(input_data.to_dict(), ensure_ascii=False, indent=2)
    system = _load_prompt("report_system.md")
    user = _load_prompt("report_user.md").replace("{{payload}}", payload)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek response missing choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("DeepSeek response missing message content")
    return content.strip()


class DeepSeekReportGenerator:
    def __init__(self, settings: DeepSeekSettings) -> None:
        self._settings = settings

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> "DeepSeekReportGenerator":
        resolved_api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not resolved_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        settings = DeepSeekSettings(
            api_key=resolved_api_key,
            model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url=base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=float(timeout if timeout is not None else os.getenv("DEEPSEEK_TIMEOUT", "60")),
        )
        return cls(settings)

    def generate(self, input_data: ReportInput) -> ReportResult:
        messages = _build_messages(input_data)
        response = requests.post(
            f"{self._settings.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._settings.model,
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=self._settings.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        report_text = _extract_content(payload)
        return ReportResult(
            report_text=report_text,
            input_data=input_data,
            raw_response=payload,
            model=self._settings.model,
        )


def load_input(path: str) -> ReportInput:
    return ReportInput.from_json_file(path)


def save_result(result: ReportResult, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
