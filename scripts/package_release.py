"""Build and verify portable skill and plugin release archives."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile
from build_skill import build, _write

VERSION = "0.2.4"


def package(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    skill = output / "contract-check-2026-development.zip"
    plugin = output / "contract-check-plugin.zip"
    build(skill, 2026)
    with ZipFile(skill) as archive:
        with tempfile.TemporaryDirectory() as temp:
            archive.extractall(temp)
            root = Path(temp) / "contract-check"
            content = (root / "SKILL.md").read_text()
            assert content.startswith("---\nname: contract-check\ndescription: ")
            assert "\n---\n" in content[4:]
            description = content.split("description: ", 1)[1].splitlines()[0]
            assert len(description) <= 200
            manifest = json.loads((root / "edition-manifest.json").read_text())
            for name, expected in manifest["files"].items():
                assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
            for name in ("SKILL.md", "references/runtime.md", "references/enforcement-analysis.md"):
                for link in re.findall(r"`((?:references/|assets/|scripts/)[^`]+)`", (root / name).read_text()):
                    if " " not in link:
                        assert (root / link).exists(), link
            forms = root / "assets/forms"
            assert len(list(forms.iterdir())) == 4
            for form in forms.glob("*.json"):
                json.loads(form.read_text())
            source = root / "sample.txt"
            source.write_text("1. Services\n\nSupplier must deliver a report.\n\n2. Fees\n\nCustomer must pay $900.")
            command = [sys.executable, str(root / "scripts/contract_check_cli.py")]
            for args in [
                ["ingest", str(source), str(root / "project.json")],
                ["preview", str(root / "project.json"), str(root / "preview.md")],
                ["render", str(root / "project.json"), str(root / "clean.txt")],
            ]:
                subprocess.run(command + args, check=True, capture_output=True, text=True, cwd=temp)
            assert "Supplier must deliver" in (root / "clean.txt").read_text()
            assert (root / "scripts/contract_check/enforcement/schema.py").is_file()
            assert (root / "scripts/contract_check/enforcement/prediction/train.py").is_file()
    interface = {
        "displayName": "Contract Check",
        "shortDescription": "Review contracts with choices",
        "longDescription": "Review contract structure and language, trace payment and performance terms, record evidence-linked findings, ask for material decisions, and produce guarded revisions and comparisons.",
        "developerName": "Sage",
        "category": "Productivity",
        "defaultPrompt": "Use Contract Check to review this agreement, show structural choices, and propose evidence-linked revisions.",
    }
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "contract-check", "version": VERSION,
        "description": "Review and revise contracts with evidence-linked findings, explicit choices, guarded edits, and comparisons.",
        "author": {"name": "Sage"},
        "extensions": {"com.openai": {"interface": interface}},
    }
    legacy = {key: manifest[key] for key in ("name", "version", "description", "author")}
    legacy.update(interface=dict(interface, capabilities=[]), keywords=[], skills="./skills")
    with ZipFile(skill) as source, ZipFile(plugin, "w") as target:
        _write(target, "contract-check/plugin.json", (json.dumps(manifest, indent=2) + "\n").encode())
        _write(target, "contract-check/.codex-plugin/plugin.json", (json.dumps(legacy, indent=2) + "\n").encode())
        for name in source.namelist():
            _write(target, name.replace("contract-check/", "contract-check/skills/contract-check/", 1), source.read(name))
    direct = output / "contract-check-direct-upload.zip"
    with ZipFile(skill) as source, ZipFile(direct, "w") as target:
        for name in source.namelist():
            _write(target, name.removeprefix("contract-check/"), source.read(name))
    with ZipFile(direct) as archive:
        assert "SKILL.md" in archive.namelist()
        assert "references/transaction-review.md" in archive.namelist()
        assert len([name for name in archive.namelist() if name.startswith("assets/forms/")]) == 4
    claude = output / "contract-check-claude-skill.zip"
    shutil.copyfile(skill, claude)
    with ZipFile(claude) as archive:
        assert "contract-check/SKILL.md" in archive.namelist()
        assert "contract-check/references/enforcement-analysis.md" in archive.namelist()
        assert "contract-check/scripts/contract_check/enforcement/analysis.py" in archive.namelist()
        assert all(name.startswith("contract-check/") for name in archive.namelist())
    checksums = []
    for artifact in (skill, plugin, direct, claude):
        checksums.append(hashlib.sha256(artifact.read_bytes()).hexdigest() + "  " + artifact.name)
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n")
    print("Verified ChatGPT, Claude, and plugin archives, all four forms, references, hashes, and extracted runtime.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    package(parser.parse_args().output)
