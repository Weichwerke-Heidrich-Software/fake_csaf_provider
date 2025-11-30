import flask

from .consts import directory_listing_base_path, rolie_feed_path_white
from .state import get_config
from .util import domain, now

def provider_metadata():
    canonical_url = f"http://{domain}/obscure/path/to/provider-metadata.json"
    metadata = {
        "canonical_url": canonical_url,
        "distributions": [],
        "last_updated": now(),
        "list_on_CSAF_aggregators": True,
        "metadata_version": "2.0",
        "mirror_on_CSAF_aggregators": True,
        "publisher": {
            "category": "vendor",
            "contact_details": "Contact.",
            "issuing_authority": "Test.",
            "name": "Test-Vendor",
            "namespace": f"http://{domain}"
        },
        "role": "csaf_provider"
    }
    offer_dirlisting = get_config('directory_listing')
    if offer_dirlisting:
        dirlisting = {
            "directory_url": f"http://{domain}/{directory_listing_base_path}/"
        }
        metadata["distributions"].append(dirlisting)
    offer_rolie = get_config('rolie_feed')
    if offer_rolie:
        rolie = {
        "rolie": {
            "feeds": [
                {
                    "summary": "WHITE advisories",
                    "tlp_label": "WHITE",
                    "url": f"http://{domain}/{rolie_feed_path_white}"
                }
            ]
        }
        }
        metadata["distributions"].append(rolie)
    return flask.jsonify(metadata)
