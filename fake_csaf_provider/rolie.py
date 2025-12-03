import flask

from .consts import rolie_feed_path_white, rolie_feed_csaf_dir_white
from .files import csaf_file_exists, find_white_advisory_files
from .state import get_current_release_date, get_latest_release_date
from .util import domain, now

def rolie_feed():
    updated = get_latest_release_date()
    if updated:
        updated_str = updated.replace(microsecond=0).isoformat()
    else:
        updated_str = now()
    rolie = {
      "feed": {
        "id": "csaf-feed-tlp-white",
        "title": "CSAF feed (TLP:WHITE)",
        "link": [
          {
            "rel": "self",
            "href": f"https://{domain}/{rolie_feed_path_white}"
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
    for year, file in find_white_advisory_files():
      date = get_current_release_date(year, file)
      if date:
        updated_str = date.replace(microsecond=0).isoformat()
      else:
        updated_str = now()
      id = file[:-5] if file.endswith('.json') else file
      entry = {
          "id": f"{id}",
          "title": f"{id}",
          "link": [
            {
              "rel": "self",
              "href": f"https://{domain}{rolie_feed_csaf_dir_white}/{year}/{file}"
            }
          ],
          "published": updated_str, # This is not technically correct, but irrelevant for our purposes.
          "updated": updated_str,
          "content": {
            "type": "application/json",
            "src": f"https://{domain}{rolie_feed_csaf_dir_white}/{year}/{file}"
          },
          "format": {
            "schema": "https://docs.oasis-open.org/csaf/csaf/v2.0/csaf_json_schema.json",
            "version": "2.0"
          }
        }
      if csaf_file_exists("white", year, f"{file}.asc"):
          entry["link"].append({
              "rel": "signature",
              "href": f"https://{domain}{rolie_feed_csaf_dir_white}/{year}/{file}.asc"
          })
      if csaf_file_exists("white", year, f"{file}.sha256"):
          entry["link"].append({
              "rel": "hash",
              "href": f"https://{domain}{rolie_feed_csaf_dir_white}/{year}/{file}.sha256"
          })
      if csaf_file_exists("white", year, f"{file}.sha512"):
          entry["link"].append({
              "rel": "hash",
              "href": f"https://{domain}{rolie_feed_csaf_dir_white}/{year}/{file}.sha512"
          })
      rolie['feed']['entry'].append(entry)
    return flask.jsonify(rolie)
