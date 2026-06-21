from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path


def fetch_download_url(asin: str) -> str:
    import audible
    from .auth import load_auth

    auth = load_auth()
    with audible.Client(auth=auth) as client:
        resp = client.post(
            f"content/{asin}/licenserequest",
            body={
                "drm_type": "Adrm",
                "consumption_type": "Download",
                "quality": "Extreme",
            },
        )

    try:
        return resp["content_license"]["content_metadata"]["content_url"]["offline_url"]
    except KeyError:
        raise RuntimeError(f"Could not get download URL for {asin}. Response: {resp}")


def download_aax(url: str, dest: Path) -> None:
    import httpx

    with httpx.stream("GET", url, follow_redirects=True, timeout=None) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with dest.open("wb") as f:
            for chunk in r.iter_bytes(chunk_size=1024 * 64):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  downloading... {pct}%", end="", flush=True)
        print()


def decrypt_aax(aax_path: Path, output_path: Path, activation_bytes: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-activation_bytes", activation_bytes,
            "-i", str(aax_path),
            "-vn", "-c:a", "copy",
            str(output_path),
        ],
        check=True,
    )


def download_book(asin: str, output_dir: Path, title: str = "") -> Path:
    from .auth import get_activation_bytes

    ab = get_activation_bytes()
    if not ab:
        raise RuntimeError("No activation bytes. Run 'hearworm auth login' first.")

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title or asin).strip()
    output_path = output_dir / f"{safe_title}.m4b"

    print(f"Fetching download URL for {asin}...")
    url = fetch_download_url(asin)

    with tempfile.TemporaryDirectory() as tmp:
        aax_path = Path(tmp) / f"{asin}.aax"
        print(f"Downloading {safe_title}...")
        download_aax(url, aax_path)

        print("Decrypting...")
        decrypt_aax(aax_path, output_path, ab)

    print(f"Saved: {output_path}")
    return output_path
