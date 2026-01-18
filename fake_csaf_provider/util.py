import datetime
import os

domain = os.environ.get("FAKE_CSAF_DOMAIN", "localhost")
port = os.environ.get("FAKE_CSAF_PORT", 34443)
port_print = f":{port}" if port not in (80, 443) else ""
domain_print = f"{domain}{port_print}"

def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def security_txt_content(canonical_path: str):
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).replace(microsecond=0).isoformat()
    # Most of this is just example content.
    # Only the URLs behind Canonical and CSAF are supported.
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

Expires: {expires}
"""
