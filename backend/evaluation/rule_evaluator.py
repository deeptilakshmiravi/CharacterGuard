"""
rule_evaluator.py
A declarative rule engine for detecting obvious safety violations.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict

import yaml

DEFAULT_RULES_PATH = Path(__file__).parent.parent / "configs" / "rules.yaml"


# ---------------------------------------------------------------------------
# Rule dataclass
# ---------------------------------------------------------------------------

class Rule:
    """A single safety rule loaded from the rules file."""

    def __init__(self, id: str, category: str, field: str, type: str, patterns: List[str]):
        self.id = id
        self.category = category
        self.field = field
        self.type = type
        self.patterns = patterns

    def __repr__(self):
        return "Rule(id={}, category={}, field={})".format(
            self.id, self.category, self.field
        )


# ---------------------------------------------------------------------------
# RuleEngine
# ---------------------------------------------------------------------------

class RuleEngine:
    def evaluate(self, rules: List[Rule], facts: Dict[str, str]) -> List[str]:
        flagged_categories = []

        for rule in rules:
            text = facts.get(rule.field)
            if not text:
                continue

            if self._rule_fires(rule, text):
                if rule.category not in flagged_categories:
                    flagged_categories.append(rule.category)

        return flagged_categories

    def _rule_fires(self, rule: Rule, text: str) -> bool:
        text_lower = text.lower()

        if rule.type == "keyword":
            return any(pattern.lower() in text_lower for pattern in rule.patterns)

        elif rule.type == "regex":
            return any(
                re.search(pattern, text, flags=re.IGNORECASE)
                for pattern in rule.patterns
            )

        else:
            return False


# ---------------------------------------------------------------------------
# RuleEvaluator
# ---------------------------------------------------------------------------

class RuleEvaluator:
    def __init__(self, rules_path: Optional[Path] = None):
        path = rules_path or DEFAULT_RULES_PATH
        self.rules = self._load_rules(path)
        self.engine = RuleEngine()

    def evaluate(
        self,
        answer: str,
        description: str = "",
        question: str = "",
    ) -> List[str]:
        facts = {
            "answer": answer
        }

        flags = self.engine.evaluate(self.rules, facts)
        return flags

    def _load_rules(self, path: Path) -> List[Rule]:
        if not path.exists():
            raise FileNotFoundError(
                "Rules file not found at {}. "
                "Make sure rules.yaml exists in your configs/ directory.".format(path)
            )

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        raw_rules = data.get("rules", [])
        if not raw_rules:
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
            except KeyError:
                continue

        return rules