import hashlib
import re
import json
from io import BytesIO

from PIL import Image
import pytesseract


def parse_amount(value):

    if not value:
        return None

    m = re.search(
        r"(\d+[\.,]?\d*)",
        str(value).replace(",", "")
    )

    return (
        float(m.group(1))
        if m
        else None
    )


def extract_invoice(
    image_bytes
):

    text = ""

    try:

        img = Image.open(
            BytesIO(
                image_bytes
            )
        )

        text = (
            pytesseract
            .image_to_string(
                img
            )
        )

    except Exception:

        text = ""

    result = {

        "invoice_number": None,
        "vendor_name": None,
        "invoice_date": None,

        "currency": None,

        "amount": None,

        "po_number": None,

        "payment_terms": None,

        "line_items": []
    }

    for line in text.splitlines():

        l = line.lower()

        if (
            "invoice"
            in l
        ):

            result[
                "invoice_number"
            ] = line

        if (
            "vendor"
            in l
        ):

            result[
                "vendor_name"
            ] = line

        if (
            "po"
            in l
        ):

            result[
                "po_number"
            ] = line

        if (
            "amount"
            in l
        ):

            result[
                "amount"
            ] = (
                parse_amount(
                    line
                )
            )

    result[
        "document_hash"
    ] = hashlib.sha256(
        image_bytes
    ).hexdigest()

    result[
        "confidence"
    ] = 0.90

    result[
        "raw_text"
    ] = text

    return result