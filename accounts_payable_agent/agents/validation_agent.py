from .base import BaseAgent


class ValidationAgent(BaseAgent):
    """
    Validates invoice against SAP information.

    Inputs:
        context["extracted_invoice"]
        context["sap_data"]
        context["match_result"]

    Outputs:
        context["validation_result"]
        context["workflow_status"]
    """

    def __init__(self):
        super().__init__("ValidationAgent")

    def run(self, context: dict) -> dict:

        invoice = context.get("extracted_invoice", {})
        sap = context.get("sap_data", {})
        match = context.get("match_result", {})

        issues = []
        auto_fix_actions = []

        # ---------------------------------------------------
        # Mandatory invoice checks
        # ---------------------------------------------------

        mandatory_fields = [
            "invoice_number",
            "vendor_name",
            "amount",
            "invoice_date"
        ]

        for field in mandatory_fields:
            if not invoice.get(field):
                issues.append(
                    {
                        "type": "MISSING_FIELD",
                        "field": field
                    }
                )

        # ---------------------------------------------------
        # Vendor checks
        # ---------------------------------------------------

        if not sap.get("vendor_exists"):
            issues.append({
                "type": "VENDOR_NOT_FOUND"
            })

        if sap.get("vendor_blocked"):
            issues.append({
                "type": "VENDOR_BLOCKED"
            })

        # ---------------------------------------------------
        # PO Validation
        # ---------------------------------------------------

        if not sap.get("po_exists"):
            issues.append({
                "type": "PO_MISSING"
            })

        # ---------------------------------------------------
        # GRN Validation
        # ---------------------------------------------------

        if not sap.get("grn_exists"):
            issues.append({
                "type": "GRN_MISSING"
            })

        elif not sap.get("grn_posted"):
            issues.append({
                "type": "GRN_NOT_POSTED"
            })

        # ---------------------------------------------------
        # Duplicate Invoice
        # ---------------------------------------------------

        if sap.get("invoice_already_posted"):
            issues.append({
                "type": "DUPLICATE_INVOICE"
            })

        # ---------------------------------------------------
        # Match Validation
        # ---------------------------------------------------

        if not sap.get("price_match"):
            issues.append({
                "type": "PRICE_MISMATCH"
            })

        if not sap.get("quantity_match"):
            issues.append({
                "type": "QUANTITY_MISMATCH"
            })

        if (
            invoice.get("currency")
            and sap.get("currency")
            and invoice["currency"] != sap["currency"]
        ):
            issues.append({
                "type": "CURRENCY_MISMATCH"
            })

        # ---------------------------------------------------
        # Auto Resolution Logic
        # ---------------------------------------------------

        if (
            invoice.get("po_number") is None
            and sap.get("po_exists")
        ):

            invoice["po_number"] = sap["po_number"]

            auto_fix_actions.append(
                "AUTO_POPULATED_PO"
            )

        # ---------------------------------------------------
        # Final Decision
        # ---------------------------------------------------

        clean_invoice = len(issues) == 0

        validation_result = {

            "clean_invoice": clean_invoice,

            "validation_status":
                (
                    "READY_FOR_POSTING"
                    if clean_invoice
                    else "EXCEPTION"
                ),

            "issue_count": len(issues),

            "issues": issues,

            "auto_fix_actions": auto_fix_actions,

            "three_way_match": match
        }

        context["extracted_invoice"] = invoice
        context["validation_result"] = validation_result

        context["workflow_status"] = (
            "VALIDATED"
            if clean_invoice
            else "EXCEPTION_FOUND"
        )

        context.setdefault("audit_log", []).append(
            {
                "agent": self.name,
                "status": "SUCCESS",
                "issues_found": len(issues)
            }
        )

        return context