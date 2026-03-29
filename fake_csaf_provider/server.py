import flask
import pathlib

from .auth import is_client_authenticated, require_client_cert
from .dirlisting import changes_csv, index_txt
from .files import send_doc
from .metadata import provider_metadata
from .paths import directory_listing_base_path, rolie_feed_path, rolie_feed_csaf_dir
from .rolie import rolie_feed, rolie_feed
from .state import configure, offer_if_enabled, rate_limit_headers, get_retry_after_seconds, log_request
from .util import security_txt_content


app = flask.Flask(__name__)
# Disable host validation to allow requests from any hostname (useful in Docker networks)
app.config['SERVER_NAME'] = None


@app.before_request
def enforce_rate_limit():
    if flask.request.path == '/config':
        return None

    client = flask.request.headers.get('X-Forwarded-For', None)
    if client:
        client = client.split(',')[0].strip()
    else:
        client = flask.request.remote_addr or 'unknown'

    log_request(client)
    headers = rate_limit_headers(client)
    flask.g.rate_limit_headers = headers # Stored for after_request
    is_allowed = int(headers.get('X-RateLimit-Remaining', 100)) > 0
    if not is_allowed:
        retry_after = str(get_retry_after_seconds())
        resp = flask.jsonify({'error': 'Too Many Requests'})
        resp.status_code = 429
        resp.headers['Retry-After'] = retry_after
        return resp


@app.after_request
def attach_rate_limit_headers(response):
    headers = getattr(flask.g, 'rate_limit_headers', None)
    if headers:
        for k, v in headers.items():
            response.headers[k] = str(v)
    return response


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


@app.route(f'{directory_listing_base_path("white")}/index.txt', methods=['GET'])
def directory_listing_index():
    return offer_if_enabled('directory_listing', index_txt('white'))


@app.route(f'{directory_listing_base_path("white")}/changes.csv', methods=['GET'])
def directory_listing_changes():
    return offer_if_enabled('directory_listing', changes_csv('white'))


@app.route(f'{directory_listing_base_path("white")}/<string:year>/<string:filename>', methods=['GET'])
def dir_listing_csaf(year, filename):
    return offer_if_enabled('directory_listing', send_doc('white', year, filename))


@app.route(f'{directory_listing_base_path("clear")}/index.txt', methods=['GET'])
def directory_listing_index_clear():
    return offer_if_enabled('directory_listing', index_txt('clear'))


@app.route(f'{directory_listing_base_path("clear")}/changes.csv', methods=['GET'])
def directory_listing_changes_clear():
    return offer_if_enabled('directory_listing', changes_csv('clear'))


@app.route(f'{directory_listing_base_path("clear")}/<string:year>/<string:filename>', methods=['GET'])
def dir_listing_csaf_clear(year, filename):
    return offer_if_enabled('directory_listing', send_doc('clear', year, filename))


@app.route(f'{directory_listing_base_path("green")}/index.txt', methods=['GET'])
@require_client_cert
def directory_listing_index_green():
    return offer_if_enabled('directory_listing', index_txt('green'))


@app.route(f'{directory_listing_base_path("green")}/changes.csv', methods=['GET'])
@require_client_cert
def directory_listing_changes_green():
    return offer_if_enabled('directory_listing', changes_csv('green'))


@app.route(f'{directory_listing_base_path("green")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def dir_listing_csaf_green(year, filename):
    return offer_if_enabled('directory_listing', send_doc('green', year, filename))


@app.route(f'{directory_listing_base_path("amber")}/index.txt', methods=['GET'])
@require_client_cert
def directory_listing_index_amber():
    return offer_if_enabled('directory_listing', index_txt('amber'))


@app.route(f'{directory_listing_base_path("amber")}/changes.csv', methods=['GET'])
@require_client_cert
def directory_listing_changes_amber():
    return offer_if_enabled('directory_listing', changes_csv('amber'))


@app.route(f'{directory_listing_base_path("amber")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def dir_listing_csaf_amber(year, filename):
    return offer_if_enabled('directory_listing', send_doc('amber', year, filename))


@app.route(f'{directory_listing_base_path("amber-strict")}/index.txt', methods=['GET'])
@require_client_cert
def directory_listing_index_amber_strict():
    return offer_if_enabled('directory_listing', index_txt('amber+strict'))


@app.route(f'{directory_listing_base_path("amber-strict")}/changes.csv', methods=['GET'])
@require_client_cert
def directory_listing_changes_amber_strict():
    return offer_if_enabled('directory_listing', changes_csv('amber+strict'))


@app.route(f'{directory_listing_base_path("amber-strict")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def dir_listing_csaf_amber_strict(year, filename):
    return offer_if_enabled('directory_listing', send_doc('amber+strict', year, filename))


@app.route(f'{directory_listing_base_path("red")}/index.txt', methods=['GET'])
@require_client_cert
def directory_listing_index_red():
    return offer_if_enabled('directory_listing', index_txt('red'))


@app.route(f'{directory_listing_base_path("red")}/changes.csv', methods=['GET'])
@require_client_cert
def directory_listing_changes_red():
    return offer_if_enabled('directory_listing', changes_csv('red'))


@app.route(f'{directory_listing_base_path("red")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def dir_listing_csaf_red(year, filename):
    return offer_if_enabled('directory_listing', send_doc('red', year, filename))


@app.route(f'{directory_listing_base_path("unlabeled")}/index.txt', methods=['GET'])
@require_client_cert
def directory_listing_index_unlabeled():
    return offer_if_enabled('directory_listing', index_txt('unlabeled'))


@app.route(f'{directory_listing_base_path("unlabeled")}/changes.csv', methods=['GET'])
@require_client_cert
def directory_listing_changes_unlabeled():
    return offer_if_enabled('directory_listing', changes_csv('unlabeled'))


@app.route(f'{directory_listing_base_path("unlabeled")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def dir_listing_csaf_unlabeled(year, filename):
    return offer_if_enabled('directory_listing', send_doc('unlabeled', year, filename))


@app.route(rolie_feed_path('white'), methods=['GET'])
def rolie_feed_endpoint():
    return offer_if_enabled('rolie_feed', rolie_feed('white'))


@app.route(rolie_feed_path('clear'), methods=['GET'])
def rolie_feed_clear():
    return offer_if_enabled('rolie_feed', rolie_feed('clear'))


@app.route(rolie_feed_path('green'), methods=['GET'])
@require_client_cert
def rolie_feed_green():
    return offer_if_enabled('rolie_feed', rolie_feed('green'))


@app.route(rolie_feed_path('amber'), methods=['GET'])
@require_client_cert
def rolie_feed_amber():
    return offer_if_enabled('rolie_feed', rolie_feed('amber'))


@app.route(rolie_feed_path('amber-strict'), methods=['GET'])
@require_client_cert
def rolie_feed_amber_strict():
    return offer_if_enabled('rolie_feed', rolie_feed('amber+strict'))


@app.route(rolie_feed_path('red'), methods=['GET'])
@require_client_cert
def rolie_feed_red():
    return offer_if_enabled('rolie_feed', rolie_feed('red'))


@app.route(rolie_feed_path('unlabeled'), methods=['GET'])
@require_client_cert
def rolie_feed_unlabeled():
    return offer_if_enabled('rolie_feed', rolie_feed('unlabeled'))


@app.route(f'{rolie_feed_csaf_dir("white")}/<string:year>/<string:filename>', methods=['GET'])
def rolie_feed_csaf(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('white', year, filename))


@app.route(f'{rolie_feed_csaf_dir("clear")}/<string:year>/<string:filename>', methods=['GET'])
def rolie_feed_csaf_clear(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('clear', year, filename))


@app.route(f'{rolie_feed_csaf_dir("green")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def rolie_feed_csaf_green(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('green', year, filename))


@app.route(f'{rolie_feed_csaf_dir("amber")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def rolie_feed_csaf_amber(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('amber', year, filename))


@app.route(f'{rolie_feed_csaf_dir("amber-strict")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def rolie_feed_csaf_amber_strict(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('amber+strict', year, filename))


@app.route(f'{rolie_feed_csaf_dir("red")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def rolie_feed_csaf_red(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('red', year, filename))


@app.route(f'{rolie_feed_csaf_dir("unlabeled")}/<string:year>/<string:filename>', methods=['GET'])
@require_client_cert
def rolie_feed_csaf_unlabeled(year, filename):
    return offer_if_enabled('rolie_feed', send_doc('unlabeled', year, filename))


@app.route('/.well-known/openpgpkey.asc', methods=['GET'])
def openpgp_key():
    project_root = pathlib.Path(__file__).resolve().parents[1]
    key_path = project_root / 'crypto' / 'openpgp.pub.asc'
    
    if not key_path.exists():
        flask.abort(404, description='OpenPGP public key not found')
    
    return offer_if_enabled('openpgp', flask.send_file(str(key_path), mimetype='application/pgp-keys'))
