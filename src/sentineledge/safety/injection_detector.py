
import re
from dataclasses import dataclass


@dataclass
class InjectionResult:
    is_suspicious: bool
    matched_patterns: list[str]


class PromptInjectionDetector:
    """
    Rule-based baseline detector.

    Detects selected direct injection commands at the beginning
    of a message. This is not a comprehensive security solution.
    """

    PATTERNS = {
        "ignore_previous_instructions": (
            r"^\s*(?:please\s+)?"
            r"(?:ignore|disregard)\s+"
            r"(?:(?:all|any|the)\s+)?"
            r"(?:previous|prior|above)\s+"
            r"(?:instructions?|prompts?|rules?|directives?)\b"
        ),

        "reveal_system_prompt": (
            r"^\s*(?:please\s+)?"
            r"(?:reveal|show|print|display|expose|disclose)\s+"
            r"(?:(?:the|your)\s+)?"
            r"(?:(?:hidden|system|developer)\s+)*"
            r"(?:system\s+)?"
            r"(?:prompt|message|instructions?)\b"
        ),

        "override_instructions": (
            r"^\s*(?:please\s+)?"
            r"(?:override|bypass|disable)\s+"
            r"(?:(?:all|the)\s+)?"
            r"(?:safety|security|system)\s+"
            r"(?:rules?|instructions?|restrictions?)\b"
        ),

        "unrestricted_persona": (
            r"^\s*(?:please\s+)?"
            r"(?:act|behave)\s+as\s+"
            r"(?:an?\s+)?"
            r"(?:unrestricted|unfiltered|uncensored)\b"
        ),

        "do_not_follow_previous_rules": (
            r"^\s*(?:please\s+)?"
            r"do\s+not\s+(?:follow|obey)\s+"
            r"(?:the\s+)?"
            r"(?:rules?|instructions?|directives?)\s+"
            r"(?:above|previous|prior)\b"
        ),

        "forget_previous_context": (
            r"^\s*(?:please\s+)?"
            r"forget\s+"
            r"(?:everything|all)\s+"
            r"(?:you\s+were\s+told|previous\s+instructions?)\b"
        ),
    }

    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }

    def detect(self, text: str) -> InjectionResult:

        matches = [
            name
            for name, pattern in self.compiled_patterns.items()
            if pattern.search(text)
        ]

        return InjectionResult(
            is_suspicious=bool(matches),
            matched_patterns=matches,
        )
