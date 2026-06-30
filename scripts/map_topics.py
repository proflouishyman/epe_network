#!/usr/bin/env python3
"""
map_topics.py — Fetch each scholar's personal page and map research interests
to the canonical topic taxonomy in data/topics.json.

Writes updated topics_current into data/individuals.json.
Run: python3 scripts/map_topics.py
"""

import json, re, unicodedata, urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path

ROOT    = Path(__file__).parent.parent
INDS    = ROOT / 'data' / 'individuals.json'
TOPICS  = ROOT / 'data' / 'topics.json'
TODAY   = '2026-06-30'
TIMEOUT = 12

# ── Load taxonomy ──────────────────────────────────────────────────────────────
taxonomy = json.loads(TOPICS.read_text())
LABEL_LIST = [t['label'] for t in taxonomy]

# Keyword → canonical topic IDs (checked against page text + titles)
KEYWORD_MAP = [
    # patterns are lowercase substrings or regex
    (r'\blabor market|employment\b|wages?\b|job polariz',    'Labor Markets & Employment'),
    (r'\bunion|collective bargain|labor organiz',             'Labor, Unions & Collective Action'),
    (r'\bfuture of work|automation.{0,20}work|gig economy',  'Future of Work & Automation'),
    (r'\bmigration\b|immigrant|emigration|labor mobility',    'Migration & Labor'),
    (r'\bindustrial polic|structural transformation',         'Industrial Policy & Structural Transformation'),
    (r'\bglobal south|developing countr|development econ',    'Economic Development'),
    (r'\bglobal south political|post.?colonial|decolonial',   'Global South Political Economy'),
    (r'\bstate.market|state capacity|regulation',             'State & Markets'),
    (r'\btrade\b|globalization|global value chain|export',    'Trade & Globalization'),
    (r'\binnovation polic|science polic|r&d\b|research and development', 'Innovation Policy'),
    (r'\bdigital economy|platform labor|gig\b|platform work', 'Digital Economy & Platform Labor'),
    (r'\bartificial intelligence|machine learning|ai\b.{0,15}econom|automation.{0,20}technolog', 'AI, Automation & Technology'),
    (r'\bmacroeconom|monetary polic|central bank|inflation\b', 'Macroeconomics & Monetary Policy'),
    (r'\bpublic financ|fiscal polic|taxation|tax polic',      'Public Finance & Fiscal Policy'),
    (r'\bfinance\b|banking\b|credit\b|financializ',           'Finance, Banking & Credit'),
    (r'\bfinancial regulation|financial stability',            'Financial Regulation'),
    (r'\bclimate\b|green transition|decarboniz|net.?zero',    'Climate & Green Transition'),
    (r'\benvironmental econ|natural resource|pollution\b',    'Environmental Economics'),
    (r'\benergy polic|renewable energy|energy transition',    'Energy Policy'),
    (r'\bdemocracy\b|governance\b|democratic institution',    'Democracy & Governance'),
    (r'\bpublic polic|policy analysis|welfare state',         'Public Policy'),
    (r'\bpolitical institution|comparative politics|electoral', 'Political Institutions'),
    (r'\beconomic history|history of capitalism|historical',  'Economic History'),
    (r'\blaw and political economy|law & political|legal',    'Law & Political Economy'),
    (r'\binequality\b|redistribution|income distribution',    'Inequality'),
    (r'\brace\b|racial|ethnic|racism\b',                      'Race, Ethnicity & Economic Inequality'),
    (r'\bgender\b|feminist|women.{0,10}econom|care economy',  'Gender & the Economy'),
    (r'\bhealth econom|health polic|public health',           'Health Economics'),
    (r'\beducation econom|school\b|human capital',            'Education Economics'),
    (r'\blatin america|brazil|mexico|colombia|argentina',     'Latin America'),
    (r'\bsouth asia|india\b|pakistan\b|bangladesh\b',         'South Asia'),
    (r'\bpolitical economy\b|political economist',            'Political Economy'),
    (r'\binstitutional econ|institutions and\b',              'Institutional Economics'),
    (r'\bcomparative capitalism|varieties of capitalism',     'Comparative Capitalism'),
    (r'\beconomic sociology|sociology of econ',               'Economic Sociology'),
]

# Compile patterns
COMPILED = [(re.compile(pat, re.I), label) for pat, label in KEYWORD_MAP]


class TextExtractor(HTMLParser):
    """Simple HTML → text extractor."""
    def __init__(self):
        super().__init__()
        self._skip = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'footer', 'head'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'footer', 'head'):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.chunks.append(data)

    def get_text(self):
        return ' '.join(self.chunks)


def fetch_text(url):
    if not url.startswith('http'):
        url = 'https://' + url
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read(80_000).decode('utf-8', errors='replace')
        p = TextExtractor()
        p.feed(raw)
        return p.get_text()
    except Exception:
        return ''


def map_topics(text, title=''):
    combined = (title + ' ' + text).lower()
    found = []
    for pattern, label in COMPILED:
        if pattern.search(combined):
            found.append(label)
    # Deduplicate preserving order
    seen = set()
    result = []
    for label in found:
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result[:8]  # cap at 8


def main():
    inds = json.loads(INDS.read_text())
    total = 0

    for i, ind in enumerate(inds):
        if ind.get('topics_current'):
            continue  # already mapped — don't overwrite richer existing data
        url = ind.get('website', '')
        if not url or '/pesquisadores/' in url:
            continue
        title = ind.get('title', '')
        print(f'[{i+1}] {ind["name"]} — fetching {url[:60]}…', end=' ', flush=True)
        text = fetch_text(url)
        if not text.strip():
            print('no content')
            continue
        topics = map_topics(text, title)
        if topics:
            ind['topics_current'] = topics
            total += 1
            print(f'{len(topics)} topics: {topics[:3]}')
        else:
            # Fallback: map from title alone
            fallback = map_topics('', title)
            if fallback:
                ind['topics_current'] = fallback
                total += 1
                print(f'title-only: {fallback[:3]}')
            else:
                print('none found')

    INDS.write_text(json.dumps(inds, indent=2, ensure_ascii=False) + '\n')
    print(f'\nDone. Wrote topics for {total} scholars.')


if __name__ == '__main__':
    main()
