import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/release_manifest_v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_release_manifest_matches_package_files():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["release_stage"] == "v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1"
    listed = {item["path"]: item for item in data["files"]}
    actual = {
        path.relative_to(ROOT).as_posix(): path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path != MANIFEST
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix != ".pyc"
        and path.name != ".coverage"
    }
    assert set(listed) == set(actual)
    assert data["file_count_excluding_manifest"] == len(actual)
    for relative, path in actual.items():
        assert listed[relative]["size_bytes"] == path.stat().st_size
        assert listed[relative]["sha256"] == _sha256(path)
