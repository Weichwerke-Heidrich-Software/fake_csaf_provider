import datetime
import flask
import json as json_module
import threading

from .files import collect_current_release_dates, read_available_tlp_levels, refresh_csaf_dir


_state = {
    'well_known_meta': False,
    'security_data_meta': False,
    'advisories_csaf_meta': False,
    'security_csaf_meta': False,
    'security_txt': False,
    'directory_listing': False,
    'rolie_feed': False,
    'openpgp': False,
    'sha256': False,
    'sha512': False,
    'rate_limit_requests': 0,
    'rate_limit_period_seconds': 0,
}
_state_lock = threading.Lock()


_cache = {
    'current_release_dates': {},
    'available_tlp_labels': [],
}
_cache_lock = threading.Lock()


_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()


def set_state(json: dict):
    with _state_lock:
        _state['well_known_meta'] = json.get('well_known_meta', False)
        _state['security_data_meta'] = json.get('security_data_meta', False)
        _state['advisories_csaf_meta'] = json.get('advisories_csaf_meta', False)
        _state['security_csaf_meta'] = json.get('security_csaf_meta', False)
        _state['well_known_security_txt'] = json.get('well_known_security_txt', False)
        _state['root_security_txt'] = json.get('root_security_txt', False)
        _state['directory_listing'] = json.get('directory_listing', False)
        _state['rolie_feed'] = json.get('rolie_feed', False)
        _state['openpgp'] = json.get('openpgp', False)
        _state['sha256'] = json.get('sha256', False)
        _state['sha512'] = json.get('sha512', False)
        _state['rate_limit_requests'] = json.get('rate_limit_requests', 0)
        _state['rate_limit_period_seconds'] = json.get('rate_limit_period_seconds', 0)
        flask.current_app.logger.info(f'State updated:\n{json_module.dumps(_state, indent=2)}')

    with _rate_limit_lock:
        _rate_limit_store.clear()

def get_config(key: str):
    with _state_lock:
        return _state.get(key, False)


def configure():
    if flask.request.method != 'PATCH':
        flask.abort(405)

    if not flask.request.is_json:
        return flask.jsonify({'error': 'expected application/json'}), 400
    body = flask.request.get_json()
    if not isinstance(body, dict):
        return flask.jsonify({'error': 'expected JSON object'}), 400
    set_state(body)
    
    refresh_csaf_dir()
    refresh_available_tlp_labels()
    refresh_current_release_dates()
    
    return 'Configured server.', 200


def offer_if_enabled(feature_name, return_value):
    with _state_lock:
        offer = _state.get(feature_name, False)
        if not offer:
            flask.abort(404)
    return return_value


def refresh_available_tlp_labels():
    """Refresh the available TLP labels cache."""
    with _cache_lock:
        _cache['available_tlp_labels'] = read_available_tlp_levels()
        flask.current_app.logger.info(f'Available TLP labels: {_cache["available_tlp_labels"]}')


def refresh_current_release_dates():
    """Refresh release dates cache for all TLP levels."""
    with _cache_lock:
        _cache['current_release_dates'].clear()
        available_tlps = _cache.get('available_tlp_labels', [])
        for tlp in available_tlps:
            dates = collect_current_release_dates(tlp)
            _cache['current_release_dates'][tlp] = dates
        flask.current_app.logger.info('Refreshed document release dates cache.')


def get_current_release_date(year: str, filename: str, tlp: str) -> datetime.datetime | None:
    """Get the release date for a specific file in a TLP level."""
    with _cache_lock:
        tlp_dates = _cache['current_release_dates'].get(tlp, {})
        if not tlp_dates:
            return None
        return tlp_dates.get((year, filename))


def get_sorted_release_dates(tlp: str) -> dict[(str, str), datetime.datetime]:
    """Get sorted release dates for a specific TLP level."""
    sorted_dates = {}
    with _cache_lock:
        tlp_dates = _cache['current_release_dates'].get(tlp, {})
        if not tlp_dates:
            return sorted_dates
        sorted_list = sorted(tlp_dates.items(), key=lambda item: item[1], reverse=True)
        return sorted_list


def get_latest_release_date(tlp: str) -> datetime.datetime | None:
    """Get the latest release date for a specific TLP level."""
    with _cache_lock:
        tlp_dates = _cache['current_release_dates'].get(tlp, {})
        if not tlp_dates:
            return None
        return max(tlp_dates.values())


def get_available_tlp_levels() -> list[str]:
    """Get the cached available TLP labels."""
    with _cache_lock:
        return _cache.get('available_tlp_labels', []).copy()


def log_request(remote_addr: str):
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    with _rate_limit_lock:
        timestamps = _rate_limit_store.setdefault(remote_addr, [])
        timestamps.append(now)


def rate_limit_headers(remote_addr: str) -> dict[str, str]:
    with _state_lock:
        limit = int(_state.get('rate_limit_requests', 0))
        period = int(_state.get('rate_limit_period_seconds', 0))
    enabled = limit > 0 and period > 0

    headers = {}
    if not enabled:
        return headers

    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    cutoff = now - period

    with _rate_limit_lock:
        timestamps = _rate_limit_store.setdefault(remote_addr, [])
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        remaining = max(0, limit - len(timestamps))
        headers['X-RateLimit-Limit'] = str(limit)
        headers['X-RateLimit-Remaining'] = str(remaining)
        if timestamps:
            reset_time = timestamps[0] + period
            headers['X-RateLimit-Reset'] = str(int(reset_time))
        else:
            headers['X-RateLimit-Reset'] = str(int(now + period))
    return headers


def get_retry_after_seconds() -> int:
    with _state_lock:
        period = int(_state.get('rate_limit_period_seconds', 0))
    return period

