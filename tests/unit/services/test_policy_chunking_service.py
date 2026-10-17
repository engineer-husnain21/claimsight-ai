from app.services.policy_chunking_service import PolicyChunkingService

SAMPLE_POLICY = """# Coverage Policy

## COV-01 Annual Limit
Each member has a limit of PKR 1,000,000.

## COV-02 Inpatient Treatment
Admissions of at least 24 hours are covered.
Room rent is covered up to PKR 15,000 per day.
"""


def test_split_document_when_rules_present_returns_one_chunk_per_rule() -> None:
    chunks = PolicyChunkingService().split_document("coverage_policy", SAMPLE_POLICY)

    assert [chunk.rule_code for chunk in chunks] == ["COV-01", "COV-02"]
    assert chunks[0].id == "coverage_policy:COV-01"
    assert chunks[0].title == "Annual Limit"
    assert chunks[0].text.startswith("Coverage Policy - COV-01 Annual Limit")
    assert "PKR 15,000 per day" in chunks[1].text


def test_split_document_when_section_body_empty_skips_section() -> None:
    text = "# Policy\n\n## COV-01 Empty\n\n## COV-02 Filled\nSome rule text.\n"

    chunks = PolicyChunkingService().split_document("policy", text)

    assert [chunk.rule_code for chunk in chunks] == ["COV-02"]


def test_split_document_when_no_rule_headings_returns_empty_list() -> None:
    chunks = PolicyChunkingService().split_document("notes", "# Notes\nJust text.\n")

    assert chunks == []
