from .extraction_agent import ExtractionAgent
from .sap_data_agent import SAPDataAgent
from .validation_agent import ValidationAgent
from .decision_agent import DecisionAgent
from .classifier_agent import ClassifierAgent
from .resolution_agent import ResolutionAgent
from .communication_agent import CommunicationAgent


class Orchestrator:
    """
    End-to-end Accounts Payable workflow orchestrator.

    Invoice closes only after successful SAP posting.
    """

    MAX_CYCLES = 30

    def __init__(self):

        self.extraction = ExtractionAgent()
        self.sap = SAPDataAgent()

        self.validation = ValidationAgent()
        self.decision = DecisionAgent()

        self.classifier = ClassifierAgent()
        self.resolution = ResolutionAgent()

        self.communication = CommunicationAgent()

    def run(self, invoice_blob: dict):

        context = {

            "invoice_blob": invoice_blob,

            "workflow_status": "STARTED",

            "audit_log": [],

            "cycle": 0
        }

        while context["cycle"] < self.MAX_CYCLES:

            context["cycle"] += 1

            # -------------------------------------
            # Extract
            # -------------------------------------

            if "extracted_invoice" not in context:

                context = (
                    self.extraction
                    .run(context)
                )

            # -------------------------------------
            # Fetch SAP
            # -------------------------------------

            context = (
                self.sap
                .run(context)
            )

            # -------------------------------------
            # Validate
            # -------------------------------------

            context = (
                self.validation
                .run(context)
            )

            # -------------------------------------
            # Decide
            # -------------------------------------

            context = (
                self.decision
                .run(context)
            )

            action = (
                context
                .get(
                    "decision",
                    {}
                )
                .get(
                    "action"
                )
            )

            # -------------------------------------
            # Direct posting
            # -------------------------------------

            if action == "POST_TO_SAP":

                context[
                    "workflow_status"
                ] = "POSTED"

                context[
                    "outcome"
                ] = {

                    "posted": True
                }

                return context

            # -------------------------------------
            # Exception
            # -------------------------------------

            if (
                action
                ==
                "CLASSIFY_EXCEPTION"
            ):

                context = (
                    self.classifier
                    .run(context)
                )

                context = (
                    self.resolution
                    .run(context)
                )

                next_action = (
                    context
                    .get(
                        "resolution_result",
                        {}
                    )
                    .get(
                        "next_action"
                    )
                )

                # -----------------------------
                # Auto resolved
                # -----------------------------

                if (
                    next_action
                    ==
                    "REVALIDATE"
                ):

                    continue

                # -----------------------------
                # Communication
                # -----------------------------

                context = (
                    self.communication
                    .run(context)
                )

                # Check replies

                context = (
                    self.communication
                    .process_inbox(
                        context
                    )
                )

                # Follow up

                context = (
                    self.communication
                    .run_followups(
                        context
                    )
                )

                if (
                    context[
                        "workflow_status"
                    ]
                    ==
                    "REVALIDATE"
                ):

                    continue

                return context

            # -------------------------------------
            # Manual Review
            # -------------------------------------

            if (
                action
                ==
                "MANUAL_REVIEW"
            ):

                context[
                    "workflow_status"
                ] = (
                    "WAITING_HUMAN"
                )

                return context

        context[
            "workflow_status"
        ] = (
            "MAX_RETRY_REACHED"
        )

        return context