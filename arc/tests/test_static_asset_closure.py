from pathlib import Path
from tempfile import TemporaryDirectory

from static_asset_closure import check_static_closure


def test_static_closure_detects_root_script_mismatch():
    with TemporaryDirectory() as root:
        project = Path(root)
        dist = project / "frontend" / "dist"
        (dist / "scripts").mkdir(parents=True)
        (dist / "index.html").write_text('<script src="/app.js"></script><link rel="stylesheet" href="/styles.css">')
        (dist / "scripts" / "app.js").write_text("ok")
        result = check_static_closure(project)
        assert result["status"] == "failed"
        assert "/app.js" in result["missing_assets"]
        assert "/styles.css" in result["missing_assets"]


def test_static_closure_accepts_matching_assets():
    with TemporaryDirectory() as root:
        project = Path(root)
        dist = project / "frontend" / "dist"
        (dist / "scripts").mkdir(parents=True)
        (dist / "index.html").write_text('<script src="/scripts/app.js"></script>')
        (dist / "scripts" / "app.js").write_text("ok")
        result = check_static_closure(project)
        assert result["status"] == "passed"
        assert result["local_references"] == ["/scripts/app.js"]
\n