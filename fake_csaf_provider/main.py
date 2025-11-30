"""
A simple, dynamically configurable, fake CSAF provider server used for testing.
"""

from .consts import port
from .server import app
from .state import initialize_current_release_dates


initialize_current_release_dates()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
