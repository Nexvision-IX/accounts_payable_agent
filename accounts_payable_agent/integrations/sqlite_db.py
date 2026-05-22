import sqlite3
import json

from pathlib import Path


# -----------------------------------------
# Connection
# -----------------------------------------

def get_conn(db_path):

    conn = sqlite3.connect(
        str(db_path)
    )

    conn.row_factory = (
        sqlite3.Row
    )

    return conn


# -----------------------------------------
# Schema
# -----------------------------------------

def init_db(db_path):

    db = Path(db_path)

    db.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = get_conn(db)

    cur = conn.cursor()

    # ----------------------------
    # Invoice Master
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (

        id INTEGER PRIMARY KEY,

        invoice_number TEXT UNIQUE,

        vendor_name TEXT,

        amount REAL,

        currency TEXT,

        invoice_date TEXT,

        workflow_status TEXT,

        document_hash TEXT,

        confidence REAL,

        raw_json TEXT,

        created_at TEXT
            DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ----------------------------
    # SAP Data
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sap_data (

        id INTEGER PRIMARY KEY,

        invoice_id INTEGER,

        po_exists INTEGER,

        po_number TEXT,

        grn_exists INTEGER,

        grn_posted INTEGER,

        price_match INTEGER,

        quantity_match INTEGER,

        invoice_posted INTEGER,

        retrieved_at TEXT,

        FOREIGN KEY(invoice_id)
        REFERENCES invoices(id)
    )
    """)

    # ----------------------------
    # Exception Tracking
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exceptions (

        id INTEGER PRIMARY KEY,

        invoice_id INTEGER,

        issue TEXT,

        severity TEXT,

        owner TEXT,

        status TEXT,

        created_at TEXT
            DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ----------------------------
    # Communication
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (

        id INTEGER PRIMARY KEY,

        invoice_id INTEGER,

        recipients TEXT,

        message TEXT,

        reply_received INTEGER,

        followup_count INTEGER,

        sent_at TEXT,

        next_followup TEXT
    )
    """)

    # ----------------------------
    # Audit
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (

        id INTEGER PRIMARY KEY,

        invoice_id INTEGER,

        agent TEXT,

        action TEXT,

        created_at TEXT
            DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    conn.close()


# -----------------------------------------
# Save Invoice
# -----------------------------------------

def save_invoice(
    db_path,
    invoice
):

    conn = get_conn(
        db_path
    )

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO invoices (

            invoice_number,

            vendor_name,

            amount,

            currency,

            invoice_date,

            workflow_status,

            document_hash,

            confidence,

            raw_json

        )

        VALUES (

            ?,?,?,?,?,?,?,?,?

        )
        """,

        (

            invoice.get(
                "invoice_number"
            ),

            invoice.get(
                "vendor_name"
            ),

            invoice.get(
                "amount"
            ),

            invoice.get(
                "currency"
            ),

            invoice.get(
                "invoice_date"
            ),

            invoice.get(
                "workflow_status"
            ),

            invoice.get(
                "document_hash"
            ),

            invoice.get(
                "confidence"
            ),

            json.dumps(
                invoice
            )
        )
    )

    invoice_id = (
        cur.lastrowid
    )

    conn.commit()

    conn.close()

    return invoice_id


# -----------------------------------------
# Save SAP
# -----------------------------------------

def save_sap_data(
    db_path,
    invoice_id,
    sap
):

    conn = get_conn(
        db_path
    )

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO sap_data (

            invoice_id,

            po_exists,

            po_number,

            grn_exists,

            grn_posted,

            price_match,

            quantity_match,

            invoice_posted,

            retrieved_at

        )

        VALUES (

            ?,?,?,?,?,?,?,?,
            CURRENT_TIMESTAMP

        )
        """,

        (

            invoice_id,

            int(
                sap.get(
                    "po_exists",
                    False
                )
            ),

            sap.get(
                "po_number"
            ),

            int(
                sap.get(
                    "grn_exists",
                    False
                )
            ),

            int(
                sap.get(
                    "grn_posted",
                    False
                )
            ),

            int(
                sap.get(
                    "price_match",
                    False
                )
            ),

            int(
                sap.get(
                    "quantity_match",
                    False
                )
            ),

            int(
                sap.get(
                    "invoice_posted",
                    False
                )
            )
        )
    )

    conn.commit()

    conn.close()


# -----------------------------------------
# Save Notification
# -----------------------------------------

def save_notification(
    db_path,
    invoice_id,
    recipients,
    message
):

    conn = get_conn(
        db_path
    )

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO notifications (

            invoice_id,

            recipients,

            message,

            reply_received,

            followup_count,

            sent_at

        )

        VALUES (

            ?,?,?,0,0,
            CURRENT_TIMESTAMP

        )
        """,

        (

            invoice_id,

            json.dumps(
                recipients
            ),

            message
        )
    )

    conn.commit()

    conn.close()