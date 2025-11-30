import flask

from .consts import directory_listing_base_path, rolie_feed_csaf_dir_white, rolie_feed_path_white
from .files import send_csaf
from .metadata import provider_metadata
from .rolie import rolie_feed
from .state import configure, offer_if_enabled
from .util import security_txt_content


app = flask.Flask(__name__)


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
def security_txt():
    return offer_if_enabled('security_txt', security_txt_content())


@app.route(f'{directory_listing_base_path}/index.txt', methods=['GET'])
def directory_listing_index():
    return offer_if_enabled('directory_listing', 'TODO: directory listing index.txt')


@app.route(f'{directory_listing_base_path}/changes.csv', methods=['GET'])
def directory_listing_changes():
    return offer_if_enabled('directory_listing', 'TODO: directory listing changes.csv')


@app.route(f'{directory_listing_base_path}/<string:year>/<string:filename>', methods=['GET'])
def dir_listing_csaf(year, filename):
    return send_csaf("white", year, filename)


@app.route(rolie_feed_path_white, methods=['GET'])
def rolie_feed_endpoint():
    return offer_if_enabled('rolie_feed', rolie_feed())


@app.route(f'{rolie_feed_csaf_dir_white}/<string:year>/<string:filename>', methods=['GET'])
def rolie_feed_csaf(year, filename):
    return send_csaf("white", year, filename)
