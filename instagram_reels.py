#!/usr/bin/env python3
"""
Instagram Reels API 자동화 스크립트
인생준준 & 여백의 지도 브랜드 영상 자동 업로드
"""

import requests
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

class InstagramReelsUploader:
    def __init__(self, access_token=None, business_account_id=None):
        """초기화"""
        # 환경변수 또는 전달된 토큰 사용
        self.access_token = access_token or os.environ.get('INSTAGRAM_ACCESS_TOKEN')
        self.business_account_id = business_account_id or os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        self.api_url = "https://graph.instagram.com"

        if not self.access_token:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN 환경변수가 필요합니다")
        if not self.business_account_id:
            raise ValueError("INSTAGRAM_BUSINESS_ACCOUNT_ID 환경변수가 필요합니다")

    def upload_reels(self, video_path, caption, thumbnail_path=None):
        """
        Reels 업로드
        Args:
            video_path: MP4 비디오 파일 경로
            caption: 캡션 텍스트
            thumbnail_path: 썸네일 이미지 경로 (선택사항)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"비디오 파일 없음: {video_path}")

        print(f"📹 업로드 중: {video_path}")
        print(f"📝 캡션: {caption}")

        try:
            # Step 1: 미디어 컨테이너 생성
            container_response = self._create_media_container(video_path, caption, thumbnail_path)
            if not container_response:
                return False

            container_id = container_response.get('id')
            print(f"✅ 컨테이너 생성: {container_id}")

            # Step 2: 업로드 완료 대기
            if not self._wait_for_upload(container_id):
                return False

            print(f"✅ 업로드 완료")

            # Step 3: Reels 게시 (선택사항)
            publish_response = self._publish_reels(container_id)
            if publish_response:
                print(f"✅ 게시됨: {publish_response.get('id')}")
                return True
            else:
                print("⚠️ 게시 대기 중 (수동 확인 필요)")
                return container_id

        except Exception as e:
            print(f"❌ 에러: {str(e)}")
            return False

    def _create_media_container(self, video_path, caption, thumbnail_path=None):
        """미디어 컨테이너 생성"""
        url = f"{self.api_url}/v18.0/{self.business_account_id}/media"

        files = {'video': open(video_path, 'rb')}
        data = {
            'media_type': 'REELS',
            'caption': caption,
            'access_token': self.access_token
        }

        if thumbnail_path and os.path.exists(thumbnail_path):
            files['thumbnail'] = open(thumbnail_path, 'rb')

        try:
            response = requests.post(url, files=files, data=data, timeout=60)
            response.raise_for_status()
            return response.json()
        finally:
            for f in files.values():
                f.close()

    def _wait_for_upload(self, container_id, max_wait=300):
        """업로드 완료 대기 (최대 5분)"""
        import time
        url = f"{self.api_url}/v18.0/{container_id}"

        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = requests.get(url, params={'access_token': self.access_token})
            if response.status_code != 200:
                return False

            data = response.json()
            status = data.get('status')

            if status == 'FINISHED':
                return True
            elif status == 'ERROR':
                print(f"❌ 업로드 에러: {data.get('status_reason')}")
                return False

            print(f"⏳ 상태: {status}... ({int(time.time() - start_time)}s)")
            time.sleep(5)

        print("⏰ 타임아웃 (계속 진행)")
        return True

    def _publish_reels(self, container_id):
        """Reels 게시"""
        url = f"{self.api_url}/v18.0/{self.business_account_id}/media_publish"
        data = {
            'creation_id': container_id,
            'access_token': self.access_token
        }

        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"게시 실패: {response.text}")
            return None


def generate_mp4_from_html(html_url, output_path, duration=30):
    """
    runfx.js HTML을 MP4로 변환 (Puppeteer + FFmpeg)
    """
    print(f"🎥 HTML → MP4 변환: {html_url}")

    try:
        # Step 1: Puppeteer로 스크린샷 캡처 및 Canvas 녹화
        node_script = f"""
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {{
  const browser = await puppeteer.launch({{headless: true}});
  const page = await browser.newPage();
  await page.setViewport({{width: 1080, height: 1920}});

  // HTML 페이지 로드
  await page.goto('{html_url}', {{waitUntil: 'networkidle2'}});

  // Canvas 녹화 또는 스크린샷
  // 이 부분은 실제 구현 필요
  await browser.close();
}})();
"""

        print("⚠️  Canvas 녹화는 고급 설정 필요 (Puppeteer FFmpeg 플러그인)")
        return None

    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        return None


def create_film_caption(film_id, brand="both"):
    """films.json 기반 캡션 생성"""
    captions = {
        "film-01-silence": {
            "both": "🏔️ SILENCE · 함께 걷는 세계\n천 년의 길 위에서\n\n인생준준 / 여백의 지도\n#러닝 #트레킹 #여행 #함께",
            "lifejunjun": "🏔️ 함께 달리고, 함께 걷는다\nSILENCE · RUN & TREK",
            "yeobaek": "🌍 여백의 지도 · 런더맵\n조용한 풍경을 달리다"
        },
        "film-02-momentum": {
            "both": "💨 MOMENTUM · 움직임의 에너지\n정상은 생각 이상으로 가깝다\n\n인생준준 / 여백의 지도\n#마라톤 #트레일러닝",
            "lifejunjun": "💨 움직임의 에너지 · MOMENTUM",
            "yeobaek": "🏃 RUN THE MAP · 에너지"
        },
        "film-03-altitude": {
            "both": "⛰️ ALTITUDE · 고도의 경험\n구름 위에서 만나다\n\n인생준준 / 여백의 지도\n#산행 #고산 #함께하기",
            "lifejunjun": "⛰️ 정상에서 만나는 세계 · ALTITUDE",
            "yeobaek": "🌤️ 고도의 풍경들"
        }
    }

    return captions.get(film_id, {}).get(brand, "인생준준 & 여백의 지도")


if __name__ == "__main__":
    import sys

    # 사용 예시
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        caption = sys.argv[2] if len(sys.argv) > 2 else "인생준준 & 여백의 지도"

        uploader = InstagramReelsUploader()
        result = uploader.upload_reels(video_path, caption)
        print(f"결과: {result}")
    else:
        print("사용법: python instagram_reels.py <video_path> <caption>")
        print("\n설정 필요:")
        print("  export INSTAGRAM_ACCESS_TOKEN='your_token'")
        print("  export INSTAGRAM_BUSINESS_ACCOUNT_ID='account_id'")
