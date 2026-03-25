import datetime
import flask
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


def find_white_year_dirs():
    path = _csaf_dir / 'white'
    dirs = []
    for entry in path.iterdir():
        if entry.is_dir() and entry.name.isdigit():
            dirs.append(entry.name)
    return dirs


def find_white_advisory_files():
    path = _csaf_dir / 'white'
    files = []
    for year in find_white_year_dirs():
        year_path = path / year
        for entry in year_path.iterdir():
            if entry.is_file() and entry.name.endswith('.json'):
                files.append((year, entry.name))
    return files


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


def collect_current_release_dates() -> dict[(str, str), datetime.datetime]:
    dates = {}
    for year, filename in find_white_advisory_files():
        path = _csaf_dir / 'white' / year / filename
        try:
            date = read_current_release_date(path)
            dates[(year, filename)] = date
        except ValueError:
            continue
    return dates


def read_csaf_id(year: str, file: str) -> str:
    path = _csaf_dir / 'white' / year / file
    with path.open('r', encoding='utf-8') as f:
        csaf = f.read()
    csaf_json = json.loads(csaf)
    return csaf_json.get("document", {}).get("tracking", {}).get("id", "")