from .base import BaseAgent


class SAPDataAgent(BaseAgent):
    """
    Retrieves SAP information required for invoice validation.

    Inputs:
        context["extracted_invoice"]

    Outputs:
        context["sap_data"]
        context["match_result"]
        context["workflow_status"]
    """

    def __init__(self):
        super().__init__("SAPDataAgent")

    def run(self, context: dict) -> dict:

        invoice = context.get("extracted_invoice", {})
        invoice_blob = context.get("invoice_blob", {})

        po_number = invoice.get("po_number")
        invoice_amount = invoice.get("amount")
        invoice_currency = invoice.get("currency", "USD")
        vendor = invoice.get("vendor_name")

        # ------------------------------------------------------------------
        # Use mockup data from invoice blob (for demo purposes)
        # In production, this would call actual SAP RFC / OData / API
        # ------------------------------------------------------------------

        sap_data = {

            # Vendor Information
            "vendor_exists": invoice_blob.get("vendor_exists", True),
            "vendor_blocked": invoice_blob.get("vendor_blocked", False),
            "vendor_code": f"VEND{int(invoice_blob.get('id', '001')):03d}",

            # Purchase Order
            "po_exists": invoice_blob.get("po_exists", True),
            "po_number": po_number,
            "po_status": "OPEN" if invoice_blob.get("po_exists", True) else "NOT_FOUND",

            # Goods Receipt
            "grn_exists": invoice_blob.get("grn_exists", True),
            "grn_posted": invoice_blob.get("grn_posted", True),
            "grn_number": f"GRN-{int(invoice_blob.get('id', '5678')):04d}",

            # Financial Information
            "currency": invoice_currency,
            "payment_terms": "NET30",
            "tax_code": "TX01",

            # Duplicate Detection
            "invoice_already_posted": False,

            # Matching Checks
            "price_match": invoice_blob.get("price_match", True),
            "quantity_match": invoice_blob.get("quantity_match", True),

            # Line Level Data
            "po_lines": [
                {
                    "material": "ITEM001",
                    "qty": 10,
                    "price": invoice_amount / 10 if invoice_amount else 100
                }
            ],

            "grn_lines": [
                {
                    "material": "ITEM001",
                    "received_qty": 10
                }
            ]
        }

        # ----------------------------------------------------
        # Build 3-way match summary
        # ----------------------------------------------------

        match_result = {

            "invoice_po_match":
                sap_data["po_exists"],

            "po_grn_match":
                (
                    sap_data["grn_exists"]
                    and sap_data["grn_posted"]
                ),

            "invoice_grn_match":
                (
                    sap_data["currency"] == invoice_currency
                    and sap_data["price_match"]
                    and sap_data["quantity_match"]
                )
        }

        # ----------------------------------------------------
        # Save to workflow context
        # ----------------------------------------------------

        context["sap_data"] = sap_data
        context["match_result"] = match_result

        context["workflow_status"] = "SAP_DATA_RETRIEVED"

        context.setdefault("audit_log", []).append({
            "agent": self.name,
            "status": "SUCCESS"
        })

        return context