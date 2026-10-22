import base64
import datetime
import os
import pickle
import re
import threading
import uuid
import zipfile
from io import BytesIO

from flask import Flask, jsonify, request, render_template, send_file, abort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
# 데스크톱(tkinter) 버전과 같은 템플릿 파일을 공유한다.
TEMPLATES_FILE = os.path.join(PROJECT_DIR, 'filetree_templates.pkl')

BINARY_EXTENSIONS = {
    '.xlsx', '.docx', '.pptx', '.pdf', '.exe', '.dll', '.so', '.dylib',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
    '.bmp', '.tiff', '.ico', '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB (파일 첨부 업로드 여유치)

_LOCK = threading.Lock()


def get_file_content_by_extension(filename):
    """파일 확장자에 따라 기본 내용을 반환 (데스크톱 버전과 동일한 로직)"""
    ext = os.path.splitext(filename)[1].lower()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    base_name = os.path.splitext(filename)[0]

    content_map = {
        '.txt': f'이 파일은 텍스트 파일입니다.\n\n작성자: 파일트리 자동생성기\n작성일: {today}',
        '.md': f'# {base_name}\n\n이 문서는 마크다운 파일입니다.\n\n## 개요\n\n## 내용\n\n## 참고사항',
        '.py': f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\n{base_name}\n\n설명: 이 파일은 Python 스크립트입니다.\n작성자: 파일트리 자동생성기\n작성일: {today}\n"""\n\n\ndef main():\n    """메인 함수"""\n    print("Hello, World!")\n\n\nif __name__ == "__main__":\n    main()',
        '.js': f'// {base_name}\n// 설명: 이 파일은 JavaScript 파일입니다.\n// 작성자: 파일트리 자동생성기\n// 작성일: {today}\n\n\nfunction main() {{\n    console.log("Hello, World!");\n}}\n\n\n// 메인 함수 실행\nmain();',
        '.html': f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
</head>
<body>
    <h1>{base_name}</h1>
    <p>이 파일은 HTML 파일입니다.</p>
    <p>작성자: 파일트리 자동생성기</p>
    <p>작성일: {today}</p>
</body>
</html>''',
        '.css': f'/* {base_name} */\n/* 설명: 이 파일은 CSS 파일입니다. */\n/* 작성자: 파일트리 자동생성기 */\n/* 작성일: {today} */\n\n\nbody {{\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f5f5f5;\n}}\n\n\nh1 {{\n    color: #333;\n    text-align: center;\n}}',
        '.json': f'{{\n    "name": "{base_name}",\n    "description": "이 파일은 JSON 파일입니다.",\n    "author": "파일트리 자동생성기",\n    "created": "{today}",\n    "version": "1.0.0",\n    "data": {{\n        "example": "샘플 데이터"\n    }}\n}}',
        '.xml': f'''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <n>{base_name}</n>
    <description>이 파일은 XML 파일입니다.</description>
    <author>파일트리 자동생성기</author>
    <created>{today}</created>
    <version>1.0.0</version>
    <data>
        <example>샘플 데이터</example>
    </data>
</root>''',
        '.csv': f'이름,설명,작성자,작성일\n{base_name},이 파일은 CSV 파일입니다,파일트리 자동생성기,{today}',
        '.sql': f'-- {base_name}\n-- 설명: 이 파일은 SQL 파일입니다.\n-- 작성자: 파일트리 자동생성기\n-- 작성일: {today}\n\n\n-- 샘플 쿼리\nSELECT * FROM example_table;\n\n\n-- 테이블 생성 예시\n-- CREATE TABLE example_table (\n--     id INT PRIMARY KEY,\n--     name VARCHAR(100),\n--     created_at TIMESTAMP\n-- );',
        '.bat': f'@echo off\nREM {base_name}\nREM 설명: 이 파일은 Windows 배치 파일입니다.\nREM 작성자: 파일트리 자동생성기\nREM 작성일: {today}\n\n\necho Hello, World!\npause',
        '.sh': f'#!/bin/bash\n# {base_name}\n# 설명: 이 파일은 Linux/Unix 쉘 스크립트입니다.\n# 작성자: 파일트리 자동생성기\n# 작성일: {today}\n\n\necho "Hello, World!"',
    }

    return content_map.get(ext, f'이 파일은 {ext} 확장자를 가진 파일입니다.\n\n작성자: 파일트리 자동생성기\n작성일: {today}')


# ---------------------------------------------------------------------------
# 템플릿 저장/로드 (pickle 파일은 데스크톱 tkinter 버전과 동일한 포맷 + 파일 공유)
# ---------------------------------------------------------------------------

def _ensure_ids(nodes):
    """오래된(데스크톱 전용) 템플릿 데이터에 웹에서 쓸 안정적인 id를 부여한다."""
    changed = False
    for node in nodes:
        if 'id' not in node:
            node['id'] = uuid.uuid4().hex
            changed = True
        if node.get('type') == 'folder':
            children = node.setdefault('children', [])
            if _ensure_ids(children):
                changed = True
    return changed


def _load_templates_raw():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'rb') as f:
            return pickle.load(f)
    return {}


def load_templates():
    templates = _load_templates_raw()
    dirty = False
    for tree in templates.values():
        if _ensure_ids(tree):
            dirty = True
    if dirty:
        save_templates(templates)
    return templates


def save_templates(templates):
    tmp_path = TEMPLATES_FILE + '.tmp'
    with open(tmp_path, 'wb') as f:
        pickle.dump(templates, f)
    os.replace(tmp_path, TEMPLATES_FILE)


def clean_tree_for_save(nodes):
    """클라이언트가 보낸 트리를 검증하고 id가 없는 새 노드에 id를 채운다."""
    cleaned = []
    for node in nodes:
        name = (node.get('name') or '').strip()
        ntype = node.get('type')
        if not name or ntype not in ('folder', 'file'):
            continue
        out = {
            'id': node.get('id') or uuid.uuid4().hex,
            'name': name,
            'type': ntype,
        }
        if ntype == 'folder':
            out['children'] = clean_tree_for_save(node.get('children') or [])
        else:
            if node.get('content_b64'):
                out['content_b64'] = node['content_b64']
            if node.get('source_path'):
                out['source_path'] = node['source_path']
        cleaned.append(out)
    return cleaned


def tree_for_client(nodes):
    """저장된 트리를 클라이언트로 그대로 전달한다.

    편집 후 재저장할 때 content_b64를 잃지 않으려면(사용자가 건드리지 않은
    파일까지) 클라이언트가 항상 전체 데이터를 들고 있어야 하므로 그대로 반환한다.
    """
    out = []
    for node in nodes:
        item = {'id': node['id'], 'name': node['name'], 'type': node['type']}
        if node['type'] == 'folder':
            item['children'] = tree_for_client(node.get('children', []))
        else:
            if node.get('content_b64'):
                item['content_b64'] = node['content_b64']
            if node.get('source_path'):
                item['source_path'] = node['source_path']
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# ZIP 생성 (데스크톱 버전 create_tree / create_default_file 로직을 이식)
# ---------------------------------------------------------------------------

def _default_file_bytes(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return b''
    return get_file_content_by_extension(filename).encode('utf-8')


def _node_bytes(node):
    if node.get('content_b64'):
        try:
            return base64.b64decode(node['content_b64'])
        except Exception:
            pass
    source_path = node.get('source_path')
    if source_path and os.path.isfile(source_path):
        try:
            with open(source_path, 'rb') as f:
                return f.read()
        except Exception:
            pass
    return _default_file_bytes(node['name'])


def _write_nodes(zf, base_path, nodes):
    for node in nodes:
        path = f'{base_path}/{node["name"]}' if base_path else node['name']
        if node['type'] == 'folder':
            children = node.get('children') or []
            if not children:
                zf.writestr(path.rstrip('/') + '/', '')
            else:
                _write_nodes(zf, path, children)
        else:
            zf.writestr(path, _node_bytes(node))


def build_zip(tree, root_name):
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not tree:
            zf.writestr(root_name.rstrip('/') + '/', '')
        else:
            _write_nodes(zf, root_name, tree)
    buf.seek(0)
    return buf


def sanitize_filename(name, fallback='root'):
    name = (name or '').strip()
    name = re.sub(r'[\\/:*?"<>|]+', '_', name)
    name = name.strip('. ')
    return name or fallback


# ---------------------------------------------------------------------------
# 라우트
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/templates', methods=['GET'])
def api_list_templates():
    with _LOCK:
        templates = load_templates()
    return jsonify({'names': list(templates.keys())})


@app.route('/api/templates/<name>', methods=['GET'])
def api_get_template(name):
    with _LOCK:
        templates = load_templates()
    if name not in templates:
        abort(404, description='템플릿을 찾을 수 없습니다.')
    return jsonify({'name': name, 'tree': tree_for_client(templates[name])})


@app.route('/api/templates', methods=['POST'])
def api_create_template():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    tree = data.get('tree') or []
    if not name:
        return jsonify({'error': '템플릿 이름을 입력하세요.'}), 400
    with _LOCK:
        templates = load_templates()
        if name in templates:
            return jsonify({'error': '이미 존재하는 템플릿 이름입니다.'}), 400
        templates[name] = clean_tree_for_save(tree)
        save_templates(templates)
    return jsonify({'ok': True})


@app.route('/api/templates/<name>', methods=['PUT'])
def api_update_template(name):
    data = request.get_json(force=True) or {}
    tree = data.get('tree') or []
    with _LOCK:
        templates = load_templates()
        if name not in templates:
            return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
        templates[name] = clean_tree_for_save(tree)
        save_templates(templates)
    return jsonify({'ok': True})


@app.route('/api/templates/<name>/rename', methods=['POST'])
def api_rename_template(name):
    data = request.get_json(force=True) or {}
    new_name = (data.get('new_name') or '').strip()
    if not new_name:
        return jsonify({'error': '새 이름을 입력하세요.'}), 400
    with _LOCK:
        templates = load_templates()
        if name not in templates:
            return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
        if new_name != name and new_name in templates:
            return jsonify({'error': '이미 존재하는 템플릿 이름입니다.'}), 400
        rebuilt = {}
        for k, v in templates.items():
            if k == name:
                rebuilt[new_name] = v
            else:
                rebuilt[k] = v
        save_templates(rebuilt)
    return jsonify({'ok': True})


@app.route('/api/templates/<name>', methods=['DELETE'])
def api_delete_template(name):
    with _LOCK:
        templates = load_templates()
        if name not in templates:
            return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
        del templates[name]
        save_templates(templates)
    return jsonify({'ok': True})


@app.route('/api/templates/reorder', methods=['POST'])
def api_reorder_templates():
    data = request.get_json(force=True) or {}
    order = data.get('order') or []
    with _LOCK:
        templates = load_templates()
        if set(order) != set(templates.keys()) or len(order) != len(templates):
            return jsonify({'error': '순서 목록이 현재 템플릿 목록과 일치하지 않습니다.'}), 400
        rebuilt = {name: templates[name] for name in order}
        save_templates(rebuilt)
    return jsonify({'ok': True})


@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json(force=True) or {}
    root_name = sanitize_filename(data.get('root_name'), fallback='filetree')
    tree = data.get('tree')

    if tree is None:
        template_name = data.get('template_name')
        if not template_name:
            return jsonify({'error': '템플릿 또는 트리 데이터가 필요합니다.'}), 400
        with _LOCK:
            templates = load_templates()
        if template_name not in templates:
            return jsonify({'error': '템플릿을 찾을 수 없습니다.'}), 404
        tree = templates[template_name]
    else:
        tree = clean_tree_for_save(tree)

    buf = build_zip(tree, root_name)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{root_name}.zip',
    )


if __name__ == '__main__':
    # LAN 상의 다른 사람들도 접속할 수 있도록 모든 인터페이스에서 대기.
    # 이 스크립트를 192.168.134.130 로 잡히는 PC에서 실행하면
    # http://192.168.134.130:8004 로 접속할 수 있습니다.
    app.run(host='0.0.0.0', port=8004, debug=False)
