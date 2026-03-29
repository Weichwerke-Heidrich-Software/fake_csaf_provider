import datetime
import os

from .auth import is_client_authenticated
from .state import get_config

domain = os.environ.get('FAKE_CSAF_DOMAIN', 'localhost')
port = os.environ.get('FAKE_CSAF_PORT', 34443)
port_print = f':{port}' if port not in (80, 443) else ''
domain_print = f'{domain}{port_print}'

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def security_txt_content(canonical_path: str):
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).replace(microsecond=0).isoformat()
    
    openpgp_line = ''
    if get_config('openpgp'):
        openpgp_line = f'\n# Our OpenPGP key\nEncryption: https://{domain_print}/.well-known/openpgpkey.asc\n'
    
    # Most of this is just example content.
    # Only the URLs behind Canonical, CSAF and Encryption are supported.
    return f"""
# Our canonical URI.
Canonical: https://{domain_print}{canonical_path}

# Our security addresses.
Contact: mailto:info@example.com

# Our security acknowledgements page.
Acknowledgments: https://{domain_print}/acknowledgments

# Our preferred languages.
Preferred-Languages: en, de

# Our security policy.
Policy: https://{domain_print}/policy

# Our security advisories
CSAF: https://{domain_print}/obscure/path/to/provider-metadata.json
{openpgp_line}
Expires: {expires}
"""


def get_accessible_tlp_levels(available_tlps: list[str]) -> list[str]:
    """
    Filter TLP levels based on client authentication status.
    
    Returns only 'white' and 'clear' TLP levels for unauthenticated clients.
    Returns all available TLP levels for authenticated clients.
    
    Args:
        available_tlps: List of all available TLP levels
        
    Returns:
        List of TLP levels accessible to the current client
    """
    if is_client_authenticated():
        return available_tlps
    else:
        return [tlp for tlp in available_tlps if tlp in ('white', 'clear')]
