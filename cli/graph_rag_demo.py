"""Graph-RAG demo for Stage4."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from graph_rag import GraphRAG
from report_generator import load_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Graph-RAG demo for the fluorosis graph")
    parser.add_argument("--input", help="Path to a Stage4 input JSON")
    parser.add_argument("--depth", type=int, default=2, help="Neo4j retrieval depth")
    parser.add_argument("--output-dir", default=str(ROOT / "output" / "rag_result"), help="RAG result output directory")
    parser.add_argument("--feature-label", default="Sign", help="Neo4j label used for imaging signs")
    parser.add_argument("--disease-label", default="Disease", help="Neo4j label used for diseases")
    parser.add_argument("--uri", help="Neo4j URI")
    parser.add_argument("--username", help="Neo4j username")
    parser.add_argument("--password", help="Neo4j password")
    parser.add_argument("--database", help="Neo4j database")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rag = GraphRAG.from_env(
            uri=args.uri,
            username=args.username,
            password=args.password,
            database=args.database,
            feature_label=args.feature_label,
            disease_label=args.disease_label,
        )
    except ValueError as exc:
        print(exc)
        return 2
    try:
        if not args.input:
            print("--input is required")
            return 2
        input_data = load_input(args.input)
        result = rag.build_result(input_data, depth=args.depth)
        output_path = rag.save_result(result, Path(args.output_dir))
        print(f"saved: {output_path}")
        print(result.to_markdown())
        return 0
    finally:
        rag.close()


if __name__ == "__main__":
    raise SystemExit(main())
