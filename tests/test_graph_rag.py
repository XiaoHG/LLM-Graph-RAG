from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src", ROOT / "cli"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from graph_rag import GraphRAG
from schemas import ReportInput


class DummyNeo4jClient:
    def __init__(self) -> None:
        self.node_count_calls: list[str] = []
        self.subgraph_calls: list[tuple[str, str, int]] = []

    def fetch_node_count(self, label: str) -> int:
        self.node_count_calls.append(label)
        return {"Sign": 3, "Disease": 2}.get(label, 0)

    def fetch_related_subgraph(self, label: str, name: str, *, depth: int = 2) -> dict[str, object]:
        self.subgraph_calls.append((label, name, depth))
        if label == "Sign":
            return {
                "root": {"node_label": label, "node_name": name, "depth": 0},
                "depth": depth,
                "nodes": [
                    {
                        "node_label": label,
                        "node_name": name,
                        "depth": 0,
                        "node_properties": {
                            "embedText": "影像征象：尺骨近端骨膜微小增生线；所属模块：氟骨症X线；分度：早期；是否早期筛查：true；征象描述：骨膜细线状新生骨",
                            "grade": "早期",
                            "module": "氟骨症X线",
                            "name": "尺骨近端骨膜微小增生线",
                            "source": "Coal-burning Type of Endemic Fluorosis.pdf",
                            "isEarlyScreen": True,
                            "desc": "骨膜细线状新生骨",
                        },
                    },
                    {
                        "node_label": "Anatomy",
                        "node_name": "尺骨",
                        "depth": 1,
                        "node_properties": {
                            "embedText": "解剖结构：尺骨；分类：四肢长骨；位置：前臂内侧；模块：骨骼影像分割",
                            "module": "骨骼影像分割",
                            "name": "尺骨",
                            "location": "前臂内侧",
                            "source": "WS/T 1922021.pdf",
                            "category": "四肢长骨",
                        },
                    },
                    {
                        "node_label": "Disease",
                        "node_name": "轻度氟骨症",
                        "depth": 1,
                        "node_properties": {
                            "embedText": "疾病名称：轻度氟骨症；分型模块：氟骨症；分度：Ⅰ度；类型：分度疾病；标准说明：存在持续性休息痛，无运动障碍；轻度骨间膜骨化",
                            "grade": "Ⅰ度",
                            "module": "氟骨症",
                            "name": "轻度氟骨症",
                            "source": "WS/T 1922021.pdf",
                            "type": "分度疾病",
                            "desc": "存在持续性休息痛，无运动障碍；轻度骨间膜骨化",
                        },
                    },
                ],
                "relations": [
                    {
                        "source_label": "Sign",
                        "source_name": name,
                        "relation": "LOCATED_AT",
                        "relation_properties": {},
                        "target_label": "Anatomy",
                        "target_name": "尺骨",
                        "direction": "OUT",
                        "depth": 1,
                    },
                    {
                        "source_label": "Disease",
                        "source_name": "轻度氟骨症",
                        "relation": "HAS_SIGN",
                        "relation_properties": {},
                        "target_label": "Sign",
                        "target_name": name,
                        "direction": "IN",
                        "depth": 1,
                    },
                ],
            }

        return {
            "root": {"node_label": label, "node_name": name, "depth": 0},
            "depth": depth,
            "nodes": [
                {
                    "node_label": label,
                    "node_name": name,
                    "depth": 0,
                    "node_properties": {
                        "embedText": "疾病名称：关节强直；分型模块：氟骨症；分度：无分度；类型：并发症；标准说明：关节僵硬和活动受限",
                        "module": "氟骨症",
                        "name": "关节强直",
                        "source": "WS/T 1922021.pdf",
                        "type": "并发症",
                        "desc": "关节僵硬和活动受限",
                    },
                },
                {
                    "node_label": "Disease",
                    "node_name": "中度氟骨症",
                    "depth": 1,
                    "node_properties": {
                        "embedText": "疾病名称：中度氟骨症；分型模块：氟骨症；分度：Ⅱ度；类型：分度疾病；标准说明：伴轻微活动障碍，尺桡/胫腓骨间膜明显骨化",
                        "grade": "Ⅱ度",
                        "module": "氟骨症",
                        "name": "中度氟骨症",
                        "source": "WS/T 1922021.pdf",
                        "type": "分度疾病",
                        "desc": "伴轻微活动障碍，尺桡/胫腓骨间膜明显骨化",
                    },
                },
            ],
            "relations": [
                {
                    "source_label": "Disease",
                    "source_name": "中度氟骨症",
                    "relation": "HAS_COMPLICATION",
                    "relation_properties": {},
                    "target_label": "Disease",
                    "target_name": name,
                    "direction": "IN",
                    "depth": 1,
                }
            ],
        }

    def close(self) -> None:
        return None


def sample_input() -> dict[str, object]:
    return {
        "anatomy_site": "前臂",
        "site_confidence": 0.96,
        "feature_detail": [
            {
                "feat_name": "尺骨近端骨膜微小增生线",
                "model_prob": 0.88,
                "evidence_level": "强证据",
                "is_counter_evidence": False,
                "is_legal_for_site": True,
            },
            {
                "feat_name": "尺骨近端骨膜微小增生线",
                "model_prob": 0.73,
                "evidence_level": "中证据",
                "is_counter_evidence": False,
                "is_legal_for_site": True,
            },
        ],
        "image_risk": {"score": 0.72, "level": "高风险", "basis": ["尺骨近端骨膜微小增生线（强证据）"]},
        "exposure_risk": {"score": 0.8, "level": "高暴露", "basis": ["高氟病区居住15年"]},
        "total_risk": {"score": 0.75, "level": "高风险", "basis": ["综合评估"]},
        "exclusion": {
            "excluded_diseases": ["关节强直", "关节强直"],
            "remaining_differential": ["骨质疏松", "退行性骨关节病"],
        },
        "missing_evidence": ["脊柱影像"],
        "uncertainty": {
            "total_score": 0.35,
            "level": "中等",
            "perception_score": 0.22,
            "cognitive_score": 0.44,
            "reasons": ["缺少脊柱影像，无法评估重度征象"],
        },
    }


def test_build_context_matches_input_json() -> None:
    parsed = ReportInput.from_mapping(sample_input())
    rag = GraphRAG(DummyNeo4jClient())
    assert rag.build_context(parsed).to_dict() == sample_input()


def test_render_keeps_duplicate_queries_and_full_node_details() -> None:
    client = DummyNeo4jClient()
    rag = GraphRAG(client)
    text = rag.build_result(ReportInput.from_mapping(sample_input()), depth=2).to_markdown()

    assert client.subgraph_calls == [
        ("Sign", "尺骨近端骨膜微小增生线", 2),
        ("Sign", "尺骨近端骨膜微小增生线", 2),
        ("Disease", "关节强直", 2),
        ("Disease", "关节强直", 2),
    ]
    assert "feature_detail[0]:feat_name" in text
    assert "feature_detail[1]:feat_name" in text
    assert "exclusion.excluded_diseases[0]" in text
    assert "exclusion.excluded_diseases[1]" in text
    assert "尺骨近端骨膜微小增生线 -- LOCATED_AT --> 尺骨" in text
    assert "尺骨近端骨膜微小增生线 <-- HAS_SIGN -- 轻度氟骨症" in text
    assert "尺骨近端骨膜微小增生线属性：embedText='影像征象：尺骨近端骨膜微小增生线；所属模块：氟骨症X线；分度：早期；是否早期筛查：true；征象描述：骨膜细线状新生骨'" in text
    assert "尺骨属性：embedText='解剖结构：尺骨；分类：四肢长骨；位置：前臂内侧；模块：骨骼影像分割'" in text
    assert "关节强直属性：embedText='疾病名称：关节强直；分型模块：氟骨症；分度：无分度；类型：并发症；标准说明：关节僵硬和活动受限'" in text


def test_save_result_writes_md_only(tmp_path: Path) -> None:
    rag = GraphRAG(DummyNeo4jClient())
    result = rag.build_result(ReportInput.from_mapping(sample_input()), depth=2)
    output_path = rag.save_result(result, tmp_path / "rag_result")
    assert output_path.suffix == ".md"
    assert output_path.exists()
    assert not output_path.with_suffix(".json").exists()


def test_demo_main_outputs_markdown(monkeypatch, tmp_path: Path) -> None:
    from cli.graph_rag_demo import main

    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(sample_input(), ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("cli.graph_rag_demo.GraphRAG.from_env", lambda **kwargs: GraphRAG(DummyNeo4jClient()))
    code = main(["--input", str(input_path), "--output-dir", str(tmp_path / "rag_result")])
    assert code == 0
