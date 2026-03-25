# These paths are chosen deliberately obscure, so that clients rely on the metadata instead of on assumptions.
directory_listing_base_path = "/some-csaf-base-path"


def rolie_feed_path(tlp):
    """Generate ROLIE feed path for a given TLP level."""
    return f"/some-{tlp}-rolie-dir/some-feed.json"


def rolie_feed_csaf_dir(tlp):
    """Generate ROLIE CSAF directory path for a given TLP level."""
    return f"/some-{tlp}-csaf-dir-for-rolie"
