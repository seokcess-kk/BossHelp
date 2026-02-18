"""Wiki 크롤러 디버깅 스크립트"""
import requests
from bs4 import BeautifulSoup

def debug_wiki():
    url = "https://eldenring.wiki.fextralife.com/Bosses"

    print(f"1. URL 요청: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"2. 응답 상태: {response.status_code}")
        print(f"3. 응답 길이: {len(response.text)} bytes")
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 다양한 선택자 테스트
    selectors = [
        "#article-body a",
        ".article-body a",
        "#wiki-content-block a",
        ".wiki-content a",
        "article a",
        ".page-content a",
        "a[href*='wiki']",
    ]

    print("\n4. 선택자별 링크 수:")
    for sel in selectors:
        links = soup.select(sel)
        print(f"   {sel}: {len(links)}개")

    # 모든 a 태그
    all_links = soup.select("a")
    print(f"\n5. 전체 a 태그: {len(all_links)}개")

    # 샘플 링크 출력
    print("\n6. 샘플 링크 (처음 10개):")
    for a in all_links[:10]:
        href = a.get("href", "")
        text = a.get_text(strip=True)[:30]
        print(f"   {href} -> {text}")

    # body 내 주요 ID/Class 확인
    print("\n7. 주요 컨테이너:")
    for tag in soup.select("[id], [class]"):
        tag_id = tag.get("id", "")
        tag_class = " ".join(tag.get("class", []))
        if tag_id or ("content" in tag_class.lower() or "article" in tag_class.lower() or "wiki" in tag_class.lower()):
            if tag_id:
                print(f"   #{tag_id}")
            if tag_class and len(tag_class) < 50:
                print(f"   .{tag_class}")

if __name__ == "__main__":
    debug_wiki()
