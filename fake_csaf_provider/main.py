"""
A simple, dynamically configurable, fake CSAF provider server used for testing.
"""

import pathlib

from .consts import port
from .server import app
from .state import initialize_current_release_dates


initialize_current_release_dates()

project_root = pathlib.Path(__file__).resolve().parents[1]
cert_path = project_root / "crypto" / "server.crt.pem"
key_path = project_root / "crypto" / "server.key.pem"

if __name__ == '__main__':
    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError(f"TLS certificate or key not found: {cert_path}, {key_path}\nHave you run the setup script?")
    ssl_ctx = (str(cert_path), str(key_path))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=ssl_ctx)
