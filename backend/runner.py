"""
runner.py
Orchestrates a full adversarial test run against a target AI character.

Flow:
    1. Load character config (YAML) and attack dataset (CSV/JSON)
    2. For each attack prompt, run a multi-turn conversation via conversation_engine
    3. Pass each conversation turn through the evaluator pipeline
    4. Aggregate scores and return a structured RunResult
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional

# from conversation_engine import ConversationEngine
# from evaluator.rule_evaluator import RuleEvaluator
# from evaluator.llm_judge import LLMJudge
# from evaluator.scorer import Scorer
# from utils.file_io import load_character_config, load_attack_dataset, save_run_result

logger = logging.getLogger(__name__)


# Data contracts

@dataclass
class TurnResult:
    """Result for a single conversation turn."""
    turn_index: int
    attack_prompt: str
    character_response: str
    rule_flags: list[str]           # e.g. ["self_harm", "explicit_content"]
    llm_judge_verdict: Optional[str]  # "safe" or "unsafe" or "ambiguous" or None
    severity: Optional[str]          # "minor" or "major" or None
    raw_scores: dict                  # dimension -> float, e.g. {"toxicity": 0.8}


@dataclass
class RunResult:
    """Aggregated result for a full test run."""
    run_id: str
    character_id: str
    total_turns: int
    unsafe_count: int
    turn_results: list[TurnResult]
    aggregate_scores: dict            # dimension -> float (averaged across turns)
    remediation_tips: list[str]
    status: str = "completed"         # "completed" or "error"
    error_message: Optional[str] = None


# Runner

class Runner:
    """
    Orchestrates a full test run.

    Usage:
        runner = Runner(character_config_path="configs/my_char.yaml",
                        attack_dataset_path="data/attacks.json")
        result = runner.run()
    """

    def __init__(
        self,
        character_config_path: str,
        attack_dataset_path: str,
        use_llm_judge: bool = True,
    ):
        self.character_config = load_character_config(character_config_path)
        self.attacks = load_attack_dataset(attack_dataset_path)
        self.use_llm_judge = use_llm_judge

        # Sub-components (swap implementations here without touching this file)
        self.conversation_engine = ConversationEngine(self.character_config)
        self.rule_evaluator = RuleEvaluator()
        self.llm_judge = LLMJudge() if use_llm_judge else None
        self.scorer = Scorer()

    # Public entry point

    def run(self):
        run_id = str(uuid.uuid4())
        character_id = self.character_config.get("id", "unknown")
        logger.info(f"Starting run {run_id} for character '{character_id}'")

        turn_results: list[TurnResult] = []

        for i, attack in enumerate(self.attacks):
            logger.debug(f"Turn {i+1}/{len(self.attacks)}: {attack['prompt'][:60]}...")
            turn_result = self._run_single_turn(i, attack)
            turn_results.append(turn_result)

        run_result = self._aggregate(run_id, character_id, turn_results)
        save_run_result(run_result)

        logger.info(f"Run {run_id} complete — {run_result.unsafe_count}/{run_result.total_turns} unsafe turns")
        return run_result

    # Private helpers

    def _run_single_turn(self, index: int, attack: dict):
        """Run one attack prompt through the full eval pipeline."""
        prompt = attack["prompt"]

        # 1. Get character response
        response = self.conversation_engine.send(prompt)

        # 2. Rule-based evaluation (always runs)
        rule_flags = self.rule_evaluator.evaluate(prompt, response)

        # 3. LLM judge (only runs if rules are inconclusive)
        llm_verdict = None
        severity = None
        if self.llm_judge and self._needs_llm_review(rule_flags):
            llm_verdict, severity = self.llm_judge.judge(prompt, response)
        elif rule_flags:
            # Rules flagged something — assign severity without LLM
            severity = "major" if len(rule_flags) > 1 else "minor"
            llm_verdict = "unsafe"

        # 4. Per-turn dimension scores
        raw_scores = self.scorer.score_turn(
            prompt=prompt,
            response=response,
            rule_flags=rule_flags,
            llm_verdict=llm_verdict,
        )

        return TurnResult(
            turn_index=index,
            attack_prompt=prompt,
            character_response=response,
            rule_flags=rule_flags,
            llm_judge_verdict=llm_verdict,
            severity=severity,
            raw_scores=raw_scores,
        )

    def _needs_llm_review(self, rule_flags: list[str]):
        """
        Decides whether to escalate to the LLM judge.
        Rule flags = definite hit → no LLM needed (save API calls).
        No flags     = possibly fine, but LLM can catch subtle cases.
        """
        return len(rule_flags) == 0  # Only use LLM when rules are silent

    def _aggregate(
        self, run_id: str, character_id: str, turn_results: list[TurnResult]
    ) -> RunResult:
        """Aggregate per-turn scores into a final RunResult."""
        unsafe_turns = [t for t in turn_results if t.llm_judge_verdict == "unsafe" or t.rule_flags]
        aggregate_scores = self.scorer.aggregate([t.raw_scores for t in turn_results])
        remediation_tips = self.scorer.generate_remediation_tips(aggregate_scores)

        return RunResult(
            run_id=run_id,
            character_id=character_id,
            total_turns=len(turn_results),
            unsafe_count=len(unsafe_turns),
            turn_results=turn_results,
            aggregate_scores=aggregate_scores,
            remediation_tips=remediation_tips,
        )