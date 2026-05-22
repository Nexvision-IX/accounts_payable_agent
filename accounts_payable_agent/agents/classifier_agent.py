from .base import BaseAgent


class ClassifierAgent(BaseAgent):
    """
    Classifies validation issues and determines
    owner, severity, action, and SLA.
    """

    def __init__(self):
        super().__init__("ClassifierAgent")

    def run(self, context: dict) -> dict:

        validation = context.get(
            "validation_result",
            {}
        )

        issues = validation.get(
            "issues",
            []
        )

        classifications = []

        for issue in issues:

            issue_type = issue["type"]

            mapping = {

                "PO_MISSING": {
                    "severity": "MEDIUM",
                    "owner": "SUPPLIER",
                    "action": "REQUEST_PO"
                },

                "GRN_MISSING": {
                    "severity": "HIGH",
                    "owner": "PROCUREMENT",
                    "action": "POST_GRN"
                },

                "GRN_NOT_POSTED": {
                    "severity": "HIGH",
                    "owner": "PROCUREMENT",
                    "action": "POST_GRN"
                },

                "PRICE_MISMATCH": {
                    "severity": "HIGH",
                    "owner": "AP_TEAM",
                    "action": "INVESTIGATE"
                },

                "QUANTITY_MISMATCH": {
                    "severity": "HIGH",
                    "owner": "PROCUREMENT",
                    "action": "VERIFY_RECEIPT"
                },

                "DUPLICATE_INVOICE": {
                    "severity": "CRITICAL",
                    "owner": "AP_MANAGER",
                    "action": "MANUAL_REVIEW"
                },

                "VENDOR_BLOCKED": {
                    "severity": "CRITICAL",
                    "owner": "VENDOR_MASTER",
                    "action": "UNBLOCK_VENDOR"
                },

                "CURRENCY_MISMATCH": {
                    "severity": "MEDIUM",
                    "owner": "AP_TEAM",
                    "action": "VERIFY_CURRENCY"
                },

                "MISSING_FIELD": {
                    "severity": "LOW",
                    "owner": "SUPPLIER",
                    "action": "REQUEST_CORRECTION"
                }
            }

            rule = mapping.get(
                issue_type,
                {
                    "severity": "MEDIUM",
                    "owner": "AP_TEAM",
                    "action": "MANUAL_REVIEW"
                }
            )

            classifications.append(
                {
                    "issue": issue_type,
                    **rule
                }
            )

        # ---------------------------------------------------
        # Overall Severity
        # ---------------------------------------------------

        severity_order = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4
        }

        overall = "NONE"

        if classifications:
            overall = max(
                classifications,
                key=lambda x:
                severity_order[
                    x["severity"]
                ]
            )["severity"]

        context["exception_result"] = {

            "has_exception":
                len(classifications) > 0,

            "overall_severity":
                overall,

            "exceptions":
                classifications
        }

        context["workflow_status"] = (
            "EXCEPTION_CLASSIFIED"
        )

        context.setdefault(
            "audit_log",
            []
        ).append(
            {
                "agent": self.name,
                "exception_count":
                    len(classifications)
            }
        )

        return context