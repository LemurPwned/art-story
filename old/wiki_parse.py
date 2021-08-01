import glob
import os


import mwparserfromhell
import requests
import ujson as json
from tqdm import tqdm

session = requests.Session()

forbidden_words = ['thumb|', 'left|', 'right|',
                   'References', 'Category:', 'External links', 'See also', 'Relating to']
URL = "https://en.wikipedia.org/w/api.php"


def request_wiki_page(title):
    params = {
        'action': "query",
        'titles': title,
        'format': "json",
        'prop': 'revisions',
        'rvprop': 'content',
    }
    response = session.get(url=URL, params=params)
    response = response.json()
    page = next(iter(response['query']['pages'].values()))
    wikicode = page['revisions'][0]['*']
    parsed_wikicode = mwparserfromhell.parse(wikicode)
    text = purify(parsed_wikicode.strip_code())
    return text


def purify(wiki_text):
    """
    Remove unwanted stuff from our wiki page.
    """
    new_text = []
    for line in wiki_text.split('\n'):
        if line == '':
            continue
        contains = False
        for character in forbidden_words:
            if character in line:
                contains = True
                break
        if not contains:
            new_text.append(line)
    return '\n'.join(new_text)


def parse_author_notes(source: str):
    """ 
    Parse a list of authors from the WikiArt download
    """
    authors = json.load(open(source, 'r'))
    authors_text = {}
    author_count = 0
    failed = 0
    for author in tqdm(authors):
        complete = True
        for key in ['artistName',  'image', 'wikipediaUrl']:
            if (key not in author) or (author[key] is None):
                complete = False
        if not complete:
            continue

        query = '_'.join(author['artistName'].split(' '))
        try:
            wiki_page = request_wiki_page(query)
        except KeyError:
            failed += 1
            continue
        author_note = {
            'name': author['artistName'],
            'birth': author['birthDayAsString'],
            'death': author['deathDayAsString'],
            'image': author['image'],
            'note': wiki_page
        }
        authors_text[author['artistName']] = author_note
        author_count += 1

        # save the json file
        if (author_count % 500 == 0) and (author_count > 0):
            json.dump(authors_text, open(f'Authors_{author_count}.json', 'w'))

    json.dump(authors_text, open(f'Authors_{author_count}.json', 'w'))
    print(f"Failed to parse: {failed}/{len(authors)}")


def parse_tag_notes(source):
    tags = json.load(open(source, 'r')).keys()
    wiki_text = []
    for tag in tags:
        print(f"Parsing tag: {tag}")
        query = '_'.join(tag.split(' '))
        try:
            tag_note = request_wiki_page(query)
            wiki_text += tag_note
        except KeyError:
            print("\tFailed to parse...")
    with open('tag_long_text.txt', 'w') as f:
        # for txt in wiki_text:
        f.writelines(wiki_text)


def normalise_name(x):
    x = x.strip()
    for sym in ('!', '.', ',', '\\', '/', ':', ';', '\'',
                '"', '$', '(', ')', '[', ']'):
        x = x.replace(sym, "")

    x = x.split(" ")
    return "_".join(x)


def parse_images(authors: str, img_folder: str):
    failed = 0
    all_authors = glob.glob(os.path.join(authors, "*.json"))
    for author in tqdm(all_authors):
        author_json = json.load(open(author, "r"))
        absn = os.path.basename(author).replace(".json", "")
        apath = os.path.join(img_folder, absn)
        os.makedirs(apath, exist_ok=True)
        for painting in author_json:
            if (not 'image' in painting) or (not 'title' in painting):
                continue
            pname = normalise_name(painting['title'])
            pname += ".jpg"
            fn = os.path.join(apath, pname)
            if os.path.isfile(fn):
                continue
            try:
                r = requests.get(painting['image'], stream=True)
                if r.status_code in (200, 202):
                    with open(fn, 'wb') as f:
                        f.write(r.content)
            except:
                failed += 1

    print(f"Failed {failed} images")


if __name__ == "__main__":
    # parse_author_notes("artists.json")
    parse_images(authors='/Users/jm/data/wikiart/meta',
                 img_folder='/Users/jm/data/wikiart/images/')
