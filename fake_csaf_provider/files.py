import datetime
import flask
import hashlib
import json
import pgpy

from pathlib import Path


def find_csaf_dir():
    current_dir = Path(__file__).resolve().parent
    csaf_dir = current_dir / 'csafs'
    if not csaf_dir.is_dir():
        csaf_dir = current_dir.parent / 'csafs'
    if not csaf_dir.is_dir():
        raise FileNotFoundError("Could not find 'csafs' directory")
    print(f"Using CSAF directory: {csaf_dir}")
    return csaf_dir


_csaf_dir = find_csaf_dir()


def find_year_dirs(tlp):
    """Find year directories for a given TLP level."""
    path = _csaf_dir / tlp
    dirs = []
    if not path.is_dir():
        return dirs
    for entry in path.iterdir():
        if entry.is_dir() and entry.name.isdigit():
            dirs.append(entry.name)
    return dirs


def find_advisory_files(tlp):
    """Find advisory files for a given TLP level."""
    path = _csaf_dir / tlp
    files = []
    if not path.is_dir():
        return files
    for year in find_year_dirs(tlp):
        year_path = path / year
        for entry in year_path.iterdir():
            if entry.is_file() and entry.name.endswith('.json'):
                files.append((year, entry.name))
    return files


def get_available_tlp_levels():
    """Return list of TLP directories that exist in the csafs directory."""
    levels = []
    for tlp in ['white', 'clear', 'green', 'amber', 'amber+strict', 'red', 'unlabeled']:
        if (_csaf_dir / tlp).is_dir():
            levels.append(tlp)
    return levels


def csaf_file_exists(tlp, year, filename):
    path = _csaf_dir / tlp / year / filename
    return path.is_file()


def _load_private_key():
    project_root = Path(__file__).resolve().parents[1]
    key_path = project_root / "crypto" / "openpgp.key.asc"
    
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found at {key_path}")
    
    key_text = key_path.read_text()
    private_key, _ = pgpy.PGPKey.from_blob(key_text)
    return private_key


def _create_signature(json_path: Path) -> str:
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found at {json_path}")
    
    private_key = _load_private_key()
    json_content = json_path.read_text()
    signature = private_key.sign(json_content)
    return str(signature)


def _create_hash(json_path: Path, algorithm: str) -> str:
    """Create a hash of the JSON file using the specified algorithm (sha256 or sha512)."""
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found at {json_path}")
    
    json_content = json_path.read_bytes()
    
    if algorithm == 'sha256':
        hash_obj = hashlib.sha256(json_content)
    elif algorithm == 'sha512':
        hash_obj = hashlib.sha512(json_content)
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    hash_hex = hash_obj.hexdigest()
    filename = json_path.name
    return f"{hash_hex}  {filename}\n"


def send_csaf(tlp, year, filename):
    if filename.endswith('.asc'):
        # Remove the .asc extension to get the JSON filename
        json_filename = filename[:-4]
        json_path = _csaf_dir / tlp / year / json_filename
        
        if not json_path.is_file():
            flask.abort(404, description="CSAF file not found")
        
        try:
            signature = _create_signature(json_path)
            response = flask.Response(signature, mimetype='application/pgp-signature')
            return response
        except Exception as e:
            flask.abort(500, description=f"Failed to create signature: {str(e)}")
    
    if filename.endswith('.sha256'):
        # Remove the .sha256 extension to get the JSON filename
        json_filename = filename[:-7]
        json_path = _csaf_dir / tlp / year / json_filename
        
        if not json_path.is_file():
            flask.abort(404, description="CSAF file not found")
        
        try:
            hash_content = _create_hash(json_path, 'sha256')
            response = flask.Response(hash_content, mimetype='text/plain')
            return response
        except Exception as e:
            flask.abort(500, description=f"Failed to create SHA-256 hash: {str(e)}")
    
    if filename.endswith('.sha512'):
        # Remove the .sha512 extension to get the JSON filename
        json_filename = filename[:-7]
        json_path = _csaf_dir / tlp / year / json_filename
        
        if not json_path.is_file():
            flask.abort(404, description="CSAF file not found")
        
        try:
            hash_content = _create_hash(json_path, 'sha512')
            response = flask.Response(hash_content, mimetype='text/plain')
            return response
        except Exception as e:
            flask.abort(500, description=f"Failed to create SHA-512 hash: {str(e)}")
    
    # Handle regular JSON file requests
    path = _csaf_dir / tlp / year / filename
    if not path.is_file():
        flask.abort(404, description="CSAF file not found")
    return flask.send_file(str(path), mimetype='application/json')


def read_current_release_date(path: str) -> datetime.datetime:
    p = Path(path)
    with p.open('r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        datestring = data['document']['tracking']['current_release_date']
        return datetime.datetime.fromisoformat(datestring.replace('Z', '+00:00'))
    except (KeyError, TypeError) as err:
        raise ValueError("current_release_date not found in JSON") from err


def collect_current_release_dates(tlp) -> dict[(str, str), datetime.datetime]:
    """Collect release dates for advisories of a given TLP level."""
    dates = {}
    for year, filename in find_advisory_files(tlp):
        path = _csaf_dir / tlp / year / filename
        try:
            date = read_current_release_date(path)
            dates[(year, filename)] = date
        except ValueError:
            continue
    return dates


def read_csaf_id(year: str, file: str, tlp) -> str:
    """Read the CSAF ID from a document."""
    path = _csaf_dir / tlp / year / file
    with path.open('r', encoding='utf-8') as f:
        csaf = f.read()
    csaf_json = json.loads(csaf)
    return csaf_json.get("document", {}).get("tracking", {}).get("id", "")