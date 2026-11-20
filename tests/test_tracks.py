import base64
import json

from src import agent_vault, erc8004, x402
from src.altana import run as run_altana, transfer_calldata
from src.attribution import parse_suffix
from src.config import TOKENS


def test_erc8004_registration_document_and_data_uri():
    doc = erc8004.build_registration(
        name="Test Agent",
        description="does a real job",
        endpoint="https://example.com",
        agent_id=42,
    )
    assert doc["type"].endswith("#registration-v1")
    assert doc["registrations"][0]["agentId"] == 42

    uri = erc8004.to_data_uri(doc)
    assert uri.startswith("data:application/json;base64,")
    payload = uri.split(",", 1)[1]
    assert json.loads(base64.b64decode(payload)) == doc


def test_session_handle_is_parsed_from_text_result():
    assert agent_vault._handle("Opened https://x\n\nsession: s_8f3kABC (pass this)") == "s_8f3kABC"
    assert agent_vault._handle('{"status":"ok","session":"s_abc123"}') == "s_abc123"
    assert agent_vault._handle("no session here") is None


def test_x402_dry_run_needs_no_credentials(capsys):
    assert x402.pay("https://example.com/premium", dry_run=True) is None
    assert "https://example.com/premium" in capsys.readouterr().out


def test_altana_calldata_is_tagged(capsys):
    recipient = "0x1111111111111111111111111111111111111111"
    data = transfer_calldata(TOKENS["USDC"], recipient, 1_000_000)
    result = run_altana(
        to=TOKENS["USDC"],
        calldata=data,
        recipient=recipient,
        amount=1_000_000,
        attribution_code="celo_test1234",
        dry_run=True,
    )
    assert result is None
    out = capsys.readouterr().out
    assert "spend cap" in out and "allowlist" in out
    # calldata asli + tag harus bisa di-parse
    tagged = data[:10] + "00" * 32
    from src.attribution import append_tag

    assert parse_suffix(bytes.fromhex(append_tag(tagged, ["celo_test1234"])[2:])) == {
        "codes": ["celo_test1234"],
        "schema_id": 0,
    }
