# -*- coding: utf-8 -*-
"""
저장공간 관리 프로그램 - Flask 웹 버전
데스크톱 tkinter 버전(../CODE.py)의 분석/휴지통 로직을 그대로 이식해서 웹 허브 형태로 재구성.
휴지통 폴더(~/.disk_manager_trash)와 trash_info.json / delete_history.json 형식을
데스크톱 버전과 동일하게 사용하므로 두 버전을 같이 써도 상태가 어긋나지 않는다.
"""
import ctypes
import datetime
import io
import json
import os
import platform
import re
import shutil
import string
import threading
import time
from collections import defaultdict
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

FILE_TYPES = {
    "문서": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".hwp"],
    "이미지": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp"],
    "오디오 파일": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "동영상": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "압축파일": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "설치 파일": [".exe", ".msi", ".dmg", ".deb", ".rpm"],
    "기타": [],
}

LARGE_FILE_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1GB
OLD_FILE_SECONDS = 365 * 24 * 3600
MAX_FILES_PER_TYPE = 2000
MAX_LARGE_FILES_COLLECT = 500
MAX_LARGE_FILES_KEEP = 100
MAX_OLD_FILES_COLLECT = 2000
MAX_OLD_FILES_KEEP = 500
MAX_DUP_GROUP_SIZE = 50
MAX_DUP_GROUPS_KEEP = 500

TRASH_DIR = Path.home() / ".disk_manager_trash"
TRASH_DIR.mkdir(exist_ok=True)
TRASH_INFO_FILE = TRASH_DIR / "trash_info.json"
DELETE_HISTORY_FILE = TRASH_DIR / "delete_history.json"

_lock = threading.Lock()
_control = {"paused": False, "stop": False}
_scan_thread = None
_cache = {"file_data_full": {}, "large_files": [], "old_files": [], "duplicates": {}, "drive": None}

state = {
    "status": "idle",  # idle | running | paused | done | stopped | error
    "drive": None,
    "processed_files": 0,
    "elapsed_seconds": 0,
    "rate_per_sec": 0,
    "result": None,
    "error": None,
}


# ==================================================================== util
def get_file_type(ext):
    for file_type, extensions in FILE_TYPES.items():
        if ext in extensions:
            return file_type
    return "기타"


def normalize_filename(filename):
    """중복 파일 탐지를 위한 파일명 정규화 (원본 데스크톱 앱과 동일 로직)."""
    name_parts = filename.rsplit(".", 1)
    if len(name_parts) == 2:
        name, ext = name_parts
    else:
        name, ext = filename, ""

    name = re.sub(r"\s*[-_\s]*복사본\s*\d*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*[-_\s]*복사\s*\d*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*[-_\s]*copy\s*\d*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s*\(\d+\)$", "", name)
    name = re.sub(r"\s*-\s*\d+\s*$", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    name = name.strip()

    return f"{name}.{ext}" if ext else name


def format_bytes(value):
    value = float(value)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def list_drives():
    drives = []
    if platform.system() == "Windows":
        kernel32 = ctypes.windll.kernel32
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if not os.path.exists(drive):
                continue
            label = ""
            try:
                volume_buf = ctypes.create_unicode_buffer(1024)
                fs_buf = ctypes.create_unicode_buffer(1024)
                ok = kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(drive), volume_buf, ctypes.sizeof(volume_buf),
                    None, None, None, fs_buf, ctypes.sizeof(fs_buf),
                )
                if ok:
                    label = volume_buf.value
            except Exception:
                label = ""
            try:
                total, used, free = shutil.disk_usage(drive)
            except Exception:
                total = used = free = 0
            drives.append({
                "path": drive,
                "label": f"{drive} ({label})" if label else drive,
                "total": total, "used": used, "free": free,
            })
    else:
        try:
            total, used, free = shutil.disk_usage("/")
        except Exception:
            total = used = free = 0
        drives.append({"path": "/", "label": "/", "total": total, "used": used, "free": free})
    return drives


# ==================================================================== trash
def load_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_trash_info():
    return load_json(TRASH_INFO_FILE, {})


def save_trash_info(info):
    save_json(TRASH_INFO_FILE, info)


def load_delete_history():
    return load_json(DELETE_HISTORY_FILE, [])


def save_delete_history(history):
    save_json(DELETE_HISTORY_FILE, history)


def add_to_delete_history(files_info, drive, operation_type="휴지통으로 이동"):
    history = load_delete_history()
    total_size = sum(f["size"] for f in files_info)
    before_free = after_free = 0
    if drive:
        try:
            _, _, free = shutil.disk_usage(drive)
            after_free = free
            before_free = free - total_size
        except Exception:
            pass
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "operation_type": operation_type,
        "drive": drive,
        "file_count": len(files_info),
        "total_size": total_size,
        "before_free_space": before_free,
        "after_free_space": after_free,
        "files": files_info,
    })
    save_delete_history(history)


def move_to_trash(file_path):
    """실제 삭제 대신 ~/.disk_manager_trash 로 이동 (데스크톱 버전과 동일한 휴지통)."""
    source = Path(file_path)
    if not source.exists() or not source.is_file():
        return False, None
    file_size = source.stat().st_size
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")
    trash_filename = f"{timestamp}_{source.name}"
    trash_path = TRASH_DIR / trash_filename
    try:
        with _lock:
            shutil.move(str(source), str(trash_path))
            trash_info = load_trash_info()
            trash_info[trash_filename] = {
                "original_path": str(source),
                "deleted_date": datetime.datetime.now().isoformat(),
                "auto_delete_date": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
                "size": file_size,
            }
            save_trash_info(trash_info)
    except Exception:
        return False, None
    return True, {
        "path": str(source), "name": source.name, "size": file_size,
        "type": source.suffix.upper()[1:] if source.suffix else "파일",
    }


def get_trash_files():
    trash_info = load_trash_info()
    files = []
    for trash_filename, info in trash_info.items():
        trash_path = TRASH_DIR / trash_filename
        size = trash_path.stat().st_size if trash_path.exists() else info.get("size", 0)
        deleted_ts = 0
        try:
            deleted_ts = datetime.datetime.fromisoformat(info["deleted_date"]).timestamp()
        except Exception:
            pass
        files.append({
            "trash_filename": trash_filename,
            "name": Path(info["original_path"]).name,
            "path": info["original_path"],
            "size": size,
            "modified": deleted_ts,
            "deleted_date": info.get("deleted_date"),
        })
    return files


def restore_from_trash(trash_filenames):
    trash_info = load_trash_info()
    restored = []
    with _lock:
        for trash_filename in trash_filenames:
            info = trash_info.get(trash_filename)
            if not info:
                continue
            trash_path = TRASH_DIR / trash_filename
            if not trash_path.exists():
                del trash_info[trash_filename]
                continue
            target = Path(info["original_path"])
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    base, ext = target.stem, target.suffix
                    counter = 1
                    while target.exists():
                        target = target.parent / f"{base}_복원{counter}{ext}"
                        counter += 1
                shutil.move(str(trash_path), str(target))
                del trash_info[trash_filename]
                restored.append(str(target))
            except Exception:
                pass
        save_trash_info(trash_info)
    return restored


def purge_from_trash(trash_filenames):
    """휴지통 안에서 완전(영구) 삭제 - 별도 확인 절차를 거친 2단계 동작."""
    trash_info = load_trash_info()
    purged = []
    with _lock:
        for trash_filename in trash_filenames:
            trash_path = TRASH_DIR / trash_filename
            try:
                if trash_path.exists():
                    trash_path.unlink()
                if trash_filename in trash_info:
                    del trash_info[trash_filename]
                purged.append(trash_filename)
            except Exception:
                pass
        save_trash_info(trash_info)
    return purged


# ================================================================= analyze
def run_analysis(drive_path):
    file_data = defaultdict(lambda: {"count": 0, "size": 0, "files": []})
    groups_by_name = defaultdict(list)
    large_files = []
    old_files = []
    total_files = 0
    start_time = time.time()
    now = time.time()

    try:
        for root, dirs, files in os.walk(drive_path):
            if _control["stop"]:
                break
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "System Volume Information"]

            for name in files:
                while _control["paused"] and not _control["stop"]:
                    time.sleep(0.2)
                if _control["stop"]:
                    break
                if name.startswith("."):
                    continue

                total_files += 1
                if total_files % 200 == 0:
                    elapsed = time.time() - start_time
                    with _lock:
                        state["processed_files"] = total_files
                        state["elapsed_seconds"] = round(elapsed, 1)
                        state["rate_per_sec"] = round(total_files / elapsed, 1) if elapsed > 0 else 0

                file_path = Path(root) / name
                try:
                    st = file_path.stat()
                except (PermissionError, OSError):
                    continue

                size = st.st_size
                ext = file_path.suffix.lower()
                ftype = get_file_type(ext)

                bucket = file_data[ftype]
                bucket["count"] += 1
                bucket["size"] += size
                if len(bucket["files"]) < MAX_FILES_PER_TYPE:
                    bucket["files"].append({"path": str(file_path), "name": name, "size": size, "modified": st.st_mtime})

                if size > LARGE_FILE_THRESHOLD and len(large_files) < MAX_LARGE_FILES_COLLECT:
                    large_files.append({"path": str(file_path), "name": name, "size": size, "modified": st.st_mtime})

                if now - st.st_mtime > OLD_FILE_SECONDS and len(old_files) < MAX_OLD_FILES_COLLECT:
                    old_files.append({"path": str(file_path), "name": name, "size": size, "modified": st.st_mtime})

                norm = normalize_filename(name)
                group = groups_by_name[norm]
                if len(group) < MAX_DUP_GROUP_SIZE:
                    group.append({"path": str(file_path), "name": name, "size": size, "modified": st.st_mtime})

            if _control["stop"]:
                break

        duplicates = {k: v for k, v in groups_by_name.items() if len(v) > 1}
        total, used, free = shutil.disk_usage(drive_path)

        result = {
            "drive": drive_path,
            "total": total, "used": used, "free": free,
            "file_data": {k: {"count": v["count"], "size": v["size"]} for k, v in file_data.items()},
            "total_files": total_files,
            "large_count": len(large_files),
            "large_size": sum(f["size"] for f in large_files),
            "old_count": len(old_files),
            "old_size": sum(f["size"] for f in old_files),
            "dup_group_count": len(duplicates),
            "dup_size": sum(sum(d["size"] for d in v[1:]) for v in duplicates.values()),
            "elapsed_seconds": round(time.time() - start_time, 1),
        }

        _cache["file_data_full"] = dict(file_data)
        _cache["large_files"] = sorted(large_files, key=lambda x: x["size"], reverse=True)[:MAX_LARGE_FILES_KEEP]
        _cache["old_files"] = sorted(old_files, key=lambda x: x["modified"])[:MAX_OLD_FILES_KEEP]
        _cache["duplicates"] = duplicates
        _cache["drive"] = drive_path

        with _lock:
            state["status"] = "stopped" if _control["stop"] else "done"
            state["processed_files"] = total_files
            state["result"] = result

    except Exception as e:
        with _lock:
            state["status"] = "error"
            state["error"] = str(e)


# =================================================================== routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/drives")
def api_drives():
    return jsonify(list_drives())


@app.route("/api/analyze", methods=["POST"])
def api_analyze_start():
    global _scan_thread
    data = request.get_json(force=True) or {}
    drive = data.get("drive")
    if not drive or not os.path.exists(drive):
        return jsonify({"error": "유효한 드라이브를 선택해주세요."}), 400
    with _lock:
        if state["status"] == "running":
            return jsonify({"error": "이미 분석 중입니다."}), 409
        state.update({
            "status": "running", "drive": drive, "processed_files": 0,
            "elapsed_seconds": 0, "rate_per_sec": 0, "result": None, "error": None,
        })
    _control["paused"] = False
    _control["stop"] = False
    _scan_thread = threading.Thread(target=run_analysis, args=(drive,), daemon=True)
    _scan_thread.start()
    return jsonify({"ok": True})


@app.route("/api/analyze/pause", methods=["POST"])
def api_analyze_pause():
    _control["paused"] = True
    with _lock:
        if state["status"] == "running":
            state["status"] = "paused"
    return jsonify({"ok": True})


@app.route("/api/analyze/resume", methods=["POST"])
def api_analyze_resume():
    _control["paused"] = False
    with _lock:
        if state["status"] == "paused":
            state["status"] = "running"
    return jsonify({"ok": True})


@app.route("/api/analyze/stop", methods=["POST"])
def api_analyze_stop():
    _control["stop"] = True
    _control["paused"] = False
    return jsonify({"ok": True})


@app.route("/api/analyze/status")
def api_analyze_status():
    with _lock:
        return jsonify(dict(state))


@app.route("/api/files/type/<path:ftype>")
def api_files_by_type(ftype):
    bucket = _cache.get("file_data_full", {}).get(ftype)
    if bucket is None:
        return jsonify({"files": [], "count": 0, "size": 0})
    files = sorted(bucket["files"], key=lambda x: x["size"], reverse=True)
    return jsonify({"files": files, "count": bucket["count"], "size": bucket["size"]})


@app.route("/api/files/large")
def api_files_large():
    return jsonify({"files": _cache.get("large_files", [])})


@app.route("/api/files/old")
def api_files_old():
    return jsonify({"files": _cache.get("old_files", [])})


@app.route("/api/files/duplicates")
def api_files_duplicates():
    duplicates = _cache.get("duplicates", {})
    ordered = sorted(duplicates.items(), key=lambda x: sum(f["size"] for f in x[1]), reverse=True)[:MAX_DUP_GROUPS_KEEP]
    groups = [{"group": idx + 1, "name": name, "files": files} for idx, (name, files) in enumerate(ordered)]
    saveable = sum(sum(f["size"] for f in files[1:]) for _, files in ordered)
    return jsonify({"groups": groups, "saveable_size": saveable})


@app.route("/api/trash")
def api_trash():
    files = get_trash_files()
    files.sort(key=lambda x: x.get("deleted_date") or "", reverse=True)
    return jsonify({"files": files, "total_size": sum(f["size"] for f in files)})


@app.route("/api/delete", methods=["POST"])
def api_delete():
    data = request.get_json(force=True) or {}
    paths = data.get("paths", [])
    moved, failed = [], []
    for p in paths:
        ok, info = move_to_trash(p)
        if ok:
            moved.append(info)
        else:
            failed.append(p)
    if moved:
        add_to_delete_history(moved, _cache.get("drive") or state.get("drive"))
    return jsonify({"moved": len(moved), "failed": failed})


@app.route("/api/restore", methods=["POST"])
def api_restore():
    data = request.get_json(force=True) or {}
    names = data.get("trash_filenames", [])
    restored = restore_from_trash(names)
    return jsonify({"restored": len(restored)})


@app.route("/api/trash/purge", methods=["POST"])
def api_trash_purge():
    data = request.get_json(force=True) or {}
    names = data.get("trash_filenames", [])
    purged = purge_from_trash(names)
    return jsonify({"purged": len(purged)})


@app.route("/api/history")
def api_history():
    return jsonify(load_delete_history()[-100:][::-1])


@app.route("/api/report")
def api_report():
    history = load_delete_history()
    lines = [
        "저장공간 관리 프로그램 - 삭제 이력 보고서",
        f"생성일: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    if not history:
        lines.append("삭제 이력이 없습니다.")
    else:
        total_saved = sum(h["total_size"] for h in history)
        lines.append(f"총 {len(history)}건, 정리한 용량: {format_bytes(total_saved)}")
        lines.append("")
        for h in reversed(history):
            lines.append(f"[{h['timestamp']}] {h['operation_type']} - {h['file_count']}개 파일, {format_bytes(h['total_size'])}")
            for f in h["files"][:20]:
                lines.append(f"    - {f['name']} ({format_bytes(f['size'])})")
            if h["file_count"] > 20:
                lines.append(f"    ... 외 {h['file_count'] - 20}개")
            lines.append("")

    buf = io.BytesIO("\n".join(lines).encode("utf-8-sig"))
    return send_file(buf, as_attachment=True, download_name="저장공간_관리_보고서.txt", mimetype="text/plain")


if __name__ == "__main__":
    from waitress import serve

    print("저장공간 관리 프로그램 시작: http://192.168.134.130:8006")
    serve(app, host="0.0.0.0", port=8006)
