import pandas as pd
import json
from datetime import datetime
from accounts_payable_agent.agents.orchestrator import Orchestrator


def run_agent_with_html_report():
    """
    Run the Accounts Payable agent and generate an HTML report with step-by-step data.
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
    
    print("🔄 Running Accounts Payable Agent...")
    
    try:
        result = orch.run(sample_invoice)
        
        # Extract all relevant data
        audit_log = result.get("audit_log", [])
        workflow_status = result.get("workflow_status", "UNKNOWN")
        extracted_invoice = result.get("extracted_invoice", {})
        validation_result = result.get("validation_result", {})
        sap_data = result.get("sap_data", {})
        match_result = result.get("match_result", {})
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accounts Payable Agent - Audit Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9ff;
        }}
        .status-success {{
            color: #10b981;
            font-weight: 600;
        }}
        .status-failed {{
            color: #ef4444;
            font-weight: 600;
        }}
        .status-pending {{
            color: #f59e0b;
            font-weight: 600;
        }}
        .check-pass {{
            color: #10b981;
        }}
        .check-fail {{
            color: #ef4444;
        }}
        .summary-box {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .info-box-label {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        .info-box-value {{
            font-size: 1.5em;
            font-weight: 600;
        }}
        .step {{
            display: flex;
            margin-bottom: 20px;
            align-items: flex-start;
        }}
        .step-number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-right: 20px;
            flex-shrink: 0;
        }}
        .step-content {{
            flex: 1;
        }}
        .step-title {{
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }}
        .step-description {{
            color: #666;
            font-size: 0.95em;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
        .passed {{
            background: #ecfdf5;
            border-left: 4px solid #10b981;
        }}
        .failed {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Accounts Payable Agent</h1>
            <p>Automated Invoice Processing Audit Report</p>
        </div>
        
        <div class="content">
            <!-- Summary Section -->
            <div class="section">
                <h2 class="section-title">📋 Executive Summary</h2>
                <div class="summary-box">
                    <div class="info-box">
                        <div class="info-box-label">Workflow Status</div>
                        <div class="info-box-value">{workflow_status}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-box-label">Posted to SAP</div>
                        <div class="info-box-value">{'✓ Yes' if result.get('outcome', {}).get('posted') else '✗ No'}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-box-label">Processing Cycles</div>
                        <div class="info-box-value">{result.get('cycle', 0)}</div>
                    </div>
                </div>
            </div>
            
            <!-- Audit Log Section -->
            <div class="section">
                <h2 class="section-title">🔍 Audit Log - Step by Step</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>Agent</th>
                            <th>Status</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for idx, entry in enumerate(audit_log, 1):
            agent_name = entry.get("agent", "Unknown")
            status = entry.get("status", "N/A")
            status_class = "status-success" if status == "SUCCESS" else "status-failed" if status == "FAILED" else "status-pending"
            
            # Build details
            details = []
            if agent_name == "ExtractionAgent":
                confidence = entry.get("confidence", "N/A")
                details.append(f"Confidence: {confidence * 100:.1f}%")
            elif agent_name == "SAPDataAgent":
                details.append(f"Vendor Code: {sap_data.get('vendor_code', 'N/A')}")
                details.append(f"PO Status: {sap_data.get('po_status', 'N/A')}")
                details.append(f"GRN: {sap_data.get('grn_number', 'N/A')}")
            elif agent_name == "ValidationAgent":
                details.append(f"Issues Found: {entry.get('issues_found', 0)}")
                details.append(f"Three-Way Match: {'✓ Pass' if validation_result.get('clean_invoice') else '✗ Fail'}")
            elif agent_name == "DecisionAgent":
                decision = entry.get("decision", {})
                details.append(f"Action: {decision.get('action', 'N/A')}")
                details.append(f"Reason: {decision.get('reason', 'N/A')}")
            
            html_content += f"""
                        <tr class="{'passed' if status == 'SUCCESS' else 'failed'}">
                            <td>{idx}</td>
                            <td><strong>{agent_name}</strong></td>
                            <td class="{status_class}">{status}</td>
                            <td>{'<br>'.join(details) if details else 'N/A'}</td>
                        </tr>
"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <!-- Invoice Details Section -->
            <div class="section">
                <h2 class="section-title">📄 Invoice Details</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        invoice_details = [
            ("Invoice Number", extracted_invoice.get("invoice_number", "N/A")),
            ("Vendor Name", extracted_invoice.get("vendor_name", "N/A")),
            ("Amount", f"{extracted_invoice.get('amount', 'N/A')} {extracted_invoice.get('currency', 'USD')}"),
            ("Invoice Date", extracted_invoice.get("invoice_date", "N/A")),
            ("PO Number", extracted_invoice.get("po_number", "N/A")),
            ("Extraction Confidence", f"{result.get('extraction_metadata', {}).get('confidence', 0) * 100:.1f}%"),
        ]
        
        for field, value in invoice_details:
            html_content += f"""
                        <tr>
                            <td><strong>{field}</strong></td>
                            <td>{value}</td>
                        </tr>
"""
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <!-- Validation Checks Section -->
            <div class="section">
                <h2 class="section-title">✓ Validation Checks</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Check</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        validation_checks = [
            ("Invoice-PO Match", match_result.get("invoice_po_match", False)),
            ("Invoice-GRN Match", match_result.get("invoice_grn_match", False)),
            ("PO-GRN Match", match_result.get("po_grn_match", False)),
            ("Vendor Exists", sap_data.get("vendor_exists", False)),
            ("Vendor Not Blocked", not sap_data.get("vendor_blocked", False)),
            ("PO Exists", sap_data.get("po_exists", False)),
            ("GRN Exists", sap_data.get("grn_exists", False)),
            ("GRN Posted", sap_data.get("grn_posted", False)),
            ("Price Match", sap_data.get("price_match", False)),
            ("Quantity Match", sap_data.get("quantity_match", False)),
        ]
        
        for check, result_val in validation_checks:
            status_class = "check-pass" if result_val else "check-fail"
            status_text = "✓ PASS" if result_val else "✗ FAIL"
            html_content += f"""
                        <tr>
                            <td><strong>{check}</strong></td>
                            <td class="{status_class}"><strong>{status_text}</strong></td>
                        </tr>
"""
        
        html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Accounts Payable Agent - Automated Processing System</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Save HTML report
        html_filename = f"ap_agent_report_{timestamp}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML report generated: {html_filename}")
        print(f"✓ Open the HTML file in your browser to view the formatted report")
        
    except Exception as e:
        print(f"✗ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_agent_with_html_report()
