from __future__ import annotations

import json
import sys
from pathlib import Path

from graph_rag import GraphRAG
from schemas import ReportInput

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "cli"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


class DummyNeo4jClient:
    def __init__(self) -> None:
        self.node_count_calls: list[str] = []
        self.direct_relation_calls: list[tuple[str, str]] = []

    def fetch_node_count(self, label: str) -> int:
        self.node_count_calls.append(label)
        return {"Sign": 3, "Disease": 2}.get(label, 0)

    def fetch_direct_relations(self, label: str, name: str) -> list[dict[str, object]]:
        self.direct_relation_calls.append((label, name))
        return [
            {
                "node_name": name,
                "node_label": label,
                "relation": "INDICATES",
                "relation_properties": {"evidence_level": "strong"},
                "related_name": "fluorosis",
                "related_label": "Disease",
                "direction": "OUT",
            }
        ]

    def close(self) -> None:
        return None


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
            },
            {
                "feat_name": "骨质增生",
                "model_prob": 0.73,
                "evidence_level": "中证据",
                "is_counter_evidence": False,
                "is_legal_for_site": True,
            },
            {
                "feat_name": "肾性骨病",
                "model_prob": 0.12,
                "evidence_level": "反证",
                "is_counter_evidence": True,
                "is_legal_for_site": False,
            },
        ],
        "image_risk": {
            "score": 0.72,
            "level": "高风险",
            "basis": ["尺桡骨间膜骨化（强证据）", "骨质增生（中证据）"],
        },
        "exposure_risk": {
            "score": 0.8,
            "level": "高暴露",
            "basis": ["高氟病区居住15年", "长期饮用高氟水"],
        },
        "total_risk": {"score": 0.75, "level": "高风险", "basis": ["综合评估"]},
        "exclusion": {
            "excluded_diseases": ["肾性骨病"],
            "remaining_differential": ["骨质疏松", "退行性骨关节病"],
        },
        "missing_evidence": ["脊柱影像"],
        "uncertainty": {
            "total_score": 0.35,
            "level": "中等",
            "perception_score": 0.22,
            "cognitive_score": 0.44,
            "reasons": ["缺少脊柱影像，无法评估重度征象", "部分征象预测置信度存在波动"],
        },
    }


def test_build_context_matches_input_json():
    parsed = ReportInput.from_mapping(sample_input())
    rag = GraphRAG(DummyNeo4jClient())
    context = rag.build_context(parsed)
    assert context.to_dict() == sample_input()


def test_build_background_queries_all_feature_items():
    rag = GraphRAG(DummyNeo4jClient())
    background = rag.build_background(ReportInput.from_mapping(sample_input()))
    assert [node.node_name for node in background.feature_nodes] == ["尺桡骨间膜骨化", "骨质增生", "肾性骨病"]
    assert [node.node_name for node in background.disease_nodes] == ["肾性骨病"]
    assert rag.client.node_count_calls == ["Sign", "Disease"]
    assert rag.client.direct_relation_calls == [
        ("Sign", "尺桡骨间膜骨化"),
        ("Sign", "骨质增生"),
        ("Sign", "肾性骨病"),
        ("Disease", "肾性骨病"),
    ]


def test_prompt_context_contains_json_and_background():
    rag = GraphRAG(DummyNeo4jClient())
    text = rag.build_prompt_context(ReportInput.from_mapping(sample_input()))
    assert '"anatomy_site": "前臂"' in text
    assert "feature_nodes" in text
    assert "INDICATES" in text


def test_demo_main_outputs_context(monkeypatch, tmp_path):
    from cli.graph_rag_demo import main

    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(sample_input(), ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("cli.graph_rag_demo.GraphRAG.from_env", lambda **kwargs: GraphRAG(DummyNeo4jClient()))
    code = main(["--input", str(input_path)])
    assert code == 0
