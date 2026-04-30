import csv
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = 'https://ferbi.com.ar'
CATEGORY_URLS = [
    'https://ferbi.com.ar/shop/category/celulares-38',
    'https://ferbi.com.ar/shop/category/celulares-38/page/2',
]

OUT_DIR = Path(__file__).resolve().parent / 'dataset'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / 'ferbi_celulares_modelos.csv'

def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()


def norm(text: str) -> str:
    x = clean(text).lower()
    return ''.join(c for c in unicodedata.normalize('NFKD', x) if not unicodedata.combining(c))


def fetch_soup(session: requests.Session, url: str) -> BeautifulSoup:
    html = session.get(url, timeout=30).text
    return BeautifulSoup(html, 'html.parser')


def parse_listing(session: requests.Session, url: str):
    soup = fetch_soup(session, url)
    found = []
    seen = set()
    for a in soup.select('a[itemprop="url"][href^="/shop/"]'):
        full = urljoin(BASE, a.get('href', ''))
        if '/shop/category/' in full or full in seen:
            continue
        seen.add(full)
        found.append((full, url))
    return found


def parse_product(session: requests.Session, url: str):
    soup = fetch_soup(session, url)
    name_node = soup.select_one('h1[itemprop="name"], a[itemprop="name"], h1')
    phone_name = clean(name_node.get_text()) if name_node else clean((soup.title.get_text() if soup.title else '').replace('| Ferbi', ''))

    attrs = {}
    for li in soup.select('li.variant_attribute'):
        attr_name = clean(li.get('data-attribute_name', ''))
        values = [
            clean(i.get('data-value_name', ''))
            for i in li.select('input.js_variant_change')
            if clean(i.get('data-value_name', ''))
        ]
        if attr_name and values:
            attrs[attr_name] = list(dict.fromkeys(values))

    price_text = ''
    price_node = soup.select_one('span.oe_price .oe_currency_value, .oe_price .oe_currency_value')
    if price_node:
        price_text = clean(price_node.get_text())
        if price_text and not price_text.startswith('$'):
            price_text = f'$ {price_text}'

    return phone_name, attrs, price_text


def pick_attr(attrs: dict, key_type: str):
    for k, v in attrs.items():
        nk = norm(k)
        if key_type == 'condition' and nk == 'condicion del equipo':
            return v
        if key_type == 'color' and nk == 'color':
            return v
        if key_type == 'memory' and 'memoria interna' in nk:
            return v
        if key_type == 'brand' and nk == 'marca':
            return v
    return []


def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    listing_rows = []
    for category_url in CATEGORY_URLS:
        listing_rows.extend(parse_listing(session, category_url))

    unique_products = {}
    for product_url, listing_url in listing_rows:
        unique_products[product_url] = listing_url

    scraped_at = datetime.now(timezone.utc).isoformat()
    rows = []

    for product_url, listing_url in unique_products.items():
        phone_name, attrs, price_text = parse_product(session, product_url)
        phone_id_match = re.search(r'-(\d+)(?:\?|$)', product_url)
        phone_id = phone_id_match.group(1) if phone_id_match else ''

        conditions = pick_attr(attrs, 'condition')
        colors = pick_attr(attrs, 'color')
        memories = pick_attr(attrs, 'memory')
        brands = pick_attr(attrs, 'brand')

        rows.append({
            'brand_slug': 'ferbi',
            'brand_id': 'ferbi',
            'phone_id': phone_id,
            'phone_name': phone_name,
            'phone_url': product_url,
            'image_url': '',
            'listing_page_url': listing_url,
            'scraped_at_utc': scraped_at,
            'status': '|'.join(conditions),
            'storage_options_gb': '|'.join(memories),
            'price_text': price_text,
            'price_currency': 'ARS',
            'ferbi_colores': '|'.join(colors),
            'ferbi_marcas': '|'.join(brands),
            'ferbi_attributes_json': json.dumps(attrs, ensure_ascii=False),
        })

    rows.sort(key=lambda r: (r['phone_name'], r['phone_id']))

    fieldnames = list(rows[0].keys()) if rows else []
    with OUT_CSV.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'products={len(rows)}')
    print(str(OUT_CSV))


if __name__ == '__main__':
    main()
