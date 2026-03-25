"""Generate OpenPGP key pairs for testing purposes.

Produces:
- openpgp.key.asc (ASCII-armored private key)
- openpgp.pub.asc (ASCII-armored public key)

Uses the PGPy13 library with ED25519 keys.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pgpy
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm, EllipticCurveOID


DEFAULT_OUTDIR = Path("./crypto")
DEFAULT_NAME = "Fake CSAF Provider"
DEFAULT_EMAIL = "fake-csaf-provider@example.com"
DEFAULT_COMMENT = "Generated for testing"


def generate_openpgp_keypair(
    name: str,
    email: str,
    comment: str = "",
) -> tuple[str, str]:
    """Generate an OpenPGP key pair using ED25519.
    
    Args:
        name: User's name for the key
        email: User's email for the key
        comment: Optional comment for the key
        
    Returns:
        Tuple of (private_key_armor, public_key_armor)
    """
    # Create user ID
    if comment:
        user_id = pgpy.PGPUID.new(name, comment=comment, email=email)
    else:
        user_id = pgpy.PGPUID.new(name, email=email)
    
    # Generate ED25519 key pair
    key = pgpy.PGPKey.new(PubKeyAlgorithm.EdDSA, EllipticCurveOID.Ed25519)
    
    # Add user ID to the key
    key.add_uid(
        user_id,
        usage={KeyFlags.Sign, KeyFlags.Certify},
        hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512],
        ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
        compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP]
    )
    
    # Export keys as ASCII-armored strings
    private_key_armor = str(key)
    public_key_armor = str(key.pubkey)
    
    return private_key_armor, public_key_armor


def write_key(path: Path, key_data: str) -> None:
    """Write an OpenPGP key to a file.
    
    Args:
        path: Path to write the key to
        key_data: ASCII-armored key data
    """
    path.write_text(key_data)
    try:
        path.chmod(0o600)
    except Exception:
        pass


def load_or_generate_keypair(
    private_key_path: Path,
    public_key_path: Path,
    name: str,
    email: str,
    comment: str,
) -> tuple[str, str]:
    """Load existing OpenPGP key pair or generate a new one.
    
    Args:
        private_key_path: Path to private key file
        public_key_path: Path to public key file
        name: User's name for the key
        email: User's email for the key
        comment: Comment for the key
        
    Returns:
        Tuple of (private_key, public_key)
    """
    if private_key_path.exists() and public_key_path.exists():
        try:
            # Try to read existing keys
            private_key = private_key_path.read_text()
            public_key = public_key_path.read_text()
            
            # Verify they are valid by checking for PGP headers
            if "-----BEGIN PGP PRIVATE KEY BLOCK-----" in private_key and \
               "-----BEGIN PGP PUBLIC KEY BLOCK-----" in public_key:
                print(f"Found existing OpenPGP key pair at {private_key_path}. It will be reused.")
                return private_key, public_key
        except Exception as e:
            print(f"Failed to load existing OpenPGP key pair: {e}. A new one will be generated.")
    
    # Generate new key pair
    print(f"Generating new OpenPGP key pair (ED25519) at {private_key_path}.")
    private_key, public_key = generate_openpgp_keypair(name, email, comment)
    
    # Write keys to files
    write_key(private_key_path, private_key)
    write_key(public_key_path, public_key)
    
    return private_key, public_key


def main(argv: list[str] | None = None) -> None:
    """Main entry point for OpenPGP key generation."""
    parser = argparse.ArgumentParser(
        description="Generate an OpenPGP key pair for testing purposes using ED25519."
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help=f"Name for the key (default: {DEFAULT_NAME})",
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_EMAIL,
        help=f"Email for the key (default: {DEFAULT_EMAIL})",
    )
    parser.add_argument(
        "--comment",
        default=DEFAULT_COMMENT,
        help=f"Comment for the key (default: {DEFAULT_COMMENT})",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default=str(DEFAULT_OUTDIR),
        help=f"Output directory (default: {DEFAULT_OUTDIR})",
    )
    
    args = parser.parse_args(argv)
    
    outdir: Path = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    private_key_path = outdir / "openpgp.key.asc"
    public_key_path = outdir / "openpgp.pub.asc"
    
    private_key, public_key = load_or_generate_keypair(
        private_key_path,
        public_key_path,
        args.name,
        args.email,
        args.comment,
    )
    
    print("Wrote:")
    print(f" - {private_key_path} (private key, ED25519)")
    print(f" - {public_key_path} (public key, ED25519)")


if __name__ == "__main__":
    main()
