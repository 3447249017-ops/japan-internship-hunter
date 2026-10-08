#!/usr/bin/env python3
"""Find publicly indexed internship leads via Google News RSS. No API key required."""
import csv
import datetime as dt
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

QUERIES = [
    'インターン 留学生 東京 募集',
    '2027卒 インターン 外資系 東京',
    '長期インターン 横浜 マーケティング',
    'インターンシップ コンサルティング 東京 応募',
    'internship Japan international students business',
]
KEYWORDS = {'留学生': 5, '外国人': 4, 'international': 4, 'インターン': 3,
            'internship': 3, '東京': 2, '横浜': 2, 'マーケティング': 2,
            'コンサル': 2, '英語': 2, '募集': 1, '採用': 1}
OUTPUT = Path(__file__).parent / 'output' / 'internship_leads.csv'

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s or ''))).strip()

def collect():
    out, seen = [], set()
    for query in QUERIES:
        qs = urllib.parse.urlencode({'q': query, 'hl': 'ja', 'gl': 'JP', 'ceid': 'JP:ja'})
        url = 'https://news.google.com/rss/search?' + qs
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (educational project)'})
            with urllib.request.urlopen(request, timeout=20) as response:
                root = ET.fromstring(response.read())
        except (OSError, ET.ParseError) as e:
            print(f'[WARN] Could not fetch {query}: {e}')
            continue
        for item in root.findall('./channel/item'):
            title = clean(item.findtext('title'))
            link = (item.findtext('link') or '').strip()
            source = clean(item.findtext('source'))
            pub = (item.findtext('pubDate') or '').strip()
            key = title.casefold()
            if not title or not link or key in seen:
                continue
            seen.add(key)
            text = (title + ' ' + clean(item.findtext('description'))).casefold()
            score = sum(points for word, points in KEYWORDS.items() if word.casefold() in text)
            out.append({'score': score, 'title': title, 'source': source,
                        'published': pub, 'url': link, 'matched_query': query,
                        'verification': '未核实：请打开原始招聘页面确认截止日期及资格'})
    return sorted(out, key=lambda row: (-row['score'], row['title']))

def main():
    rows = collect()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    columns = ['score', 'title', 'source', 'published', 'url', 'matched_query', 'verification']
    with OUTPUT.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f'{dt.datetime.now().isoformat(timespec="seconds")}: {len(rows)} leads -> {OUTPUT}')
    if not rows:
        print('No results retrieved. Check network access, RSS availability, or query terms.')

if __name__ == '__main__':
    main()
