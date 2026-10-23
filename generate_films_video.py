#!/usr/bin/env python3
"""
films.json 기반 고급 영상 생성 (FFmpeg)
Wikimedia 사진들을 cinematic 비디오로 변환
"""

import json
import os
import subprocess
import tempfile
import requests
from pathlib import Path
from urllib.parse import urlparse

class FilmsVideoGenerator:
    def __init__(self, films_json_path):
        """초기화"""
        with open(films_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.work_dir = tempfile.mkdtemp(prefix='films_')
        print(f"🎬 작업 디렉토리: {self.work_dir}")

    def generate_video(self, film_id, output_path="/tmp/output.mp4", width=1080, height=1920):
        """
        Film을 MP4로 변환
        Args:
            film_id: films[].id (e.g., "film-01-silence")
            output_path: 저장할 MP4 경로
            width, height: 해상도 (Instagram Reels: 1080x1920)
        """
        # 1. Film 찾기
        film = None
        for f in self.data.get('films', []):
            if f['id'] == film_id:
                film = f
                break

        if not film:
            raise ValueError(f"Film 없음: {film_id}")

        print(f"\n🎞️  생성 중: {film['title']} ({film['style']})")

        # 2. 사진 다운로드 + 타이밍 정보 준비
        scene_files = []
        ffmpeg_concat = []

        for i, scene in enumerate(film.get('scenes', [])):
            img_url = scene.get('img')
            duration = scene.get('d', 2000) / 1000.0  # ms → seconds

            if not img_url:
                continue

            # 2a. 사진 다운로드
            local_path = self._download_image(img_url, i)
            if not local_path:
                continue

            scene_files.append({
                'path': local_path,
                'duration': duration,
                'text': scene.get('big', ''),
                'subtext': scene.get('small', ''),
                'color_on': scene.get('color_on', False)
            })

            # FFmpeg concat 파일 형식
            ffmpeg_concat.append(f"file '{local_path}'")
            ffmpeg_concat.append(f"duration {duration}")

        if not scene_files:
            print("❌ 사진 없음")
            return False

        # 3. FFmpeg concat 파일 생성
        concat_file = os.path.join(self.work_dir, f"{film_id}_concat.txt")
        with open(concat_file, 'w') as f:
            f.write('\n'.join(ffmpeg_concat))

        print(f"✅ 다운로드 완료: {len(scene_files)}개 씬")

        # 4. FFmpeg로 비디오 생성
        return self._ffmpeg_encode(concat_file, output_path, width, height, film['style'])

    def _download_image(self, url, index):
        """Wikimedia 사진 다운로드"""
        try:
            # Wikimedia 썸네일 URL 처리
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"⚠️  다운로드 실패: {url}")
                return None

            # 확장자 추출
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[-1] or '.jpg'

            local_path = os.path.join(self.work_dir, f"scene_{index:02d}{ext}")
            with open(local_path, 'wb') as f:
                f.write(response.content)

            return local_path

        except Exception as e:
            print(f"❌ 사진 다운로드 에러: {e}")
            return None

    def _ffmpeg_encode(self, concat_file, output_path, width, height, style):
        """
        FFmpeg로 비디오 인코딩

        스타일별 필터:
        - sport: 빠른 속도, 밝은 색감, 에너지감
        - luxe: 느린 속도, 저채도, 고급스러움
        - cinematic: 기본 필터
        """

        # 스타일별 필터 설정
        if style == "sport":
            # 빠르고 선명한 느낌
            video_filter = (
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                "fps=30,"
                "xfade=transition=fade:duration=0.5,"
                "normalize"
            )
            preset = "fast"
        elif style == "luxe":
            # 느리고 우아한 느낌
            video_filter = (
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                "fps=24,"
                "xfade=transition=dissolve:duration=1.0,"
                "curves=vintage"
            )
            preset = "slower"
        else:  # cinematic
            video_filter = (
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                "fps=30,"
                "xfade=transition=smoothleft:duration=0.7"
            )
            preset = "medium"

        # FFmpeg 명령어
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]

        try:
            print(f"🎥 FFmpeg 인코딩 중... ({style} 스타일)")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)

            # 파일 크기 확인
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✅ 완료: {output_path} ({size_mb:.1f}MB)")
                return True
            else:
                print("❌ 파일 생성 실패")
                return False

        except subprocess.TimeoutExpired:
            print("❌ 타임아웃 (300초 초과)")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg 에러: {e.stderr}")
            return False

    def cleanup(self):
        """임시 파일 정리"""
        import shutil
        try:
            shutil.rmtree(self.work_dir)
            print(f"🧹 작업 디렉토리 삭제: {self.work_dir}")
        except:
            pass


def generate_film_sequence(films_json_path, output_dir="/tmp/films_mp4"):
    """
    여러 films를 순서대로 생성
    """
    os.makedirs(output_dir, exist_ok=True)

    generator = FilmsVideoGenerator(films_json_path)

    results = {}
    for film in generator.data.get('films', [])[:3]:  # 최대 3개
        film_id = film['id']
        output_path = os.path.join(output_dir, f"{film_id}.mp4")

        try:
            success = generator.generate_video(film_id, output_path)
            results[film_id] = {
                'success': success,
                'path': output_path if success else None
            }
        except Exception as e:
            print(f"❌ {film_id}: {e}")
            results[film_id] = {'success': False, 'error': str(e)}

    generator.cleanup()
    return results


if __name__ == "__main__":
    import sys

    films_json = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/lifejunjun/films.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/films_mp4"

    print("🎬 Films Video Generator")
    print(f"📁 소스: {films_json}")
    print(f"📁 출력: {output_dir}\n")

    results = generate_film_sequence(films_json, output_dir)

    print("\n📊 결과:")
    for film_id, result in results.items():
        status = "✅" if result['success'] else "❌"
        msg = f"({result.get('path')})" if result.get('path') else f"({result.get('error')})"
        print(f"  {status} {film_id} {msg}")
