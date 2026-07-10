"""Platform-aware SSL environment for HTTP clients (aiohttp, httpx, urllib)."""

from __future__ import annotations

import base64
import os
import ssl
import sys
from pathlib import Path

_MERGED_BUNDLE_NAME = "merged_cacert.pem"


def _merged_bundle_path() -> Path:
    return Path(sys.prefix) / "Library" / "ssl" / _MERGED_BUNDLE_NAME


def build_merged_ca_bundle() -> str:
    """Mozilla CA bundle plus Windows ROOT store (for corporate proxy roots)."""
    import certifi

    parts: list[bytes] = [Path(certifi.where()).read_bytes()]
    if sys.platform == "win32":
        for cert, encoding, _trust in ssl.enum_certificates("ROOT"):
            if encoding != "x509_asn":
                continue
            parts.append(b"\n-----BEGIN CERTIFICATE-----\n")
            parts.append(base64.encodebytes(cert))
            parts.append(b"-----END CERTIFICATE-----\n")

    path = _merged_bundle_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(parts))
    return str(path)


def ca_bundle_path() -> str:
    """Return the CA bundle path google-genai should use."""
    if sys.platform == "win32":
        return build_merged_ca_bundle()
    import certifi

    return certifi.where()


def _apply_bundle_env(bundle: str) -> None:
    os.environ["SSL_CERT_FILE"] = bundle
    os.environ["REQUESTS_CA_BUNDLE"] = bundle
    os.environ["HTTPX_CA_BUNDLE"] = bundle


def configure_process_ssl() -> None:
    """Apply SSL env vars for the current process.

    google-genai defaults to certifi when ``SSL_CERT_FILE`` is unset. On Windows
    that misses corporate proxy roots from the OS store, so we publish a merged
    bundle (Mozilla + Windows ROOT) via ``SSL_CERT_FILE``.
  """
    _apply_bundle_env(ca_bundle_path())


def ssl_env_for_subprocess(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    bundle = ca_bundle_path()
    env["SSL_CERT_FILE"] = bundle
    env["REQUESTS_CA_BUNDLE"] = bundle
    env["HTTPX_CA_BUNDLE"] = bundle
    return env
