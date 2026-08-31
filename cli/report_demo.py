"""Report generation demo."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from report_generator import DeepSeekReportGenerator, load_input, save_result


def _resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate = ROOT / "test_data" / path
    if candidate.exists():
        return candidate
    return candidate


def _next_output_path(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = output_dir / f"report_{index:03d}.json"
        if not candidate.exists():
            return candidate
        index += 1


def _save_report_markdown(json_path: Path, report_text: str) -> Path:
    md_path = json_path.with_suffix(".md")
    md_path.write_text(report_text, encoding="utf-8")
    return md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a report from JSON input")
    parser.add_argument(
        "--input",
        default="input_example.json",
        help="Path to the input JSON",
    )
    parser.add_argument("--output", help="Optional output JSON path; defaults to output/report_###.json")
    parser.add_argument("--api-key", default=os.getenv("DEEPSEEK_API_KEY"), help="DeepSeek API key")
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), help="DeepSeek model")
    parser.add_argument(
        "--base-url",
        default=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        help="DeepSeek base URL",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("DEEPSEEK_TIMEOUT", "60")),
        help="Request timeout in seconds",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        input_data = load_input(str(_resolve_input_path(args.input)))
        generator = DeepSeekReportGenerator.from_env(
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            timeout=args.timeout,
        )
        result = generator.generate(input_data)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(exc)
        return 2

    output_path = Path(args.output) if args.output else _next_output_path(ROOT / "output")
    save_result(result, str(output_path))
    md_path = _save_report_markdown(output_path, result.report_text)
    print(f"saved: {output_path}")
    print(f"saved: {md_path}")
    print(result.report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
