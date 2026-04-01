"""
Orchestrates a full test run in either Validation or Production mode.

VALIDATION MODE
    Input : transcript rows from the research dataset (already has ground truth labels)
    Output: our scores + side-by-side comparison with ground truth

PRODUCTION MODE
    Input : a content creator's own character description + conversations (questions + answers)
    Output: safety report with scores, flags, and remediation tips (no ground truth)

In both modes, the same evaluation pipeline runs the only difference is whether
runner compares the results against ground truth labels at the end.

Flow:
    1. Receive parsed transcript rows (from file_io.py)
    2. For each row, pass (description + question + answer) to the evaluator pipeline
    3. Evaluator returns scores, flags, category, severity
    4. Aggregate all rows into a RunResult
    5. If validation mode: attach ground truth comparison
    6. Save and return RunResult
"""

import uuid
#import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

from evaluation.rule_evaluator import RuleEvaluator
from evaluation.llm_judge import LLMJudge
from evaluation.scorer import Scorer
#from utils.file_io import save_run_result

#logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data contracts
# These dataclasses are the "language" the whole team speaks.
# Frontend, backend, and evaluator all read/write these shapes.
# See docs/json_contract.md for the full spec.
# ---------------------------------------------------------------------------

@dataclass
class TranscriptRow:
    """
    One row of input which is a single question/answer exchange.
    This is what file_io.py produces after parsing the user's upload.
    Both modes use this same shape.
    """
    row_index: int
    character_description: str
    question: str                        # the user/attacker turn
    answer: str                          # the character's response

    # Only populated in validation mode (from the research dataset)
    ground_truth_score: Optional[float] = None
    ground_truth_category: Optional[str] = None
    ground_truth_nsfw: Optional[bool] = None


@dataclass
class RowResult:
    # Result for a single transcript row after evaluation
    row_index: int
    question: str
    answer: str

    # Our evaluator outputs
    rule_flags: List[str]                # e.g. ["self_harm", "hate_speech"]
    llm_judge_verdict: Optional[str]     # "safe" | "unsafe" | "ambiguous"
    judge_category: Optional[str]        # e.g. "O2: Unfair Representation"
    question_category: Optional[str]     # e.g. "Hypothetical Scenario"
    nsfw: bool
    severity: Optional[str]             # "minor" | "major"
    scores: Dict                         # dimension -> float e.g. {"toxicity": 0.8}
    all_categories: List[str]
     
    # Only populated in validation mode
    ground_truth_score: Optional[float] = None
    ground_truth_category: Optional[str] = None
    ground_truth_nsfw: Optional[bool] = None
    score_delta: Optional[float] = None  # our score - ground truth score


@dataclass
class RunResult:
    # Aggregated result for a full test run. This is what the frontend reads.
    run_id: str
    mode: str                            # "validation" | "production"
    total_rows: int
    unsafe_count: int
    nsfw_count: int
    row_results: List[RowResult]
    aggregate_scores: Dict               # dimension -> float (averaged across rows)
    remediation_tips: List[str]

    # Only populated in validation mode
    ground_truth_agreement_rate: Optional[float] = None   # 0.0 - 1.0
    category_match_rate: Optional[float] = None

    status: str = "completed"            # "completed" | "error"
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class Runner:
    """
    Orchestrates a full test run.

    Usage for Production mode:
        rows = file_io.parse_upload(uploaded_file)
        runner = Runner(mode="production")
        result = runner.run(rows)

    Usage for Validation mode:
        rows = file_io.parse_dataset_sample("data/validation_sample.csv")
        runner = Runner(mode="validation")
        result = runner.run(rows)
    """

    VALID_MODES = {"production", "validation"}

    def __init__(self, mode: str = "production"):
        if mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of {self.VALID_MODES}, got '{mode}'")

        self.mode = mode
        self.rule_evaluator = RuleEvaluator()
        self.llm_judge = LLMJudge()
        self.scorer = Scorer()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, rows: List[TranscriptRow]) -> RunResult:
        from utils.file_io import save_run_result
        run_id = str(uuid.uuid4())
        #logger.info(f"Starting {self.mode} run {run_id} - {len(rows)} rows")

        row_results: List[RowResult] = []

        for row in rows:
            #logger.debug(f"Evaluating row {row.row_index}")
            row_result = self._evaluate_row(row)
            row_results.append(row_result)

        result = self._aggregate(run_id, row_results)
        save_run_result(result)
        
        """
        logger.info(
            f"Run {run_id} complete — "
            f"{result.unsafe_count}/{result.total_rows} unsafe, "
            f"{result.nsfw_count}/{result.total_rows} NSFW"
        )"""
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _evaluate_row(self, row: TranscriptRow) -> RowResult:
        # Run one transcript row through the full evaluation pipeline
        # 1. Rule-based layer (always runs first — fast, no API cost)
        rule_flags = self.rule_evaluator.evaluate(
            description=row.character_description,
            question=row.question,
            answer=row.answer,
        )
        
        # 2. LLM judge layer
        llm_verdict, llm_category, question_category, nsfw, severity = \
            self.llm_judge.judge(
                description=row.character_description,
                question=row.question,
                answer=row.answer,
                rule_flags=rule_flags,
            )
        
        # Primary category: rule wins if fired, otherwise use LLM
        final_judge_category = rule_flags[0] if rule_flags else llm_category

        # 3. Dimension scores
        scores = self.scorer.score_row(
            rule_flags=rule_flags,
            llm_verdict=llm_verdict,
            severity=severity,
            nsfw=nsfw
        )
        # 4. Ground truth delta (validation mode only)
        our_score = scores.get("overall", 0.0)
        score_delta = None
        if self.mode == "validation" and row.ground_truth_score is not None:
            score_delta = round(our_score - row.ground_truth_score, 3)
        return RowResult(
            row_index=row.row_index,
            question=row.question,
            answer=row.answer,
            rule_flags=rule_flags,
            llm_judge_verdict=llm_verdict,
            judge_category=final_judge_category,
            all_categories=list(set(rule_flags + ([llm_category] if llm_category else []))),
            question_category=question_category,
            nsfw=nsfw,
            severity=severity,
            scores=scores,
            ground_truth_score=row.ground_truth_score,
            ground_truth_category=row.ground_truth_category,
            ground_truth_nsfw=row.ground_truth_nsfw,
            score_delta=score_delta,
        )

    def _aggregate(self, run_id: str, row_results: List[RowResult]) -> RunResult:
        # Aggregate per-row results into a final RunResult
        unsafe_rows = [r for r in row_results if r.llm_judge_verdict == "unsafe" or r.rule_flags]
        nsfw_rows = [r for r in row_results if r.nsfw]

        aggregate_scores = self.scorer.aggregate([r.scores for r in row_results])
        remediation_tips = self.scorer.generate_remediation_tips(aggregate_scores)

        # Validation mode: compute agreement metrics
        ground_truth_agreement_rate = None
        category_match_rate = None
        if self.mode == "validation":
            ground_truth_agreement_rate = self._compute_agreement_rate(row_results)
            category_match_rate = self._compute_category_match_rate(row_results)

        return RunResult(
            run_id=run_id,
            mode=self.mode,
            total_rows=len(row_results),
            unsafe_count=len(unsafe_rows),
            nsfw_count=len(nsfw_rows),
            row_results=row_results,
            aggregate_scores=aggregate_scores,
            remediation_tips=remediation_tips,
            ground_truth_agreement_rate=ground_truth_agreement_rate,
            category_match_rate=category_match_rate,
        )

    def _compute_agreement_rate(self, row_results: List[RowResult]) -> float:
        """
        Measures how closely our overall scores match the dataset's judge_score.
        Uses a tolerance threshold — if our score is within 1 point of ground truth,
        we count it as agreement. Adjust TOLERANCE as needed after calibration.
        """
        TOLERANCE = 1.0
        rows_with_truth = [r for r in row_results if r.ground_truth_score is not None]
        if not rows_with_truth:
            return 0.0
        agreements = [r for r in rows_with_truth if abs(r.score_delta) <= TOLERANCE]
        return round(len(agreements) / len(rows_with_truth), 3)

    def _compute_category_match_rate(self, row_results: List[RowResult]) -> float:
        # Measures how often our judge_category matches the dataset's judge_category
        rows_with_truth = [r for r in row_results if r.ground_truth_category is not None]
        if not rows_with_truth:
            return 0.0
        matches = [
            r for r in rows_with_truth
            if r.judge_category == r.ground_truth_category
        ]
        return round(len(matches) / len(rows_with_truth), 3)