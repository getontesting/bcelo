import pytest

from src.attribution import (
    MARKER_HEX,
    append_tag,
    build_data_suffix,
    code_from_hostname,
    code_from_repo,
    parse_suffix,
)


def test_hostname_vectors_from_docs():
    assert code_from_hostname("mondeto.app") == "celo_b057492a5aa5"
    assert code_from_hostname("celo.org") == "celo_8549372f8229"
    assert code_from_hostname("app.mondeto.app") == "celo_1a8ba29dac7a"


def test_code_from_repo_vector_from_docs():
    assert code_from_repo("gigahierz/trading-bot-updown") == "celo_7b3c251337be"


def test_build_suffix_layout():
    suffix = build_data_suffix(["celo_test1234"])
    code = b"celo_test1234"
    assert suffix[: len(code)] == code
    assert suffix[len(code)] == len(code)
    assert suffix[len(code) + 1] == 0x00
    assert suffix[-16:].hex() == MARKER_HEX


def test_append_and_parse_roundtrip():
    calldata = "0xa9059cbb" + "00" * 64
    tagged = append_tag(calldata, ["celo_test1234"])
    parsed = parse_suffix(bytes.fromhex(tagged[2:]))
    assert parsed == {"codes": ["celo_test1234"], "schema_id": 0}


def test_append_merges_existing_tag_instead_of_stacking():
    calldata = "0xa9059cbb" + "00" * 64
    first = append_tag(calldata, ["textile_api"])
    second = append_tag(first, ["celo_assigned1234"])
    parsed = parse_suffix(bytes.fromhex(second[2:]))
    assert parsed["codes"] == ["textile_api", "celo_assigned1234"]
    # marker harus tetap tepat satu di akhir
    assert bytes.fromhex(second[2:]).count(bytes.fromhex(MARKER_HEX)) == 1


def test_untagged_calldata_returns_none():
    assert parse_suffix(bytes.fromhex("a9059cbb" + "00" * 64)) is None


@pytest.mark.parametrize("bad", ["CELO_X", "has space", "a,b", "", "x" * 33])
def test_invalid_codes_rejected(bad):
    with pytest.raises(ValueError):
        build_data_suffix([bad])
