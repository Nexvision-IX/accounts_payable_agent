from accounts_payable_agent.agents.orchestrator import Orchestrator


def test_orchestrator_posts_when_valid(monkeypatch):
    orch = Orchestrator()

    # Patch extraction to return known invoice
    monkeypatch.setattr(orch.extraction, 'run', lambda b: {"status": "ok", "data": {"invoice_number": "INV-1", "vendor_name": "Test", "amount": 10.0}})
    # Patch sap to indicate price match
    monkeypatch.setattr(orch.sap, 'run', lambda d: {"status": "ok", "sap": {"po_exists": True, "price_match": True}})

    result = orch.run({})
    assert result.get('outcome') and result['outcome'].get('status') == 'posted'
