"""Input and output schemas."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
import json


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list")
    return value


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field_name} must be a non-empty string")
    return value


def _require_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a number")
    return float(value)


@dataclass(frozen=True)
class FeatureDetail:
    feat_name: str
    model_prob: float
    evidence_level: str
    is_counter_evidence: bool
    is_legal_for_site: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "FeatureDetail":
        return cls(
            feat_name=_require_str(data.get("feat_name"), "feat_name"),
            model_prob=_require_float(data.get("model_prob"), "model_prob"),
            evidence_level=_require_str(data.get("evidence_level"), "evidence_level"),
            is_counter_evidence=bool(data.get("is_counter_evidence")),
            is_legal_for_site=bool(data.get("is_legal_for_site")),
        )


@dataclass(frozen=True)
class RiskSummary:
    score: float
    level: str
    basis: list[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RiskSummary":
        return cls(
            score=_require_float(data.get("score"), "score"),
            level=_require_str(data.get("level"), "level"),
            basis=[_require_str(item, "basis item") for item in _require_list(data.get("basis"), "basis")],
        )


@dataclass(frozen=True)
class ExclusionSummary:
    excluded_diseases: list[str]
    remaining_differential: list[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExclusionSummary":
        return cls(
            excluded_diseases=[
                _require_str(item, "excluded_diseases item")
                for item in _require_list(data.get("excluded_diseases"), "excluded_diseases")
            ],
            remaining_differential=[
                _require_str(item, "remaining_differential item")
                for item in _require_list(data.get("remaining_differential"), "remaining_differential")
            ],
        )


@dataclass(frozen=True)
class UncertaintySummary:
    total_score: float
    level: str
    perception_score: float
    cognitive_score: float
    reasons: list[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "UncertaintySummary":
        return cls(
            total_score=_require_float(data.get("total_score"), "total_score"),
            level=_require_str(data.get("level"), "level"),
            perception_score=_require_float(data.get("perception_score"), "perception_score"),
            cognitive_score=_require_float(data.get("cognitive_score"), "cognitive_score"),
            reasons=[_require_str(item, "reasons item") for item in _require_list(data.get("reasons"), "reasons")],
        )


@dataclass(frozen=True)
class ReportInput:
    anatomy_site: str
    site_confidence: float
    feature_detail: list[FeatureDetail]
    image_risk: RiskSummary
    exposure_risk: RiskSummary
    total_risk: RiskSummary
    exclusion: ExclusionSummary
    missing_evidence: list[str]
    uncertainty: UncertaintySummary

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReportInput":
        mapping = _require_mapping(data, "input")
        return cls(
            anatomy_site=_require_str(mapping.get("anatomy_site"), "anatomy_site"),
            site_confidence=_require_float(mapping.get("site_confidence"), "site_confidence"),
            feature_detail=[
                FeatureDetail.from_mapping(_require_mapping(item, "feature_detail item"))
                for item in _require_list(mapping.get("feature_detail"), "feature_detail")
            ],
            image_risk=RiskSummary.from_mapping(_require_mapping(mapping.get("image_risk"), "image_risk")),
            exposure_risk=RiskSummary.from_mapping(_require_mapping(mapping.get("exposure_risk"), "exposure_risk")),
            total_risk=RiskSummary.from_mapping(_require_mapping(mapping.get("total_risk"), "total_risk")),
            exclusion=ExclusionSummary.from_mapping(_require_mapping(mapping.get("exclusion"), "exclusion")),
            missing_evidence=[
                _require_str(item, "missing_evidence item")
                for item in _require_list(mapping.get("missing_evidence"), "missing_evidence")
            ],
            uncertainty=UncertaintySummary.from_mapping(
                _require_mapping(mapping.get("uncertainty"), "uncertainty")
            ),
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "ReportInput":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_mapping(json.load(handle))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportResult:
    report_text: str
    input_data: ReportInput
    raw_response: dict[str, Any]
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "report_text": self.report_text,
            "input_data": self.input_data.to_dict(),
            "raw_response": self.raw_response,
        }
