#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiki 접근 테스트"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup

# Dark Souls 3 Wiki 테스트
wiki_url = "https://darksouls3.wiki.fextralife.com"

print(f"Testing: {wiki_url}")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# 메인 페이지 테스트
try:
    resp = session.get(wiki_url, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"URL: {resp.url}")
except Exception as e:
    print(f"Error: {e}")

# Bosses 카테고리 테스트
bosses_url = f"{wiki_url}/Bosses"
print(f"\nTesting: {bosses_url}")

try:
    resp = session.get(bosses_url, timeout=10)
    print(f"Status: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")

    # 링크 찾기
    links = []
    for a in soup.select("#wiki-content-block a, #article-body a, .infobox a"):
        href = a.get("href", "")
        if href and not href.startswith("#") and "/wiki/" not in href:
            continue
        if href:
            links.append(href)

    print(f"Found links: {len(links)}")
    if links[:5]:
        print("Sample links:")
        for link in links[:5]:
            print(f"  - {link}")

except Exception as e:
    print(f"Error: {e}")

# 특정 보스 페이지 테스트
boss_url = f"{wiki_url}/Iudex+Gundyr"
print(f"\nTesting boss page: {boss_url}")

try:
    resp = session.get(boss_url, timeout=10)
    print(f"Status: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")
    title = soup.select_one("h1")
    if title:
        print(f"Title: {title.get_text(strip=True)}")

    content = soup.select_one("#wiki-content-block, #article-body")
    if content:
        text = content.get_text()[:500]
        print(f"Content preview: {text[:200]}...")
    else:
        print("No content found")

except Exception as e:
    print(f"Error: {e}")
