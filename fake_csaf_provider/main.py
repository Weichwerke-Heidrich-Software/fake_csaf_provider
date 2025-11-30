"""
A simple, dynamically configurable, fake CSAF provider server used for testing.
"""

from .consts import port
from .server import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
