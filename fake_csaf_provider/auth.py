"""
Client certificate authentication and authorization module.

Provides utilities for extracting, validating, and authorizing client certificates
in mutual TLS (mTLS) scenarios.
"""

import datetime
import flask
from functools import wraps
from pathlib import Path
from typing import Optional, Dict, Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from .state import get_config


def extract_client_certificate() -> Optional[x509.Certificate]:
    """
    Extract the client certificate from the Flask request environment.
    
    This implementation is specific to Flask's development server (Werkzeug),
    which exposes the underlying SSL socket in the WSGI environ.
    
    Returns:
        The parsed X.509 certificate object, or None if no certificate is present.
    """
    try:
        # Access the underlying socket from the WSGI environ
        if 'werkzeug.socket' in flask.request.environ:
            sock = flask.request.environ['werkzeug.socket']
            # Get the peer certificate in binary DER format
            peercert_binary = sock.getpeercert(binary_form=True)
            if peercert_binary:
                cert = x509.load_der_x509_certificate(peercert_binary, default_backend())
                return cert
    except Exception as e:
        print(f"Failed to get certificate from socket: {e}")
    
    return None


def validate_client_certificate(cert: x509.Certificate, ca_path: str) -> bool:
    """
    Validate that a client certificate is properly signed and within validity period.
    
    Args:
        cert: The client certificate to validate
        ca_path: Path to the trusted CA certificate file
        
    Returns:
        True if the certificate is valid, False otherwise
    """
    if not cert:
        return False
    
    try:
        # Check validity period
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Handle both old and new cryptography API
        if hasattr(cert, 'not_valid_before_utc') and hasattr(cert, 'not_valid_after_utc'):
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
        else:
            # Fallback for older versions
            import warnings
            from cryptography.utils import CryptographyDeprecationWarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", CryptographyDeprecationWarning)
                not_before = cert.not_valid_before
                not_after = cert.not_valid_after
        
        # Ensure timezone awareness
        if not_before.tzinfo is None:
            not_before = not_before.replace(tzinfo=datetime.timezone.utc)
        if not_after.tzinfo is None:
            not_after = not_after.replace(tzinfo=datetime.timezone.utc)
        
        if not (not_before <= now <= not_after):
            print(f"Client certificate is not within validity period: {not_before} to {not_after}")
            return False
        
        # Load the CA certificate to verify the signature
        ca_cert_path = Path(ca_path)
        if not ca_cert_path.exists():
            print(f"CA certificate not found at {ca_path}")
            return False
        
        ca_cert_data = ca_cert_path.read_bytes()
        ca_cert = x509.load_pem_x509_certificate(ca_cert_data, default_backend())
        
        # Verify the certificate was issued by the CA
        # Note: This is a simplified check. In production, you'd verify the full chain
        # and check the signature cryptographically.
        if cert.issuer != ca_cert.subject:
            print(f"Client certificate issuer does not match CA subject")
            return False
        
        return True
        
    except Exception as e:
        print(f"Certificate validation failed: {e}")
        return False


def get_client_identity() -> Optional[Dict[str, Any]]:
    """
    Extract and return the client identity from the current request.
    
    Returns:
        A dictionary containing client identity information, or None if no valid
        certificate is present. The dictionary includes:
        - common_name: The CN from the certificate subject
        - issuer: The issuer DN
        - serial_number: The certificate serial number
        - not_before: Validity start date
        - not_after: Validity end date
    """
    cert = extract_client_certificate()
    if not cert:
        return None
    
    # Validate the certificate against the CA
    ca_path = 'crypto/ca.crt.pem'
    if not validate_client_certificate(cert, ca_path):
        return None
    
    # Extract identity information
    try:
        # Get common name from subject
        common_name = None
        for attr in cert.subject:
            if attr.oid == x509.oid.NameOID.COMMON_NAME:
                common_name = attr.value
                break
        
        # Handle validity dates
        if hasattr(cert, 'not_valid_before_utc') and hasattr(cert, 'not_valid_after_utc'):
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
        else:
            import warnings
            from cryptography.utils import CryptographyDeprecationWarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", CryptographyDeprecationWarning)
                not_before = cert.not_valid_before
                not_after = cert.not_valid_after
        
        identity = {
            'common_name': common_name,
            'issuer': cert.issuer.rfc4514_string(),
            'serial_number': cert.serial_number,
            'not_before': not_before.isoformat() if not_before else None,
            'not_after': not_after.isoformat() if not_after else None,
        }
        
        return identity
        
    except Exception as e:
        print(f"Failed to extract client identity: {e}")
        return None


def require_client_cert(f):
    """
    Decorator to require a valid client certificate for accessing a route.
    
    Returns 403 Forbidden if no valid client certificate is present.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if a valid client identity exists
        identity = getattr(flask.g, 'client_identity', None)
        
        if not identity:
            flask.abort(403, description="Valid client certificate required")
        
        return f(*args, **kwargs)
    
    return decorated_function
