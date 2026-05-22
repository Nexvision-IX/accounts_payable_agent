from .base import BaseAgent
from datetime import datetime, timedelta


class ResolutionAgent(BaseAgent):
    """
    Handles notifications, follow-ups,
    inbox monitoring, and response tracking.

    Inputs:
        context["resolution_result"]
        context["exception_result"]

    Outputs:
        context["communication"]
        context["workflow_status"]
    """

    FOLLOW_UP_DAYS = 1
    MAX_FOLLOWUPS = 10

    def __init__(self):
        super().__init__("ResolutionAgent")

    def run(self, context: dict) -> dict:

        resolution = context.get(
            "resolution_result",
            {}
        )

        exceptions = (
            context
            .get(
                "exception_result",
                {}
            )
            .get(
                "exceptions",
                []
            )
        )

        communications = []

        for ex in exceptions:

            owner = ex["owner"]
            action = ex["action"]

            recipients = self.get_recipients(
                owner
            )

            message = (
                f"Invoice action required: "
                f"{action}"
            )

            communications.append(
                {
                    "owner": owner,
                    "recipients": recipients,
                    "message": message,
                    "status": "EMAIL_SENT",

                    "sent_at":
                        datetime.utcnow(),

                    "next_followup":
                        datetime.utcnow()
                        + timedelta(
                            days=self.FOLLOW_UP_DAYS
                        ),

                    "followup_count": 0,

                    "reply_received": False
                }
            )

        context["communication"] = {

            "active": True,

            "items":
                communications
        }

        context["workflow_status"] = (
            "AWAITING_REPLY"
        )

        context.setdefault(
            "audit_log",
            []
        ).append(
            {
                "agent": self.name,
                "emails_sent":
                    len(
                        communications
                    )
            }
        )

        return context

    def get_recipients(
        self,
        owner
    ):

        routing = {

            "SUPPLIER": [
                "supplier@email.com"
            ],

            "PROCUREMENT": [
                "procurement@email.com"
            ],

            "AP_TEAM": [
                "ap@email.com"
            ],

            "AP_MANAGER": [
                "manager@email.com"
            ],

            "VENDOR_MASTER": [
                "vendor@email.com"
            ]
        }

        return routing.get(
            owner,
            ["support@email.com"]
        )

    def process_inbox(
        self,
        context: dict
    ):

        communications = (
            context
            .get(
                "communication",
                {}
            )
            .get(
                "items",
                []
            )
        )

        for msg in communications:

            # Replace later
            # Outlook / Gmail API

            reply_found = False

            if reply_found:

                msg[
                    "reply_received"
                ] = True

                context[
                    "workflow_status"
                ] = "REVALIDATE"

        return context

    def run_followups(
        self,
        context: dict
    ):

        communications = (
            context
            .get(
                "communication",
                {}
            )
            .get(
                "items",
                []
            )
        )

        now = datetime.utcnow()

        for msg in communications:

            if (
                not msg[
                    "reply_received"
                ]
                and
                msg[
                    "followup_count"
                ]
                < self.MAX_FOLLOWUPS
                and
                now
                >=
                msg[
                    "next_followup"
                ]
            ):

                msg[
                    "followup_count"
                ] += 1

                msg[
                    "next_followup"
                ] = (
                    now
                    + timedelta(
                        days=1
                    )
                )

        return context