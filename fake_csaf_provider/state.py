import datetime
import flask
import threading

from .files import collect_current_release_dates

_state = {
    "well_known_meta": False,
    "security_data_meta": False,
    "advisories_csaf_meta": False,
    "security_csaf_meta": False,
    "security_txt": False,
    "directory_listing": False,
    "rolie_feed": False,
}
_state_lock = threading.Lock()

_cache = {
    "current_release_dates": None,
}
_cache_lock = threading.Lock()


def set_state(json: dict):
    with _state_lock:
        _state['well_known_meta'] = json.get('well_known_meta', False)
        _state['security_data_meta'] = json.get('security_data_meta', False)
        _state['advisories_csaf_meta'] = json.get('advisories_csaf_meta', False)
        _state['security_csaf_meta'] = json.get('security_csaf_meta', False)
        _state['security_txt'] = json.get('security_txt', False)
        _state['directory_listing'] = json.get('directory_listing', False)
        _state['rolie_feed'] = json.get('rolie_feed', False)


def get_config(key: str):
    with _state_lock:
        return _state.get(key, False)


def configure():
    if flask.request.method != 'PATCH':
        flask.abort(405)

    if not flask.request.is_json:
        return flask.jsonify({"error": "expected application/json"}), 400
    body = flask.request.get_json()
    if not isinstance(body, dict):
        return flask.jsonify({"error": "expected JSON object"}), 400
    set_state(body)
    return "Configured server", 200        


def offer_if_enabled(feature_name, return_value):
    with _state_lock:
        offer = _state.get(feature_name, False)
        if not offer:
            flask.abort(404)
    return return_value


def initialize_current_release_dates():
    dates = collect_current_release_dates()
    with _cache_lock:
        _cache['current_release_dates'] = dates


def get_current_release_date(filename: str) -> datetime.datetime | None:
    with _cache_lock:
        dates = _cache['current_release_dates']
        return dates.get(filename)


def get_latest_release_date() -> datetime.datetime | None:
    with _cache_lock:
        dates = _cache['current_release_dates']
        if not dates:
            return None
        return max(dates.values())
