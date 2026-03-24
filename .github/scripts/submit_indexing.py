"""
Google Indexing API — URL 제출 스크립트

동작 모드:
  --urls  파일 경로  : 해당 파일에 적힌 URL 목록만 제출 (push 이벤트용)
  기본              : sitemap.xml 전체 제출 (수동 실행용)

제한:
  Google Indexing API는 하루 200 URL 제출 허용.
  수동 실행 시 --offset / --limit 으로 분할 제출합니다.
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET

import requests
from google.oauth2 import service_account
import google.auth.transport.requests

SCOPES = ["https://www.googleapis.com/auth/indexing"]
ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SITE_BASE = "https://kdelphinus.github.io/infra-cheatsheets"
SITEMAP_URL = f"{SITE_BASE}/sitemap.xml"
REQUEST_DELAY = 0.3


def build_credentials(key_json_str: str):
    info = json.loads(key_json_str)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def refresh_token(creds) -> str:
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def fetch_all_urls() -> list[str]:
    print(f"[INFO] sitemap 가져오는 중: {SITEMAP_URL}")
    resp = requests.get(SITEMAP_URL, timeout=15)
    resp.raise_for_status()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.fromstring(resp.content)
    urls = [el.text.strip() for el in root.findall("sm:url/sm:loc", ns)]
    print(f"[INFO] 총 {len(urls)}개 URL 발견")
    return urls


def docs_path_to_url(path: str) -> str | None:
    """docs/k8s/foo/bar.md → https://.../k8s/foo/bar/"""
    if not path.startswith("docs/") or not path.endswith(".md"):
        return None
    # docs/ 제거, .md 제거, 끝에 / 추가
    rel = path[len("docs/"):-len(".md")]
    # index.md → 상위 경로
    if rel == "index" or rel.endswith("/index"):
        rel = rel[: -len("/index")] if "/" in rel else ""
    return f"{SITE_BASE}/{rel}/" if rel else f"{SITE_BASE}/"


def load_urls_from_file(path: str) -> list[str]:
    with open(path) as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f"[INFO] {len(urls)}개 변경 URL 로드")
    return urls


def submit_url(url: str, token: str) -> tuple[int, dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"url": url, "type": "URL_UPDATED"}
    resp = requests.post(ENDPOINT, headers=headers, json=payload, timeout=10)
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, {"raw": resp.text}


def run(urls: list[str], creds):
    token = refresh_token(creds)
    success, failed = 0, 0

    for i, url in enumerate(urls, 1):
        if i % 100 == 0:
            token = refresh_token(creds)

        status, body = submit_url(url, token)
        if status == 200:
            print(f"  [OK]   ({i}/{len(urls)}) {url}")
            success += 1
        else:
            err = body.get("error", {}).get("message", body)
            print(f"  [FAIL] ({i}/{len(urls)}) {url} — {status}: {err}")
            failed += 1

        time.sleep(REQUEST_DELAY)

    print(f"\n[DONE] 성공: {success} / 실패: {failed} / 전체: {len(urls)}")
    if failed > 0:
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", help="제출할 URL 목록 파일 경로 (한 줄에 URL 하나)")
    parser.add_argument("--limit", type=int, default=200, help="최대 제출 URL 수")
    parser.add_argument("--offset", type=int, default=0, help="건너뛸 URL 수")
    args = parser.parse_args()

    key_json = os.environ.get("GOOGLE_INDEXING_KEY")
    if not key_json:
        print("[ERROR] 환경변수 GOOGLE_INDEXING_KEY 가 설정되지 않았습니다.")
        sys.exit(1)

    creds = build_credentials(key_json)

    if args.urls:
        # push 이벤트: 변경된 URL만 제출
        urls = load_urls_from_file(args.urls)
    else:
        # 수동 실행: sitemap 전체 제출
        all_urls = fetch_all_urls()
        urls = all_urls[args.offset : args.offset + args.limit]
        print(f"[INFO] {args.offset + 1} ~ {args.offset + len(urls)}번 제출")

    if not urls:
        print("[INFO] 제출할 URL이 없습니다.")
        return

    run(urls, creds)


if __name__ == "__main__":
    main()
