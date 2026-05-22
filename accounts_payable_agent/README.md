# Accounts Payable Agent (Multi-Agent AI Workflow)

An AI-powered Accounts Payable (AP) automation platform designed to automate invoice intake, validation, exception handling, communication, and SAP posting.

This project replaces traditional OCR + manual validation workflows with a custom multi-agent architecture.

The workflow remains active until the invoice is successfully posted into SAP.

---

# Objective

Automate the end-to-end Accounts Payable process by:

- Extracting invoice data automatically
- Validating invoice details against SAP
- Performing PO / GRN verification
- Detecting exceptions
- Auto-resolving recoverable issues
- Sending notifications and follow-ups
- Monitoring responses
- Revalidating automatically
- Posting invoices to SAP

---

# Architecture

```text
Invoice
   ↓
Extraction Agent
   ↓
Database Storage
   ↓
SAP Data Agent
   ↓
Validation Agent
   ↓
Decision Agent

Clean?
├── YES
│      ↓
│   Post to SAP
│      ↓
│   CLOSE
│
└── NO
       ↓
Exception Classifier
       ↓
Resolution Agent
       ↓
Communication Agent
       ↓
Send Email
       ↓
Inbox Monitoring
       ↓
Follow-Up Engine
       ↓
Revalidation
       ↓
Post to SAP
       ↓
CLOSE
```

---

# Agent Overview

## 1. ExtractionAgent

Purpose:
Extract invoice data from PDF/image documents.

Capabilities:
- OCR extraction
- LLM-assisted extraction
- Invoice parsing
- Confidence scoring
- Document hashing
- Structured JSON output

Input:

```json
{
  "filename": "INV1001.pdf"
}
```

Output:

```json
{
  "invoice_number": "INV1001",
  "vendor_name": "ACME",
  "amount": 250.0
}
```

---

## 2. SAPDataAgent

Purpose:
Retrieve invoice-related information from SAP.

Capabilities:
- PO validation
- GRN validation
- Vendor validation
- Currency matching
- Duplicate detection
- 3-way matching

Output:

```json
{
  "po_exists": true,
  "grn_posted": true
}
```

---

## 3. ValidationAgent

Purpose:
Determine invoice readiness.

Checks:
- Mandatory fields
- PO existence
- GRN posted
- Duplicate invoice
- Currency match
- Price match
- Quantity match

Output:

```json
{
  "clean_invoice": false,
  "issues": [
      "GRN_NOT_POSTED"
  ]
}
```

---

## 4. DecisionAgent

Purpose:
Determine next workflow action.

Actions:
- POST_TO_SAP
- REVALIDATE
- CLASSIFY_EXCEPTION
- MANUAL_REVIEW

---

## 5. ClassifierAgent

Purpose:
Classify invoice exceptions.

Examples:

| Issue | Owner |
|-------|-------|
| PO_MISSING | Supplier |
| GRN_NOT_POSTED | Procurement |
| PRICE_MISMATCH | AP Team |

---

## 6. ResolutionAgent

Purpose:
Attempt automatic remediation.

Examples:
- Populate PO automatically
- Retry validation
- Trigger communication

---

## 7. CommunicationAgent

Purpose:
Manage communication lifecycle.

Capabilities:
- Send emails
- Inbox monitoring
- Response tracking
- Daily follow-up
- Escalation

---

## 8. Orchestrator

Purpose:
Coordinate entire workflow.

Responsibilities:
- Execute agents
- Maintain state
- Retry processing
- Trigger revalidation
- Close workflow

---

# Database

Tables:

```text
invoices
sap_data
exceptions
notifications
audit_log
```

Features:
- Invoice tracking
- SAP enrichment
- Follow-up management
- Audit logging
- Retry support

---

# Project Structure

```text
accounts_payable_agent/

├── agents/
│   ├── base.py
│   ├── extraction_agent.py
│   ├── sap_data_agent.py
│   ├── validation_agent.py
│   ├── decision_agent.py
│   ├── classifier_agent.py
│   ├── resolution_agent.py
│   ├── communication_agent.py
│   └── orchestrator.py
│
├── services/
│   ├── sap_client.py
│   ├── extraction_service.py
│
├── storage/
│   └── database.py
│
├── streamlit_app.py
├── main.py
└── README.md
```

---

# Installation

Clone:

```bash
git clone <repository_url>
cd accounts-payable-agent
```

Install:

```bash
pip install -r requirements.txt
```

Optional OCR:

```bash
pip install pytesseract pillow
```

Optional LLM:

```bash
pip install openai
```

---

# Environment Variables

Create `.env`

```env
OPENAI_API_KEY=your_key

SAP_HOST=localhost
SAP_USER=user
SAP_PASSWORD=password
```

---

# Run Demo

```bash
python main.py
```

Example:

```text
FINAL RESULT

workflow_status = POSTED
```

---

# Run Streamlit UI

```bash
streamlit run accounts_payable_agent/streamlit_app.py
```

Features:
- Upload invoices
- Track status
- View validation
- View audit logs

---

# Success Criteria

Invoice lifecycle completes only when:

```text
Invoice → Validation → Resolution → SAP Posting → Closed
```

Email notifications alone do not complete the workflow.

---

# License

Internal / Proof of Concept