"""
Google Indexing API — sitemap.xml 기반 URL 일괄 제출 스크립트

사전 준비:
  환경변수 GOOGLE_INDEXING_KEY 에 서비스 계정 JSON 키 내용(문자열)을 설정합니다.
  GitHub Actions에서는 Secrets.GOOGLE_INDEXING_KEY 로 주입됩니다.

제한:
  Google Indexing API는 하루 200 URL 제출 허용.
  사이트 규모가 200을 넘으면 --limit 옵션으로 분할 제출합니다.
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
SITEMAP_URL = "https://kdelphinus.github.io/infra-cheatsheets/sitemap.xml"
REQUEST_DELAY = 0.3  # 초 단위 요청 간격


def build_credentials(key_json_str: str):
    info = json.loads(key_json_str)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def refresh_token(creds) -> str:
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def fetch_urls(sitemap_url: str) -> list[str]:
    print(f"[INFO] sitemap 가져오는 중: {sitemap_url}")
    resp = requests.get(sitemap_url, timeout=15)
    resp.raise_for_status()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.fromstring(resp.content)
    urls = [el.text.strip() for el in root.findall("sm:url/sm:loc", ns)]
    print(f"[INFO] 총 {len(urls)}개 URL 발견")
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


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="제출할 최대 URL 수 (기본값: 200, API 일일 한도)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="건너뛸 URL 수 (분할 제출 시 사용)",
    )
    args = parser.parse_args()

    key_json = os.environ.get("GOOGLE_INDEXING_KEY")
    if not key_json:
        print("[ERROR] 환경변수 GOOGLE_INDEXING_KEY 가 설정되지 않았습니다.")
        sys.exit(1)

    creds = build_credentials(key_json)
    token = refresh_token(creds)

    urls = fetch_urls(SITEMAP_URL)
    target = urls[args.offset : args.offset + args.limit]
    print(f"[INFO] {args.offset + 1} ~ {args.offset + len(target)}번 URL 제출 시작")

    success, failed = 0, 0
    for i, url in enumerate(target, 1):
        # 토큰 만료 전 갱신 (55분 주기)
        if i % 100 == 0:
            token = refresh_token(creds)

        status, body = submit_url(url, token)
        if status == 200:
            print(f"  [OK]   ({i}/{len(target)}) {url}")
            success += 1
        else:
            err = body.get("error", {}).get("message", body)
            print(f"  [FAIL] ({i}/{len(target)}) {url} — {status}: {err}")
            failed += 1

        time.sleep(REQUEST_DELAY)

    print(f"\n[DONE] 성공: {success} / 실패: {failed} / 전체: {len(target)}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
