from dataclasses import dataclass
from enum import Enum


class ToolRisk(str, Enum):
    READ_ONLY = "read_only"
    SENSITIVE = "sensitive"


class AuthorizationDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class ToolPermission:
    name: str
    risk: ToolRisk
    description: str


@dataclass
class AuthorizationResult:
    decision: AuthorizationDecision
    reason: str


class ToolPermissionManager:
    """
    Deterministic, application-controlled tool authorization.

    This initial version supports read-only tools.
    Sensitive tools remain blocked pending a trusted approval workflow.
    """

    TOOL_PERMISSIONS = {
        "calculator": ToolPermission(
            name="calculator",
            risk=ToolRisk.READ_ONLY,
            description="Perform basic mathematical calculations.",
        ),
        "document_search": ToolPermission(
            name="document_search",
            risk=ToolRisk.READ_ONLY,
            description="Search approved documents.",
        ),
        "send_email": ToolPermission(
            name="send_email",
            risk=ToolRisk.SENSITIVE,
            description="Send an email.",
        ),
        "delete_file": ToolPermission(
            name="delete_file",
            risk=ToolRisk.SENSITIVE,
            description="Delete a file.",
        ),
        "modify_database": ToolPermission(
            name="modify_database",
            risk=ToolRisk.SENSITIVE,
            description="Modify database records.",
        ),
    }

    def authorize(self, tool_name: str) -> AuthorizationResult:
        permission = self.TOOL_PERMISSIONS.get(tool_name)

        if permission is None:
            return AuthorizationResult(
                AuthorizationDecision.DENY,
                "Tool is not registered in the permission policy.",
            )

        if permission.risk == ToolRisk.SENSITIVE:
            return AuthorizationResult(
                AuthorizationDecision.REQUIRE_APPROVAL,
                "Sensitive tool execution requires trusted approval.",
            )

        return AuthorizationResult(
            AuthorizationDecision.ALLOW,
            "Tool is permitted by the read-only policy.",
        )