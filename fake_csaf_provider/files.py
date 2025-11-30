import flask
import os

user_home_dir = os.environ.get('HOME') or os.path.expanduser('~')
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
