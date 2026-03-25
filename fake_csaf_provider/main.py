"""
A simple, dynamically configurable, fake CSAF provider server used for testing.
"""

import pathlib
import ssl

from .server import app
from .state import initialize_current_release_dates
from .util import domain, port


initialize_current_release_dates()

project_root = pathlib.Path(__file__).resolve().parents[1]
cert_path = project_root / "crypto" / f"{domain}.crt.pem"
key_path = project_root / "crypto" / f"{domain}.key.pem"
ca_path = project_root / "crypto" / "ca.crt.pem"


def create_ssl_context():
    """Create SSL context with optional client certificate verification."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert_path), str(key_path))
    
    # Enable client certificate verification
    if ca_path.exists():
        context.load_verify_locations(str(ca_path))
        # CERT_OPTIONAL allows connections with or without client certificates
        # The auth module will enforce requirements on protected routes
        context.verify_mode = ssl.CERT_OPTIONAL
        print(f"Client certificate verification enabled using CA: {ca_path}")
    else:
        print(f"CA certificate not found at {ca_path}, client auth disabled")
    
    return context


if __name__ == '__main__':
    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError(f"TLS certificate or key not found: {cert_path}, {key_path}\nHave you run the setup script?")
    
    ssl_ctx = create_ssl_context()
    host = '127.0.0.1'
    if domain != 'localhost':
        host = '0.0.0.0'
    app.run(host=host, port=port, debug=True, ssl_context=ssl_ctx)
