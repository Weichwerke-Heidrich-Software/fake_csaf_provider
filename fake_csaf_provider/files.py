import datetime
import flask
import hashlib
import json
import pgpy

from pathlib import Path


_csaf_dir = None


def refresh_csaf_dir():
    """Refresh the CSAF directory by evaluating find_csaf_dir()."""
    global _csaf_dir
    current_dir = Path(__file__).resolve().parent
    csaf_dir = current_dir / 'csafs'
    if not csaf_dir.is_dir():
        csaf_dir = current_dir.parent / 'csafs'
    if not csaf_dir.is_dir():
        raise FileNotFoundError("Could not find 'csafs' directory")
    flask.current_app.logger.info(f'Using CSAF directory: {csaf_dir}')
    _csaf_dir = csaf_dir


def get_csaf_dir():
    """Get the CSAF directory, raising an error if not set."""
    if _csaf_dir is None:
        raise RuntimeError("CSAF directory not initialized. Call /config endpoint first.")
    return _csaf_dir


def find_year_dirs(tlp):
    """Find year directories for a given TLP level."""
    path = get_csaf_dir() / tlp
    dirs = []
    if not path.is_dir():
        return dirs
    for entry in path.iterdir():
        if entry.is_dir() and entry.name.isdigit():
            dirs.append(entry.name)
    return dirs


def find_advisory_files(tlp):
    """Find advisory files for a given TLP level."""
    path = get_csaf_dir() / tlp
    files = []
    if not path.is_dir():
        return files
    for year in find_year_dirs(tlp):
        year_path = path / year
        for entry in year_path.iterdir():
            if entry.is_file() and entry.name.endswith('.json'):
                files.append((year, entry.name))
    return files


def read_available_tlp_levels():
    """Return list of TLP directories that exist in the csafs directory."""
    levels = []
    csaf_dir = get_csaf_dir()
    for tlp in ['white', 'clear', 'green', 'amber', 'amber+strict', 'red', 'unlabeled']:
        if (csaf_dir / tlp).is_dir():
            levels.append(tlp)
    return levels


def csaf_file_exists(tlp, year, filename):
    path = get_csaf_dir() / tlp / year / filename
    return path.is_file()


def _load_private_key():
    project_root = Path(__file__).resolve().parents[1]
    key_path = project_root / 'crypto' / 'openpgp.key.asc'
    
    if not key_path.exists():
        flask.current_app.logger.error(f'Private key not found at {key_path}')
        raise FileNotFoundError(f'Private key not found at {key_path}')
    
    key_text = key_path.read_text()
    private_key, _ = pgpy.PGPKey.from_blob(key_text)
    return private_key


def _create_signature(json_path: Path) -> str:
    if not json_path.exists():
        flask.current_app.logger.error(f'JSON file not found at {json_path}')
        raise FileNotFoundError(f'JSON file not found at {json_path}')
    
    private_key = _load_private_key()
    json_content = json_path.read_text()
    signature = private_key.sign(json_content)
    return str(signature)


def _send_signature(tlp, year, filename):
    # Remove the .asc extension to get the JSON filename
    json_filename = filename[:-4]
    json_path = get_csaf_dir() / tlp / year / json_filename
    
    if not json_path.is_file():
        flask.current_app.logger.error(f'CSAF file not found at {json_path}')
        flask.abort(404, description='CSAF file not found')
    
    try:
        signature = _create_signature(json_path)
        response = flask.Response(signature, mimetype='application/pgp-signature')
        return response
    except Exception as e:
        flask.abort(500, description=f'Failed to create signature: {str(e)}')


def _create_hash(json_path: Path, algorithm: str) -> str:
    """Create a hash of the JSON file using the specified algorithm (sha256 or sha512)."""
    if not json_path.exists():
        flask.current_app.logger.error(f'JSON file not found at {json_path}')
        raise FileNotFoundError(f'JSON file not found at {json_path}')
    
    json_content = json_path.read_bytes()
    
    if algorithm == 'sha256':
        hash_obj = hashlib.sha256(json_content)
    elif algorithm == 'sha512':
        hash_obj = hashlib.sha512(json_content)
    else:
        flask.current_app.logger.error(f'Unsupported hash algorithm: {algorithm}')
        raise ValueError(f'Unsupported hash algorithm: {algorithm}')
    
    hash_hex = hash_obj.hexdigest()
    filename = json_path.name
    return f"{hash_hex}  {filename}\n"


def _send_hash(tlp, year, filename, algorithm: str):
    # Remove the .sha256 / .sha512 extension to get the JSON filename
    json_filename = filename[:-7]
    json_path = get_csaf_dir() / tlp / year / json_filename
    
    if not json_path.is_file():
        flask.abort(404, description='CSAF file not found')
    
    try:
        hash_content = _create_hash(json_path, 'sha256')
        response = flask.Response(hash_content, mimetype='text/plain')
        return response
    except Exception as e:
        flask.abort(500, description=f'Failed to create SHA-256 hash: {str(e)}')


def _send_csaf(tlp, year, filename):
    # Handle regular JSON file requests
    path = get_csaf_dir() / tlp / year / filename
    if not path.is_file():
        flask.abort(404, description='CSAF file not found')
    return flask.send_file(str(path), mimetype='application/json')


def send_doc(tlp, year, filename):
    if filename.endswith('.asc'):
        return _send_signature(tlp, year, filename)
    if filename.endswith('.sha256'):
        return _send_hash(tlp, year, filename, 'sha256')
    if filename.endswith('.sha512'):
        return _send_hash(tlp, year, filename, 'sha512')
    return _send_csaf(tlp, year, filename)


def read_current_release_date(path: str) -> datetime.datetime:
    p = Path(path)
    with p.open('r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        datestring = data['document']['tracking']['current_release_date']
        return datetime.datetime.fromisoformat(datestring.replace('Z', '+00:00'))
    except (KeyError, TypeError) as err:
        flask.current_app.logger.error('current_release_date not found in JSON')
        raise ValueError('current_release_date not found in JSON') from err


def collect_current_release_dates(tlp) -> dict[(str, str), datetime.datetime]:
    """Collect release dates for advisories of a given TLP level."""
    dates = {}
    csaf_dir = get_csaf_dir()
    for year, filename in find_advisory_files(tlp):
        path = csaf_dir / tlp / year / filename
        try:
            date = read_current_release_date(path)
            dates[(year, filename)] = date
        except ValueError:
            continue
    return dates


def read_csaf_id(year: str, file: str, tlp) -> str:
    """Read the CSAF ID from a document."""
    path = get_csaf_dir() / tlp / year / file
    with path.open('r', encoding='utf-8') as f:
        csaf = f.read()
    csaf_json = json.loads(csaf)
    return csaf_json.get('document', {}).get('tracking', {}).get('id', '')