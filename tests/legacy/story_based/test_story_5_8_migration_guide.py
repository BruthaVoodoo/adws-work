def test_migration_guide_exists_and_has_sections():
    import os

    p = os.path.join(
        os.path.dirname(__file__), "..", "ai_docs", "specs", "MIGRATION_GUIDE.md"
    )
    p = os.path.normpath(p)
    assert os.path.exists(p), f"Migration guide not found at {p}"
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    assert "OpenCode response structure" in text
    assert "Troubleshooting" in text
    assert "Step-by-step migration" in text
