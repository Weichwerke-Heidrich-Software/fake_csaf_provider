"""
Client certificate authentication module for test server.
"""

import datetime
import flask

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from functools import wraps
from pathlib import Path
from typing import Optional


def extract_client_certificate() -> Optional[x509.Certificate]:
    """
    Extract the client certificate from the Flask request environment.
    
    Returns:
        The parsed X.509 certificate object, or None if no certificate is present.
    """
    try:
        if 'werkzeug.socket' in flask.request.environ:
            sock = flask.request.environ['werkzeug.socket']
            peercert_binary = sock.getpeercert(binary_form=True)
            if peercert_binary:
                cert = x509.load_der_x509_certificate(peercert_binary, default_backend())
                return cert
    except Exception as e:
        print(f"Failed to get certificate from socket: {e}")
    
    return None


def validate_client_certificate(cert: x509.Certificate, ca_path: str) -> bool:
    """
    Validate that a client certificate is signed by the CA and within validity period.
    
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
        not_before = cert.not_valid_before_utc
        not_after = cert.not_valid_after_utc
        
        if not (not_before <= now <= not_after):
            print(f"Certificate expired or not yet valid")
            return False
        
        # Load and verify CA certificate
        ca_cert_path = Path(ca_path)
        if not ca_cert_path.exists():
            print(f"CA certificate not found at {ca_path}")
            return False
        
        ca_cert = x509.load_pem_x509_certificate(ca_cert_path.read_bytes(), default_backend())
        
        # Verify issuer matches CA subject
        if cert.issuer != ca_cert.subject:
            print(f"Certificate not signed by CA")
            return False
        
        return True
        
    except Exception as e:
        print(f"Certificate validation failed: {e}")
        return False


def is_client_authenticated() -> bool:
    """
    Check if the current request has a valid client certificate.
    
    Returns:
        True if a valid certificate is present, False otherwise
    """
    cert = extract_client_certificate()
    if not cert:
        return False
    
    ca_path = 'crypto/ca.crt.pem'
    return validate_client_certificate(cert, ca_path)


def require_client_cert(f):
    """
    Decorator to require a valid client certificate for accessing a route.
    
    Returns 403 Forbidden if no valid client certificate is present.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_client_authenticated():
            flask.abort(403, description="Valid client certificate required")
        
        return f(*args, **kwargs)
    
    return decorated_function
