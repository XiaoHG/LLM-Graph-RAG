"""Graph-RAG helpers for Stage4."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable
import json

from neo4j_client import Neo4jClient, build_neo4j_client_from_env
from schemas import ExclusionSummary, FeatureDetail, ReportInput, RiskSummary, UncertaintySummary


GraphRAGContext = ReportInput


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


@dataclass(frozen=True)
class GraphNodeContext:
    node_label: str
    node_name: str
    node_count: int
    direct_relations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphBackgroundContext:
    feature_nodes: list[GraphNodeContext]
    disease_nodes: list[GraphNodeContext]

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_nodes": [item.to_dict() for item in self.feature_nodes],
            "disease_nodes": [item.to_dict() for item in self.disease_nodes],
        }

    def render(self) -> str:
        lines: list[str] = []
        for section_name, nodes in (("feature_nodes", self.feature_nodes), ("disease_nodes", self.disease_nodes)):
            if not nodes:
                continue
            lines.append(section_name)
            for node in nodes:
                lines.append(f"- {node.node_label}: {node.node_name} ({node.node_count})")
                for relation in node.direct_relations:
                    related_name = relation.get("related_name") or "-"
                    related_label = relation.get("related_label") or "-"
                    direction = relation.get("direction") or "?"
                    rel_type = relation.get("relation") or "?"
                    lines.append(f"  - [{direction}] {rel_type} -> {related_name} ({related_label})")
        return "\n".join(lines)


class GraphRAG:
    def __init__(
        self,
        client: Neo4jClient,
        *,
        feature_label: str = "Sign",
        disease_label: str = "Disease",
    ) -> None:
        self._client = client
        self._feature_label = feature_label
        self._disease_label = disease_label

    @classmethod
    def from_env(
        cls,
        *,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        feature_label: str = "Sign",
        disease_label: str = "Disease",
    ) -> "GraphRAG":
        client = build_neo4j_client_from_env(
            uri=uri,
            username=username,
            password=password,
            database=database,
        )
        return cls(client, feature_label=feature_label, disease_label=disease_label)

    @property
    def client(self) -> Neo4jClient:
        return self._client

    def close(self) -> None:
        self._client.close()

    def build_context(self, input_data: ReportInput) -> GraphRAGContext:
        return input_data

    def describe_node(
        self,
        node_label: str,
        node_name: str,
        *,
        node_count: int | None = None,
    ) -> GraphNodeContext:
        return GraphNodeContext(
            node_label=node_label,
            node_name=node_name,
            node_count=node_count if node_count is not None else self._client.fetch_node_count(node_label),
            direct_relations=self._client.fetch_direct_relations(node_label, node_name),
        )

    def build_background(self, input_data: ReportInput) -> GraphBackgroundContext:
        node_count_cache: dict[str, int] = {}

        def node_count_for(label: str) -> int:
            if label not in node_count_cache:
                node_count_cache[label] = self._client.fetch_node_count(label)
            return node_count_cache[label]

        feature_names = _unique_preserve_order(item.feat_name for item in input_data.feature_detail)
        disease_names = _unique_preserve_order(input_data.exclusion.excluded_diseases)

        feature_nodes = [
            self.describe_node(self._feature_label, name, node_count=node_count_for(self._feature_label))
            for name in feature_names
        ]
        disease_nodes = [
            self.describe_node(self._disease_label, name, node_count=node_count_for(self._disease_label))
            for name in disease_names
        ]
        return GraphBackgroundContext(feature_nodes=feature_nodes, disease_nodes=disease_nodes)

    def build_prompt_context(self, input_data: ReportInput) -> str:
        payload = json.dumps(self.build_context(input_data).to_dict(), ensure_ascii=False, indent=2)
        background = self.build_background(input_data).render()
        if not background:
            return payload
        return payload + "\n\n" + background
