import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(__file__).resolve().with_name("model_manifest.json")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_url(entry: dict) -> str | None:
    direct = entry.get("url")
    if direct:
        return str(direct)
    env_name = entry.get("url_env")
    if env_name:
        value = os.getenv(env_name)
        if value:
            return value
    return None


def download(url: str, destination: Path) -> None:
    ensure_parent(destination)
    urllib.request.urlretrieve(url, destination)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download model weights listed in "
            "scripts/model_manifest.json"
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if destination file already exists",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"Manifest not found: {MANIFEST_PATH}")
        return 1

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    missing_required = []

    for entry in manifest:
        rel_path = entry["path"]
        required = bool(entry.get("required", False))
        description = entry.get("description", "")
        dest = ROOT_DIR / rel_path

        if dest.exists() and not args.force:
            print(f"Skip (exists): {rel_path}")
            continue

        url = resolve_url(entry)
        if not url:
            msg = f"No URL configured for {rel_path}"
            if description:
                msg += f" ({description})"
            print(f"WARN: {msg}")
            if required:
                missing_required.append(rel_path)
            continue

        print(f"Downloading {url} -> {rel_path}")
        try:
            download(url, dest)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: failed to download {rel_path}: {exc}")
            if required:
                missing_required.append(rel_path)
            continue

        print(f"Saved: {rel_path}")

    if missing_required:
        print("\nMissing required models:")
        for item in missing_required:
            print(f"- {item}")
        print(
            "\nSet the required *_MODEL_URL environment variables "
            "and rerun."
        )
        return 1

    print("\nModel fetch complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
