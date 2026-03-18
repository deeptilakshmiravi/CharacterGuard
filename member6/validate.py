"""
validate.py — CharacterGuard Data Contract Enforcer
Member 6: Integration Lead & QA

Usage:
    python validate.py <path_to_json_file> [--type transcript|config|attacks]

Examples:
    python validate.py transcripts/mock_transcript_001.json
    python validate.py mock_data/mock_config.json --type config
    python validate.py mock_data/mock_attacks.json --type attacks

If no --type is given, the script auto-detects by inspecting the file's keys.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ValidationError


# ─────────────────────────────────────────────
# SCHEMA DEFINITIONS
# ─────────────────────────────────────────────

class EvaluationBlock(BaseModel):
    status: str = Field(..., description="Must be 'PASS' or 'FAIL'")
    violation_type: Optional[str] = Field(default=None)
    reason: str
    persona_drift_score: float = Field(..., ge=0.0, le=1.0)
    forbidden_disclosure_detected: bool

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v not in ("PASS", "FAIL"):
            raise ValueError(f"status must be 'PASS' or 'FAIL', got '{v}'")
        return v


class TurnBlock(BaseModel):
    turn_number: int = Field(..., ge=1)
    user_message: str
    bot_response: str  # ← CRITICAL: must be 'bot_response', NOT 'bot_text'
    latency_ms: int = Field(..., ge=0)


class TranscriptSchema(BaseModel):
    transcript_id: str
    config_id: str
    attack_id: str
    attack_type: str
    timestamp: str
    turns: List[TurnBlock] = Field(..., min_length=1)
    evaluations: EvaluationBlock


class ConfigSchema(BaseModel):
    config_id: str
    character_name: str
    character_description: str
    system_prompt: str
    forbidden_disclosures: List[str]
    temperature: float = Field(..., ge=0.0, le=2.0)
    model: str
    version: str


class AttackEntry(BaseModel):
    attack_id: str
    type: str
    category: str
    description: str
    expected_failure: str


class AttacksSchema(BaseModel):
    schema_version: str
    attacks: List[AttackEntry] = Field(..., min_length=1)


# ─────────────────────────────────────────────
# AUTO-DETECT FILE TYPE
# ─────────────────────────────────────────────

def detect_type(data: dict) -> str:
    if "transcript_id" in data:
        return "transcript"
    if "config_id" in data and "system_prompt" in data:
        return "config"
    if "attacks" in data and "schema_version" in data:
        return "attacks"
    return "unknown"


# ─────────────────────────────────────────────
# VALIDATOR
# ─────────────────────────────────────────────

SCHEMA_MAP = {
    "transcript": TranscriptSchema,
    "config": ConfigSchema,
    "attacks": AttacksSchema,
}


def validate_file(filepath: str, file_type: Optional[str] = None) -> bool:
    path = Path(filepath)

    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{filepath}': {e}")
        return False

    # Auto-detect if not specified
    resolved_type = file_type or detect_type(data)

    if resolved_type not in SCHEMA_MAP:
        print(f"ERROR: Could not determine file type for '{filepath}'. "
              f"Use --type transcript|config|attacks")
        return False

    schema_class = SCHEMA_MAP[resolved_type]

    try:
        schema_class.model_validate(data)
        print(f"✅  VALID [{resolved_type.upper()}]: {path.name}")
        return True
    except ValidationError as e:
        print(f"❌  INVALID [{resolved_type.upper()}]: {path.name}")
        for error in e.errors():
            field_path = " → ".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            print(f"    ERROR: Missing or invalid key '{field_path}': {msg}")
        return False


# ─────────────────────────────────────────────
# BATCH MODE — validate a whole folder
# ─────────────────────────────────────────────

def validate_folder(folder: str, file_type: Optional[str] = None):
    folder_path = Path(folder)
    json_files = list(folder_path.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in '{folder}'")
        return

    print(f"\n{'='*50}")
    print(f" Validating {len(json_files)} files in: {folder}")
    print(f"{'='*50}")

    results = [validate_file(str(f), file_type) for f in sorted(json_files)]
    passed = sum(results)
    failed = len(results) - passed

    print(f"\n{'─'*50}")
    print(f" Results: {passed} PASSED | {failed} FAILED out of {len(results)}")
    print(f"{'─'*50}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CharacterGuard JSON Validator — checks files against the data contract."
    )
    parser.add_argument("path", help="Path to a JSON file or a folder of JSON files")
    parser.add_argument(
        "--type",
        choices=["transcript", "config", "attacks"],
        default=None,
        help="Force file type (auto-detected if omitted)",
    )

    args = parser.parse_args()
    target = Path(args.path)

    if target.is_dir():
        validate_folder(args.path, args.type)
    else:
        success = validate_file(args.path, args.type)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()