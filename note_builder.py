import yaml
from pyzotero import zotero
from pathlib import Path
from tqdm import tqdm

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Set global values
ZOTERO_STORAGE = Path(config['ZOTERO_STORAGE'])
OBS_VAULT = Path(config['OBS_VAULT'])
PDF_FOLDER = OBS_VAULT / Path(config['PDF_FOLDER'])
NOTE_FOLDER = OBS_VAULT / Path(config['NOTE_FOLDER'])
TEMPLATE_PATH = Path(config['TEMPLATE_PATH'])

API_KEY = Path(config['API_KEY'])
LIBRARY_ID = Path(config['LIBRARY_ID'])
LIBRARY_TYPE = Path(config['LIBRARY_TYPE'])


def load_zot():
    zot = zotero.Zotero(
        library_id=LIBRARY_ID,
        library_type=LIBRARY_TYPE,
        api_key=API_KEY
    )
    return zot

def create_symlink(
        source_path: Path,
        dest_path: Path
):
    if not dest_path.exists():
        dest_path.symlink_to(source_path)


def get_authors(
        authors: list[dict]
):
    names = []
    for author in authors:
        if 'name' in author:    
            # For items like reports/organizations
            names.append(author['name'])
        else:
            first = author.get('firstName', '')
            last = author.get('lastName', '')
            names.append(f"{first} {last}".strip())
    authors_yaml = "[" + ", ".join(f'"{author}"' for author in names) + "]"
    
    return authors_yaml


def create_note(
        note_path: Path,
        template_path: Path,
        metadata: dict
):
    template = template_path.read_text()
    note_content = template.format(**metadata)
    note_path.write_text(note_content)


def get_metadata(
        item: dict
):
    return {
        'key' : item['key'],
        'title' : item['data'].get('title', ''),
        'url' : item['data'].get('url', ''),
        'authors' : get_authors(item['data']['creators']),
        'year' : item['data'].get('date', 'Unknown'),
    }

def get_file_path(
        zot: zotero.Zotero,
        key: str
):
    child = zot.children(key)[0]
    storage_key = child['data'].get('key')
    file_name = child['data'].get('filename')
    pdf_file_path = ZOTERO_STORAGE / storage_key / file_name

    return pdf_file_path


def add_to_vault(
        pdf_file_path: Path,
        metadata: dict
):
    if pdf_file_path.exists():
        # Create symlink
        title = metadata['title']
        safe_title = "".join(c if c.isalnum() else "_" for c in title)
        link_path = PDF_FOLDER / f'{safe_title}.pdf'
        if not link_path.exists():
            create_symlink(pdf_file_path, link_path)

        # Make note for the paper
        note_path = NOTE_FOLDER / f'{title}.md'
        metadata['pdf_link'] = f'[[Papers/{safe_title}.pdf]]'
        del metadata['key']
        if note_path.exists():
            create_note(
                note_path,
                TEMPLATE_PATH,
                metadata
            )
    else:
        print(f"No PDF found for {title}")


def main():
    # Load Zotero vault
    zot = load_zot()
    items = zot.everything(zot.top(limit=1000))

    # Add PDFs
    for item in tqdm(items, total=len(items)):
        metadata = get_metadata(item)
        file_path = get_file_path(zot, metadata['key'])
        add_to_vault(file_path, metadata)


if __name__ == '__main__':
    main()