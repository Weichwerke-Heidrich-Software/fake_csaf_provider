import datetime
import flask
import json
from pathlib import Path


def find_csaf_dir():
    current_dir = Path(__file__).resolve().parent
    csaf_dir = current_dir / 'csafs' / 'some'
    if not csaf_dir.is_dir():
        csaf_dir = current_dir.parent / 'csafs' / 'some'
    if not csaf_dir.is_dir():
        raise FileNotFoundError("Could not find 'csafs/some' directory")
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


def send_csaf(tlp, year, filename):
    path = _csaf_dir / tlp / year / filename
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