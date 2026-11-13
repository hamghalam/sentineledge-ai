
from enum import Enum
from dataclasses import dataclass


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str


class PolicyEngine:
    """
    Deterministic policy enforcement.

    This is an initial policy layer, not a complete
    prompt-injection or AI safety detector.
    """

    MAX_INPUT_LENGTH = 4000

    ALLOWED_ACTIONS = {
        "answer",
        "search_document",
    }

    APPROVAL_REQUIRED_ACTIONS = {
        "send_email",
        "delete_file",
        "modify_database",
    }

    def evaluate(self, action: str, text: str) -> PolicyResult:

        if not text or not text.strip():
            return PolicyResult(
                PolicyDecision.DENY,
                "Input cannot be empty."
            )

        if len(text) > self.MAX_INPUT_LENGTH:
            return PolicyResult(
                PolicyDecision.DENY,
                "Input exceeds the maximum allowed length."
            )

        if action in self.APPROVAL_REQUIRED_ACTIONS:
            return PolicyResult(
                PolicyDecision.REQUIRE_APPROVAL,
                "This action requires explicit authorization."
            )

        if action not in self.ALLOWED_ACTIONS:
            return PolicyResult(
                PolicyDecision.DENY,
                "Action is not permitted by the policy."
            )

        return PolicyResult(
            PolicyDecision.ALLOW,
            "Request passed the policy checks."
        )
