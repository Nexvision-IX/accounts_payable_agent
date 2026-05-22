from .base import BaseAgent


class DecisionAgent(BaseAgent):
    """
    Determines the next workflow action.

    Inputs:
        context["validation_result"]

    Outputs:
        context["decision"]
        context["workflow_status"]
    """

    def __init__(self):
        super().__init__("DecisionAgent")

    def run(self, context: dict) -> dict:

        validation = context.get(
            "validation_result",
            {}
        )

        issues = validation.get(
            "issues",
            []
        )

        auto_fix = validation.get(
            "auto_fix_actions",
            []
        )

        clean = validation.get(
            "clean_invoice",
            False
        )

        decision = {}

        # --------------------------------------------------
        # Clean invoice → Post directly
        # --------------------------------------------------

        if clean:

            decision = {
                "action": "POST_TO_SAP",
                "reason": "VALIDATION_SUCCESS"
            }

        # --------------------------------------------------
        # Auto corrected → Revalidate
        # --------------------------------------------------

        elif auto_fix:

            decision = {
                "action": "REVALIDATE",
                "reason": auto_fix
            }

        else:

            issue_types = [
                i["type"]
                for i in issues
            ]

            # ------------------------------------------
            # Manual review
            # ------------------------------------------

            if (
                "DUPLICATE_INVOICE"
                in issue_types
            ):

                decision = {
                    "action": "MANUAL_REVIEW",
                    "reason": issue_types
                }

            # ------------------------------------------
            # Exception routing
            # ------------------------------------------

            else:

                decision = {
                    "action": "CLASSIFY_EXCEPTION",
                    "reason": issue_types
                }

        context["decision"] = decision

        context["workflow_status"] = (
            decision["action"]
        )

        context.setdefault(
            "audit_log",
            []
        ).append(
            {
                "agent": self.name,
                "decision": decision
            }
        )

        return context