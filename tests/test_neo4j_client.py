from __future__ import annotations

import os

import pytest

from neo4j_client import Neo4jClient, Neo4jSettings, build_neo4j_client_from_env


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        for row in self._rows:
            yield row


class DummyRecord:
    def __init__(self, payload):
        self._payload = payload

    def data(self):
        return self._payload


class DummySession:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, cypher, **parameters):
        self.calls.append((cypher, parameters))
        return DummyResult([DummyRecord(row) for row in self.rows])


class DummyDriver:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.closed = False
        self.connected = False
        self.session_calls = []
        self.last_session = None

    def verify_connectivity(self):
        self.connected = True

    def session(self, database=None):
        self.session_calls.append(database)
        self.last_session = DummySession(self.rows)
        return self.last_session

    def close(self):
        self.closed = True


def test_client_run_and_fetch_helpers(monkeypatch):
    driver = DummyDriver(rows=[{"label": "Sign"}])
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: driver)

    client = Neo4jClient(Neo4jSettings("bolt://x", "neo4j", "pw", "fluorosis"))
    assert client.fetch_labels() == ["Sign"]
    assert driver.session_calls == ["fluorosis"]
    client.close()
    assert driver.closed is True


def test_client_fetch_node_count(monkeypatch):
    driver = DummyDriver(rows=[{"count": 12}])
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: driver)

    client = Neo4jClient(Neo4jSettings("bolt://x", "neo4j", "pw", "fluorosis"))
    assert client.fetch_node_count("Sign") == 12
    client.close()


def test_client_fetch_direct_relations(monkeypatch):
    rows = [
        {
            "node_name": "尺桡骨间膜骨化",
            "node_label": "Sign",
            "relation": "INDICATES",
            "relation_properties": {"source": "WS/T 192-2021"},
            "related_name": "骨质增生",
            "related_label": "Disease",
            "direction": "OUT",
        }
    ]
    driver = DummyDriver(rows=rows)
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: driver)

    client = Neo4jClient(Neo4jSettings("bolt://x", "neo4j", "pw", "fluorosis"))
    result = client.fetch_direct_relations("Sign", "尺桡骨间膜骨化")
    assert result == rows
    assert driver.last_session.calls[0][1] == {"name": "尺桡骨间膜骨化"}
    client.close()


def test_client_fetch_node_details(monkeypatch):
    rows = [
        {
            "node_name": "尺桡骨间膜骨化",
            "node_label": "Sign",
            "node_properties": {"name": "尺桡骨间膜骨化", "code": "S001"},
        }
    ]
    driver = DummyDriver(rows=rows)
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: driver)

    client = Neo4jClient(Neo4jSettings("bolt://x", "neo4j", "pw", "fluorosis"))
    result = client.fetch_node_details("Sign", "尺桡骨间膜骨化")
    assert result["node_name"] == "尺桡骨间膜骨化"
    assert result["node_properties"] == {"name": "尺桡骨间膜骨化", "code": "S001"}
    client.close()


def test_build_client_from_env(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "alice")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    monkeypatch.setenv("NEO4J_DATABASE", "fluorosis")
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: DummyDriver())
    client = build_neo4j_client_from_env()
    assert client.database == "fluorosis"


@pytest.mark.integration
def test_real_database_connectivity():
    if os.getenv("NEO4J_PASSWORD") is None:
        pytest.skip("NEO4J_PASSWORD not set")
    client = build_neo4j_client_from_env()
    try:
        client.verify_connectivity()
        labels = client.fetch_labels()
        assert "Anatomy" in labels
    finally:
        client.close()


def test_client_fetch_related_subgraph(monkeypatch):
    rows = [
        {
            "node_name": "尺桡骨间膜骨化",
            "node_label": "Sign",
            "relation": "INDICATES",
            "relation_properties": {"source": "WS/T 192-2021"},
            "related_name": "骨质增生",
            "related_label": "Disease",
            "direction": "OUT",
        }
    ]
    driver = DummyDriver(rows=rows)
    monkeypatch.setattr("neo4j_client.GraphDatabase.driver", lambda *args, **kwargs: driver)

    client = Neo4jClient(Neo4jSettings("bolt://x", "neo4j", "pw", "fluorosis"))
    result = client.fetch_related_subgraph("Sign", "尺桡骨间膜骨化", depth=2)
    assert result["depth"] == 2
    assert result["root"]["node_name"] == "尺桡骨间膜骨化"
    assert result["relations"][0]["target_name"] == "骨质增生"
    client.close()
