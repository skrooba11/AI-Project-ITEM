"""
폼텍 라벨 디자인 편집기 - 웹 서버 (Flask)

사내 LAN에서 여러 사람이 동시에 접속해 사용할 수 있도록
기존 Electron용 HTML 편집기를 그대로 웹으로 서빙한다.

실행:
    python app.py

접속:
    http://192.168.134.130:8002
"""

import os

from flask import Flask, abort, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILENAME = "폼텍 라벨 디자인 편집기.html"
MOLD_FILENAME = "@금형번호.xlsm"

HOST = "0.0.0.0"
PORT = 8002

app = Flask(__name__)


@app.route("/")
def index():
    """편집기 메인 페이지."""
    return send_from_directory(BASE_DIR, HTML_FILENAME)


@app.route("/mold-data-file")
def mold_data_file():
    """
    금형번호.xlsm 파일 제공.

    편집기가 브라우저에서 열릴 때(Electron이 아닐 때) 이 엔드포인트를
    자동으로 fetch 해서 금형 데이터를 채운다. 이 서버가 돌고 있는
    컴퓨터의 @금형번호.xlsm 파일이 그대로 최신 데이터로 쓰인다
    (파일을 교체하면 다음 새로고침부터 바로 반영됨).
    """
    file_path = os.path.join(BASE_DIR, MOLD_FILENAME)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(
        BASE_DIR,
        MOLD_FILENAME,
        mimetype="application/vnd.ms-excel.sheet.macroEnabled.12",
    )


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, threaded=True)
