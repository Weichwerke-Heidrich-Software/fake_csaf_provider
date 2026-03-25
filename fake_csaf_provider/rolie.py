import flask

from .consts import rolie_feed_path, rolie_feed_csaf_dir
from .files import csaf_file_exists, find_advisory_files, read_csaf_id
from .state import get_current_release_date, get_latest_release_date, get_config
from .util import domain_print, now

def rolie_feed(tlp):
    """Generate a ROLIE feed for a specific TLP level."""
    feed_path = rolie_feed_path(tlp)
    csaf_dir = rolie_feed_csaf_dir(tlp)
    
    updated = get_latest_release_date()
    if updated:
        updated_str = updated.replace(microsecond=0).isoformat()
    else:
        updated_str = now()
    
    tlp_display = tlp.upper()
    rolie = {
      "feed": {
        "id": f"csaf-feed-tlp-{tlp}",
        "title": f"CSAF feed (TLP:{tlp_display})",
        "link": [
          {
            "rel": "self",
            "href": f"https://{domain_print}{feed_path}"
          }
        ],
        "category": [
          {
            "scheme": "urn:ietf:params:rolie:category:information-type",
            "term": "csaf"
          }
        ],
        "updated": updated_str,
        "entry": []
      }
    }
    
    for year, file in find_advisory_files(tlp):
      date = get_current_release_date(year, file)
      if date:
        updated_str = date.replace(microsecond=0).isoformat()
      else:
        updated_str = now()
      id = read_csaf_id(year, file, tlp)
      entry = {
          "id": f"{id}",
          "title": f"{id}",
          "link": [
            {
              "rel": "self",
              "href": f"https://{domain_print}{csaf_dir}/{year}/{file}"
            }
          ],
          "published": updated_str,
          "updated": updated_str,
          "content": {
            "type": "application/json",
            "src": f"https://{domain_print}{csaf_dir}/{year}/{file}"
          },
          "format": {
            "schema": "https://docs.oasis-open.org/csaf/csaf/v2.0/csaf_json_schema.json",
            "version": "2.0"
          }
        }
      if get_config('openpgp'):
          entry["link"].append({
              "rel": "signature",
              "href": f"https://{domain_print}{csaf_dir}/{year}/{file}.asc"
          })
      if csaf_file_exists(tlp, year, f"{file}.sha256"):
          entry["link"].append({
              "rel": "hash",
              "href": f"https://{domain_print}{csaf_dir}/{year}/{file}.sha256"
          })
      if csaf_file_exists(tlp, year, f"{file}.sha512"):
          entry["link"].append({
              "rel": "hash",
              "href": f"https://{domain_print}{csaf_dir}/{year}/{file}.sha512"
          })
      rolie['feed']['entry'].append(entry)
    return flask.jsonify(rolie)
