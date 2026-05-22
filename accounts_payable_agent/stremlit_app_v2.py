import os
import re
import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st

from accounts_payable_agent.demo_workflow_runner import DemoWorkflowRunner


st.set_page_config(
    page_title="AP Agent Workflow Demo",
    layout="wide"
)

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = DATA_DIR / "agent_demo_uploads"
DB_PATH = DATA_DIR / "agent_demo.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS workflow_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        invoice_number TEXT,
        vendor_name TEXT,
        amount REAL,
        scenario TEXT,
        workflow_status TEXT,
        agent_result TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def reset_db():
    conn = get_conn()
    conn.execute("DELETE FROM workflow_runs")
    conn.commit()
    conn.close()


def fetch_runs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM workflow_runs").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def extract_basic_invoice(uploaded_file, index):
    file_name = uploaded_file.name

    match = re.search(
        r"INV[-_]?\d{4}[-_]?\d+",
        file_name.upper()
    )

    invoice_number = (
        match.group(0).replace("_", "-")
        if match
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
        "filename": file_name,
        "invoice_number": invoice_number,
        "vendor_name": vendors[index],
        "vendor": vendors[index],
        "amount": amounts[index],
        "currency": "USD",
        "date": "2026-05-21",
        "invoice_date": "2026-05-21",
        "po_number": po_numbers[index],
    }


def assign_scenario(index):
    if index in [0, 1, 2]:
        return "clean"
    if index == 3:
        return "po_issue"
    return "grn_issue"


def save_run(file_name, invoice, scenario, result):
    conn = get_conn()

    conn.execute("""
    INSERT INTO workflow_runs (
        file_name,
        invoice_number,
        vendor_name,
        amount,
        scenario,
        workflow_status,
        agent_result,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        file_name,
        invoice["invoice_number"],
        invoice["vendor_name"],
        invoice["amount"],
        scenario,
        result.get("workflow_status"),
        json.dumps(result, default=str),
        datetime.now().isoformat(),
    ))

    conn.commit()
    conn.close()


def render_status_card(title, value, color):
    st.markdown(f"""
    <div style="
        background:{color};
        padding:18px;
        border-radius:12px;
        text-align:center;
        border:1px solid #ddd;
    ">
        <h2>{value}</h2>
        <p style="font-weight:600;">{title}</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    init_db()

    st.markdown("""
    <div style="
        background:linear-gradient(to right,#1f4e79,#4f81bd);
        padding:24px;
        border-radius:14px;
        margin-bottom:20px;
    ">
        <h1 style="color:white;">Accounts Payable Agent Workflow Demo</h1>
        <p style="color:white;font-size:18px;">
            Upload 5 invoice PDFs and run the complete multi-agent AP workflow.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "Demo rule: first 3 invoices are clean, 4th invoice has PO issue, 5th invoice has GRN issue."
    )

    with st.sidebar:
        st.header("Demo Controls")

        if st.button("Reset Demo"):
            reset_db()
            st.success("Demo data cleared.")
            st.rerun()

    uploaded_files = st.file_uploader(
        "Upload exactly 5 invoice PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"Uploaded files: {len(uploaded_files)}")

    if st.button("Run Multi-Agent Workflow"):
        if not uploaded_files or len(uploaded_files) != 5:
            st.error("Please upload exactly 5 invoice PDFs.")
        else:
            reset_db()
            runner = DemoWorkflowRunner()

            progress = st.progress(0)
            status = st.empty()

            for idx, file in enumerate(uploaded_files):
                file_path = UPLOAD_DIR / file.name

                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                scenario = assign_scenario(idx)
                invoice_blob = extract_basic_invoice(file, idx)

                status.info(
                    f"Running agents for {invoice_blob['invoice_number']}..."
                )

                result = runner.run_invoice(
                    invoice_blob=invoice_blob,
                    scenario=scenario
                )

                save_run(
                    file.name,
                    invoice_blob,
                    scenario,
                    result
                )

                progress.progress((idx + 1) / len(uploaded_files))

            status.success("All invoices processed through agents.")
            st.balloons()
            st.rerun()

    st.divider()

    runs = fetch_runs()

    posted = len([
        r for r in runs
        if r["workflow_status"] == "POSTED"
    ])

    exceptions = len([
        r for r in runs
        if r["workflow_status"] != "POSTED"
    ])

    c1, c2, c3 = st.columns(3)

    with c1:
        render_status_card("Invoices Processed", len(runs), "#f5f7ff")

    with c2:
        render_status_card("Posted", posted, "#e8fff0")

    with c3:
        render_status_card("Exceptions", exceptions, "#ffe5e5")

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "Workflow Results",
        "Agent Details",
        "Exception View"
    ])

    with tab1:
        st.subheader("Processed Invoices")
        st.dataframe(runs, use_container_width=True)

    with tab2:
        st.subheader("Agent Execution Details")

        for run in runs:
            result = json.loads(run["agent_result"])

            with st.expander(
                f"{run['invoice_number']} - {run['workflow_status']}"
            ):
                st.json(result)

    with tab3:
        st.subheader("Exceptions")

        for run in runs:
            if run["workflow_status"] != "POSTED":
                result = json.loads(run["agent_result"])

                st.markdown(f"""
                <div style="
                    background:#ffe5e5;
                    padding:15px;
                    border-radius:10px;
                    border-left:6px solid #ff4b4b;
                    margin-bottom:12px;
                ">
                    <h4 style="color:#b30000;">
                        ⚠️ {run['invoice_number']} requires action
                    </h4>
                    <p><b>Vendor:</b> {run['vendor_name']}</p>
                    <p><b>Scenario:</b> {run['scenario']}</p>
                    <p><b>Status:</b> {run['workflow_status']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.json(result.get("exception_result", {}))


if __name__ == "__main__":
    main()