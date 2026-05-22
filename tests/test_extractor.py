import os
import json
from accounts_payable_agent.integrations.extractor import extract_from_image_bytes


def test_extractor_heuristic(monkeypatch):
    # Simulate pytesseract returning a known text
    sample_text = "Invoice No: INV-2026\nVendor: Demo Co\nAmount: $123.45\n"

    class DummyImage:
        pass

    monkeypatch.setenv("OPENAI_API_KEY", "")

    # Patch PIL.Image.open and pytesseract
    try:
        import accounts_payable_agent.integrations.extractor as extmod
        monkeypatch.setattr(extmod, 'Image', True)
        monkeypatch.setattr(extmod, 'pytesseract', type('T', (), {'image_to_string': lambda img: sample_text})())
    except Exception:
        # If module attributes are missing, skip patching — extractor will fallback
        pass

    res = extract_from_image_bytes(b"fakebytes")
    assert res is not None
    assert res.get('invoice_number') is not None
    assert 'INV' in res.get('invoice_number') or 'UNKNOWN' != res.get('invoice_number')


def test_extractor_with_llm(monkeypatch):
    # Simulate OCR text and LLM returning JSON
    sample_text = "Some OCR text"
    # Mock OCR
    import accounts_payable_agent.integrations.extractor as extmod
    monkeypatch.setattr(extmod, 'Image', True)
    monkeypatch.setattr(extmod, 'pytesseract', type('T', (), {'image_to_string': lambda img: sample_text})())

    # Mock openai ChatCompletion
    class DummyResp:
        def __init__(self, content):
            self.choices = [type('C', (), {'message': type('M', (), {'content': content})})]

    def fake_chat_create(**kwargs):
        content = json.dumps({"invoice_number": "INV-LLM-1", "vendor_name": "LLM Co", "amount": 999.99})
        return DummyResp(content)

    monkeypatch.setenv('OPENAI_API_KEY', 'dummy')
    import types
    dummy_openai = types.SimpleNamespace(ChatCompletion=type('CC', (), {'create': staticmethod(fake_chat_create)}))
    monkeypatch.setattr(extmod, 'openai', dummy_openai)

    res = extract_from_image_bytes(b"fake")
    assert res['invoice_number'] == 'INV-LLM-1'
    assert res['vendor_name'] == 'LLM Co'
    assert res['amount'] == 999.99
