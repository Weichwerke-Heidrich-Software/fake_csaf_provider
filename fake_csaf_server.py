#!/usr/bin/env python3
"""
Simple, dynamically configurable, fake CSAF server used for testing.
"""

from flask import Flask, jsonify, request, abort, send_file
from threading import Lock
from datetime import datetime, timezone
import os

app = Flask(__name__)

user_home_dir = os.environ.get('HOME') or os.path.expanduser('~')
csaf_dir = os.path.join('csafs', 'some')
domain = 'localhost:34080'
# These paths are chosen deliberately obscure, so that clients rely on the metadata instead of on assumptions.
rolie_feed_path_white = "some-white-rolie-dir/some-feed.json"
rolie_feed_csaf_dir_white = "some-white-csaf-dir-for-rolie"

_state = {
    "well_known_meta": False,
    "security_data_meta": False,
    "advisories_csaf_meta": False,
    "security_csaf_meta": False,
    "security_txt": False,
    "directory_listing": False,
    "rolie_feed": False,
}
_state_lock = Lock()

def set_state(json: dict):
    with _state_lock:
        _state['well_known_meta'] = json.get('well_known_meta', False)
        _state['security_data_meta'] = json.get('security_data_meta', False)
        _state['advisories_csaf_meta'] = json.get('advisories_csaf_meta', False)
        _state['security_csaf_meta'] = json.get('security_csaf_meta', False)
        _state['security_txt'] = json.get('security_txt', False)
        _state['directory_listing'] = json.get('directory_listing', False)
        _state['rolie_feed'] = json.get('rolie_feed', False)

@app.route('/config', methods=['PATCH'])
def configure():
    if request.method != 'PATCH':
        abort(405)

    if not request.is_json:
        return jsonify({"error": "expected application/json"}), 400
    body = request.get_json()
    if not isinstance(body, dict):
        return jsonify({"error": "expected JSON object"}), 400
    set_state(body)
    return "Configured server", 200        

def offer_if_enabled(feature_name, return_value):
    with _state_lock:
        offer = _state.get(feature_name, False)
        if not offer:
            abort(404)
    return return_value

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
    with _state_lock:
        offer_rolie = _state.get('rolie_feed', False)
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
    return jsonify(metadata)

def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

@app.route('/.well-known/csaf/provider-metadata.json', methods=['GET'])
def well_known_meta():
    return offer_if_enabled('well_known_meta', provider_metadata())


@app.route('/security/data/csaf/provider-metadata.json', methods=['GET'])
def security_data_meta():
    return offer_if_enabled('security_data_meta', provider_metadata())


@app.route('/advisories/csaf/provider-metadata.json', methods=['GET'])
def advisories_csaf_meta():
    return offer_if_enabled('advisories_csaf_meta', provider_metadata())


@app.route('/security/csaf/provider-metadata.json', methods=['GET'])
def security_csaf_meta():
    return offer_if_enabled('security_csaf_meta', provider_metadata())


@app.route('/obscure/path/to/provider-metadata.json', methods=['GET'])
def obscure_meta():
    return provider_metadata()


def security_txt_content():
    return f"CSAF: http://{domain}/obscure/path/to/provider-metadata.json\n"


@app.route('/.well-known/security.txt', methods=['GET'])
def security_txt():
    return offer_if_enabled('security_txt', security_txt_content())


def find_white_year_dirs():
    path = os.path.join(csaf_dir, 'white')
    dirs = []
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path) and entry.isdigit():
            dirs.append(entry)
    return dirs


def find_white_advisory_files():
    path = os.path.join(csaf_dir, 'white')
    files = []
    for year in find_white_year_dirs():
        year_path = os.path.join(path, year)
        for entry in os.listdir(year_path):
            full_path = os.path.join(year_path, entry)
            if os.path.isfile(full_path) and entry.endswith('.json'):
                files.append((year, entry))
    return files


@app.route('/csaf/white/', methods=['GET'])
def white_directory_listing():
    return offer_if_enabled('directory_listing', 'TODO: directory listing')


@app.route('/csaf/white/<int:year>', methods=['GET'])
def white_year_directory_listing(year):
    return offer_if_enabled('directory_listing', 'TODO: directory listing')
    

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
    return jsonify(rolie)


@app.route(rolie_feed_path_white, methods=['GET'])
def rolie_feed_endpoint():
    return offer_if_enabled('rolie_feed', rolie_feed())


@app.route(f'{rolie_feed_csaf_dir_white}/<string:year>/<string:filename>', methods=['GET'])
def csaf(year, filename):
    path = os.path.join(csaf_dir, "white", year, filename)
    return send_file(path, mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=34080, debug=True)
