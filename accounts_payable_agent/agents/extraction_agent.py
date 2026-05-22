from .base import BaseAgent


class ExtractionAgent(BaseAgent):

    def __init__(self):
        super().__init__("ExtractionAgent")

    def run(self, context: dict) -> dict:

        invoice = context["invoice_blob"]

        extracted = {
            "invoice_number": invoice.get("invoice_number") or invoice.get("filename"),
            "vendor_name": invoice.get("vendor_name") or invoice.get("vendor"),
            "invoice_date": invoice.get("date"),
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency", "USD"),
            "po_number": invoice.get("po_number"),
            "tax_amount": invoice.get("tax_amount") or invoice.get("tax"),
            "line_items": invoice.get("line_items", invoice.get("items", []))
        }

        context["extracted_invoice"] = extracted

        context["extraction_metadata"] = {
            "confidence": 0.96,
            "status": "SUCCESS"
        }
        
        context.setdefault("audit_log", []).append({
            "agent": self.name,
            "status": "SUCCESS",
            "confidence": 0.96
        })

        return context