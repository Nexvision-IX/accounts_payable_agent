import json
from datetime import datetime

from accounts_payable_agent.agents.extraction_agent import ExtractionAgent
from accounts_payable_agent.agents.sap_data_agent import SAPDataAgent
from accounts_payable_agent.agents.validation_agent import ValidationAgent
from accounts_payable_agent.agents.decision_agent import DecisionAgent
from accounts_payable_agent.agents.classifier_agent import ClassifierAgent
from accounts_payable_agent.agents.resolution_agent import ResolutionAgent
from accounts_payable_agent.agents.communication_agent import CommunicationAgent


class DemoWorkflowRunner:
    """
    Streamlit demo runner that uses all AP agents.
    """

    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.sap_agent = SAPDataAgent()
        self.validation_agent = ValidationAgent()
        self.decision_agent = DecisionAgent()
        self.classifier_agent = ClassifierAgent()
        self.resolution_agent = ResolutionAgent()
        self.communication_agent = CommunicationAgent()

    def run_invoice(self, invoice_blob: dict, scenario: str) -> dict:
        context = {
            "invoice_blob": invoice_blob,
            "scenario": scenario,
            "workflow_status": "STARTED",
            "audit_log": [],
            "started_at": datetime.now().isoformat(),
        }

        # 1. Extraction Agent
        context = self.extraction_agent.run(context)

        # 2. SAP Data Agent
        context = self.sap_agent.run(context)

        # Override SAP result for demo scenarios
        context["sap_data"] = self._demo_sap_data(
            context["extracted_invoice"],
            scenario
        )

        # 3. Validation Agent
        context = self.validation_agent.run(context)

        # 4. Decision Agent
        context = self.decision_agent.run(context)

        decision = context.get("decision", {}).get("action")

        if decision == "POST_TO_SAP":
            context["workflow_status"] = "POSTED"
            context["posting_result"] = {
                "posted": True,
                "sap_document": f"SAP-{context['extracted_invoice']['invoice_number']}",
                "posted_at": datetime.now().isoformat(),
            }
            return context

        # 5. Classifier Agent
        context = self.classifier_agent.run(context)

        # 6. Resolution Agent
        context = self.resolution_agent.run(context)

        # 7. Communication Agent
        context = self.communication_agent.run(context)

        context["workflow_status"] = "AWAITING_REPLY"

        return context

    def _demo_sap_data(self, invoice: dict, scenario: str) -> dict:
        """
        Demo SAP response.

        3 clean invoices
        1 PO issue
        1 GRN issue
        """

        if scenario == "clean":
            return {
                "vendor_exists": True,
                "vendor_blocked": False,
                "po_exists": True,
                "po_number": invoice.get("po_number"),
                "po_status": "OPEN",
                "grn_exists": True,
                "grn_posted": True,
                "grn_number": "GRN-1001",
                "invoice_already_posted": False,
                "currency": invoice.get("currency", "USD"),
                "price_match": True,
                "quantity_match": True,
            }

        if scenario == "po_issue":
            return {
                "vendor_exists": True,
                "vendor_blocked": False,
                "po_exists": False,
                "po_number": None,
                "po_status": None,
                "grn_exists": False,
                "grn_posted": False,
                "grn_number": None,
                "invoice_already_posted": False,
                "currency": invoice.get("currency", "USD"),
                "price_match": True,
                "quantity_match": True,
            }

        if scenario == "grn_issue":
            return {
                "vendor_exists": True,
                "vendor_blocked": False,
                "po_exists": True,
                "po_number": invoice.get("po_number"),
                "po_status": "OPEN",
                "grn_exists": False,
                "grn_posted": False,
                "grn_number": None,
                "invoice_already_posted": False,
                "currency": invoice.get("currency", "USD"),
                "price_match": True,
                "quantity_match": True,
            }

        return {}