from .state import get_sorted_release_dates, get_config

def index_txt(tlp):
    """Generate index.txt for a specific TLP level."""
    filenames = []
    openpgp_enabled = get_config('openpgp')
    
    for (year, file), _ in get_sorted_release_dates(tlp):
        filenames.append(f'{year}/{file}')
        if openpgp_enabled and file.endswith('.json'):
            filenames.append(f'{year}/{file}.asc')
    
    content = '\n'.join(filenames) + '\n'
    return content

def changes_csv(tlp):
    """Generate changes.csv for a specific TLP level."""
    lines = []
    openpgp_enabled = get_config('openpgp')
    
    for (year, filename), date in get_sorted_release_dates(tlp):
        date_str = date.replace(microsecond=0).isoformat()
        lines.append(f'"{year}/{filename}","{date_str}"')
        if openpgp_enabled and filename.endswith('.json'):
            lines.append(f'"{year}/{filename}.asc","{date_str}"')
    
    content = '\n'.join(lines) + '\n'
    return content
