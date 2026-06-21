from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_ERROR_LOG = Path.cwd() / "errors.txt"


@dataclass
class LicenseInfo:
    url: str
    key: str | None = None
    iv: str | None = None

    @property
    def is_aaxc(self) -> bool:
        return bool(self.key and self.iv)


def _decrypt_voucher(auth: "audible.Authenticator", asin: str, voucher_b64: str) -> tuple[str, str]:
    device_info = auth.device_info or {}
    customer_info = auth.customer_info or {}
    buf = (
        device_info.get("device_type", "")
        + device_info.get("device_serial_number", "")
        + customer_info.get("user_id", "")
        + asin
    ).encode("ascii")
    digest = hashlib.sha256(buf).digest()
    key, iv = digest[:16], digest[16:]

    pad = len(voucher_b64) % 4
    ciphertext = base64.b64decode(voucher_b64 + "=" * (4 - pad) if pad else voucher_b64)

    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        plaintext = dec.update(ciphertext) + dec.finalize()
    except ImportError:
        try:
            from Crypto.Cipher import AES as _AES
            plaintext = _AES.new(key, _AES.MODE_CBC, iv).decrypt(ciphertext)
        except ImportError:
            import pyaes
            aes = pyaes.AESModeOfOperationCBC(key, iv=iv)
            plaintext = b"".join(
                aes.decrypt(ciphertext[i:i + 16]) for i in range(0, len(ciphertext), 16)
            )

    data = json.loads(plaintext.rstrip(b"\x00").decode("utf-8"))
    return data["key"], data["iv"]


def fetch_license(asin: str) -> LicenseInfo:
    import audible
    from .auth import load_auth

    auth = load_auth()
    with audible.Client(auth=auth) as client:
        resp = client.post(
            f"content/{asin}/licenserequest",
            body={
                "drm_type": "Adrm",
                "consumption_type": "Download",
                "quality": "High",
            },
        )

    try:
        cl = resp["content_license"]
        url = cl["content_metadata"]["content_url"]["offline_url"]
    except KeyError:
        raise RuntimeError(f"Could not get download URL for {asin}. Response: {resp}")

    key = iv = None
    raw = cl.get("license_response")
    if raw:
        lr = raw if isinstance(raw, dict) else None
        if lr is None:
            try:
                lr = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                pass
        if isinstance(lr, dict):
            key, iv = lr.get("key"), lr.get("iv")

        if not (key and iv):
            key, iv = _decrypt_voucher(auth, asin, raw)

    return LicenseInfo(url=url, key=key, iv=iv)


def download_aaxc(url: str, dest: Path) -> None:
    import httpx
    from .auth import load_auth

    auth = load_auth()
    cookies = auth.website_cookies or {}
    headers = {"User-Agent": "Audible Download Manager"}

    with httpx.stream("GET", url, headers=headers, cookies=cookies,
                      follow_redirects=True, timeout=None) as r:
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


def _run_ffmpeg(args: list[str]) -> None:
    _ERROR_LOG.write_text("")
    with _ERROR_LOG.open("w") as err_f:
        result = subprocess.run(["ffmpeg"] + args, stdout=err_f, stderr=err_f)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, ["ffmpeg"] + args)


def decrypt_file(src: Path, output_path: Path, license: LicenseInfo,
                 activation_bytes: str, bitrate: str = "64k") -> None:
    if license.is_aaxc:
        _run_ffmpeg([
            "-y",
            "-audible_key", license.key,
            "-audible_iv", license.iv,
            "-i", str(src),
            "-vn", "-c:a", "copy",
            str(output_path),
        ])
    else:
        _run_ffmpeg([
            "-y",
            "-activation_bytes", activation_bytes,
            "-i", str(src),
            "-vn", "-c:a", "aac", "-b:a", bitrate,
            str(output_path),
        ])


def download_book(asin: str, output_dir: Path, title: str = "") -> Path:
    from .auth import get_activation_bytes

    ab = get_activation_bytes()
    if not ab:
        raise RuntimeError("No activation bytes. Run 'hearworm auth login' first.")

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title or asin).strip()
    output_path = output_dir / f"{safe_title}.m4b"

    print(f"Fetching license for {asin}...")
    license = fetch_license(asin)

    ext = ".aaxc" if license.is_aaxc else ".aax"
    raw_path = output_dir / f"{safe_title}{ext}"

    if raw_path.exists():
        print(f"Using cached {raw_path.name}")
    else:
        fmt = "AAXC" if license.is_aaxc else "AAX"
        print(f"Downloading {safe_title} ({fmt})...")
        download_aaxc(license.url, raw_path)

    print("Decrypting...")
    try:
        decrypt_file(raw_path, output_path, license, ab)
    except subprocess.CalledProcessError:
        print(f"Decryption failed — ffmpeg log: {_ERROR_LOG}")
        print(f"Raw file kept at: {raw_path}")
        raise

    raw_path.unlink(missing_ok=True)
    print(f"Saved: {output_path}")
    return output_path
