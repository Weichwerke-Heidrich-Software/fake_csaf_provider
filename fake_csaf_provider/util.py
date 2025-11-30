import datetime

from .consts import domain


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def security_txt_content():
    return f"CSAF: http://{domain}/obscure/path/to/provider-metadata.json\n"
