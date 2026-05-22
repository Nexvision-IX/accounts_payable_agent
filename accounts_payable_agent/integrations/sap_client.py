from datetime import datetime


class SAPClient:
    """
    SAP integration layer.

    Replace later with:
    - RFC
    - OData
    - BAPI
    - SAP REST API
    """

    def __init__(self, config=None):

        self.config = config or {}

        self.timeout = (
            self.config
            .get(
                "timeout",
                30
            )
        )

    # ----------------------------------------
    # Retrieve PO / GRN / Vendor data
    # ----------------------------------------

    def fetch_invoice_related(
        self,
        invoice_number,
        po_number=None
    ):

        try:

            # Replace with SAP call

            return {

                "status": "SUCCESS",

                "invoice_number":
                    invoice_number,

                # Vendor

                "vendor_exists": True,

                "vendor_blocked": False,

                # Purchase Order

                "po_exists": True,

                "po_number":
                    (
                        po_number
                        or
                        "PO-0001"
                    ),

                "po_status": "OPEN",

                # GRN

                "grn_exists": True,

                "grn_posted": True,

                "grn_number":
                    "GRN-1001",

                # Validation

                "currency":
                    "USD",

                "price_match": True,

                "quantity_match": True,

                # Duplicate Detection

                "invoice_already_posted":
                    False,

                # Metadata

                "retrieved_at":
                    (
                        datetime
                        .utcnow()
                        .isoformat()
                    )
            }

        except Exception as e:

            return {

                "status": "FAILED",

                "error":
                    str(e),

                "retryable": True
            }

    # ----------------------------------------
    # Post Invoice to SAP
    # ----------------------------------------

    def post_invoice(
        self,
        invoice_payload
    ):

        try:

            invoice = (
                invoice_payload
                .get(
                    "invoice_number"
                )
            )

            # Replace later:
            # BAPI_INCOMINGINVOICE_CREATE

            return {

                "status": "POSTED",

                "sap_document":
                    "SAP-1001",

                "invoice_number":
                    invoice,

                "posted_at":
                    (
                        datetime
                        .utcnow()
                        .isoformat()
                    )
            }

        except Exception as e:

            return {

                "status": "FAILED",

                "error":
                    str(e)
            }

    # ----------------------------------------
    # Check Invoice Status
    # ----------------------------------------

    def get_post_status(
        self,
        sap_document
    ):

        try:

            return {

                "status":
                    "POSTED",

                "sap_document":
                    sap_document
            }

        except Exception:

            return {

                "status":
                    "UNKNOWN"
            }

    # ----------------------------------------
    # Health Check
    # ----------------------------------------

    def ping(self):

        return {

            "connected": True,

            "system": "SAP"
        }