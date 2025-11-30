from .state import get_sorted_release_dates

def index_txt():
    filenames = [f'{year}/{file}' for (year, file), _ in get_sorted_release_dates()]
    content = '\n'.join(filenames) + '\n'
    return content

def changes_csv():
    lines = []
    for (year, filename), date in get_sorted_release_dates():
        date_str = date.replace(microsecond=0).isoformat()
        lines.append(f'"{year}/{filename}","{date_str}"')
    content = '\n'.join(lines) + '\n'
    return content
