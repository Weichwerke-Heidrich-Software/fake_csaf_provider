import datetime
import flask
import json
import os

csaf_dir = os.path.join('csafs', 'some')


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


def send_csaf(tlp, year, filename):
    path = os.path.join(csaf_dir, tlp, year, filename)
    return flask.send_file(path, mimetype='application/json')


def read_current_release_date(path: str) -> datetime.datetime:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        datestring = data['document']['tracking']['current_release_date']
        return datetime.datetime.fromisoformat(datestring.replace('Z', '+00:00'))
    except (KeyError, TypeError) as err:
        raise ValueError("current_release_date not found in JSON") from err


def collect_current_release_dates() -> dict[str, datetime.datetime]:
    dates = {}
    for year, filename in find_white_advisory_files():
        path = os.path.join(csaf_dir, 'white', year, filename)
        try:
            date = read_current_release_date(path)
            dates[filename] = date
        except ValueError:
            continue
    return dates
