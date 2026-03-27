import flask

from .files import get_available_tlp_levels
from .paths import directory_listing_base_path, rolie_feed_path
from .state import get_config
from .util import domain_print, now

def provider_metadata():
    canonical_url = f"https://{domain_print}/obscure/path/to/provider-metadata.json"
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
            "namespace": f"https://{domain_print}"
        },
        "role": "csaf_provider"
    }
    offer_dirlisting = get_config('directory_listing')
    if offer_dirlisting:
        for tlp in get_available_tlp_levels():
            dirlisting = {
                "directory_url": f"https://{domain_print}/{directory_listing_base_path(tlp)}/"
            }
            metadata["distributions"].append(dirlisting)
    
    offer_rolie = get_config('rolie_feed')
    if offer_rolie:
        # Build list of all available TLP feeds
        feeds = []
        available_tlps = get_available_tlp_levels()
        
        for tlp in available_tlps:
            tlp_display = tlp.upper().replace('+', ':')
            feed_path = rolie_feed_path(tlp)
            feeds.append({
                "summary": f"{tlp_display} advisories",
                "tlp_label": tlp_display,
                "url": f"https://{domain_print}{feed_path}"
            })
        
        if feeds:
            rolie = {
                "rolie": {
                    "feeds": feeds
                }
            }
            metadata["distributions"].append(rolie)
    
    return flask.jsonify(metadata)
