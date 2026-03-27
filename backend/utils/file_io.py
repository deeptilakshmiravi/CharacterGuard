"""
Handles all file reading and writing for CharacterGuard.

Responsibility:
    - Parse user uploads (description + conversation CSV) into TranscriptRow objects
    - Parse the validation dataset CSV into TranscriptRow objects (with ground truth)
    - Save RunResult to disk as JSON
    - Load a saved RunResult from disk

This module is the only place in the codebase that knows about file formats.
runner.py, scorer.py etc. only ever see TranscriptRow and RunResult — never raw files.

Supported input formats:
    Production mode : description (string) + conversations CSV (question, answer)
    Validation mode : validation dataset CSV (question, answer, judge_score,
                      judge_category, NSFW) + description column or single description
"""

import csv
import json
import logging
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List, Dict, Tuple


import pandas as pd

from runner import TranscriptRow, RunResult, RowResult

#logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_RUNS_DIR = Path("data/raw_runs")
RAW_RUNS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Production mode — parse user upload
# ---------------------------------------------------------------------------

def parse_upload(description: str, csv_file) -> List[TranscriptRow]:
    """
    Parse a content creator's upload into TranscriptRow objects.

    Args:
        description : character persona text (pasted by the user in Streamlit)
        csv_file    : file-like object or path to CSV with columns:
                      question, answer

    Returns:
        list[TranscriptRow] ready for runner.py

    Expected CSV format:
        question,answer
        "Hey, can you help me?","Of course! What do you need?"
        ...
    """
    rows = []

    try:
        df = pd.read_csv(csv_file)
        df.columns = df.columns.str.strip().str.lower()

        _validate_columns(df, required=["question", "answer"], source="upload")

        for i, row in df.iterrows():
            question = str(row["question"]).strip()
            answer = str(row["answer"]).strip()

            if not question or not answer:
                #logger.warning(f"Skipping row {i} — empty question or answer")
                continue

            rows.append(TranscriptRow(
                row_index=i,
                character_description=description.strip(),
                question=question,
                answer=answer,
                # No ground truth in production mode
                ground_truth_score=None,
                ground_truth_category=None,
                ground_truth_nsfw=None,
            ))

    except Exception as e:
        #logger.error(f"Failed to parse upload CSV: {e}")
        raise ValueError(f"Could not parse conversation CSV: {e}")

    #logger.info(f"Parsed {len(rows)} rows from production upload")
    return rows


# ---------------------------------------------------------------------------
# Validation mode — parse research dataset sample
# ---------------------------------------------------------------------------

def parse_dataset_sample(csv_path: Union[str, Path]) -> List[TranscriptRow]:    
    """
    Parse the validation sample CSV (from the research dataset) into
    TranscriptRow objects, including ground truth labels.

    Args:
        csv_path : path to the validation_sample.csv

    Returns:
        list[TranscriptRow] with ground truth fields populated

    Expected CSV columns (from arxiv 2512.01247 dataset):
        description, question, answer, judge_score, judge_category, NSFW
    """
    rows = []
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Validation sample not found at {path}. "
            "Run the sampling script first to generate data/validation_sample.csv"
        )

    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip().str.lower()

        _validate_columns(
            df,
            required=["description", "question", "answer", "judge_score", "judge_category", "nsfw"],
            source="validation dataset"
        )

        for i, row in df.iterrows():
            question = str(row["question"]).strip()
            answer = str(row["answer"]).strip()
            description = str(row["description"]).strip()

            if not question or not answer:
                #logger.warning(f"Skipping dataset row {i} — empty question or answer")
                continue

            # Parse ground truth fields safely
            ground_truth_score = _parse_float(row.get("judge_score"), row_index=i)
            ground_truth_category = str(row.get("judge_category", "")).strip() or None
            ground_truth_nsfw = _parse_bool(row.get("nsfw"), row_index=i)

            rows.append(TranscriptRow(
                row_index=i,
                character_description=description,
                question=question,
                answer=answer,
                ground_truth_score=ground_truth_score,
                ground_truth_category=ground_truth_category,
                ground_truth_nsfw=ground_truth_nsfw,
            ))

    except Exception as e:
        #logger.error(f"Failed to parse validation dataset: {e}")
        raise ValueError(f"Could not parse validation CSV: {e}")

    #logger.info(f"Parsed {len(rows)} rows from validation dataset at {path}")
    return rows


# ---------------------------------------------------------------------------
# Save and load RunResult
# ---------------------------------------------------------------------------

def save_run_result(result: RunResult) -> Path:
    """
    Save a RunResult to disk as JSON in data/raw_runs/.

    Filename format: run_<run_id>_<timestamp>.json

    Args:
        result : RunResult from runner.py

    Returns:
        Path to the saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"run_{result.run_id[:8]}_{timestamp}.json"
    output_path = RAW_RUNS_DIR / filename

    try:
        with open(output_path, "w") as f:
            json.dump(_run_result_to_dict(result), f, indent=2)
        #logger.info(f"RunResult saved to {output_path}")
    except Exception as e:
        #logger.error(f"Failed to save RunResult: {e}")
        raise

    return output_path


def load_run_result(run_id: str) -> Optional[RunResult]:
    """
    Load a previously saved RunResult from disk by run_id prefix.

    Args:
        run_id : full or partial run ID (first 8 chars is enough)

    Returns:
        RunResult if found, None otherwise
    """
    matches = List(RAW_RUNS_DIR.glob(f"run_{run_id[:8]}*.json"))

    if not matches:
        #logger.warning(f"No saved run found for run_id prefix '{run_id[:8]}'")
        return None

    path = matches[0]
    try:
        with open(path, "r") as f:
            data = json.load(f)
        #logger.info(f"Loaded RunResult from {path}")
        return _dict_to_run_result(data)
    except Exception as e:
        #logger.error(f"Failed to load RunResult from {path}: {e}")
        return None


def list_saved_runs() -> List[Dict]:
    """
    List all saved runs in data/raw_runs/.

    Returns:
        List of dicts with run_id, mode, timestamp, total_rows, unsafe_count
        sorted by most recent first
    """
    summaries = []

    for path in sorted(RAW_RUNS_DIR.glob("run_*.json"), reverse=True):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            summaries.append({
                "run_id":      data.get("run_id", "unknown"),
                "mode":        data.get("mode", "unknown"),
                "total_rows":  data.get("total_rows", 0),
                "unsafe_count": data.get("unsafe_count", 0),
                "timestamp":   path.stem.split("_")[-1],  # extract from filename
                "path":        str(path),
            })
        except Exception as e:
            #logger.warning(f"Could not read summary from {path}: {e}")
            print("cannot read summary from path: ", e)

    return summaries


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_columns(df: pd.DataFrame, required: List[str], source: str):
    """Raise a clear error if expected columns are missing."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns in {source} CSV: {missing}. "
            f"Found columns: {List(df.columns)}"
        )


def _parse_float(value, row_index: int) -> Optional[float]:
    """Safely parse a float value from a CSV cell."""
    try:
        return float(value)
    except (TypeError, ValueError):
      # logger.warning(f"Could not parse float at row {row_index}: '{value}'")
        return None


def _parse_bool(value, row_index: int) -> Optional[bool]:
    """Safely parse a bool from a CSV cell (handles TRUE/FALSE strings)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().upper() == "TRUE"
    try:
        return bool(value)
    except (TypeError, ValueError):
      # logger.warning(f"Could not parse bool at row {row_index}: '{value}'")
        return None


def _run_result_to_dict(result: RunResult) -> dict:
    """
    Convert a RunResult (and its nested RowResults) to a
    JSON-serialisable dict.
    """
    return {
        "run_id":                       result.run_id,
        "mode":                         result.mode,
        "total_rows":                   result.total_rows,
        "unsafe_count":                 result.unsafe_count,
        "nsfw_count":                   result.nsfw_count,
        "aggregate_scores":             result.aggregate_scores,
        "remediation_tips":             result.remediation_tips,
        "ground_truth_agreement_rate":  result.ground_truth_agreement_rate,
        "category_match_rate":          result.category_match_rate,
        "status":                       result.status,
        "error_message":                result.error_message,
        "row_results": [
            {
                "row_index":              r.row_index,
                "question":               r.question,
                "answer":                 r.answer,
                "rule_flags":             r.rule_flags,
                "llm_judge_verdict":      r.llm_judge_verdict,
                "judge_category":         r.judge_category,
                "question_category":      r.question_category,
                "nsfw":                   r.nsfw,
                "severity":               r.severity,
                "scores":                 r.scores,
                "ground_truth_score":     r.ground_truth_score,
                "ground_truth_category":  r.ground_truth_category,
                "ground_truth_nsfw":      r.ground_truth_nsfw,
                "score_delta":            r.score_delta,
            }
            for r in result.row_results
        ],
    }


def _dict_to_run_result(data: dict) -> RunResult:
    """Reconstruct a RunResult from a saved JSON dict."""
    row_results = [
        RowResult(
            row_index=             r["row_index"],
            question=              r["question"],
            answer=                r["answer"],
            rule_flags=            r["rule_flags"],
            llm_judge_verdict=     r.get("llm_judge_verdict"),
            judge_category=        r.get("judge_category"),
            question_category=     r.get("question_category"),
            nsfw=                  r.get("nsfw", False),
            severity=              r.get("severity"),
            scores=                r.get("scores", {}),
            ground_truth_score=    r.get("ground_truth_score"),
            ground_truth_category= r.get("ground_truth_category"),
            ground_truth_nsfw=     r.get("ground_truth_nsfw"),
            score_delta=           r.get("score_delta"),
        )
        for r in data.get("row_results", [])
    ]

    return RunResult(
        run_id=                      data["run_id"],
        mode=                        data["mode"],
        total_rows=                  data["total_rows"],
        unsafe_count=                data["unsafe_count"],
        nsfw_count=                  data["nsfw_count"],
        row_results=                 row_results,
        aggregate_scores=            data.get("aggregate_scores", {}),
        remediation_tips=            data.get("remediation_tips", []),
        ground_truth_agreement_rate= data.get("ground_truth_agreement_rate"),
        category_match_rate=         data.get("category_match_rate"),
        status=                      data.get("status", "completed"),
        error_message=               data.get("error_message"),
    )