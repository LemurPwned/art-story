import json
import requests
import mwparserfromhell
from lxml import html
import pickle
import os
session = requests.Session()

forbidden_words = ['thumb|', 'left|', 'right|',
                   'References', 'Category:', 'External links', 'See also', 'Relating to']
URL = "https://en.wikipedia.org/w/api.php"

directory = 'artist_notes'


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


def parse_author_notes(source):
    authors = json.load(open(source, 'r'))
    authors_text = {'authors': []}
    author_count = 0
    wiki_text = []
    for author in authors:
        complete = True
        for key in ['artistName',  'image', 'wikipediaUrl']:
            if (key not in author) or (author[key] is None):
                complete = False
        if not complete:
            continue
        # if (author_count % 500 == 0) and (author_count > 0):
        #     json.dump(authors_text, open(os.path.join(
        #         directory, f'Authors_{author_count}'), 'w'))
        #     authors_text = {'authors': []}
        query = '_'.join(author['artistName'].split(' '))
        print(
            f"Processing {author_count}: {author['artistName']} with query {query}...")
        try:
            wiki_page = request_wiki_page(query)
        except KeyError:
            print(f"\tFailed to parse...")
            continue
        author_note = {
            'name': author['artistName'],
            'birth': author['birthDayAsString'],
            'death': author['deathDayAsString'],
            'image': author['image'],
            'note': wiki_page
        }
        # authors_text['authors'].append(author_note)
        author_count += 1
        wiki_text += wiki_page
    json.dump(authors_text, open(os.path.join(
        directory, f'Authors_{author_count}'), 'w'))
    with open('long_text.txt', 'w') as f:
        # for txt in wiki_text:
        f.writelines(wiki_text)


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

# parse_author_notes('artists.json')
parse_tag_notes('tags.json')