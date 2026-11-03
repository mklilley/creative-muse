#!/usr/bin/env python3
"""Build and inspect a draft upload ZIP from an explicit, audited file list."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
from urllib.parse import urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "LICENSE",
    "assets/gpt-icon.png",
    "plugin.json",
    "skills/instructions/SKILL.md",
    "skills/instructions/agents/openai.yaml",
    "skills/instructions/lookup/knowledge-index.json",
)
IDENTITY = "gpt-1f5d658a3af702b7ac5c5b28f7b1c14e"
PROMPTS = [
    "I need a journalling prompt for my morning pages today",
    "I need an artist's date idea for the weekend",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def collect_and_validate():
    payload = {}
    for name in FILES:
        path = ROOT / name
        require(path.is_file(), f"Missing package file: {name}")
        require(not path.is_symlink() and not any(
            (ROOT / parent).is_symlink() for parent in path.relative_to(ROOT).parents
        ), f"Symlink in package path: {name}")
        payload[name] = path.read_bytes()

    manifest = json.loads(payload["plugin.json"])
    require(manifest.get("$schema") ==
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "Keep the portable Agent Plugins schema.")
    require(manifest.get("name") == IDENTITY, "Imported package identity changed.")
    version = manifest.get("version", "")
    require(re.fullmatch(r"\d+\.\d+\.\d+", version), "Use a numeric package version.")
    extension = manifest["extensions"]["com.openai"]
    listing = extension["interface"]
    for key, limit in {"displayName": 30, "shortDescription": 30,
                       "longDescription": 4000, "developerName": 80}.items():
        value = listing.get(key)
        require(isinstance(value, str) and 0 < len(value) <= limit,
                f"Invalid {key}: must contain 1–{limit} characters.")
    require(listing["displayName"] == "Creative Muse", "Display name changed.")
    require(listing.get("category") == "Creativity", "Check the intended category.")
    require(listing.get("defaultPrompt") == PROMPTS, "Original starter prompts changed.")
    require(all(len(prompt) <= 128 for prompt in PROMPTS), "Starter prompt exceeds limit.")
    require(extension.get("publication", {}).get("countries") == [],
            "Worldwide availability should use an empty country restriction list.")
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        value = listing.get(key, "")
        parsed = urlsplit(value)
        require(len(value) <= 1024 and parsed.scheme == "https" and parsed.hostname
                and parsed.username is None and parsed.password is None,
                f"Invalid HTTPS listing URL: {key}")
    for key in ("logo", "composerIcon"):
        value = listing.get(key, "")
        require(value.startswith("./") and value[2:] in payload,
                f"Icon must reference an included file: {key}")

    png = payload["assets/gpt-icon.png"]
    require(len(png) >= 33 and png[:8] == b"\x89PNG\r\n\x1a\n"
            and png[12:16] == b"IHDR", "Invalid PNG header.")
    width, height = struct.unpack(">II", png[16:24])
    require(48 <= width == height <= 4096, "Icon dimensions outside submission limits.")
    require(len(png) <= 5 * 1024 * 1024, "Icon exceeds 5 MiB.")
    require(payload["skills/instructions/SKILL.md"].startswith(b"---\n"),
            "Skill front matter missing.")
    json.loads(payload["skills/instructions/lookup/knowledge-index.json"])
    return payload, version, width, height


def build():
    payload, version, width, height = collect_and_validate()
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    archive_path = destination / f"creative-muse-{version}-draft.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)

    # Inspect the actual completed archive, including every hidden-path component.
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.namelist() == list(FILES), "Unexpected or duplicate ZIP entries.")
        require(archive.testzip() is None, "ZIP integrity check failed.")
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            require(not path.is_absolute() and not any(
                part.startswith(".") or part == "__MACOSX" for part in path.parts
            ), f"Hidden or unsafe ZIP path: {item.filename}")
            require(archive.read(item) == payload[item.filename],
                    f"Archived bytes differ from source: {item.filename}")

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    report = [
        f"Archive: {archive_path.name}",
        f"SHA-256: {digest}",
        "Local checks passed. This is a draft package, not an OpenAI approval.",
        "Listing URLs are configured; live availability is not checked by this script.",
        f"PNG icon: {width} x {height}, {len(payload['assets/gpt-icon.png'])} bytes",
        "", "Actual archive contents (size, SHA-256, path):",
    ]
    for name, data in payload.items():
        report.append(f"{len(data):7d}  {hashlib.sha256(data).hexdigest()}  {name}")
    report_path = archive_path.with_suffix(".contents.txt")
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    try:
        build()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Package check failed: {error}") from error
