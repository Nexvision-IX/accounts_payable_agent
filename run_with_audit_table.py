import pandas as pd
import json
from datetime import datetime
from pprint import pprint

from accounts_payable_agent.agents.orchestrator import Orchestrator


def run_agent_with_audit_table():
    """
    Run the Accounts Payable agent and generate an audit table with step-by-step data.
    """
    
    orch = Orchestrator()
    
    sample_invoice = {
        "filename": "INV-1001.pdf",
        "vendor": "Acme Ltd",
        "amount": 250.0,
        "currency": "USD",
        "date": "2026-05-21",
        "po_number": "PO-1234"
    }
    
    print("=" * 80)
    print("RUNNING ACCOUNTS PAYABLE AGENT")
    print("=" * 80)
    print()
    
    try:
        result = orch.run(sample_invoice)
        
        # Extract audit log
        audit_log = result.get("audit_log", [])
        workflow_status = result.get("workflow_status", "UNKNOWN")
        extracted_invoice = result.get("extracted_invoice", {})
        validation_result = result.get("validation_result", {})
        sap_data = result.get("sap_data", {})
        match_result = result.get("match_result", {})
        
        # Create audit table
        audit_table_data = []
        
        for idx, entry in enumerate(audit_log, 1):
            agent_name = entry.get("agent", "Unknown")
            status = entry.get("status", "N/A")
            
            # Build details column
            details = {}
            
            # Extract agent-specific details
            if agent_name == "ExtractionAgent":
                details["Confidence"] = entry.get("confidence", "N/A")
                
            elif agent_name == "SAPDataAgent":
                details["Vendor Code"] = sap_data.get("vendor_code", "N/A")
                details["PO Status"] = sap_data.get("po_status", "N/A")
                details["GRN Number"] = sap_data.get("grn_number", "N/A")
                
            elif agent_name == "ValidationAgent":
                details["Issues Found"] = entry.get("issues_found", 0)
                details["Three-Way Match"] = validation_result.get("validation_status", "N/A")
                details["Clean Invoice"] = validation_result.get("clean_invoice", False)
                
            elif agent_name == "DecisionAgent":
                decision = entry.get("decision", {})
                details["Action"] = decision.get("action", "N/A")
                details["Reason"] = decision.get("reason", "N/A")
            
            audit_table_data.append({
                "Step": idx,
                "Agent": agent_name,
                "Status": status,
                "Details": json.dumps(details, indent=2)
            })
        
        # Create DataFrame
        df = pd.DataFrame(audit_table_data)
        
        # Display audit table
        print("\n" + "=" * 80)
        print("AUDIT LOG TABLE")
        print("=" * 80)
        print()
        print(df.to_string(index=False))
        print()
        
        # Save audit table to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"audit_log_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"✓ Audit table saved to: {csv_filename}")
        
        # Create detailed summary table
        print("\n" + "=" * 80)
        print("DETAILED SUMMARY")
        print("=" * 80)
        print()
        
        summary_data = {
            "Item": [
                "Workflow Status",
                "Total Cycles",
                "Invoice Number",
                "Vendor Name",
                "Invoice Amount",
                "Currency",
                "PO Number",
                "Extraction Confidence",
                "Validation Status",
                "Three-Way Match",
                "Posted to SAP",
                "Extraction Date"
            ],
            "Value": [
                workflow_status,
                result.get("cycle", 0),
                extracted_invoice.get("invoice_number", "N/A"),
                extracted_invoice.get("vendor_name", "N/A"),
                extracted_invoice.get("amount", "N/A"),
                extracted_invoice.get("currency", "N/A"),
                extracted_invoice.get("po_number", "N/A"),
                result.get("extraction_metadata", {}).get("confidence", "N/A"),
                validation_result.get("validation_status", "N/A"),
                validation_result.get("clean_invoice", False),
                result.get("outcome", {}).get("posted", False),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        print(df_summary.to_string(index=False))
        print()
        
        # Save summary table
        summary_filename = f"summary_{timestamp}.csv"
        df_summary.to_csv(summary_filename, index=False)
        print(f"✓ Summary table saved to: {summary_filename}")
        
        # Create detailed validation table
        print("\n" + "=" * 80)
        print("VALIDATION DETAILS")
        print("=" * 80)
        print()
        
        validation_data = {
            "Check": [
                "Invoice-PO Match",
                "Invoice-GRN Match",
                "PO-GRN Match",
                "Vendor Exists",
                "Vendor Blocked",
                "PO Exists",
                "GRN Exists",
                "GRN Posted",
                "Price Match",
                "Quantity Match"
            ],
            "Result": [
                match_result.get("invoice_po_match", "N/A"),
                match_result.get("invoice_grn_match", "N/A"),
                match_result.get("po_grn_match", "N/A"),
                sap_data.get("vendor_exists", "N/A"),
                not sap_data.get("vendor_blocked", False),
                sap_data.get("po_exists", "N/A"),
                sap_data.get("grn_exists", "N/A"),
                sap_data.get("grn_posted", "N/A"),
                sap_data.get("price_match", "N/A"),
                sap_data.get("quantity_match", "N/A")
            ]
        }
        
        df_validation = pd.DataFrame(validation_data)
        print(df_validation.to_string(index=False))
        print()
        
        # Save validation table
        validation_filename = f"validation_{timestamp}.csv"
        df_validation.to_csv(validation_filename, index=False)
        print(f"✓ Validation table saved to: {validation_filename}")
        
        # Print final outcome
        print("\n" + "=" * 80)
        print("FINAL OUTCOME")
        print("=" * 80)
        print(f"Workflow Status: {workflow_status}")
        print(f"Invoice Posted: {result.get('outcome', {}).get('posted', False)}")
        print()
        
    except Exception as e:
        print(f"\n✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_agent_with_audit_table()
