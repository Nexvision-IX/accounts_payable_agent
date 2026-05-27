import os
import re
import json
import sqlite3
import smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st


st.set_page_config(
    page_title="AP Multi-Agent Demo",
    layout="wide",
    initial_sidebar_state="expanded"
)


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploaded_invoices"
DB_PATH = DATA_DIR / "ap_demo.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": os.getenv("SMTP_USER", "kkashyap@flairzapp.com"),
    "smtp_password": os.getenv("SMTP_PASSWORD", "cete lnqb cvpz jidc"),
    "email_from": os.getenv("EMAIL_FROM", "accounts.payable.demo@gmail.com"),
    "recipient": os.getenv("EMAIL_TO", "kkashyap@flairzapp.com"),
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    def table_exists(table_name):
        cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
        """, (table_name,))
        return cur.fetchone() is not None

    def get_columns(table_name):
        if not table_exists(table_name):
            return []
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]

    def add_column_if_missing(table_name, column_name, column_type):
        existing_columns = get_columns(table_name)
        if column_name not in existing_columns:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        invoice_number TEXT,
        vendor_name TEXT,
        amount REAL,
        currency TEXT,
        invoice_date TEXT,
        po_number TEXT,
        status TEXT,
        scenario TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS po_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT,
        po_number TEXT,
        po_amount REAL,
        currency TEXT,
        vendor_name TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grn_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT,
        grn_number TEXT,
        grn_posted INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS validation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        invoice_number TEXT,
        validation_status TEXT,
        issues TEXT,
        decision TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        invoice_number TEXT,
        recipient TEXT,
        subject TEXT,
        body TEXT,
        sent INTEGER,
        sent_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        invoice_number TEXT,
        followup_count INTEGER,
        reply_received INTEGER,
        current_status TEXT,
        updated_at TEXT
    )
    """)

    # Safe migrations for existing deployed SQLite DB.
    # This does not delete any existing table or data.
    add_column_if_missing("po_data", "invoice_number", "TEXT")
    add_column_if_missing("grn_data", "invoice_number", "TEXT")
    add_column_if_missing("validation_results", "invoice_number", "TEXT")
    add_column_if_missing("email_logs", "invoice_number", "TEXT")
    add_column_if_missing("followups", "invoice_number", "TEXT")

    # Backfill invoice_number for old rows that still only have invoice_id.
    cur.execute("""
    UPDATE po_data
    SET invoice_number = (
        SELECT invoices.invoice_number
        FROM invoices
        WHERE invoices.id = po_data.invoice_id
    )
    WHERE invoice_number IS NULL
      AND EXISTS (
        SELECT 1
        FROM invoices
        WHERE invoices.id = po_data.invoice_id
    )
    """)

    cur.execute("""
    UPDATE grn_data
    SET invoice_number = (
        SELECT invoices.invoice_number
        FROM invoices
        WHERE invoices.id = grn_data.invoice_id
    )
    WHERE invoice_number IS NULL
      AND EXISTS (
        SELECT 1
        FROM invoices
        WHERE invoices.id = grn_data.invoice_id
    )
    """)

    cur.execute("""
    UPDATE validation_results
    SET invoice_number = (
        SELECT invoices.invoice_number
        FROM invoices
        WHERE invoices.id = validation_results.invoice_id
    )
    WHERE invoice_number IS NULL
      AND EXISTS (
        SELECT 1
        FROM invoices
        WHERE invoices.id = validation_results.invoice_id
    )
    """)

    cur.execute("""
    UPDATE email_logs
    SET invoice_number = (
        SELECT invoices.invoice_number
        FROM invoices
        WHERE invoices.id = email_logs.invoice_id
    )
    WHERE invoice_number IS NULL
      AND EXISTS (
        SELECT 1
        FROM invoices
        WHERE invoices.id = email_logs.invoice_id
    )
    """)

    cur.execute("""
    UPDATE followups
    SET invoice_number = (
        SELECT invoices.invoice_number
        FROM invoices
        WHERE invoices.id = followups.invoice_id
    )
    WHERE invoice_number IS NULL
      AND EXISTS (
        SELECT 1
        FROM invoices
        WHERE invoices.id = followups.invoice_id
    )
    """)

    conn.commit()
    conn.close()


def reset_db():
    conn = get_conn()
    cur = conn.cursor()

    for table in [
        "invoices",
        "po_data",
        "grn_data",
        "validation_results",
        "email_logs",
        "followups",
    ]:
        cur.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()


def fetch_table(table_name):
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def render_header():
    st.markdown("""
    <div style="
        background: linear-gradient(to right, #1f4e79, #4f81bd);
        padding:24px;
        border-radius:14px;
        margin-bottom:20px;
    ">
        <h1 style="color:white;margin-bottom:5px;">
            AI-Powered Accounts Payable Automation
        </h1>
        <p style="color:white;font-size:18px;margin-bottom:0;">
            Multi-Agent Invoice Validation, Exception Handling, Follow-up & SAP Posting Demo
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_workflow():
    st.markdown("""
    <div style="
        background:#f8f9fb;
        padding:18px;
        border-radius:12px;
        border:1px solid #e0e0e0;
        margin-bottom:20px;
    ">
        <b>Workflow:</b>
        📤 Upload Invoice → 🔍 Extraction → 💾 SQLite Storage → 🔗 SAP PO/GRN Retrieval →
        ✅ Validation → 🧠 Decision → ⚠️ Exception → 📧 Email → 🔁 Follow-up → 🚀 Posting
    </div>
    """, unsafe_allow_html=True)


def render_kpi_card(column, title, value, bg_color):
    column.markdown(f"""
    <div style="
        background:{bg_color};
        padding:20px;
        border-radius:14px;
        text-align:center;
        border:1px solid #e6e6e6;
        box-shadow:0 1px 4px rgba(0,0,0,0.08);
    ">
        <h2 style="margin-bottom:4px;">{value}</h2>
        <p style="margin:0;font-weight:600;">{title}</p>
    </div>
    """, unsafe_allow_html=True)


def render_success_box(message):
    st.markdown(f"""
    <div style="
        background-color:#e8fff0;
        padding:15px;
        border-radius:10px;
        border-left:6px solid #00b050;
        margin-bottom:10px;
    ">
        <h4 style="color:#006400;margin:0;">
            ✅ {message}
        </h4>
    </div>
    """, unsafe_allow_html=True)


def render_exception_box(message):
    st.markdown(f"""
    <div style="
        background-color:#ffe5e5;
        padding:15px;
        border-radius:10px;
        border-left:6px solid #ff4b4b;
        margin-bottom:10px;
    ">
        <h4 style="color:#b30000;margin:0;">
            ⚠️ {message}
        </h4>
    </div>
    """, unsafe_allow_html=True)


def render_waiting_box(message):
    st.markdown(f"""
    <div style="
        background-color:#fff4cc;
        padding:12px;
        border-radius:10px;
        border-left:6px solid #ffb300;
        margin-bottom:10px;
    ">
        <b>⏳ {message}</b>
    </div>
    """, unsafe_allow_html=True)


def extract_invoice_from_pdf(uploaded_file, index):
    file_name = uploaded_file.name

    invoice_no_match = re.search(
        r"INV[-_]?\d{4}[-_]?\d+",
        file_name.upper()
    )

    invoice_number = (
        invoice_no_match.group(0).replace("_", "-")
        if invoice_no_match
        else f"INV-2026-00{index + 1}"
    )

    vendors = [
        "Industrial Parts Ltd",
        "Tech Supplies Inc",
        "Office Equipment Ltd",
        "Facility Services Co",
        "Consulting Partners",
    ]

    amounts = [
        7850.00,
        1917.00,
        8424.00,
        3996.00,
        10260.00,
    ]

    po_numbers = [
        "PO-7890",
        "PO-4521",
        "PO-6640",
        "PO-7782",
        "PO-9901",
    ]

    return {
        "file_name": file_name,
        "invoice_number": invoice_number,
        "vendor_name": vendors[index],
        "amount": amounts[index],
        "currency": "USD",
        "invoice_date": "2026-05-21",
        "po_number": po_numbers[index],
    }


def assign_demo_scenario(index):
    if index in [0, 1, 2]:
        return "clean"

    if index == 3:
        return "po_issue"

    return "grn_issue"


def generate_po_grn_data(invoice, scenario):
    if scenario == "clean":
        return {
            "po_exists": True,
            "po_number": invoice["po_number"],
            "po_amount": invoice["amount"],
            "grn_exists": True,
            "grn_posted": True,
            "grn_number": f"GRN-{invoice['id']:04d}",
        }

    if scenario == "po_issue":
        return {
            "po_exists": False,
            "po_number": None,
            "po_amount": None,
            "grn_exists": True,
            "grn_posted": True,
            "grn_number": f"GRN-{invoice['id']:04d}",
        }

    if scenario == "grn_issue":
        return {
            "po_exists": True,
            "po_number": invoice["po_number"],
            "po_amount": invoice["amount"],
            "grn_exists": False,
            "grn_posted": False,
            "grn_number": None,
        }


def save_invoice(invoice, scenario):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO invoices (
        file_name,
        invoice_number,
        vendor_name,
        amount,
        currency,
        invoice_date,
        po_number,
        status,
        scenario,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice["file_name"],
        invoice["invoice_number"],
        invoice["vendor_name"],
        invoice["amount"],
        invoice["currency"],
        invoice["invoice_date"],
        invoice["po_number"],
        "EXTRACTED",
        scenario,
        datetime.now().isoformat(),
    ))

    invoice_id = cur.lastrowid
    conn.commit()
    conn.close()

    return invoice_id


def save_po_grn(invoice_id, invoice, sap_data):
    conn = get_conn()
    cur = conn.cursor()

    if sap_data["po_exists"]:
        cur.execute("""
        INSERT INTO po_data (
            invoice_number,
            po_number,
            po_amount,
            currency,
            vendor_name,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            invoice["invoice_number"],
            sap_data["po_number"],
            sap_data["po_amount"],
            invoice["currency"],
            invoice["vendor_name"],
            datetime.now().isoformat(),
        ))

    if sap_data["grn_exists"]:
        cur.execute("""
        INSERT INTO grn_data (
            invoice_number,
            grn_number,
            grn_posted,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """, (
            invoice["invoice_number"],
            sap_data["grn_number"],
            int(sap_data["grn_posted"]),
            datetime.now().isoformat(),
        ))

    conn.commit()
    conn.close()


def validate_invoice(invoice_id):
    conn = get_conn()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    po = conn.execute(
        "SELECT * FROM po_data WHERE invoice_number = ?",
        (invoice["invoice_number"],)
    ).fetchone()

    grn = conn.execute(
        "SELECT * FROM grn_data WHERE invoice_number = ?",
        (invoice["invoice_number"],)
    ).fetchone()

    issues = []

    if po is None:
        issues.append("PO_MISSING")

    if grn is None:
        issues.append("GRN_MISSING")
    elif not grn["grn_posted"]:
        issues.append("GRN_NOT_POSTED")

    if not issues:
        validation_status = "PASSED"
        decision = "POST_TO_SAP"
        final_status = "POSTED"
    else:
        validation_status = "FAILED"
        decision = "EXCEPTION"
        final_status = "EXCEPTION"

    conn.execute("""
    INSERT INTO validation_results (
        invoice_id,
        invoice_number,
        validation_status,
        issues,
        decision,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        invoice["invoice_number"],
        validation_status,
        json.dumps(issues),
        decision,
        datetime.now().isoformat(),
    ))

    conn.execute(
        "UPDATE invoices SET status = ? WHERE id = ?",
        (final_status, invoice_id)
    )

    if decision == "EXCEPTION":
        conn.execute("""
        INSERT INTO followups (
            invoice_id,
            invoice_number,
            followup_count,
            reply_received,
            current_status,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            invoice["invoice_number"],
            0,
            0,
            "EMAIL_REQUIRED",
            datetime.now().isoformat(),
        ))

    conn.commit()
    conn.close()

    return {
        "invoice_id": invoice["id"],
        "invoice_number": invoice["invoice_number"],
        "status": validation_status,
        "decision": decision,
        "issues": issues,
    }


def build_exception_email(invoice, issues):
    issue_text = ", ".join(issues)

    subject = f"Action Required: Invoice {invoice['invoice_number']} validation failed"

    if "PO_MISSING" in issues:
        action_required = (
            "Purchase Order is not available in SAP. "
            "Please verify the PO details and update the system."
        )
    elif "GRN_MISSING" in issues or "GRN_NOT_POSTED" in issues:
        action_required = (
            "Goods Receipt is not available or not posted in SAP. "
            "Please post the GRN so that AP can continue invoice processing."
        )
    else:
        action_required = (
            "Please review the invoice exception and provide the required update."
        )

    body = f"""
    <h3>Accounts Payable Exception Alert</h3>

    <p>Hello Team,</p>

    <p>The following invoice failed validation and requires action.</p>

    <table border="1" cellpadding="6" cellspacing="0">
        <tr><td><b>Invoice Number</b></td><td>{invoice['invoice_number']}</td></tr>
        <tr><td><b>Vendor</b></td><td>{invoice['vendor_name']}</td></tr>
        <tr><td><b>Amount</b></td><td>{invoice['currency']} {invoice['amount']}</td></tr>
        <tr><td><b>PO Number on Invoice</b></td><td>{invoice['po_number']}</td></tr>
        <tr><td><b>Issue</b></td><td>{issue_text}</td></tr>
    </table>

    <p><b>Action Required:</b> {action_required}</p>

    <p>Please review and take the required action so that AP can proceed with posting.</p>

    <p>Regards,<br/>AP Automation Agent</p>
    """

    return subject, body


def send_email(config, subject, body):
    if not all([
        config["smtp_server"],
        config["smtp_user"],
        config["smtp_password"],
        config["email_from"],
        config["recipient"],
    ]):
        return False, "SMTP details missing"

    try:
        msg = MIMEMultipart()
        msg["From"] = config["email_from"]
        msg["To"] = config["recipient"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(config["smtp_server"], int(config["smtp_port"])) as server:
            server.starttls()
            server.login(config["smtp_user"], config["smtp_password"])
            server.send_message(msg)

        return True, "Email sent"

    except Exception as e:
        return False, str(e)


def save_email_log(invoice_id, invoice_number, recipient, subject, body, sent):
    conn = get_conn()

    conn.execute("""
    INSERT INTO email_logs (
        invoice_id,
        invoice_number,
        recipient,
        subject,
        body,
        sent,
        sent_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        invoice_number,
        recipient,
        subject,
        body,
        int(sent),
        datetime.now().isoformat(),
    ))

    conn.execute("""
    UPDATE followups
    SET current_status = ?
    WHERE invoice_number = ?
    """, (
        "WAITING_FOR_REPLY" if sent else "EMAIL_FAILED",
        invoice_number,
    ))

    conn.commit()
    conn.close()


def send_followup(invoice_id):
    conn = get_conn()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    validation = conn.execute(
        """
        SELECT * FROM validation_results
        WHERE invoice_number = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (invoice["invoice_number"],)
    ).fetchone()

    issues = json.loads(validation["issues"])

    subject = f"Follow-up Required: Invoice {invoice['invoice_number']}"

    body = f"""
    <h3>Follow-up: Accounts Payable Exception</h3>

    <p>Hello Team,</p>

    <p>This is a follow-up for invoice <b>{invoice['invoice_number']}</b>.</p>

    <p><b>Vendor:</b> {invoice['vendor_name']}</p>
    <p><b>Pending Issue:</b> {", ".join(issues)}</p>

    <p>Please provide the required update so AP can continue invoice processing.</p>

    <p>Regards,<br/>AP Automation Agent</p>
    """

    sent, message = send_email(EMAIL_CONFIG, subject, body)

    if sent:
        conn.execute("""
        UPDATE followups
        SET followup_count = followup_count + 1,
            current_status = ?,
            updated_at = ?
        WHERE invoice_number = ?
        """, (
            "FOLLOWUP_SENT",
            datetime.now().isoformat(),
            invoice["invoice_number"],
        ))

        conn.execute("""
        INSERT INTO email_logs (
            invoice_id,
            invoice_number,
            recipient,
            subject,
            body,
            sent,
            sent_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            invoice["invoice_number"],
            EMAIL_CONFIG["recipient"],
            subject,
            body,
            1,
            datetime.now().isoformat(),
        ))

    conn.commit()
    conn.close()

    return sent, message


def mark_reply_received(invoice_id):
    conn = get_conn()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    conn.execute("""
    UPDATE followups
    SET reply_received = 1,
        current_status = ?,
        updated_at = ?
    WHERE invoice_number = ?
    """, (
        "REPLY_RECEIVED",
        datetime.now().isoformat(),
        invoice["invoice_number"],
    ))

    conn.commit()
    conn.close()


def revalidate_and_post(invoice_id):
    conn = get_conn()

    invoice = conn.execute(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    conn.execute(
        "UPDATE invoices SET status = ? WHERE id = ?",
        ("POSTED_AFTER_RESOLUTION", invoice_id)
    )

    conn.execute("""
    UPDATE followups
    SET current_status = ?,
        updated_at = ?
    WHERE invoice_number = ?
    """, (
        "RESOLVED_AND_POSTED",
        datetime.now().isoformat(),
        invoice["invoice_number"],
    ))

    conn.commit()
    conn.close()


def main():
    init_db()

    render_header()
    render_workflow()

    with st.sidebar:
        st.header("AP Multi-Agent Demo")
        st.success("Demo environment active")

        st.markdown("""
        ### Workflow

        ✅ Invoice Upload  
        ✅ Data Extraction  
        ✅ SQLite Storage  
        ✅ SAP PO / GRN Retrieval  
        ✅ Validation  
        ✅ Exception Handling  
        ✅ Email Notification  
        ✅ Follow-up  
        ✅ Revalidation  
        ✅ Posting  
        """)

        st.divider()

        if st.button("🗑️ Reset Demo Database"):
            reset_db()
            st.success("Database cleared.")
            st.rerun()

    uploaded_files = st.file_uploader(
        "Upload exactly 5 invoice PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} invoice(s) uploaded.")

    agent_status = st.empty()

    if st.button("🚀 Process Uploaded Invoices"):
        if not uploaded_files or len(uploaded_files) != 5:
            st.error("Please upload exactly 5 invoice PDFs.")
        else:
            reset_db()
            progress = st.progress(0)

            for idx, uploaded_file in enumerate(uploaded_files):
                agent_status.info(f"🔍 Extraction Agent running for {uploaded_file.name}")

                file_path = UPLOAD_DIR / uploaded_file.name

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                scenario = assign_demo_scenario(idx)

                extracted = extract_invoice_from_pdf(uploaded_file, idx)

                invoice_id = save_invoice(extracted, scenario)
                extracted["id"] = invoice_id

                agent_status.info(
                    f"🔗 SAP PO / GRN Retrieval Agent running for {extracted['invoice_number']}"
                )

                sap_data = generate_po_grn_data(extracted, scenario)
                save_po_grn(invoice_id, extracted, sap_data)

                agent_status.info(
                    f"✅ Validation Agent running for {extracted['invoice_number']}"
                )

                validation = validate_invoice(invoice_id)

                if validation["decision"] == "EXCEPTION":
                    agent_status.warning(
                        f"⚠️ Exception Agent triggered for {extracted['invoice_number']}"
                    )

                    conn = get_conn()
                    invoice = conn.execute(
                        "SELECT * FROM invoices WHERE id = ?",
                        (invoice_id,)
                    ).fetchone()
                    conn.close()

                    subject, body = build_exception_email(
                        invoice,
                        validation["issues"]
                    )

                    sent, _ = send_email(EMAIL_CONFIG, subject, body)

                    save_email_log(
                        invoice_id,
                        invoice["invoice_number"],
                        EMAIL_CONFIG["recipient"],
                        subject,
                        body,
                        sent,
                    )

                progress.progress((idx + 1) / len(uploaded_files))

            agent_status.success("🚀 Workflow completed")
            st.balloons()
            st.success("""
            ✅ Invoice processing completed.

            3 invoices posted automatically.  
            2 invoices moved to exception workflow.
            """)
            st.rerun()

    st.divider()

    invoices = fetch_table("invoices")
    po_data = fetch_table("po_data")
    grn_data = fetch_table("grn_data")
    validations = fetch_table("validation_results")
    emails = fetch_table("email_logs")
    followups = fetch_table("followups")

    posted = len([
        x for x in invoices
        if x["status"] in ["POSTED", "POSTED_AFTER_RESOLUTION"]
    ])

    exceptions = len([
        x for x in invoices
        if x["status"] == "EXCEPTION"
    ])

    emails_sent = len([
        x for x in emails
        if x["sent"] == 1
    ])

    k1, k2, k3, k4 = st.columns(4)
    render_kpi_card(k1, "Invoices Uploaded", len(invoices), "#f5f7ff")
    render_kpi_card(k2, "Posted", posted, "#e8fff0")
    render_kpi_card(k3, "Exceptions", exceptions, "#ffe5e5")
    render_kpi_card(k4, "Emails Sent", emails_sent, "#fff7e6")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Invoices",
        "PO Data From SAP",
        "GRN Data From SAP",
        "Validation",
        "Emails",
        "Follow-ups",
    ])

    with tab1:
        st.subheader("Extracted Invoices Saved in SQLite")
        st.dataframe(invoices, use_container_width=True)

    with tab2:
        st.subheader("PO Data Retrieved From SAP")
        st.dataframe(po_data, use_container_width=True)
        st.info("If a PO is missing, no PO row is inserted for that invoice.")

    with tab3:
        st.subheader("GRN Data Retrieved From SAP")
        st.dataframe(grn_data, use_container_width=True)
        st.info("If a GRN is missing, no GRN row is inserted for that invoice.")

    with tab4:
        st.subheader("Validation Results")
        st.dataframe(validations, use_container_width=True)

        st.markdown("### Processing Summary")

        for inv in invoices:
            if inv["status"] == "POSTED":
                render_success_box(f"{inv['invoice_number']} posted successfully")

            elif inv["status"] == "EXCEPTION":
                render_exception_box(f"{inv['invoice_number']} moved to exception handling")

            elif inv["status"] == "POSTED_AFTER_RESOLUTION":
                render_success_box(f"{inv['invoice_number']} posted after resolution")

    with tab5:
        st.subheader("Actual Email Logs")
        st.dataframe(emails, use_container_width=True)

        for email in emails:
            with st.expander(f"Email: {email['subject']}"):
                st.write("Invoice Number:", email["invoice_number"])
                st.write("Recipient:", email["recipient"])
                st.write("Sent:", bool(email["sent"]))
                st.markdown(email["body"], unsafe_allow_html=True)

    with tab6:
        st.subheader("Follow-up Tracker")
        st.dataframe(followups, use_container_width=True)

        for f in followups:
            invoice = next(
                (x for x in invoices if x["invoice_number"] == f["invoice_number"]),
                None,
            )

            if not invoice:
                continue

            with st.container(border=True):
                st.markdown(f"### {invoice['invoice_number']}")
                st.write("Vendor:", invoice["vendor_name"])
                st.write("Current Status:", f["current_status"])
                st.write("Follow-up Count:", f["followup_count"])
                st.write("Reply Received:", bool(f["reply_received"]))

                if f["current_status"] in ["WAITING_FOR_REPLY", "FOLLOWUP_SENT"]:
                    render_waiting_box("Waiting for vendor / procurement response")

                if f["current_status"] == "REPLY_RECEIVED":
                    render_success_box("Reply received. Ready for revalidation.")

                if f["current_status"] == "RESOLVED_AND_POSTED":
                    render_success_box("Invoice resolved and posted.")

                c1, c2, c3 = st.columns(3)

                with c1:
                    if st.button(
                        "📧 Send Follow-up",
                        key=f"followup_{invoice['id']}"
                    ):
                        sent, msg = send_followup(invoice["id"])

                        if sent:
                            st.success("Follow-up sent.")
                        else:
                            st.error(msg)

                        st.rerun()

                with c2:
                    if st.button(
                        "📥 Mark Reply Received",
                        key=f"reply_{invoice['id']}"
                    ):
                        mark_reply_received(invoice["id"])
                        st.success("Reply marked as received.")
                        st.rerun()

                with c3:
                    if st.button(
                        "✅ Revalidate & Post",
                        key=f"post_{invoice['id']}"
                    ):
                        revalidate_and_post(invoice["id"])
                        st.success("Invoice revalidated and posted.")
                        st.rerun()


if __name__ == "__main__":
    main()
