"""
A declarative rule engine for detecting obvious safety violations.

Architecture using Logic Programming Principles (inspired by an assignment from class):
    This module follows logic programming principles by separating
    KNOWLEDGE (the rules in rules.yaml) from INFERENCE (the engine here).

    - Facts    : the text fields being evaluated (answer, description)
    - Rules    : declared in rules.yaml — patterns that define unsafe content
    - Engine   : evaluates which rules fire against the facts
    - Query    : "which safety categories does this transcript violate?"

    This mirrors how Prolog separates facts/rules from query resolution,
    but implemented in Python without a Prolog interpreter.

When it runs:
    Always — for every single row, before llm_judge is considered.
    If any rules fire, runner.py skips the LLM call entirely.

Output:
    A list of category strings that were flagged, e.g.:
    ["O3: Sexual Content", "O4: Self-Harm"]
    Empty list if nothing triggered.
"""

import re
import logging
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Default path to the rules file — can be overridden in the constructor
DEFAULT_RULES_PATH = Path(__file__).parent.parent / "configs" / "rules.yaml"


# ---------------------------------------------------------------------------
# Rule dataclass
# Represents a single declared rule loaded from rules.yaml
# ---------------------------------------------------------------------------

class Rule:
    """A single safety rule loaded from the rules file."""

    def __init__(self, id: str, category: str, field: str, type: str, patterns: list[str]):
        self.id = id
        self.category = category
        self.field = field          # "answer" or "description"
        self.type = type            # "keyword" or "regex"
        self.patterns = patterns

    def __repr__(self):
        return f"Rule(id={self.id}, category={self.category}, field={self.field})"


# ---------------------------------------------------------------------------
# RuleEngine
# The inference mechanism — evaluates rules against facts
# ---------------------------------------------------------------------------

class RuleEngine:
    """
    Evaluates a set of rules against a set of text fields.

    Separating the engine from RuleEvaluator means the engine
    can be tested independently of file loading.
    """

    def evaluate(self, rules: list[Rule], facts: dict[str, str]) -> list[str]:
        """
        Evaluate all rules against the provided facts.

        Args:
            rules : list of Rule objects (loaded from rules.yaml)
            facts : dict mapping field name to text, e.g.
                    {"answer": "...", "description": "..."}

        Returns:
            Deduplicated list of flagged category strings.
            Order reflects first occurrence.
        """
        flagged_categories = []

        for rule in rules:
            # Skip if the field this rule checks isn't in our facts
            text = facts.get(rule.field)
            if not text:
                continue

            if self._rule_fires(rule, text):
                logger.debug(f"Rule {rule.id} fired → {rule.category}")
                # Deduplicate — multiple rules can map to the same category
                if rule.category not in flagged_categories:
                    flagged_categories.append(rule.category)

        return flagged_categories

    def _rule_fires(self, rule: Rule, text: str) -> bool:
        """
        Check whether a single rule fires against a piece of text.

        Keyword rules : check if any pattern is a substring of the text
        Regex rules   : check if any pattern matches anywhere in the text
        All checks are case-insensitive.
        """
        text_lower = text.lower()

        if rule.type == "keyword":
            return any(pattern.lower() in text_lower for pattern in rule.patterns)

        elif rule.type == "regex":
            return any(
                re.search(pattern, text, flags=re.IGNORECASE)
                for pattern in rule.patterns
            )

        else:
            logger.warning(f"Unknown rule type '{rule.type}' in rule {rule.id} — skipping")
            return False


# ---------------------------------------------------------------------------
# RuleEvaluator
# Public interface — loads rules and runs the engine
# ---------------------------------------------------------------------------

class RuleEvaluator:
    """
    Loads rules from rules.yaml and evaluates them against transcript rows.

    Usage:
        evaluator = RuleEvaluator()
        flags = evaluator.evaluate(
            description="Your Bimbo cock addicted aunt...",
            answer="I need it inside me again..."
        )
        # flags → ["O3: Sexual Content"]
    """

    def __init__(self, rules_path: Optional[Path] = None):
        path = rules_path or DEFAULT_RULES_PATH
        self.rules = self._load_rules(path)
        self.engine = RuleEngine()
        logger.info(f"RuleEvaluator loaded {len(self.rules)} rules from {path}")

    def evaluate(
        self,
        answer: str,
        description: str = "",
        question: str = "",       # accepted but not checked — reserved for future use
    ) -> list[str]:
        """
        Evaluate a transcript row against all loaded rules.

        Args:
            answer      : the character's response (always checked)
            description : the character's persona definition (always checked)
            question    : the user's message (not checked — reserved for future use)

        Returns:
            List of flagged category strings. Empty list if nothing triggered.
        """
        facts = {
            "answer": answer,
            "description": description,
        }
        flags = self.engine.evaluate(self.rules, facts)

        if flags:
            logger.debug(f"Rule evaluator flagged: {flags}")
        else:
            logger.debug("Rule evaluator: no flags — escalating to LLM judge")

        return flags

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_rules(self, path: Path) -> list[Rule]:
        """
        Load and parse rules from the YAML file.
        Each entry in the 'rules' key becomes a Rule object.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Rules file not found at {path}. "
                "Make sure rules.yaml exists in your configs/ directory."
            )

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        raw_rules = data.get("rules", [])
        if not raw_rules:
            logger.warning(f"No rules found in {path}")
            return []

        rules = []
        for entry in raw_rules:
            try:
                rules.append(Rule(
                    id=entry["id"],
                    category=entry["category"],
                    field=entry["field"],
                    type=entry["type"],
                    patterns=entry["patterns"],
                ))
            except KeyError as e:
                logger.warning(f"Skipping malformed rule (missing field {e}): {entry}")

        return rules