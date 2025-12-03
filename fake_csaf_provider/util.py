import datetime

from .consts import domain


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def security_txt_content(canonical_path: str):
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).replace(microsecond=0).isoformat()
    # Most of this is just example content.
    # Only the URLs behind Canonical and CSAF are supported.
    return f"""
# Our canonical URI.
Canonical: https://{domain}{canonical_path}

# Our security addresses.
Contact: mailto:info@example.com

# Our security acknowledgements page.
Acknowledgments: https://{domain}/acknowledgments

# Our preferred languages.
Preferred-Languages: en, de

# Our security policy.
Policy: https://{domain}/policy

# Our security advisories
CSAF: https://{domain}/obscure/path/to/provider-metadata.json

Expires: {expires}
"""
