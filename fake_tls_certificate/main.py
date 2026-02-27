"""Generate a test CA and a localhost TLS certificate.

Produces:
- ca.key.pem (private key for the test CA)
- ca.crt.pem (CA certificate)
- server.key.pem (private key for the server)
- server.crt.pem (server certificate signed by the CA)
- server.chain.pem (concatenation of server key + cert)
"""


from __future__ import annotations

import datetime
import ipaddress
from pathlib import Path
import argparse
from typing import Iterable, List
import warnings

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption
from cryptography.x509.oid import NameOID
from cryptography.utils import CryptographyDeprecationWarning


DEFAULT_OUTDIR = Path("./crypto")
DEFAULT_DAYS = 365
KEY_SIZE = 2048
DEFAULT_COMMON_NAME = "localhost"
DEFAULT_SAN = ["localhost", "127.0.0.1", "::1"]
CA_NAME = "Fake CA"


def make_rsa_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=key_size)


def write_key(path: Path, key: rsa.RSAPrivateKey, password: str | None = None) -> None:
    if password:
        encryption = BestAvailableEncryption(password.encode())
    else:
        encryption = NoEncryption()

    data = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=encryption,
    )
    path.write_bytes(data)
    try:
        path.chmod(0o600)
    except Exception:
        pass


def write_cert(path: Path, cert: x509.Certificate) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def build_ca(key: rsa.RSAPrivateKey, common_name: str, days: int) -> x509.Certificate:
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    )
    cert = builder.sign(private_key=key, algorithm=hashes.SHA256())
    return cert


def build_server_cert(
    server_key: rsa.RSAPrivateKey,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    common_name: str,
    san: Iterable[str],
    days: int,
) -> x509.Certificate:
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)

    alt_names: List[x509.GeneralName] = []
    for n in san:
        try:
            ip = ipaddress.ip_address(n)
            alt_names.append(x509.IPAddress(ip))
        except ValueError:
            alt_names.append(x509.DNSName(n))

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    )

    cert = builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
    return cert


def load_or_build_ca(ca_key_path: Path, ca_cert_path: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    now = datetime.datetime.now(datetime.timezone.utc)
    if ca_key_path.exists() and ca_cert_path.exists():
        try:
            key_data = ca_key_path.read_bytes()
            key = serialization.load_pem_private_key(key_data, password=None)
            cert_data = ca_cert_path.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)
            # Prefer the timezone-aware `_utc` properties when available.
            # Only access the deprecated naive properties inside a
            # localized warning-suppression block to avoid global noise.
            if hasattr(cert, "not_valid_before_utc") and hasattr(cert, "not_valid_after_utc"):
                not_before = cert.not_valid_before_utc
                not_after = cert.not_valid_after_utc
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", CryptographyDeprecationWarning)
                    nb = cert.not_valid_before
                    na = cert.not_valid_after
                not_before = nb
                not_after = na

            if not_before.tzinfo is None:
                not_before = not_before.replace(tzinfo=datetime.timezone.utc)
            if not_after.tzinfo is None:
                not_after = not_after.replace(tzinfo=datetime.timezone.utc)

            if not_before <= now <= not_after:
                print(f"Found existing CA certificate at {ca_cert_path}. It will be reused.")
                return key, cert
            else:
                print(f"Existing CA certificate at {ca_cert_path} is expired or not yet valid. It will be regenerated.")
        except Exception as e:
            print(f"Failed to load existing CA files: {e}. They will be regenerated.")

    # build and persist a new CA
    print(f"Generating new CA certificate at {ca_cert_path}.")
    key = make_rsa_key(KEY_SIZE)
    cert = build_ca(key, CA_NAME, 1000)
    write_key(ca_key_path, key)
    write_cert(ca_cert_path, cert)
    return key, cert


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate a test CA and a localhost TLS certificate.")
    parser.add_argument(
        "common_name",
        nargs="?",
        default=DEFAULT_COMMON_NAME,
        help=f"Server certificate common name (default: {DEFAULT_COMMON_NAME})",
    )
    parser.add_argument("-d", "--days", type=int, default=DEFAULT_DAYS, help=f"Certificate validity days (default: {DEFAULT_DAYS})")
    parser.add_argument(
        "-o",
        "--outdir",
        default=str(DEFAULT_OUTDIR),
        help=f"Output directory (default: {DEFAULT_OUTDIR})",
    )

    args = parser.parse_args(argv)

    outdir: Path = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = {
        "ca_key": outdir / "ca.key.pem",
        "ca_cert": outdir / "ca.crt.pem",
        "server_key": outdir / f"{args.common_name}.key.pem",
        "server_cert": outdir / f"{args.common_name}.crt.pem",
        "server_pem": outdir / f"{args.common_name}.chain.pem",
    }

    ca_key, ca_cert = load_or_build_ca(files["ca_key"], files["ca_cert"])

    server_key = make_rsa_key(KEY_SIZE)
    sans = DEFAULT_SAN
    if args.common_name not in sans:
        sans += [args.common_name]
    server_cert = build_server_cert(server_key, ca_key, ca_cert, args.common_name, sans, args.days)

    # write server files
    write_key(files["server_key"], server_key)
    write_cert(files["server_cert"], server_cert)

    # combined server pem (key + cert)
    server_pem_data = files["server_key"].read_bytes() + b"\n" + files["server_cert"].read_bytes()
    files["server_pem"].write_bytes(server_pem_data)

    print("Wrote:")
    for k, p in files.items():
        print(f" - {p}")


if __name__ == "__main__":
    main()
