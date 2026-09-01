"""Graph-RAG helpers for Stage4."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from neo4j_client import Neo4jClient, build_neo4j_client_from_env
from schemas import ReportInput


GraphRAGContext = ReportInput


def _format_properties(properties: Mapping[str, Any] | None) -> str:
    if not properties:
        return ""
    return ", ".join(f"{key}={value!r}" for key, value in properties.items())


@dataclass(frozen=True)
class GraphNodeContext:
    source_field: str
    node_label: str
    node_name: str
    depth: int
    node_count: int
    subgraph: dict[str, Any] = field(default_factory=dict)

    def _render_relation_line(self, relation: Mapping[str, Any]) -> str | None:
        source_label = str(relation.get("source_label") or "")
        source_name = str(relation.get("source_name") or "")
        target_label = str(relation.get("target_label") or "")
        target_name = str(relation.get("target_name") or "")
        relation_type = str(relation.get("relation") or "?")
        current_key = (self.node_label, self.node_name)

        if current_key == (source_label, source_name):
            return f"{source_name} -- {relation_type} --> {target_name}"
        if current_key == (target_label, target_name):
            return f"{target_name} <-- {relation_type} -- {source_name}"
        return f"{source_name} -- {relation_type} --> {target_name}"

    def render_block(self) -> list[str]:
        lines = [self.source_field]
        for relation in self.subgraph.get("relations") or []:
            rendered = self._render_relation_line(relation)
            if rendered:
                lines.append(rendered)

        seen_nodes: set[tuple[str, str]] = set()
        for node in self.subgraph.get("nodes") or []:
            node_label = str(node.get("node_label") or "")
            node_name = str(node.get("node_name") or "")
            node_key = (node_label, node_name)
            if node_key in seen_nodes:
                continue
            seen_nodes.add(node_key)
            rendered = _format_properties(node.get("node_properties") or {})
            lines.append(f"{node_name}：{rendered}" if rendered else f"{node_name}：")
        return lines


@dataclass(frozen=True)
class GraphBackgroundContext:
    depth: int
    feature_nodes: list[GraphNodeContext]
    disease_nodes: list[GraphNodeContext]

    def render(self) -> str:
        lines: list[str] = []
        for nodes in (self.feature_nodes, self.disease_nodes):
            for node in nodes:
                lines.extend(node.render_block())
                lines.append("")
        if lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)


@dataclass(frozen=True)
class GraphRAGResult:
    input_data: ReportInput
    background: GraphBackgroundContext

    def to_markdown(self) -> str:
        return self.background.render()


def _next_output_path(output_dir: Path, stem: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = output_dir / f"{stem}_{index:03d}.md"
        if not candidate.exists():
            return candidate
        index += 1


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

    def _build_node_context(
        self,
        node_label: str,
        node_name: str,
        depth: int,
        node_count: int,
        *,
        source_field: str,
    ) -> GraphNodeContext:
        subgraph = self._client.fetch_related_subgraph(node_label, node_name, depth=depth)
        return GraphNodeContext(
            source_field=source_field,
            node_label=node_label,
            node_name=node_name,
            depth=depth,
            node_count=node_count,
            subgraph=subgraph,
        )

    def build_background(self, input_data: ReportInput, *, depth: int = 2) -> GraphBackgroundContext:
        node_count_cache: dict[str, int] = {}

        def node_count_for(label: str) -> int:
            if label not in node_count_cache:
                node_count_cache[label] = self._client.fetch_node_count(label)
            return node_count_cache[label]

        feature_nodes = [
            self._build_node_context(
                self._feature_label,
                item.feat_name,
                depth,
                node_count_for(self._feature_label),
                source_field=f"feature_detail[{index}]:feat_name",
            )
            for index, item in enumerate(input_data.feature_detail)
        ]
        disease_nodes = [
            self._build_node_context(
                self._disease_label,
                name,
                depth,
                node_count_for(self._disease_label),
                source_field=f"exclusion.excluded_diseases[{index}]",
            )
            for index, name in enumerate(input_data.exclusion.excluded_diseases)
        ]
        return GraphBackgroundContext(depth=depth, feature_nodes=feature_nodes, disease_nodes=disease_nodes)

    def build_result(self, input_data: ReportInput, *, depth: int = 2) -> GraphRAGResult:
        return GraphRAGResult(input_data=input_data, background=self.build_background(input_data, depth=depth))

    def build_prompt_context(self, input_data: ReportInput, *, depth: int = 2) -> str:
        return self.build_result(input_data, depth=depth).to_markdown()

    def save_result(self, result: GraphRAGResult, output_dir: Path | str) -> Path:
        output_path = _next_output_path(Path(output_dir), "rag")
        output_path.write_text(result.to_markdown(), encoding="utf-8")
        return output_path
