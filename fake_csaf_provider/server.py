import flask

from .consts import directory_listing_base_path, rolie_feed_csaf_dir_white, rolie_feed_path_white
from .dirlisting import changes_csv, index_txt
from .files import send_csaf
from .metadata import provider_metadata
from .rolie import rolie_feed
from .state import configure, offer_if_enabled, is_request_allowed, get_retry_after_seconds
from .util import security_txt_content


app = flask.Flask(__name__)


@app.before_request
def enforce_rate_limit():
    if flask.request.path == '/config':
        return None

    client = flask.request.headers.get('X-Forwarded-For', None)
    if client:
        client = client.split(',')[0].strip()
    else:
        client = flask.request.remote_addr or 'unknown'

    allowed = is_request_allowed(client)
    if not allowed:
        retry_after = str(get_retry_after_seconds())
        resp = flask.jsonify({"error": "Too Many Requests"})
        resp.status_code = 429
        resp.headers['Retry-After'] = retry_after
        return resp


@app.route('/config', methods=['PATCH'])
def configure_state():
    return configure()


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


@app.route('/.well-known/security.txt', methods=['GET'])
def well_known_security_txt():
    return offer_if_enabled('well_known_security_txt', security_txt_content('/.well-known/security.txt'))


@app.route('/security.txt', methods=['GET'])
def root_security_txt():
    return offer_if_enabled('root_security_txt', security_txt_content('/security.txt'))


@app.route(f'{directory_listing_base_path}/index.txt', methods=['GET'])
def directory_listing_index():
    return offer_if_enabled('directory_listing', index_txt())


@app.route(f'{directory_listing_base_path}/changes.csv', methods=['GET'])
def directory_listing_changes():
    return offer_if_enabled('directory_listing', changes_csv())


@app.route(f'{directory_listing_base_path}/<string:year>/<string:filename>', methods=['GET'])
def dir_listing_csaf(year, filename):
    return send_csaf("white", year, filename)


@app.route(rolie_feed_path_white, methods=['GET'])
def rolie_feed_endpoint():
    return offer_if_enabled('rolie_feed', rolie_feed())


@app.route(f'{rolie_feed_csaf_dir_white}/<string:year>/<string:filename>', methods=['GET'])
def rolie_feed_csaf(year, filename):
    return send_csaf("white", year, filename)
