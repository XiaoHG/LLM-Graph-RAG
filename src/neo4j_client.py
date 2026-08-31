"""Minimal Neo4j connection helpers for the fluorosis graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from neo4j import GraphDatabase, basic_auth


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str | None = None


class Neo4jClient:
    def __init__(self, settings: Neo4jSettings) -> None:
        self._settings = settings
        self._driver = GraphDatabase.driver(
            settings.uri,
            auth=basic_auth(settings.username, settings.password),
        )

    @property
    def database(self) -> str | None:
        return self._settings.database

    def close(self) -> None:
        self._driver.close()

    def verify_connectivity(self) -> None:
        self._driver.verify_connectivity()

    def run(self, cypher: str, **parameters: Any) -> list[dict[str, Any]]:
        with self._driver.session(database=self._settings.database) as session:
            result = session.run(cypher, **parameters)
            return [record.data() for record in result]

    def fetch_labels(self) -> list[str]:
        rows = self.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
        return [row["label"] for row in rows]

    def fetch_node_count(self, label: str) -> int:
        rows = self.run(f"MATCH (n:`{label}`) RETURN count(n) AS count")
        return int(rows[0]["count"]) if rows else 0

    def fetch_direct_relations(self, label: str, name: str) -> list[dict[str, Any]]:
        rows = self.run(
            f"""
            MATCH (n:`{label}` {{name: $name}})-[r]-(m)
            RETURN
                n.name AS node_name,
                head(labels(n)) AS node_label,
                type(r) AS relation,
                properties(r) AS relation_properties,
                m.name AS related_name,
                head(labels(m)) AS related_label,
                CASE WHEN startNode(r) = n THEN 'OUT' ELSE 'IN' END AS direction
            ORDER BY related_label, related_name, relation
            """,
            name=name,
        )
        return rows


def build_neo4j_client_from_env(
    *,
    uri: str | None = None,
    username: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> Neo4jClient:
    import os

    settings = Neo4jSettings(
        uri=uri or os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=username or os.getenv("NEO4J_USERNAME", "neo4j"),
        password=password or os.getenv("NEO4J_PASSWORD", ""),
        database=database or os.getenv("NEO4J_DATABASE") or None,
    )
    if not settings.password:
        raise ValueError("NEO4J_PASSWORD is required")
    return Neo4jClient(settings)
