"""Neo4j CLI demo for the fluorosis graph."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from neo4j.exceptions import AuthError
from neo4j_client import build_neo4j_client_from_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Neo4j demo for the fluorosis graph")
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"), help="Neo4j URI")
    parser.add_argument("--username", default=os.getenv("NEO4J_USERNAME", "neo4j"), help="Neo4j username")
    parser.add_argument("--password", default=os.getenv("NEO4J_PASSWORD"), help="Neo4j password")
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE"), help="Neo4j database name")
    parser.add_argument("--label", help="Optional node label to count")
    parser.add_argument("--node-label", help="Node label to inspect")
    parser.add_argument("--node-name", help="Node name to inspect")
    return parser


def _format_properties(properties: dict[str, object] | None) -> str:
    if not properties:
        return "{}"
    parts = ", ".join(f"{key}={value!r}" for key, value in properties.items())
    return "{" + parts + "}"


def _print_direct_relations(node_label: str, node_name: str, rows: list[dict[str, object]]) -> None:
    print()
    print("Target Node")
    print("-----------")
    print(f"Label: {node_label}")
    print(f"Name : {node_name}")
    print()
    print("Direct Relations")
    print("----------------")
    if not rows:
        print("No direct relations found.")
        return
    for index, row in enumerate(rows, start=1):
        direction = row.get("direction", "?")
        relation = row.get("relation", "?")
        related_label = row.get("related_label") or "-"
        related_name = row.get("related_name") or "-"
        properties = _format_properties(row.get("relation_properties"))
        print(f"{index}. [{direction}] {relation}")
        print(f"   Node : {related_name} ({related_label})")
        print(f"   Props: {properties}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = build_neo4j_client_from_env(
            uri=args.uri,
            username=args.username,
            password=args.password,
            database=args.database,
        )
    except ValueError as exc:
        print(exc)
        return 2
    try:
        client.verify_connectivity()
        print("connected")
        print("labels:", ", ".join(client.fetch_labels()))
        if args.label:
            print(f"{args.label}:", client.fetch_node_count(args.label))
        if args.node_label and args.node_name:
            rows = client.fetch_direct_relations(args.node_label, args.node_name)
            _print_direct_relations(args.node_label, args.node_name, rows)
        elif args.node_label or args.node_name:
            print("both --node-label and --node-name are required to inspect relations")
            return 2
        return 0
    except AuthError as exc:
        print(f"auth failed: {exc}")
        return 3
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
