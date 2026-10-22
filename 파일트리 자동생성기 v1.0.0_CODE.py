import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import os
import pickle
import subprocess
import sys
import shutil
from tkinterdnd2 import TkinterDnD, DND_FILES

# Modern UI 설정은 메인 실행 부분에서 초기화

TEMPLATES_FILE = 'filetree_templates.pkl'

def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

def save_templates(templates):
    with open(TEMPLATES_FILE, 'wb') as f:
        pickle.dump(templates, f)

def get_file_content_by_extension(filename):
    """파일 확장자에 따라 기본 내용을 반환"""
    ext = os.path.splitext(filename)[1].lower()
    
    content_map = {
        '.txt': '이 파일은 텍스트 파일입니다.\n\n작성자: 파일트리 자동생성기\n작성일: ' + str(__import__('datetime').datetime.now().strftime('%Y-%m-%d')),
        '.md': '# ' + os.path.splitext(filename)[0] + '\n\n이 문서는 마크다운 파일입니다.\n\n## 개요\n\n## 내용\n\n## 참고사항',
        '.py': f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\n{os.path.splitext(filename)[0]}\n\n설명: 이 파일은 Python 스크립트입니다.\n작성자: 파일트리 자동생성기\n작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}\n"""\n\n\ndef main():\n    """메인 함수"""\n    print("Hello, World!")\n\n\nif __name__ == "__main__":\n    main()',
        '.js': f'// {os.path.splitext(filename)[0]}\n// 설명: 이 파일은 JavaScript 파일입니다.\n// 작성자: 파일트리 자동생성기\n// 작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}\n\n\nfunction main() {{\n    console.log("Hello, World!");\n}}\n\n\n// 메인 함수 실행\nmain();',
        '.html': f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.splitext(filename)[0]}</title>
</head>
<body>
    <h1>{os.path.splitext(filename)[0]}</h1>
    <p>이 파일은 HTML 파일입니다.</p>
    <p>작성자: 파일트리 자동생성기</p>
    <p>작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}</p>
</body>
</html>''',
        '.css': f'/* {os.path.splitext(filename)[0]} */\n/* 설명: 이 파일은 CSS 파일입니다. */\n/* 작성자: 파일트리 자동생성기 */\n/* 작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")} */\n\n\nbody {{\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f5f5f5;\n}}\n\n\nh1 {{\n    color: #333;\n    text-align: center;\n}}',
        '.json': f'{{\n    "name": "{os.path.splitext(filename)[0]}",\n    "description": "이 파일은 JSON 파일입니다.",\n    "author": "파일트리 자동생성기",\n    "created": "{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}",\n    "version": "1.0.0",\n    "data": {{\n        "example": "샘플 데이터"\n    }}\n}}',
        '.xml': f'''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <n>{os.path.splitext(filename)[0]}</n>
    <description>이 파일은 XML 파일입니다.</description>
    <author>파일트리 자동생성기</author>
    <created>{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}</created>
    <version>1.0.0</version>
    <data>
        <example>샘플 데이터</example>
    </data>
</root>''',
        '.csv': f'이름,설명,작성자,작성일\n{os.path.splitext(filename)[0]},이 파일은 CSV 파일입니다,파일트리 자동생성기,{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}',
        '.sql': f'-- {os.path.splitext(filename)[0]}\n-- 설명: 이 파일은 SQL 파일입니다.\n-- 작성자: 파일트리 자동생성기\n-- 작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}\n\n\n-- 샘플 쿼리\nSELECT * FROM example_table;\n\n\n-- 테이블 생성 예시\n-- CREATE TABLE example_table (\n--     id INT PRIMARY KEY,\n--     name VARCHAR(100),\n--     created_at TIMESTAMP\n-- );',
        '.bat': f'@echo off\nREM {os.path.splitext(filename)[0]}\nREM 설명: 이 파일은 Windows 배치 파일입니다.\nREM 작성자: 파일트리 자동생성기\nREM 작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}\n\n\necho Hello, World!\npause',
        '.sh': f'#!/bin/bash\n# {os.path.splitext(filename)[0]}\n# 설명: 이 파일은 Linux/Unix 쉘 스크립트입니다.\n# 작성자: 파일트리 자동생성기\n# 작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}\n\n\necho "Hello, World!"',
    }
    
    return content_map.get(ext, f'이 파일은 {ext} 확장자를 가진 파일입니다.\n\n작성자: 파일트리 자동생성기\n작성일: {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}')

def create_tree(base_path, tree):
    for node in tree:
        path = os.path.join(base_path, node['name'])
        if node['type'] == 'folder':
            os.makedirs(path, exist_ok=True)
            create_tree(path, node.get('children', []))
        else:
            # 파일 생성 시 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 실제 파일 경로가 있는지 확인
            if 'source_path' in node and os.path.exists(node['source_path']):
                # 실제 파일이 있으면 복사
                try:
                    shutil.copy2(node['source_path'], path)
                    print(f"파일 복사 완료: {node['name']} ({os.path.getsize(path)} bytes)")
                except Exception as e:
                    print(f"파일 복사 실패: {node['name']} - {e}")
                    # 복사 실패 시 기본 내용으로 생성
                    create_default_file(path, node['name'])
            else:
                # 실제 파일이 없으면 기본 내용으로 생성
                create_default_file(path, node['name'])

def create_default_file(path, filename):
    """기본 내용으로 파일 생성"""
    file_ext = os.path.splitext(filename)[1].lower()
    
    # 바이너리 파일인지 확인
    binary_extensions = {'.xlsx', '.docx', '.pptx', '.pdf', '.exe', '.dll', '.so', '.dylib', '.zip', '.rar', '.7z', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}
    
    if file_ext in binary_extensions:
        # 바이너리 파일은 빈 파일로 생성
        with open(path, 'wb') as f:
            f.write(b'')
        print(f"바이너리 파일 생성: {filename} (0 bytes)")
    else:
        # 텍스트 파일은 기본 내용과 함께 생성
        default_content = get_file_content_by_extension(filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        print(f"텍스트 파일 생성: {filename} ({len(default_content)} bytes)")

def open_folder(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

def path_to_tree(root_path):
    result = []
    if os.path.isdir(root_path):
        node = {
            'name': os.path.basename(root_path),
            'type': 'folder',
            'children': []
        }
        for item in sorted(os.listdir(root_path)):
            full = os.path.join(root_path, item)
            node['children'].extend(path_to_tree(full))
        result.append(node)
    else:
        node = {
            'name': os.path.basename(root_path),
            'type': 'file',
            'source_path': root_path  # 실제 파일 경로 저장
        }
        result.append(node)
    return result

def add_node(tree, parent_id, name, ntype, children=None, source_path=None):
    def _find_and_add(nodes, pid):
        for node in nodes:
            if id(node) == pid and node['type'] == 'folder':
                child = {'name': name, 'type': ntype}
                if ntype == 'folder':
                    child['children'] = children if children else []
                if source_path:
                    child['source_path'] = source_path
                node.setdefault('children', []).append(child)
                return True
            if node.get('children'):
                if _find_and_add(node['children'], pid):
                    return True
        return False
    if parent_id is None:
        child = {'name': name, 'type': ntype}
        if ntype == 'folder':
            child['children'] = children if children else []
        if source_path:
            child['source_path'] = source_path
        tree.append(child)
    else:
        _find_and_add(tree, parent_id)

def find_node(tree, target_id):
    for node in tree:
        if id(node) == target_id:
            return node, tree
        if node['type'] == 'folder' and node.get('children'):
            result = find_node(node['children'], target_id)
            if result:
                return result
    return None

def delete_node(tree, target_id):
    for idx, node in enumerate(tree):
        if id(node) == target_id:
            del tree[idx]
            return True
        if node['type'] == 'folder' and node.get('children'):
            if delete_node(node['children'], target_id):
                return True
    return False

def rename_node(tree, target_id, new_name):
    for node in tree:
        if id(node) == target_id:
            node['name'] = new_name
            return True
        if node['type'] == 'folder' and node.get('children'):
            if rename_node(node['children'], target_id, new_name):
                return True
    return False

def move_nodes(tree, from_ids, to_id):
    nodes_to_move = []
    for fid in from_ids:
        result = find_node(tree, fid)
        if result is not None:  # None 체크 추가
            node, parent = result
            nodes_to_move.append((fid, node))
    for fid, node in nodes_to_move:
        delete_node(tree, fid)
    if to_id is None:
        for _, node in nodes_to_move:
            tree.append(node)
    else:
        result = find_node(tree, to_id)
        if result is not None:  # None 체크 추가
            dest_node, _ = result
            if dest_node and dest_node['type'] == 'folder':
                for _, node in nodes_to_move:
                    dest_node.setdefault('children', []).append(node)

def move_node_up(tree, node_id):
    """노드를 위로 이동"""
    def _find_and_move_up(nodes):
        for i, node in enumerate(nodes):
            if id(node) == node_id:
                if i > 0:  # 첫 번째 항목이 아닌 경우에만 이동
                    nodes[i], nodes[i-1] = nodes[i-1], nodes[i]
                    return True
                return False
            if node.get('children'):
                if _find_and_move_up(node['children']):
                    return True
        return False
    return _find_and_move_up(tree)

def move_node_down(tree, node_id):
    """노드를 아래로 이동"""
    def _find_and_move_down(nodes):
        for i, node in enumerate(nodes):
            if id(node) == node_id:
                if i < len(nodes) - 1:  # 마지막 항목이 아닌 경우에만 이동
                    nodes[i], nodes[i+1] = nodes[i+1], nodes[i]
                    return True
                return False
            if node.get('children'):
                if _find_and_move_down(node['children']):
                    return True
        return False
    return _find_and_move_down(tree)

def populate_treeview(treeview, parent, nodes, nodeid2iid):
    for node in nodes:
        display = f"[폴더] {node['name']}" if node['type']=='folder' else f"[파일] {node['name']}"
        iid = treeview.insert(parent, 'end', text=display, open=True)
        nodeid2iid[id(node)] = iid
        treeview.set(iid, 'real_id', id(node))
        if node['type'] == 'folder':
            populate_treeview(treeview, iid, node.get('children', []), nodeid2iid)

class TemplateEditor(ctk.CTkToplevel):
    def __init__(self, master, templates, template_name=None):
        super().__init__(master)
        
        # 창 제목을 선택된 템플릿 이름으로 설정
        if template_name:
            self.title(template_name)
        else:
            self.title("새 템플릿")
            
        self.geometry("1200x800")  # 창 크기 증가
        self.templates = templates
        self.template_name = template_name
        self.tree = [] if template_name is None else [self._deepcopy(x) for x in templates[template_name]]
        self.selected_node_ids = []
        self.nodeid2iid = {}
        self.iid2nodeid = {}
        self._dragging_items = None
        self._drag_from_ids = None
        self._last_drag_over = None
        self._dragging = False
        self._ctrl_pressed = False
        self._shift_pressed = False
        self._last_clicked_item = None
        self.dnd_available = True  # 드래그 앤 드롭 사용 가능 여부
        self.build_gui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # ESC 키로 창 닫기 기능 추가
        self.bind("<Escape>", lambda e: self._on_close())
        
        # 창을 최상위로 가져오고 포커스 설정
        self.lift()
        self.focus_force()
        self.grab_set()  # 모달 창으로 설정
        
        # 창 자체에도 드래그 앤 드롭 설정 - 안전한 처리
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop_files)
            print("창 레벨 드래그 앤 드롭 기능 활성화됨")
        except Exception as e:
            print(f"창 레벨 드래그 앤 드롭 기능 비활성화됨: {e}")
            self.dnd_available = False

    def _deepcopy(self, node):
        import copy
        return copy.deepcopy(node)

    def build_gui(self):
        # 메인 프레임
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 제목
        if self.template_name:
            title_text = self.template_name
        else:
            title_text = "새 템플릿"
        title_label = ctk.CTkLabel(main_frame, text=title_text, 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(0, 10))
        
        # 컨텐츠 프레임 (트리뷰와 버튼을 나란히 배치)
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 좌측 패널 (트리뷰)
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # 트리뷰 프레임
        tree_frame = ctk.CTkFrame(left_panel)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 트리뷰 생성
        self.treeview = ttk.Treeview(tree_frame, columns=('real_id',), selectmode='extended')
        self.treeview.heading('#0', text='구성 (Ctrl/Shift+클릭으로 다중선택, 드래그로 이동, 더블클릭으로 폴더 접기/펼치기)')
        self.treeview.column('real_id', width=0, stretch=False)
        self.treeview.pack(fill='both', expand=True, side='left')
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.treeview.yview)
        scrollbar.pack(side='right', fill='y')
        self.treeview.configure(yscrollcommand=scrollbar.set)
        
        # 드래그 앤 드롭 설정 - 안전한 처리
        try:
            self.treeview.drop_target_register(DND_FILES)
            self.treeview.dnd_bind('<<Drop>>', self.on_drop_files)
            print("드래그 앤 드롭 기능 활성화됨")
        except Exception as e:
            print(f"드래그 앤 드롭 기능 비활성화됨: {e}")
            # 대안: 파일 선택 버튼으로 대체
            self.dnd_available = False
        
        # 키보드 이벤트 바인딩 - 더 안정적인 방법
        self.treeview.bind("<KeyPress>", self.on_key_press)
        self.treeview.bind("<KeyRelease>", self.on_key_release)
        
        # 창 레벨에서도 키보드 이벤트 처리
        self.bind("<KeyPress>", self.on_key_press)
        self.bind("<KeyRelease>", self.on_key_release)
        
        # 마우스 이벤트 바인딩 - 충돌 방지를 위해 단일 핸들러로 통합
        self.treeview.bind("<ButtonPress-1>", self.on_click)
        self.treeview.bind("<B1-Motion>", self.on_drag_motion)
        self.treeview.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.treeview.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.treeview.bind("<ButtonPress-3>", self.show_context_menu)
        self.treeview.bind("<F2>", self.rename_shortcut)
        self.treeview.bind("<Double-Button-1>", self.on_double_click)

        # 우측 패널 (버튼들)
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side='right', fill='y', padx=(5, 0))
        
        # 버튼 프레임
        btn_frame = ctk.CTkFrame(right_panel)
        btn_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 버튼들
        ctk.CTkButton(btn_frame, text="📁 폴더 추가", command=self.add_folder, 
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(btn_frame, text="📄 파일 추가", command=self.add_file, 
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(btn_frame, text="📂 내PC에서 폴더 불러오기", command=self.import_folders_loop, 
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(btn_frame, text="📋 내PC에서 파일 불러오기", command=self.import_files, 
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        
        # 선택된 항목 관련 버튼들
        self.btn_rename = ctk.CTkButton(btn_frame, text="✏️ 이름 바꾸기", command=self.rename_selected, 
                                       state='disabled', font=ctk.CTkFont(size=12))
        self.btn_rename.pack(fill='x', pady=2)
        self.btn_delete = ctk.CTkButton(btn_frame, text="🗑️ 삭제", command=self.delete_selected, 
                                       state='disabled', font=ctk.CTkFont(size=12))
        self.btn_delete.pack(fill='x', pady=2)
        
        # 항목 순서 이동 버튼
        order_frame = ctk.CTkFrame(btn_frame)
        order_frame.pack(fill='x', pady=2)
        
        ctk.CTkButton(order_frame, text="↑ 위로", command=self.move_selected_up,
                      font=ctk.CTkFont(size=12)).pack(side='left', fill='x', expand=True, padx=(0, 2))
        ctk.CTkButton(order_frame, text="↓ 아래로", command=self.move_selected_down,
                      font=ctk.CTkFont(size=12)).pack(side='right', fill='x', expand=True, padx=(2, 0))
        
        # 저장 버튼
        ctk.CTkButton(btn_frame, text="💾 저장", command=self.save_template, 
                      font=ctk.CTkFont(size=14, weight="bold")).pack(fill='x', pady=10)
        
        # 사용법 안내
        info_text = """💡 사용법:
• Ctrl+클릭: 다중선택
• Shift+클릭: 범위 선택
• 더블클릭: 폴더 접기/펼치기
• 드래그: 항목 이동
• 우클릭: 이름 바꾸기/삭제/폴더 접기펼치기
• ESC 키: 창 닫기"""
        
        info_label = ctk.CTkLabel(btn_frame, text=info_text, 
                                 font=ctk.CTkFont(size=11), justify='left')
        info_label.pack(fill='x', pady=10)
        
        self.refresh_treeview()

    def on_key_press(self, event):
        """키보드 키 누름 이벤트"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self._ctrl_pressed = True
            print("Ctrl 키 누름")
        elif event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self._shift_pressed = True
            print("Shift 키 누름")

    def on_key_release(self, event):
        """키보드 키 해제 이벤트"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self._ctrl_pressed = False
            print("Ctrl 키 해제")
        elif event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self._shift_pressed = False
            print("Shift 키 해제")

    def on_click(self, event):
        """마우스 클릭 이벤트 - 클릭과 드래그를 구분"""
        self._click_start_x = event.x
        self._click_start_y = event.y
        self._click_start_time = self.after_idle(lambda: None)  # 현재 시간 기록
        
        # 클릭된 아이템 확인
        iid = self.treeview.identify_row(event.y)
        if iid:
            # Ctrl+클릭: 다중선택
            if self._ctrl_pressed:
                current_selection = list(self.treeview.selection())
                if iid in current_selection:
                    self.treeview.selection_remove(iid)
                else:
                    self.treeview.selection_add(iid)
                # Ctrl+클릭 시 이벤트 전파 중단
                return "break"
            # Shift+클릭: 범위 선택
            elif self._shift_pressed and self._last_clicked_item:
                all_items = self.get_all_treeview_items()
                try:
                    i1 = all_items.index(self._last_clicked_item)
                    i2 = all_items.index(iid)
                    sel_range = all_items[min(i1,i2):max(i1,i2)+1]
                    self.treeview.selection_set(sel_range)
                except:
                    self.treeview.selection_set(iid)
                # Shift+클릭 시 이벤트 전파 중단
                return "break"
            # 일반 클릭: 단일 선택
            else:
                self.treeview.selection_set(iid)
            
            self._last_clicked_item = iid

    def get_all_treeview_items(self):
        """트리뷰의 모든 항목을 순서대로 가져오기"""
        def get_items_recursive(parent=''):
            items = []
            for child in self.treeview.get_children(parent):
                items.append(child)
                # 하위 항목들도 재귀적으로 가져오기
                items.extend(get_items_recursive(child))
            return items
        return get_items_recursive()

    def on_double_click(self, event):
        """더블클릭 이벤트 - 폴더 접기/펼치기"""
        iid = self.treeview.identify_row(event.y)
        if iid:
            # 폴더인지 확인
            item_text = self.treeview.item(iid, 'text')
            print(f"더블클릭: {item_text}")
            if item_text.startswith('[폴더]'):
                # 폴더 접기/펼치기
                current_state = self.treeview.item(iid, 'open')
                new_state = not current_state
                self.treeview.item(iid, open=new_state)
                print(f"폴더 상태 변경: {item_text} - {'펼침' if new_state else '접힘'}")
                # 이벤트 처리 완료 표시
                return "break"
            else:
                # 파일인 경우 선택만
                self.treeview.selection_set(iid)
                print(f"파일 선택: {item_text}")
                return "break"
        return "break"  # 더블클릭 이벤트가 다른 이벤트와 충돌하지 않도록



    def on_tree_select(self, event=None):
        sel = self.treeview.selection()
        self.selected_node_ids = [int(self.treeview.set(i, 'real_id')) for i in sel]
        state = 'normal' if self.selected_node_ids else 'disabled'
        self.btn_delete.configure(state=state)
        self.btn_rename.configure(state=state if len(self.selected_node_ids) == 1 else 'disabled')



    def on_drag_motion(self, event):
        """드래그 모션 이벤트 - 클릭과 드래그를 구분"""
        # 클릭 시작점과 현재 위치의 거리 계산
        if hasattr(self, '_click_start_x') and hasattr(self, '_click_start_y'):
            distance = ((event.x - self._click_start_x) ** 2 + (event.y - self._click_start_y) ** 2) ** 0.5
            
            # 드래그 시작 (일정 거리 이상 이동했을 때)
            if distance > 5:  # 5픽셀 이상 이동하면 드래그로 인식
                if not hasattr(self, '_dragging') or not self._dragging:
                    self._dragging = True
                    # 드래그 시작 시 선택된 아이템들 저장
                    items = self.treeview.selection()
                    if items:
                        self._dragging_items = items
                        self._drag_from_ids = [int(self.treeview.set(i, 'real_id')) for i in items]
                    else:
                        self._dragging_items = None
                        self._drag_from_ids = None
        
        # 드래그 중일 때만 타겟 하이라이트
        if hasattr(self, '_dragging') and self._dragging:
            iid = self.treeview.identify_row(event.y)
            if iid and iid != self._last_drag_over:
                self.treeview.selection_set(iid)
                self._last_drag_over = iid

    def on_drag_stop(self, event):
        """드래그 종료 이벤트 - 클릭과 드래그를 구분"""
        # 클릭으로 인식 (드래그가 아닌 경우)
        if not hasattr(self, '_dragging') or not self._dragging:
            # 클릭 이벤트 처리 완료
            return
        
        # 드래그로 인식된 경우
        if self._dragging_items and self._drag_from_ids:
            target_item = self.treeview.identify_row(event.y)
            to_id = None
            
            if target_item:
                to_id = int(self.treeview.set(target_item, 'real_id'))
                target_text = self.treeview.item(target_item, 'text')
                # 폴더가 아니거나 자기 자신을 대상으로 하는 경우 맨 위로 이동
                if not target_text.startswith('[폴더]') or any(x == to_id for x in self._drag_from_ids):
                    to_id = None  # 맨 위로 이동
            else:
                # 드래그 대상이 없으면 맨 위로 이동
                to_id = None
            
            try:
                move_nodes(self.tree, self._drag_from_ids, to_id)
                self.refresh_treeview(selected_ids=self._drag_from_ids)
            except Exception as e:
                print(f"노드 이동 오류: {e}")
                self.refresh_treeview(selected_ids=self._drag_from_ids)
        
        # 드래그 상태 초기화
        self._dragging_items = None
        self._drag_from_ids = None
        self._dragging = False
        self._last_drag_over = None

    def show_context_menu(self, event):
        iid = self.treeview.identify_row(event.y)
        if iid:
            self.treeview.selection_set(iid)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="이름 바꾸기 (F2)", command=self.rename_selected)
            menu.add_command(label="삭제", command=self.delete_selected)
            menu.add_separator()
            menu.add_command(label="폴더 접기/펼치기", command=lambda: self.toggle_folder(iid))
            menu.tk_popup(event.x_root, event.y_root)

    def toggle_folder(self, iid):
        item_text = self.treeview.item(iid, 'text')
        if item_text.startswith('[폴더]'):
            if self.treeview.item(iid, 'open'):
                self.treeview.item(iid, open=False)
            else:
                self.treeview.item(iid, open=True)

    def rename_shortcut(self, event):
        self.rename_selected()

    def add_folder(self):
        name = simpledialog.askstring("폴더 이름", "폴더명을 입력하세요:", parent=self)
        if name:
            parent_id = self.selected_node_ids[0] if self.selected_node_ids else None
            add_node(self.tree, parent_id, name, 'folder')
            self.refresh_treeview()

    def add_file(self):
        name = simpledialog.askstring("파일 이름", "파일명을 입력하세요:", parent=self)
        if name:
            parent_id = self.selected_node_ids[0] if self.selected_node_ids else None
            add_node(self.tree, parent_id, name, 'file')
            self.refresh_treeview()

    def delete_selected(self):
        ids = self.get_selected_node_ids()
        for sel_id in sorted(ids, reverse=True):
            delete_node(self.tree, sel_id)
        self.refresh_treeview()

    def rename_selected(self):
        ids = self.get_selected_node_ids()
        if len(ids) == 1:
            node, _ = find_node(self.tree, ids[0])
            
            # 커스텀 다이얼로그 생성 (더 긴 입력창)
            dialog = tk.Toplevel(self)
            dialog.title("이름 바꾸기")
            dialog.geometry("500x150")
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            
            # 중앙 정렬
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (150 // 2)
            dialog.geometry(f"500x150+{x}+{y}")
            
            # 프레임
            frame = ctk.CTkFrame(dialog)
            frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # 라벨
            label = ctk.CTkLabel(frame, text="새 이름을 입력하세요:", 
                                font=ctk.CTkFont(size=14))
            label.pack(pady=(0, 10))
            
            # 입력창 (더 긴 길이)
            entry_var = tk.StringVar(value=node['name'])
            entry = ctk.CTkEntry(frame, textvariable=entry_var, font=ctk.CTkFont(size=14), width=400)
            entry.pack(pady=(0, 20))
            entry.focus_set()
            entry.select_range(0, tk.END)
            
            # 버튼 프레임
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.pack(fill='x')
            
            result = [None]  # 결과를 저장할 리스트
            
            def on_ok():
                new_name = entry_var.get().strip()
                if not new_name:
                    messagebox.showwarning("경고", "이름을 입력하세요.", parent=dialog)
                    return
                result[0] = new_name
                dialog.destroy()
            
            def on_cancel():
                dialog.destroy()
            
            # 버튼들
            ctk.CTkButton(btn_frame, text="확인", command=on_ok, 
                          font=ctk.CTkFont(size=12)).pack(side='left', fill='x', expand=True, padx=(0, 5))
            ctk.CTkButton(btn_frame, text="취소", command=on_cancel, 
                          font=ctk.CTkFont(size=12)).pack(side='right', fill='x', expand=True, padx=(5, 0))
            
            # Enter 키와 Escape 키 바인딩
            entry.bind('<Return>', lambda e: on_ok())
            dialog.bind('<Escape>', lambda e: on_cancel())
            
            # 다이얼로그가 닫힐 때까지 대기
            dialog.wait_window()
            
            # 결과 처리
            if result[0]:
                new_name = result[0]
                rename_node(self.tree, ids[0], new_name)
                self.refresh_treeview()

    def move_selected_up(self):
        """선택된 항목을 위로 이동"""
        ids = self.get_selected_node_ids()
        if len(ids) == 1:
            if move_node_up(self.tree, ids[0]):
                self.refresh_treeview(selected_ids=ids)

    def move_selected_down(self):
        """선택된 항목을 아래로 이동"""
        ids = self.get_selected_node_ids()
        if len(ids) == 1:
            if move_node_down(self.tree, ids[0]):
                self.refresh_treeview(selected_ids=ids)

    def import_files(self):
        files = filedialog.askopenfilenames(
            title="파일 선택(복수 가능)",
            parent=self
        )
        self.lift(); self.focus_force()
        if files:
            for file_path in files:
                if os.path.exists(file_path):
                    nodes = path_to_tree(file_path)
                    for n in nodes:
                        add_node(self.tree, None, n['name'], n['type'], n.get('children'), n.get('source_path'))
            self.refresh_treeview()

    def import_folders_loop(self):
        while True:
            folder = filedialog.askdirectory(
                title="폴더 선택 (취소시 종료)",
                parent=self
            )
            self.lift(); self.focus_force()
            if not folder:
                break
            nodes = path_to_tree(folder)
            for n in nodes:
                add_node(self.tree, None, n['name'], n['type'], n.get('children'), n.get('source_path'))
            self.refresh_treeview()

    def on_drop_files(self, event):
        if not hasattr(self, 'dnd_available') or not self.dnd_available:
            print("드래그 앤 드롭 기능이 비활성화되어 있습니다.")
            messagebox.showwarning("경고", "드래그 앤 드롭 기능이 사용할 수 없습니다.\n파일 선택 버튼을 사용해주세요.", parent=self)
            return
        
        try:
            print(f"드래그 앤 드롭 이벤트 발생: {event.data}")
            files = self.split_drop_files(event.data)
            print(f"분리된 파일 목록: {files}")
            
            added_count = 0
            for f in files:
                # 경로 정규화 및 따옴표 제거
                f = os.path.normpath(f.strip('"'))
                print(f"정규화된 경로: {f}")
                
                if os.path.exists(f):
                    print(f"파일 추가 중: {f}")
                    nodes = path_to_tree(f)
                    for n in nodes:
                        add_node(self.tree, None, n['name'], n['type'], n.get('children'), n.get('source_path'))
                        added_count += 1
                else:
                    print(f"파일이 존재하지 않음: {f}")
            
            if added_count > 0:
                self.refresh_treeview()
                print(f"드래그 앤 드롭 완료: {added_count}개 항목 추가")
                messagebox.showinfo("성공", f"{added_count}개 항목이 추가되었습니다.", parent=self)
            else:
                print("추가된 항목이 없습니다.")
                messagebox.showwarning("경고", "추가할 수 있는 파일이 없습니다.", parent=self)
        except Exception as e:
            print(f"드래그 앤 드롭 오류: {e}")
            messagebox.showerror("오류", f"파일 추가 중 오류가 발생했습니다: {e}", parent=self)

    def split_drop_files(self, data):
        try:
            print(f"원본 드롭 데이터: {data}")
            
            # Windows 경로에서 중괄호 제거
            if data.startswith('{') and data.endswith('}'):
                data = data[1:-1]
                print(f"중괄호 제거 후: {data}")
            
            # 여러 파일이 중괄호로 구분된 경우 처리
            if '}{' in data:
                files = []
                parts = data.split('}{')
                for i, part in enumerate(parts):
                    if i == 0:
                        part = part.lstrip('{')
                    elif i == len(parts) - 1:
                        part = part.rstrip('}')
                    files.append(part)
                print(f"중괄호 분리 결과: {files}")
                return files
            
            # 일반적인 경우 - 더 간단한 방법 사용
            if ' ' in data:
                # 공백으로 분리하되 따옴표 처리
                files = []
                current = ""
                in_quotes = False
                for char in data:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ' ' and not in_quotes:
                        if current.strip():
                            files.append(current.strip())
                        current = ""
                    else:
                        current += char
                if current.strip():
                    files.append(current.strip())
                print(f"공백 분리 결과: {files}")
                return files
            else:
                print(f"단일 파일: {data}")
                return [data]
        except Exception as e:
            print(f"파일 경로 분리 오류: {e}")
            return [data]  # 실패 시 원본 데이터 반환

    def refresh_treeview(self, selected_ids=None):
        self.treeview.delete(*self.treeview.get_children())
        self.nodeid2iid = {}
        populate_treeview(self.treeview, '', self.tree, self.nodeid2iid)
        if selected_ids:
            select_iids = [self.nodeid2iid[x] for x in selected_ids if x in self.nodeid2iid]
            self.treeview.selection_set(select_iids)
            self.selected_node_ids = selected_ids
        else:
            self.selected_node_ids = []
            self.btn_delete.configure(state='disabled')
            self.btn_rename.configure(state='disabled')

    def get_selected_node_ids(self):
        sel = self.treeview.selection()
        return [int(self.treeview.set(i, 'real_id')) for i in sel]

    def save_template(self):
        if self.template_name is None:
            name = simpledialog.askstring("템플릿 이름", "템플릿 이름을 입력하세요:", parent=self)
            if not name or name in self.templates:
                messagebox.showerror("오류", "이름이 없거나 중복되었습니다.", parent=self)
                self.lift(); self.focus_force()
                return
            self.templates[name] = [self._deepcopy(x) for x in self.tree]
        else:
            self.templates[self.template_name] = [self._deepcopy(x) for x in self.tree]
        save_templates(self.templates)
        self.master.refresh_template_list()
        self.destroy()

    def _on_close(self):
        self.master.refresh_template_list()
        self.destroy()

class FileTreeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("파일트리 자동생성기 v1.0.0")
        self.geometry("1200x800")
        self.templates = load_templates()
        self.build_gui()
        
        # ESC 키로 창 닫기 기능 추가
        self.bind("<Escape>", lambda e: self.quit())

    def build_gui(self):
        # 메인 프레임
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 제목 프레임
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
        # 제목 (중간정렬)
        title_label = ctk.CTkLabel(title_frame, text="파일트리 자동생성기 v1.0.0", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(expand=True, pady=10)
        
        # 개발자 정보 (오른쪽 여백 추가)
        developer_label = ctk.CTkLabel(title_frame, text="개발자: 이재호", 
                                      font=ctk.CTkFont(size=12))
        developer_label.pack(side='right', pady=10, padx=(0, 20))
        
        # 컨텐츠 프레임
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 좌측 패널 (템플릿 목록)
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        
        # 템플릿 목록 제목
        template_title = ctk.CTkLabel(left_panel, text="📋 저장된 템플릿", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
        template_title.pack(pady=10)
        
        # 템플릿 목록 프레임
        template_list_frame = ctk.CTkFrame(left_panel)
        template_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 템플릿 리스트박스
        self.template_listbox = tk.Listbox(template_list_frame, 
                                          font=ctk.CTkFont(size=12),
                                          selectmode='extended',
                                          bg='#2b2b2b', fg='white',
                                          selectbackground='#1f538d',
                                          selectforeground='white')
        self.template_listbox.pack(fill='both', expand=True, side='left')
        
        # 템플릿 선택 이벤트 바인딩
        self.template_listbox.bind('<<ListboxSelect>>', lambda e: self.update_selected_template())
        # 템플릿 더블클릭 이벤트 바인딩
        self.template_listbox.bind('<Double-Button-1>', lambda e: self.edit_template())
        
        # Ctrl, Shift 키 상태 추적을 위한 변수들
        self._ctrl_pressed = False
        self._shift_pressed = False
        self._last_clicked_template = None
        
        # 키보드 이벤트 바인딩
        self.template_listbox.bind('<KeyPress>', self.on_template_key_press)
        self.template_listbox.bind('<KeyRelease>', self.on_template_key_release)
        self.template_listbox.bind('<ButtonPress-1>', self.on_template_click)
        self.template_listbox.bind('<F2>', lambda e: self.rename_template())
        
        # 템플릿 리스트 스크롤바
        template_scrollbar = ttk.Scrollbar(template_list_frame, orient="vertical", 
                                          command=self.template_listbox.yview)
        template_scrollbar.pack(side='right', fill='y')
        self.template_listbox.configure(yscrollcommand=template_scrollbar.set)
        
        # 템플릿 순서 변경 버튼 프레임
        order_frame = ctk.CTkFrame(left_panel)
        order_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkButton(order_frame, text="↑ 위로", command=self.move_template_up,
                      font=ctk.CTkFont(size=11)).pack(side='left', fill='x', expand=True, padx=(0, 2))
        ctk.CTkButton(order_frame, text="↓ 아래로", command=self.move_template_down,
                      font=ctk.CTkFont(size=11)).pack(side='right', fill='x', expand=True, padx=(2, 0))
        
        # 템플릿 관련 버튼들
        template_btn_frame = ctk.CTkFrame(left_panel)
        template_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkButton(template_btn_frame, text="📝 새 템플릿 만들기", command=self.create_new_template,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(template_btn_frame, text="✏️ 템플릿 편집", command=self.edit_template,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(template_btn_frame, text="✏️ 이름 바꾸기", command=self.rename_template,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(template_btn_frame, text="🗑️ 템플릿 삭제", command=self.delete_template,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        
        # 우측 패널 (생성 옵션)
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 생성 옵션 제목
        generate_title = ctk.CTkLabel(right_panel, text="🚀 파일트리 생성", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
        generate_title.pack(pady=10)
        
        # 생성 옵션 프레임
        options_frame = ctk.CTkFrame(right_panel)
        options_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 선택된 템플릿 표시
        self.selected_template_label = ctk.CTkLabel(options_frame, text="선택된 템플릿: 없음",
                                                  font=ctk.CTkFont(size=14))
        self.selected_template_label.pack(pady=10)
        
        # 생성 경로 프레임
        path_frame = ctk.CTkFrame(options_frame)
        path_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(path_frame, text="생성 경로:", 
                    font=ctk.CTkFont(size=12)).pack(anchor='w', padx=10, pady=(10, 5))
        
        self.path_var = tk.StringVar()
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var,
                                      font=ctk.CTkFont(size=12))
        self.path_entry.pack(fill='x', padx=10, pady=(0, 5))
        
        ctk.CTkButton(path_frame, text="📁 경로 지정", command=self.select_folder,
                      font=ctk.CTkFont(size=11)).pack(fill='x', padx=10, pady=(0, 10))
        
        # 생성 버튼
        ctk.CTkButton(options_frame, text="🎯 파일트리 생성", command=self.generate_tree,
                      font=ctk.CTkFont(size=16, weight="bold")).pack(fill='x', pady=20)
        
        # 결과 프레임
        result_frame = ctk.CTkFrame(options_frame)
        result_frame.pack(fill='both', expand=True, pady=10)
        
        ctk.CTkLabel(result_frame, text="생성 결과:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w', padx=10, pady=(10, 5))
        
        # 결과 텍스트
        self.result_text = tk.Text(result_frame, height=10, 
                                  font=ctk.CTkFont(size=11),
                                  bg='#2b2b2b', fg='white',
                                  insertbackground='white')
        self.result_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # 결과 스크롤바
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", 
                                        command=self.result_text.yview)
        result_scrollbar.pack(side='right', fill='y')
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
        
        # 하단 버튼 프레임
        bottom_frame = ctk.CTkFrame(options_frame)
        bottom_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(bottom_frame, text="📂 생성된 폴더 열기", command=self.open_generated_folder,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        ctk.CTkButton(bottom_frame, text="🗑️ 결과 지우기", command=self.clear_result,
                      font=ctk.CTkFont(size=12)).pack(fill='x', pady=2)
        
        # 사용법 안내 (스크롤바 추가)
        info_text = """💡 사용법:
1. 좌측에서 템플릿을 선택하세요 (더블클릭으로 편집)
2. 우측에서 생성 경로를 설정하세요
3. "파일트리 생성" 버튼을 클릭하세요
4. 생성된 폴더를 열어 결과를 확인하세요

✨ 새 기능:
• Ctrl+클릭으로 폴더 다중선택
• Shift+클릭으로 범위 선택
• 더블클릭으로 폴더 접기/펼치기
• 템플릿 순서 변경 가능
• F2 키로 템플릿 이름 변경
• 템플릿 이름 변경 버튼 추가
• 우클릭 컨텍스트 메뉴
• 드래그 앤 드롭으로 아이템 이동"""
        
        # 정보 텍스트를 위한 프레임과 스크롤바
        info_frame = ctk.CTkFrame(options_frame)
        info_frame.pack(fill='both', expand=True, pady=10)
        
        # 텍스트 위젯 생성
        info_text_widget = tk.Text(info_frame, 
                                  font=ctk.CTkFont(size=11),
                                  bg='#2b2b2b', fg='white',
                                  insertbackground='white',
                                  selectbackground='#1f538d',
                                  selectforeground='white',
                                  wrap='word',
                                  height=8)
        info_text_widget.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        
        # 스크롤바 추가
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", 
                                      command=info_text_widget.yview)
        info_scrollbar.pack(side='right', fill='y', pady=5)
        info_text_widget.configure(yscrollcommand=info_scrollbar.set)
        
        # 텍스트 삽입
        info_text_widget.insert('1.0', info_text)
        info_text_widget.configure(state='disabled')  # 읽기 전용으로 설정
        
        self.refresh_template_list()

    def refresh_template_list(self):
        self.template_listbox.delete(0, tk.END)
        for name in self.templates.keys():
            self.template_listbox.insert(tk.END, name)
        if self.template_listbox.size() > 0:
            self.template_listbox.selection_set(0)
            self.update_selected_template()

    def update_selected_template(self):
        selection = self.template_listbox.curselection()
        if selection:
            template_name = self.template_listbox.get(selection[0])
            self.selected_template_label.configure(text=f"선택된 템플릿: {template_name}")
        else:
            self.selected_template_label.configure(text="선택된 템플릿: 없음")

    def move_template_up(self):
        selection = self.template_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        # 템플릿 순서 변경
        template_names = list(self.templates.keys())
        current_idx = selection[0]
        template_names[current_idx], template_names[current_idx-1] = template_names[current_idx-1], template_names[current_idx]
        
        # 새로운 순서로 딕셔너리 재생성
        new_templates = {}
        for name in template_names:
            new_templates[name] = self.templates[name]
        self.templates = new_templates
        
        # 저장 및 리스트 업데이트
        save_templates(self.templates)
        self.refresh_template_list()
        
        # 선택 상태 복원 (이동된 위치로)
        try:
            self.template_listbox.selection_clear(0, tk.END)
            self.template_listbox.selection_set(current_idx-1)
            self.template_listbox.see(current_idx-1)
        except:
            pass

    def move_template_down(self):
        selection = self.template_listbox.curselection()
        if not selection or selection[0] == self.template_listbox.size() - 1:
            return
        
        # 템플릿 순서 변경
        template_names = list(self.templates.keys())
        current_idx = selection[0]
        template_names[current_idx], template_names[current_idx+1] = template_names[current_idx+1], template_names[current_idx]
        
        # 새로운 순서로 딕셔너리 재생성
        new_templates = {}
        for name in template_names:
            new_templates[name] = self.templates[name]
        self.templates = new_templates
        
        # 저장 및 리스트 업데이트
        save_templates(self.templates)
        self.refresh_template_list()
        
        # 선택 상태 복원 (이동된 위치로)
        try:
            self.template_listbox.selection_clear(0, tk.END)
            self.template_listbox.selection_set(current_idx+1)
            self.template_listbox.see(current_idx+1)
        except:
            pass

    def create_new_template(self):
        editor = TemplateEditor(self, self.templates)
        self.wait_window(editor)

    def edit_template(self):
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "편집할 템플릿을 선택하세요.")
            return
        template_name = self.template_listbox.get(selection[0])
        editor = TemplateEditor(self, self.templates, template_name)
        self.wait_window(editor)

    def delete_template(self):
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 템플릿을 선택하세요.")
            return
        template_name = self.template_listbox.get(selection[0])
        if messagebox.askyesno("확인", f"'{template_name}' 템플릿을 삭제하시겠습니까?"):
            del self.templates[template_name]
            save_templates(self.templates)
            self.refresh_template_list()

    def rename_template(self):
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "이름을 바꿀 템플릿을 선택하세요.")
            return
        template_name = self.template_listbox.get(selection[0])
        
        # 커스텀 다이얼로그 생성 (더 긴 입력창)
        dialog = tk.Toplevel(self)
        dialog.title("템플릿 이름 바꾸기")
        dialog.geometry("500x150")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 중앙 정렬
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
        dialog.geometry(f"500x150+{x}+{y}")
        
        # 프레임
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 라벨
        label = ctk.CTkLabel(frame, text=f"'{template_name}'의 새 이름을 입력하세요:", 
                            font=ctk.CTkFont(size=14))
        label.pack(pady=(0, 10))
        
        # 입력창 (더 긴 길이)
        entry_var = tk.StringVar(value=template_name)
        entry = ctk.CTkEntry(frame, textvariable=entry_var, font=ctk.CTkFont(size=14), width=400)
        entry.pack(pady=(0, 20))
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        # 버튼 프레임
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill='x')
        
        result = [None]  # 결과를 저장할 리스트
        
        def on_ok():
            new_name = entry_var.get().strip()
            if not new_name:
                messagebox.showwarning("경고", "이름을 입력하세요.", parent=dialog)
                return
            if new_name in self.templates and new_name != template_name:
                messagebox.showwarning("경고", "이미 존재하는 템플릿 이름입니다.", parent=dialog)
                return
            result[0] = new_name
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # 버튼들
        ctk.CTkButton(btn_frame, text="확인", command=on_ok, 
                      font=ctk.CTkFont(size=12)).pack(side='left', fill='x', expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="취소", command=on_cancel, 
                      font=ctk.CTkFont(size=12)).pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        # Enter 키와 Escape 키 바인딩
        entry.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # 다이얼로그가 닫힐 때까지 대기
        dialog.wait_window()
        
        # 결과 처리
        if result[0]:
            new_name = result[0]
            self.templates[new_name] = self.templates.pop(template_name)
            save_templates(self.templates)
            self.refresh_template_list()
            messagebox.showinfo("완료", f"템플릿 이름이 '{template_name}'에서 '{new_name}'으로 변경되었습니다.")

    def select_folder(self):
        folder = filedialog.askdirectory(title="파일트리 생성할 경로 선택")
        if folder:
            self.path_var.set(folder)

    def generate_tree(self):
        selection = self.template_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "사용할 템플릿을 선택하세요.")
            return
        
        template_name = self.template_listbox.get(selection[0])
        base_path = self.path_var.get().strip()
        
        if not base_path:
            messagebox.showwarning("경고", "생성할 경로를 선택하세요.")
            return
        
        if not os.path.exists(base_path):
            try:
                os.makedirs(base_path)
            except Exception as e:
                messagebox.showerror("오류", f"폴더 생성 실패: {e}")
                return
        
        try:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"파일트리 생성 시작...\n")
            self.result_text.insert(tk.END, f"템플릿: {template_name}\n")
            self.result_text.insert(tk.END, f"생성 경로: {base_path}\n")
            self.result_text.insert(tk.END, "-" * 50 + "\n")
            
            create_tree(base_path, self.templates[template_name])
            
            self.result_text.insert(tk.END, "✅ 파일트리 생성 완료!\n")
            self.result_text.insert(tk.END, f"생성된 폴더: {base_path}\n")
            
            messagebox.showinfo("완료", "파일트리가 성공적으로 생성되었습니다!")
            
        except Exception as e:
            error_msg = f"파일트리 생성 중 오류 발생: {e}"
            self.result_text.insert(tk.END, f"❌ {error_msg}\n")
            messagebox.showerror("오류", error_msg)

    def open_generated_folder(self):
        path = self.path_var.get().strip()
        if path and os.path.exists(path):
            open_folder(path)
        else:
            messagebox.showwarning("경고", "생성된 폴더가 없습니다.")

    def clear_result(self):
        self.result_text.delete(1.0, tk.END)
    
    def on_template_key_press(self, event):
        """템플릿 리스트박스 키보드 이벤트 - 키 누름"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self._ctrl_pressed = True
        elif event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self._shift_pressed = True
    
    def on_template_key_release(self, event):
        """템플릿 리스트박스 키보드 이벤트 - 키 뗌"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self._ctrl_pressed = False
        elif event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self._shift_pressed = False
    
    def on_template_click(self, event):
        """템플릿 리스트박스 클릭 이벤트 - 다중선택 처리"""
        # 클릭된 아이템 인덱스 확인
        index = self.template_listbox.nearest(event.y)
        if index >= 0:
            # Ctrl+클릭: 개별 다중선택
            if self._ctrl_pressed:
                current_selection = list(self.template_listbox.curselection())
                if index in current_selection:
                    self.template_listbox.selection_clear(index, index)
                else:
                    self.template_listbox.selection_set(index)
                return "break"
            # Shift+클릭: 범위 선택
            elif self._shift_pressed and self._last_clicked_template is not None:
                try:
                    start_idx = min(self._last_clicked_template, index)
                    end_idx = max(self._last_clicked_template, index)
                    self.template_listbox.selection_set(start_idx, end_idx)
                except:
                    self.template_listbox.selection_set(index)
                return "break"
            # 일반 클릭: 단일 선택
            else:
                self.template_listbox.selection_clear(0, tk.END)
                self.template_listbox.selection_set(index)
            
            self._last_clicked_template = index

if __name__ == "__main__":
    print("프로그램 시작...")
    try:
        import tkinter as tk
        print("tkinter import 성공")
        
        # customtkinter 초기화
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        print("customtkinter 초기화 완료")
        
        app = FileTreeApp()
        print("FileTreeApp 인스턴스 생성 성공")
        app.mainloop()
        print("mainloop 종료")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
