import flask

from .consts import rolie_feed_path_white, rolie_feed_csaf_dir_white
from .files import find_white_advisory_files
from .util import domain, now

def rolie_feed():
    rolie = {
      "feed": {
        "id": "csaf-feed-tlp-white",
        "title": "CSAF feed (TLP:WHITE)",
        "link": [
          {
            "rel": "self",
            "href": f"http://{domain}/{rolie_feed_path_white}"
          }
        ],
        "category": [
          {
            "scheme": "urn:ietf:params:rolie:category:information-type",
            "term": "csaf"
          }
        ],
        "updated": now(),
        "entry": []
      }
    }
    for year, file in find_white_advisory_files():
      id = file[:-5] if file.endswith('.json') else file
      entry = {
          "id": f"{id}",
          "title": f"{id}",
          "link": [
            {
              "rel": "self",
              "href": f"http://{domain}/{rolie_feed_csaf_dir_white}/{year}/{file}"
            },
            {
              "rel": "hash",
              "href": f"http://{domain}/{rolie_feed_csaf_dir_white}/{year}/{file}.sha256"
            },
            {
              "rel": "hash",
              "href": f"http://{domain}/{rolie_feed_csaf_dir_white}/{year}/{file}.sha512"
            },
            {
              "rel": "signature",
              "href": f"http://{domain}/{rolie_feed_csaf_dir_white}/{year}/{file}.asc"
            }
          ],
          "published": f"{year}-01-01T10:00:00Z",
          "updated": f"{year}-01-01T10:00:00Z",
          "content": {
            "type": "application/json",
            "src": f"http://{domain}/{rolie_feed_csaf_dir_white}/{year}/{file}"
          },
          "format": {
            "schema": "https://docs.oasis-open.org/csaf/csaf/v2.0/csaf_json_schema.json",
            "version": "2.0"
          }
        }
      rolie['feed']['entry'].append(entry)
    return flask.jsonify(rolie)
