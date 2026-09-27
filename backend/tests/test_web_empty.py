from pathlib import Path


def test_frontend_has_no_data_fixture_module():
    src = Path(__file__).resolve().parents[2] / "frontend" / "src"
    if not src.exists():
        return
    for path in src.rglob("*"):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert "from \"./fixtures\"" not in text
        assert "from './fixtures'" not in text
        assert "fixture.json" not in text
