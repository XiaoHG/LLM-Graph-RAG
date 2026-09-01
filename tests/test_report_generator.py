from __future__ import annotations

import json
import sys
from pathlib import Path

from report_generator import DeepSeekReportGenerator, DeepSeekSettings
from schemas import ReportInput

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "cli"
if str(CLI) not in sys.path:
    sys.path.insert(0, str(CLI))

from report_demo import main as report_main


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def sample_input() -> dict[str, object]:
    return {
        "anatomy_site": "前臂",
        "site_confidence": 0.96,
        "feature_detail": [
            {
                "feat_name": "尺桡骨间膜骨化",
                "model_prob": 0.88,
                "evidence_level": "强证据",
                "is_counter_evidence": False,
                "is_legal_for_site": True,
            }
        ],
        "image_risk": {"score": 0.72, "level": "高风险", "basis": ["尺桡骨间膜骨化（强证据）"]},
        "exposure_risk": {"score": 0.8, "level": "高暴露", "basis": ["高氟病区居住15年"]},
        "total_risk": {"score": 0.75, "level": "高风险", "basis": ["综合评估"]},
        "exclusion": {"excluded_diseases": ["肾性骨病"], "remaining_differential": ["骨质疏松"]},
        "missing_evidence": ["脊柱影像"],
        "uncertainty": {
            "total_score": 0.35,
            "level": "中等",
            "perception_score": 0.22,
            "cognitive_score": 0.44,
            "reasons": ["缺少脊柱影像"],
        },
    }


def test_input_parsing():
    parsed = ReportInput.from_mapping(sample_input())
    assert parsed.anatomy_site == "前臂"
    assert parsed.feature_detail[0].feat_name == "尺桡骨间膜骨化"


def test_generator_builds_request(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return DummyResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "1. 前臂影像提示氟骨症相关改变。\n2. 建议结合临床随访。"
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("report_generator.requests.post", fake_post)
    generator = DeepSeekReportGenerator(DeepSeekSettings(api_key="test-key"))
    result = generator.generate(ReportInput.from_mapping(sample_input()))
    assert "前臂影像提示氟骨症相关改变" in result.report_text
    assert captured["url"].endswith("/chat/completions")
    assert captured["json"]["model"] == "deepseek-chat"
    assert captured["timeout"] == 60.0


def test_cli_generates_output_file(monkeypatch, tmp_path):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    input_path.write_text(json.dumps(sample_input(), ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(
        "report_generator.requests.post",
        lambda *args, **kwargs: DummyResponse(
            {"choices": [{"message": {"content": "报告正文"}}]}
        ),
    )

    code = report_main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--api-key",
            "test-key",
        ]
    )
    assert code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["report_text"] == "报告正文"
    assert payload["input_data"]["anatomy_site"] == "前臂"
    assert output_path.with_suffix(".md").read_text(encoding="utf-8") == "报告正文"


def test_cli_uses_default_output_name(monkeypatch, tmp_path):
    input_path = tmp_path / "test_data" / "input_example.json"
    output_dir = tmp_path / "output" / "report"
    input_path.parent.mkdir(parents=True)
    input_path.write_text(json.dumps(sample_input(), ensure_ascii=False), encoding="utf-8")
    output_dir.mkdir(parents=True)
    (output_dir / "report_001.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr("report_generator.requests.post", lambda *args, **kwargs: DummyResponse({"choices": [{"message": {"content": "报告正文"}}]}))
    monkeypatch.setattr("report_demo.ROOT", tmp_path)

    code = report_main(["--api-key", "test-key"])
    assert code == 0
    assert (output_dir / "report_002.json").exists()
    assert (output_dir / "report_002.md").read_text(encoding="utf-8") == "报告正文"
def test_real_input_example_contains_three_features():
    parsed = ReportInput.from_json_file(str(ROOT / "test_data" / "input_example.json"))
    assert len(parsed.feature_detail) == 4


def test_input_rejects_unknown_fields():
    payload = sample_input()
    payload["unexpected"] = "value"
    try:
        ReportInput.from_mapping(payload)
    except TypeError as exc:
        assert "extra keys" in str(exc)
    else:
        raise AssertionError("expected TypeError")
