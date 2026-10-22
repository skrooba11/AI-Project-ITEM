#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
디스크 공간 관리 프로그램
회사 컴퓨터의 저장 공간을 효율적으로 관리하기 위한 GUI 프로그램 - Modern UI
최적화 버전: 대용량 디스크 분석 성능 개선
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import os
import sys
import shutil
import hashlib
import json
import datetime
from pathlib import Path
from collections import defaultdict
import threading
import time
import re

# 한글 폰트 설정을 위한 import
import platform
if platform.system() == 'Windows':
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

# 배치 로딩 상수
BATCH_SIZE = 100  # 한 번에 로드할 항목 수
BATCH_DELAY = 10  # 배치 간 대기 시간 (ms)
MAX_DISPLAY_FILES = 5000  # 최대 표시 파일 수
MAX_FILES_PER_TYPE = 2000  # 타입별 최대 저장 파일 수


class ModernButton(tk.Canvas):
    """모던한 버튼 위젯 (부드러운 애니메이션 효과)"""
    def __init__(self, parent, text="", command=None, bg="#FFFFFF", hover_bg="#F5F5F5",
                 fg="#333333", width=300, height=60, font=None, arrow=True):
        super().__init__(parent, width=width, height=height+4, bg=parent['bg'],
                        highlightthickness=0, cursor="hand2")

        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.fg = fg
        self.btn_text = text
        self.btn_width = width
        self.btn_height = height
        self.arrow = arrow

        # 애니메이션 상태
        self.is_hovered = False
        self.anim_progress = 0.0  # 0.0 ~ 1.0
        self.anim_id = None
        self.shadow_offset = 0
        self.arrow_offset = 0

        if font is None:
            self.font = ('맑은 고딕', 11)
        else:
            self.font = font

        self.draw()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def lerp_color(self, c1, c2, t):
        """두 색상 사이를 보간"""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw(self):
        """버튼 그리기"""
        self.delete("all")

        # 애니메이션 보간값 계산
        t = self.anim_progress
        current_bg = self.lerp_color(self.bg, self.hover_bg, t)
        self.shadow_offset = int(3 * t)
        self.arrow_offset = int(5 * t)

        # 그림자 효과 (호버 시 더 진하게)
        shadow_alpha = int(40 + 60 * t)
        shadow_color = f'#{shadow_alpha:02x}{shadow_alpha:02x}{shadow_alpha:02x}'
        if t > 0:
            self.create_rounded_rectangle(
                2, 4 + self.shadow_offset,
                self.btn_width - 2, self.btn_height + self.shadow_offset,
                radius=8, fill=shadow_color, outline=""
            )

        # 둥근 사각형 배경 (호버 시 살짝 위로)
        y_offset = -self.shadow_offset
        self.create_rounded_rectangle(
            0, y_offset,
            self.btn_width, self.btn_height + y_offset,
            radius=8, fill=current_bg, outline=""
        )

        # 텍스트
        self.create_text(15, self.btn_height//2 + y_offset, text=self.btn_text,
                        font=self.font, fill=self.fg, anchor="w")

        # 화살표 (호버 시 오른쪽으로 이동)
        if self.arrow:
            arrow_x = self.btn_width - 20 + self.arrow_offset
            arrow_y = self.btn_height // 2 + y_offset
            arrow_color = self.lerp_color("#CCCCCC", "#666666", t)
            self.create_text(arrow_x, arrow_y, text="›", font=('Arial', 18, 'bold'),
                           fill=arrow_color, anchor="center")

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """둥근 사각형 그리기"""
        points = [x1+radius, y1,
                 x1+radius, y1,
                 x2-radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1+radius,
                 x1, y1]

        return self.create_polygon(points, **kwargs, smooth=True)

    def animate_hover(self, target):
        """부드러운 호버 애니메이션"""
        if self.anim_id:
            self.after_cancel(self.anim_id)

        step = 0.15  # 애니메이션 속도
        if target > self.anim_progress:
            self.anim_progress = min(1.0, self.anim_progress + step)
        else:
            self.anim_progress = max(0.0, self.anim_progress - step)

        self.draw()

        if (target == 1.0 and self.anim_progress < 1.0) or \
           (target == 0.0 and self.anim_progress > 0.0):
            self.anim_id = self.after(16, lambda: self.animate_hover(target))

    def on_enter(self, event):
        """마우스 호버"""
        self.is_hovered = True
        self.animate_hover(1.0)

    def on_leave(self, event):
        """마우스 이탈"""
        self.is_hovered = False
        self.animate_hover(0.0)

    def on_click(self, event):
        """클릭 이벤트"""
        if self.command:
            self.command()


class DiskSpaceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("저장공간 관리")
        self.root.geometry("1300x900")

        # 밝은 배경색
        self.bg_color = '#F5F7FA'
        self.root.configure(bg=self.bg_color)

        # ESC 키로 창 닫기
        self.root.bind('<Escape>', lambda e: self.root.quit())

        # 분석 진행 상황 추적
        self.analysis_start_time = None
        self.analysis_processed_files = 0

        # 색상 테마 설정 (모던한 파스텔 톤)
        self.colors = {
            '동영상': '#9B59B6',      # 보라색
            '이미지': '#FF6B9D',      # 핑크
            '오디오 파일': '#5DADE2',  # 파란색
            '오디오': '#5DADE2',      # 파란색 (별칭)
            '비디오': '#36CFC9',      # 청록색
            '압축파일': '#95DE64',    # 연두색
            '설치 파일': '#A0A0A0',   # 회색
            '설치파일': '#A0A0A0',    # 회색 (별칭)
            '문서': '#FFB84D',        # 주황색
            '중복 파일': '#C8C8C8',   # 밝은 회색
            '용량이 큰 파일': '#FFA39E', # 연한 빨강
            '기타': '#D0D0D0',        # 회색
            'bg': '#F5F7FA',
            'card_bg': '#FFFFFF',
            'fg': '#2C3E50',
            'accent': '#5B8DEF'
        }

        # 파일 타입 분류
        self.file_types = {
            '문서': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.hwp'],
            '이미지': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp'],
            '오디오 파일': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
            '동영상': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            '압축파일': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            '설치 파일': ['.exe', '.msi', '.dmg', '.deb', '.rpm'],
            '기타': []
        }

        # 휴지통 설정
        self.trash_dir = Path.home() / '.disk_manager_trash'
        self.trash_dir.mkdir(exist_ok=True)
        self.trash_info_file = self.trash_dir / 'trash_info.json'

        # 삭제 히스토리 설정
        self.delete_history_file = self.trash_dir / 'delete_history.json'

        # 분석 결과 저장
        self.analysis_result = {}
        self.selected_drive = ""
        self.is_analyzing = False
        self.is_paused = False  # 분석 일시정지 상태

        # 배치 로딩 상태
        self._batch_loading = False
        self._batch_cancel = False

        self.setup_ui()
        self.load_trash_info()
        self.load_delete_history()

    def setup_ui(self):
        """모던한 UI 구성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # 헤더
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        # 뒤로가기 버튼
        back_btn = tk.Label(header_frame, text="<", font=('Arial', 20),
                           bg=self.bg_color, fg='#333333', cursor="hand2")
        back_btn.pack(side=tk.LEFT)

        # 타이틀
        title_label = tk.Label(header_frame, text="저장공간 관리",
                              font=('맑은 고딕', 18, 'bold'),
                              bg=self.bg_color, fg='#2C3E50')
        title_label.pack(side=tk.LEFT, padx=10)

        # 좌우 컨테이너
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # 왼쪽 프레임 (드라이브 + 용량 + 파일타입)
        left_frame = tk.Frame(content_frame, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 오른쪽 프레임 (액션 버튼들)
        right_frame = tk.Frame(content_frame, bg=self.bg_color, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        # === 왼쪽 영역 구성 ===

        # 드라이브 선택
        drive_frame = tk.Frame(left_frame, bg=self.bg_color)
        drive_frame.pack(fill=tk.X, pady=(0, 10))

        drive_label = tk.Label(drive_frame, text="드라이브:", font=('맑은 고딕', 11),
                              bg=self.bg_color, fg='#666666')
        drive_label.pack(side=tk.LEFT, padx=(0, 5))

        self.drive_combo = ttk.Combobox(drive_frame, width=15, state='readonly',
                                       font=('맑은 고딕', 10))
        self.drive_combo.pack(side=tk.LEFT, padx=5)
        self.update_drives()

        self.analyze_button = tk.Button(drive_frame, text="▶ 분석 시작",
                                  command=self.toggle_analysis,
                                  bg='#5B8DEF', fg='white',
                                  font=('맑은 고딕', 10, 'bold'),
                                  relief='flat', padx=15, pady=5,
                                  cursor="hand2", borderwidth=0)
        self.analyze_button.pack(side=tk.LEFT, padx=5)

        # 분석 진행 상황 표시
        self.progress_frame = tk.Frame(left_frame, bg=self.colors['card_bg'], relief='flat', bd=0)
        self.progress_label = tk.Label(self.progress_frame, text="",
                                       font=('맑은 고딕', 10),
                                       bg=self.colors['card_bg'], fg='#666666')
        self.progress_label.pack(pady=10)

        self.eta_label = tk.Label(self.progress_frame, text="",
                                 font=('맑은 고딕', 9),
                                 bg=self.colors['card_bg'], fg='#999999')
        self.eta_label.pack(pady=(0, 10))

        # 진행률 바
        self.analysis_progress_canvas = tk.Canvas(self.progress_frame, height=8,
                                                 bg=self.colors['card_bg'],
                                                 highlightthickness=0)
        self.analysis_progress_canvas.pack(fill=tk.X, padx=20, pady=(0, 15))

        # 용량 카드
        storage_card = tk.Frame(left_frame, bg=self.colors['card_bg'],
                               relief='flat', bd=0)
        storage_card.pack(fill=tk.X, pady=10)

        # 용량 정보
        self.storage_percent_label = tk.Label(storage_card, text="0% ",
                                             font=('맑은 고딕', 40, 'bold'),
                                             bg=self.colors['card_bg'], fg='#2C3E50')
        self.storage_percent_label.pack(pady=(20, 0))

        usage_label = tk.Label(storage_card, text="사용 중",
                              font=('맑은 고딕', 14),
                              bg=self.colors['card_bg'], fg='#666666')
        usage_label.pack()

        # 상세 용량
        self.storage_detail_label = tk.Label(storage_card, text="0 GB / 0 GB",
                                            font=('맑은 고딕', 13),
                                            bg=self.colors['card_bg'], fg='#333333')
        self.storage_detail_label.pack(side=tk.RIGHT, anchor='e', padx=20, pady=(0, 15))

        # 프로그레스 바 컨테이너
        progress_container = tk.Frame(storage_card, bg=self.colors['card_bg'])
        progress_container.pack(fill=tk.X, padx=20, pady=(5, 20))

        self.progress_canvas = tk.Canvas(progress_container, height=20,
                                        bg=self.colors['card_bg'],
                                        highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X)

        # 파일 타입별 섹션
        self.file_types_frame = tk.Frame(left_frame, bg=self.bg_color)
        self.file_types_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # === 오른쪽 영역 구성 (액션 버튼들) ===

        action_title = tk.Label(right_frame, text="빠른 정리",
                               font=('맑은 고딕', 14, 'bold'),
                               bg=self.bg_color, fg='#2C3E50')
        action_title.pack(anchor='w', pady=(0, 10))

        # 액션 버튼들 (동적으로 업데이트될 프레임 저장)
        self.action_buttons_frame = right_frame
        self.trash_button_frame = self.create_action_button(right_frame, "휴지통", "휴지통에 있는 파일",
                                 "0 GB", self.show_trash)
        self.unused_button_frame = self.create_action_button(right_frame, "사용하지 않는 파일", "지난 1년 동안 사용하지 않은 파일",
                                 "0 GB", self.show_unused_files)
        self.duplicates_button_frame = self.create_action_button(right_frame, "중복 파일", "복사본이 있는 파일",
                                 "0 GB", self.show_duplicates)
        self.large_files_button_frame = self.create_action_button(right_frame, "용량이 큰 파일", "크기가 1GB보다 큰 파일",
                                 "0 GB", self.show_large_files)

        # 보고서 생성 버튼
        report_button = tk.Button(right_frame, text="📊 보고서 생성",
                                 command=self.generate_report,
                                 bg='#5B8DEF', fg='white',
                                 font=('맑은 고딕', 11, 'bold'),
                                 relief='flat', pady=12,
                                 cursor="hand2", borderwidth=0)
        report_button.pack(fill=tk.X, pady=(10, 0))

        # 초기 파일 타입 표시
        self.update_file_types_display()

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=10, **kwargs):
        """캔버스에 둥근 사각형 그리기"""
        points = [x1+radius, y1,
                 x1+radius, y1,
                 x2-radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1+radius,
                 x1, y1]

        return canvas.create_polygon(points, **kwargs, smooth=True)

    def create_action_button(self, parent, title, subtitle, size, command):
        """액션 버튼 생성 (부드러운 호버 애니메이션)"""
        # 컨테이너 프레임 (그림자 공간 포함)
        container = tk.Frame(parent, bg=parent['bg'], height=75)
        container.pack(fill=tk.X, pady=(0, 8))
        container.pack_propagate(False)

        # 그림자 프레임
        shadow_frame = tk.Frame(container, bg='#D0D0D0', height=70)

        # 메인 버튼 프레임
        btn_frame = tk.Frame(container, bg='#FFFFFF', relief='flat', bd=0, height=70)
        btn_frame.place(x=0, y=0, relwidth=1, height=70)

        # 애니메이션 상태 저장
        btn_frame.anim_progress = 0.0
        btn_frame.anim_id = None
        btn_frame.shadow_frame = shadow_frame

        def lerp_color(c1, c2, t):
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            return f'#{r:02x}{g:02x}{b:02x}'

        def update_style(t):
            bg_color = lerp_color('#FFFFFF', '#F0F7FF', t)
            arrow_color = lerp_color('#CCCCCC', '#4A90D9', t)
            y_offset = int(-3 * t)
            shadow_opacity = int(0xE0 - 0x30 * t)
            shadow_color = f'#{shadow_opacity:02x}{shadow_opacity:02x}{shadow_opacity:02x}'

            btn_frame.config(bg=bg_color)
            btn_frame.place(x=0, y=y_offset, relwidth=1, height=70)

            if t > 0:
                shadow_frame.config(bg=shadow_color)
                shadow_frame.place(x=2, y=4, relwidth=1, height=70)
            else:
                shadow_frame.place_forget()

            for child in btn_frame.winfo_children():
                try:
                    child.config(bg=bg_color)
                    for subchild in child.winfo_children():
                        try:
                            subchild.config(bg=bg_color)
                        except:
                            pass
                except:
                    pass

            arrow_label.config(fg=arrow_color)

        def animate(target):
            if btn_frame.anim_id:
                container.after_cancel(btn_frame.anim_id)

            step = 0.2
            if target > btn_frame.anim_progress:
                btn_frame.anim_progress = min(1.0, btn_frame.anim_progress + step)
            else:
                btn_frame.anim_progress = max(0.0, btn_frame.anim_progress - step)

            update_style(btn_frame.anim_progress)

            if (target == 1.0 and btn_frame.anim_progress < 1.0) or \
               (target == 0.0 and btn_frame.anim_progress > 0.0):
                btn_frame.anim_id = container.after(16, lambda: animate(target))

        def on_enter(e):
            animate(1.0)

        def on_leave(e):
            animate(0.0)

        # 이벤트 바인딩
        for widget in [container, btn_frame]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
            widget.bind('<Button-1>', lambda e: command())
            widget.configure(cursor="hand2")

        # 왼쪽: 아이콘 영역
        icon_label = tk.Label(btn_frame, text="🗑" if "휴지통" in title else
                                            "📁" if "파일" in title else
                                            "📄" if "중복" in title else "📦",
                            font=('Arial', 18), bg='#FFFFFF', width=2)
        icon_label.pack(side=tk.LEFT, padx=(15, 10), pady=12)
        icon_label.bind('<Enter>', on_enter)
        icon_label.bind('<Leave>', on_leave)
        icon_label.bind('<Button-1>', lambda e: command())

        # 중앙: 텍스트 정보
        text_frame = tk.Frame(btn_frame, bg='#FFFFFF')
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=12)
        text_frame.bind('<Enter>', on_enter)
        text_frame.bind('<Leave>', on_leave)
        text_frame.bind('<Button-1>', lambda e: command())

        title_label = tk.Label(text_frame, text=title, font=('맑은 고딕', 12, 'bold'),
                              bg='#FFFFFF', fg='#2C3E50', anchor='w')
        title_label.pack(anchor='w')
        title_label.bind('<Enter>', on_enter)
        title_label.bind('<Leave>', on_leave)
        title_label.bind('<Button-1>', lambda e: command())

        subtitle_label = tk.Label(text_frame, text=subtitle, font=('맑은 고딕', 9),
                                 bg='#FFFFFF', fg='#999999', anchor='w')
        subtitle_label.pack(anchor='w')
        subtitle_label.bind('<Enter>', on_enter)
        subtitle_label.bind('<Leave>', on_leave)
        subtitle_label.bind('<Button-1>', lambda e: command())

        # 오른쪽: 크기와 화살표
        right_frame = tk.Frame(btn_frame, bg='#FFFFFF')
        right_frame.pack(side=tk.RIGHT, padx=(5, 15), pady=12)
        right_frame.bind('<Enter>', on_enter)
        right_frame.bind('<Leave>', on_leave)
        right_frame.bind('<Button-1>', lambda e: command())

        size_label = tk.Label(right_frame, text=size, font=('맑은 고딕', 11),
                             bg='#FFFFFF', fg='#4A90D9')
        size_label.pack(side=tk.LEFT, padx=(0, 8))
        size_label.bind('<Enter>', on_enter)
        size_label.bind('<Leave>', on_leave)
        size_label.bind('<Button-1>', lambda e: command())

        arrow_label = tk.Label(right_frame, text="›", font=('Arial', 18),
                              bg='#FFFFFF', fg='#CCCCCC')
        arrow_label.pack(side=tk.LEFT)
        arrow_label.bind('<Enter>', on_enter)
        arrow_label.bind('<Leave>', on_leave)
        arrow_label.bind('<Button-1>', lambda e: command())

        # 크기 레이블을 나중에 업데이트할 수 있도록 저장
        btn_frame.size_label = size_label
        btn_frame.container = container
        return btn_frame

    def update_file_types_display(self):
        """파일 타입별 표시 업데이트"""
        # 기존 위젯 제거
        for widget in self.file_types_frame.winfo_children():
            widget.destroy()

        if not self.analysis_result or 'file_data' not in self.analysis_result:
            # 분석 전에는 안내 메시지만 표시
            info_label = tk.Label(self.file_types_frame,
                                 text="드라이브를 선택하고 '분석 시작'을 눌러주세요",
                                 font=('맑은 고딕', 12),
                                 bg=self.bg_color, fg='#999999',
                                 pady=50)
            info_label.pack()
        else:
            # 실제 분석 데이터 표시
            sorted_types = sorted(self.analysis_result['file_data'].items(),
                                 key=lambda x: x[1]['size'], reverse=True)

            for file_type, data in sorted_types:
                if data['count'] > 0:
                    size_str = self.format_bytes(data['size'])
                    self.create_file_type_row(file_type, size_str, data)

    def create_file_type_row(self, file_type, size_str, data):
        """파일 타입 행 생성"""
        row_frame = tk.Frame(self.file_types_frame, bg='#FFFFFF', relief='flat', bd=0)
        row_frame.pack(fill=tk.X, pady=(0, 8))
        row_frame.bind('<Enter>', lambda e: row_frame.config(bg='#F8F8F8'))
        row_frame.bind('<Leave>', lambda e: row_frame.config(bg='#FFFFFF'))
        row_frame.configure(cursor="hand2")

        if data:
            row_frame.bind('<Button-1>',
                          lambda e: self.show_file_type_details(file_type, data))

        # 색상 인디케이터
        color = self.colors.get(file_type, '#D0D0D0')
        color_label = tk.Label(row_frame, text="●", font=('Arial', 16),
                              bg='#FFFFFF', fg=color, width=2)
        color_label.pack(side=tk.LEFT, padx=(15, 10), pady=12)
        if data:
            color_label.bind('<Button-1>',
                            lambda e: self.show_file_type_details(file_type, data))

        # 파일 타입 이름
        name_label = tk.Label(row_frame, text=file_type, font=('맑은 고딕', 12),
                             bg='#FFFFFF', fg='#2C3E50', anchor='w')
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=12)
        if data:
            name_label.bind('<Button-1>',
                           lambda e: self.show_file_type_details(file_type, data))

        # 크기와 화살표
        right_frame = tk.Frame(row_frame, bg='#FFFFFF')
        right_frame.pack(side=tk.RIGHT, padx=(5, 15), pady=12)
        if data:
            right_frame.bind('<Button-1>',
                            lambda e: self.show_file_type_details(file_type, data))

        size_label = tk.Label(right_frame, text=size_str, font=('맑은 고딕', 11),
                             bg='#FFFFFF', fg='#333333')
        size_label.pack(side=tk.LEFT, padx=(0, 8))
        if data:
            size_label.bind('<Button-1>',
                           lambda e: self.show_file_type_details(file_type, data))

        arrow_label = tk.Label(right_frame, text=">", font=('Arial', 14),
                              bg='#FFFFFF', fg='#CCCCCC')
        arrow_label.pack(side=tk.LEFT)
        if data:
            arrow_label.bind('<Button-1>',
                            lambda e: self.show_file_type_details(file_type, data))

    def draw_progress_bar(self):
        """프로그레스 바 그리기"""
        self.progress_canvas.delete("all")

        width = self.progress_canvas.winfo_width()
        if width <= 1:
            self.root.after(100, self.draw_progress_bar)
            return

        height = 20
        current_x = 0  # 초기화

        # 배경
        self.create_rounded_rect(self.progress_canvas, 0, 0, width, height,
                                radius=10, fill='#E8E8E8', outline='')

        if not self.analysis_result or 'file_data' not in self.analysis_result:
            # 분석 전에는 빈 프로그레스 바만 표시 (current_x는 0으로 유지)
            pass
        else:
            # 실제 데이터로 프로그레스 바 그리기
            total = self.analysis_result.get('total', 1)
            used = self.analysis_result.get('used', 0)
            used_percent = used / total if total > 0 else 0

            total_width = int(width * used_percent)

            # 파일 타입별 비율 계산
            sorted_types = sorted(self.analysis_result['file_data'].items(),
                                 key=lambda x: x[1]['size'], reverse=True)

            current_x = 0
            for file_type, data in sorted_types:
                if data['size'] > 0:
                    ratio = data['size'] / used if used > 0 else 0
                    segment_width = int(total_width * ratio)

                    if segment_width > 2:  # 최소 크기
                        color = self.colors.get(file_type, '#D0D0D0')
                        self.progress_canvas.create_rectangle(current_x, 0,
                                                             current_x + segment_width, height,
                                                             fill=color, outline='')
                        current_x += segment_width

        # 오른쪽 끝을 둥글게 처리
        if current_x > 0:
            self.progress_canvas.create_oval(current_x-10, 0, current_x+10, height,
                                            fill=self.progress_canvas.itemcget(
                                                self.progress_canvas.find_closest(current_x-5, height//2),
                                                'fill'), outline='')

    def update_drives(self):
        """사용 가능한 드라이브 목록 업데이트"""
        drives = []
        if platform.system() == 'Windows':
            import string
            import ctypes
            from ctypes import windll

            # 모든 드라이브 문자 확인
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                # 드라이브가 실제로 존재하는지 확인
                if os.path.exists(drive):
                    try:
                        # ctypes를 사용하여 볼륨 이름 가져오기
                        kernel32 = windll.kernel32
                        volumeNameBuffer = ctypes.create_unicode_buffer(1024)
                        fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
                        serial_number = None
                        max_component_length = None
                        file_system_flags = None

                        result = kernel32.GetVolumeInformationW(
                            ctypes.c_wchar_p(drive),
                            volumeNameBuffer,
                            ctypes.sizeof(volumeNameBuffer),
                            serial_number,
                            max_component_length,
                            file_system_flags,
                            fileSystemNameBuffer,
                            ctypes.sizeof(fileSystemNameBuffer)
                        )

                        if result:
                            volume_name = volumeNameBuffer.value
                            if volume_name:
                                display_name = f"{drive} ({volume_name})"
                            else:
                                display_name = drive
                        else:
                            display_name = drive

                        drives.append(display_name)
                    except:
                        # 볼륨 정보를 가져올 수 없는 경우 드라이브 문자만 표시
                        drives.append(drive)
        else:
            drives = ['/']
            home = str(Path.home())
            if home not in drives:
                drives.append(home)

        self.drive_combo['values'] = drives
        if drives:
            self.drive_combo.current(0)

    def toggle_analysis(self):
        """분석 시작/일시정지/재개 토글"""
        if not self.is_analyzing:
            # 분석 시작
            self.start_analysis()
        elif self.is_paused:
            # 분석 재개
            self.resume_analysis()
        else:
            # 분석 일시정지
            self.pause_analysis()

    def start_analysis(self):
        """분석 시작"""
        drive_display = self.drive_combo.get()
        if not drive_display:
            messagebox.showwarning("경고", "드라이브를 선택해주세요.")
            return

        # 드라이브 경로만 추출 (예: "C:\ (로컬 디스크)" -> "C:\")
        self.selected_drive = drive_display.split()[0]

        self.is_analyzing = True
        self.is_paused = False
        self.analysis_start_time = time.time()
        self.analysis_processed_files = 0

        # 버튼을 "일시정지"로 변경
        self.analyze_button.config(text="⏸ 분석 정지", bg='#FF6B6B')

        # 진행 상황 프레임 표시
        self.progress_frame.pack(fill=tk.X, pady=(5, 0), before=self.file_types_frame)
        self.progress_label.config(text="분석 준비 중...")
        self.eta_label.config(text="")

        # 백그라운드 스레드에서 분석 실행
        thread = threading.Thread(target=self.analyze_drive, daemon=True)
        thread.start()

    def pause_analysis(self):
        """분석 일시정지"""
        self.is_paused = True
        self.analyze_button.config(text="▶ 분석 재개", bg='#52C41A')
        self.progress_label.config(text=f"일시정지됨 - {self.analysis_processed_files:,}개 파일 처리됨")
        self.eta_label.config(text="분석이 일시정지되었습니다. '분석 재개'를 눌러 계속하세요.")

    def resume_analysis(self):
        """분석 재개"""
        self.is_paused = False
        self.analyze_button.config(text="⏸ 분석 정지", bg='#FF6B6B')
        self.eta_label.config(text="분석을 재개합니다...")

    def analyze_drive(self):
        """드라이브 분석 (최적화 버전)"""
        try:
            drive_path = Path(self.selected_drive)

            # 전체 용량 정보
            total, used, free = shutil.disk_usage(drive_path)

            # 파일 분석 - 최적화: 파일 목록 크기 제한
            file_data = defaultdict(lambda: {'count': 0, 'size': 0, 'files': []})
            all_files_by_normalized_name = defaultdict(list)
            large_files = []
            old_files = []

            total_files = 0
            estimated_total_files = 0

            # 파일 순회
            for root, dirs, files in os.walk(drive_path):
                # 일시정지 확인
                while self.is_paused and self.is_analyzing:
                    time.sleep(0.1)

                # 분석이 중단되었는지 확인
                if not self.is_analyzing:
                    break

                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'System Volume Information']

                for file in files:
                    # 일시정지 확인
                    while self.is_paused and self.is_analyzing:
                        time.sleep(0.1)

                    # 분석이 중단되었는지 확인
                    if not self.is_analyzing:
                        break

                    if file.startswith('.'):
                        continue

                    total_files += 1
                    self.analysis_processed_files = total_files

                    # 100개 파일마다 진행 상황 업데이트
                    if total_files % 100 == 0:
                        elapsed_time = time.time() - self.analysis_start_time

                        # 예상 총 파일 수 추정
                        if total_files >= 1000:
                            avg_file_size = sum(f.get('size', 0) for data in file_data.values()
                                              for f in data['files'][-100:]) / min(total_files, 100)
                            estimated_total_files = int(used / avg_file_size) if avg_file_size > 0 else total_files * 2
                        else:
                            estimated_total_files = total_files * 2

                        progress_percent = min(95, int((total_files / estimated_total_files) * 100)) if estimated_total_files > 0 else 0

                        # 예상 남은 시간 계산
                        if total_files > 100:
                            files_per_second = total_files / elapsed_time if elapsed_time > 0 else 1
                            remaining_files = estimated_total_files - total_files
                            eta_seconds = remaining_files / files_per_second if files_per_second > 0 else 0
                            eta_text = self.format_time(eta_seconds)
                        else:
                            eta_text = "계산 중..."

                        self.root.after(0, lambda p=progress_percent, f=total_files, e=eta_text:
                                       self.update_analysis_progress(p, f, e))

                    file_path = Path(root) / file

                    try:
                        file_stat = file_path.stat()
                        file_size = file_stat.st_size

                        ext = file_path.suffix.lower()
                        file_type = self.get_file_type(ext)

                        file_data[file_type]['count'] += 1
                        file_data[file_type]['size'] += file_size

                        # 파일 정보 - 타입별로 제한된 수만 저장
                        if len(file_data[file_type]['files']) < MAX_FILES_PER_TYPE:
                            file_data[file_type]['files'].append({
                                'path': str(file_path),
                                'name': file,
                                'size': file_size,
                                'modified': file_stat.st_mtime
                            })

                        # 1GB 이상 파일
                        if file_size > 1 * 1024 * 1024 * 1024:
                            if len(large_files) < 500:
                                large_files.append({
                                    'path': str(file_path),
                                    'name': file,
                                    'size': file_size,
                                    'modified': file_stat.st_mtime
                                })

                        # 1년 이상 사용 안한 파일
                        if time.time() - file_stat.st_mtime > 365 * 24 * 3600:
                            if len(old_files) < 2000:
                                old_files.append({
                                    'path': str(file_path),
                                    'name': file,
                                    'size': file_size,
                                    'modified': file_stat.st_mtime
                                })

                        # 중복 파일 검출 - 메모리 최적화
                        normalized_name = self.normalize_filename(file)
                        # 기존 파일 정보와 비교
                        if normalized_name in all_files_by_normalized_name:
                            # 이미 그룹이 있으면 추가
                            if len(all_files_by_normalized_name[normalized_name]) < 50:
                                all_files_by_normalized_name[normalized_name].append({
                                    'path': str(file_path),
                                    'name': file,
                                    'size': file_size,
                                    'modified': file_stat.st_mtime
                                })
                        else:
                            # 새 그룹 시작
                            all_files_by_normalized_name[normalized_name] = [{
                                'path': str(file_path),
                                'name': file,
                                'size': file_size,
                                'modified': file_stat.st_mtime
                            }]

                    except (PermissionError, OSError):
                        continue

            # 중복 파일 필터링: 2개 이상인 그룹만
            duplicates = {k: v for k, v in all_files_by_normalized_name.items() if len(v) > 1}

            # 결과 저장
            self.analysis_result = {
                'total': total,
                'used': used,
                'free': free,
                'file_data': dict(file_data),
                'large_files': sorted(large_files, key=lambda x: x['size'], reverse=True)[:100],
                'old_files': sorted(old_files, key=lambda x: x['modified'])[:500],
                'duplicates': duplicates,
                'total_files': total_files
            }

            # UI 업데이트
            self.root.after(0, self.update_analysis_ui)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"분석 중 오류 발생: {str(e)}"))
        finally:
            self.is_analyzing = False
            # 분석 완료 후 UI 리셋
            self.root.after(0, self.finish_analysis)

    def update_analysis_progress(self, percent, file_count, eta_text):
        """분석 진행 상황 업데이트"""
        self.progress_label.config(text=f"분석 중... {file_count:,}개 파일 처리됨 ({percent}%)")
        self.eta_label.config(text=f"예상 남은 시간: {eta_text}")

        # 진행률 바 그리기
        self.analysis_progress_canvas.delete("all")
        width = self.analysis_progress_canvas.winfo_width()
        if width > 1:
            height = 8
            # 배경
            self.analysis_progress_canvas.create_rectangle(0, 0, width, height,
                                                          fill='#E8E8E8', outline='')
            # 진행률
            progress_width = int(width * (percent / 100))
            if progress_width > 0:
                self.analysis_progress_canvas.create_rectangle(0, 0, progress_width, height,
                                                              fill='#5B8DEF', outline='')

    def finish_analysis(self):
        """분석 완료 후 처리"""
        # 진행 상황 프레임 숨기기
        self.progress_frame.pack_forget()

        # 분석 버튼을 "시작"으로 되돌리기
        self.analyze_button.config(text="▶ 분석 시작", bg='#5B8DEF')
        self.is_paused = False

        # 완료 메시지
        if self.analysis_result:
            elapsed_time = time.time() - self.analysis_start_time if self.analysis_start_time else 0
            messagebox.showinfo("완료",
                              f"분석이 완료되었습니다!\n\n"
                              f"처리된 파일: {self.analysis_processed_files:,}개\n"
                              f"소요 시간: {self.format_time(elapsed_time)}")

    def format_time(self, seconds):
        """초를 읽기 쉬운 시간 형식으로 변환"""
        if seconds < 60:
            return f"{int(seconds)}초"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}분 {secs}초"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}시간 {minutes}분"

    def is_duplicate_pattern(self, filename):
        """파일명이 중복 패턴을 포함하는지 확인"""
        duplicate_patterns = [
            r'복사본',
            r'\s*\(\d+\)',
            r'\s*-\s*\d+',
            r'copy',
            r'\s+\d+$',
        ]

        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename

        for pattern in duplicate_patterns:
            if re.search(pattern, name_without_ext, re.IGNORECASE):
                return True

        return False

    def normalize_filename(self, filename):
        """파일명 정규화 - 중복 패턴 제거"""
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, ext = name_parts
        else:
            name = filename
            ext = ''

        name = re.sub(r'\s*[-_\s]*복사본\s*\d*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*[-_\s]*복사\s*\d*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*[-_\s]*copy\s*\d*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\(\d+\)\s*$', '', name)
        name = re.sub(r'\s*\(\d+\)$', '', name)
        name = re.sub(r'\s*-\s*\d+\s*$', '', name)
        name = re.sub(r'\s+\d+$', '', name)
        name = name.strip()

        if ext:
            return f"{name}.{ext}"
        return name

    def get_file_type(self, ext):
        """파일 확장자로 타입 분류"""
        for file_type, extensions in self.file_types.items():
            if ext in extensions:
                return file_type
        return '기타'

    def update_analysis_ui(self):
        """분석 결과 UI 업데이트"""
        if not self.analysis_result:
            return

        total = self.analysis_result['total']
        used = self.analysis_result['used']
        free = self.analysis_result['free']

        used_percent = int((used / total) * 100)
        self.storage_percent_label.config(text=f"{used_percent}% ")
        self.storage_detail_label.config(text=f"{self.format_bytes(used)} / {self.format_bytes(total)}")

        # 파일 타입 표시 업데이트
        self.update_file_types_display()

        # 빠른 정리 버튼 업데이트
        self.update_action_buttons()

        # 프로그레스 바 그리기
        self.root.after(100, self.draw_progress_bar)

    def update_action_buttons(self):
        """빠른 정리 버튼의 크기 업데이트"""
        if not self.analysis_result:
            return

        # 휴지통 크기
        trash_files = self.get_trash_files()
        trash_size = sum(f['size'] for f in trash_files)
        self.trash_button_frame.size_label.config(text=self.format_bytes(trash_size))

        # 사용하지 않는 파일 크기
        old_files = self.analysis_result.get('old_files', [])
        old_files_size = sum(f['size'] for f in old_files)
        self.unused_button_frame.size_label.config(text=self.format_bytes(old_files_size))

        # 중복 파일 크기
        duplicates = self.analysis_result.get('duplicates', {})
        dup_size = 0
        for filename, dups in duplicates.items():
            for dup in dups[1:]:
                dup_size += dup['size']
        self.duplicates_button_frame.size_label.config(text=self.format_bytes(dup_size))

        # 용량이 큰 파일 크기
        large_files = self.analysis_result.get('large_files', [])
        large_files_size = sum(f['size'] for f in large_files)
        self.large_files_button_frame.size_label.config(text=self.format_bytes(large_files_size))

    def show_file_type_details(self, file_type, data):
        """파일 타입 상세 보기 (배치 로딩)"""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"{file_type} 상세")
        detail_window.geometry("1200x750")
        detail_window.configure(bg=self.bg_color)

        detail_window.focus_force()
        detail_window.bind('<Escape>', lambda e: detail_window.destroy())

        # 헤더
        header = tk.Frame(detail_window, bg=self.bg_color)
        header.pack(fill=tk.X, padx=20, pady=20)

        title = tk.Label(header, text=file_type, font=('맑은 고딕', 16, 'bold'),
                        bg=self.bg_color, fg='#2C3E50')
        title.pack(side=tk.LEFT)

        info = tk.Label(header,
                       text=f"{data['count']:,}개 파일 · {self.format_bytes(data['size'])}",
                       font=('맑은 고딕', 11), bg=self.bg_color, fg='#666666')
        info.pack(side=tk.LEFT, padx=20)

        # 로딩 표시
        loading_label = tk.Label(header, text="",
                                font=('맑은 고딕', 10), bg=self.bg_color, fg='#5B8DEF')
        loading_label.pack(side=tk.LEFT, padx=10)

        # 버튼 프레임
        btn_frame = tk.Frame(header, bg=self.bg_color)
        btn_frame.pack(side=tk.RIGHT)

        select_all_btn = tk.Button(btn_frame, text="모두 선택",
                                   command=lambda: self.select_all_tree_items(tree),
                                   bg='#5B8DEF', fg='white',
                                   font=('맑은 고딕', 9),
                                   relief='flat', padx=10, pady=3,
                                   cursor="hand2")
        select_all_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(btn_frame, text="선택 삭제",
                              command=lambda: self.delete_selected_from_tree(tree, data['files'], detail_window),
                              bg='#FF6B6B', fg='white',
                              font=('맑은 고딕', 9),
                              relief='flat', padx=10, pady=3,
                              cursor="hand2")
        delete_btn.pack(side=tk.LEFT, padx=5)

        # 파일 목록 (Treeview)
        list_frame = tk.Frame(detail_window, bg='#FFFFFF')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ('이름', '수정한 날짜', '유형', '크기')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                           selectmode='extended', height=20)

        tree.heading('이름', text='이름', command=lambda: self.sort_treeview(tree, '이름', False))
        tree.heading('수정한 날짜', text='수정한 날짜', command=lambda: self.sort_treeview(tree, '수정한 날짜', False))
        tree.heading('유형', text='유형', command=lambda: self.sort_treeview(tree, '유형', False))
        tree.heading('크기', text='크기', command=lambda: self.sort_treeview(tree, '크기', False))

        tree.column('이름', width=350)
        tree.column('수정한 날짜', width=150)
        tree.column('유형', width=100)
        tree.column('크기', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree.bind('<Double-Button-1>', lambda e: self.open_file_from_tree(tree))
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, tree, data['files'], detail_window))

        # 배치 로딩으로 파일 추가
        files_to_load = data['files'][:MAX_DISPLAY_FILES]
        self._load_files_in_batches(tree, files_to_load, loading_label, detail_window)

    def _load_files_in_batches(self, tree, files, loading_label, window):
        """파일을 배치로 나누어 로드"""
        total = len(files)
        loaded = [0]  # mutable로 클로저에서 수정 가능하게

        def load_batch():
            if not window.winfo_exists():
                return

            batch_end = min(loaded[0] + BATCH_SIZE, total)

            for i in range(loaded[0], batch_end):
                file_info = files[i]
                file_path = Path(file_info['path'])
                modified_date = datetime.datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
                file_ext = file_path.suffix.upper()[1:] if file_path.suffix else '파일'

                tree.insert('', 'end', values=(
                    file_info['name'],
                    modified_date,
                    file_ext,
                    self.format_bytes(file_info['size'])
                ), tags=(file_info['path'],))

            loaded[0] = batch_end

            if loaded[0] < total:
                loading_label.config(text=f"로딩 중... {loaded[0]:,}/{total:,}")
                window.after(BATCH_DELAY, load_batch)
            else:
                loading_label.config(text="")

        load_batch()

    def show_trash(self):
        """휴지통 보기"""
        self.show_file_list_window("휴지통", self.get_trash_files(), show_restore=True)

    def show_unused_files(self):
        """사용하지 않는 파일 보기"""
        if 'old_files' in self.analysis_result:
            self.show_file_list_window("사용하지 않는 파일",
                                      self.analysis_result['old_files'])
        else:
            messagebox.showinfo("알림", "먼저 드라이브 분석을 실행해주세요.")

    def show_duplicates(self):
        """중복 파일 보기 (Treeview 기반 - 최적화)"""
        if 'duplicates' not in self.analysis_result:
            messagebox.showinfo("알림", "먼저 드라이브 분석을 실행해주세요.")
            return

        duplicates = self.analysis_result['duplicates']
        if not duplicates:
            messagebox.showinfo("알림", "중복 파일이 없습니다.")
            return

        # 중복 파일 창 생성
        dup_window = tk.Toplevel(self.root)
        dup_window.title("중복 파일")
        dup_window.geometry("1100x800")
        dup_window.configure(bg=self.bg_color)
        dup_window.focus_force()
        dup_window.bind('<Escape>', lambda e: dup_window.destroy())

        # 전체 중복 파일 개수 및 크기 계산
        total_dup_count = sum(len(dups) for dups in duplicates.values())
        total_dup_size = sum(sum(d['size'] for d in dups) for dups in duplicates.values())
        saveable_size = sum(sum(d['size'] for d in dups[1:]) for dups in duplicates.values())

        # 헤더
        header = tk.Frame(dup_window, bg=self.bg_color)
        header.pack(fill=tk.X, padx=25, pady=(25, 15))

        left_header = tk.Frame(header, bg=self.bg_color)
        left_header.pack(side=tk.LEFT)

        title_label = tk.Label(left_header, text="중복 파일",
                              font=('맑은 고딕', 18, 'bold'),
                              bg=self.bg_color, fg='#2C3E50')
        title_label.pack(side=tk.LEFT)

        info_label = tk.Label(left_header,
                             text=f"  {len(duplicates)}개 그룹 · {total_dup_count}개 파일 · 절약 가능: {self.format_bytes(saveable_size)}",
                             font=('맑은 고딕', 11), bg=self.bg_color, fg='#999999')
        info_label.pack(side=tk.LEFT)

        # 로딩 표시
        loading_label = tk.Label(header, text="",
                                font=('맑은 고딕', 10), bg=self.bg_color, fg='#5B8DEF')
        loading_label.pack(side=tk.LEFT, padx=15)

        # 버튼 프레임
        btn_header = tk.Frame(header, bg=self.bg_color)
        btn_header.pack(side=tk.RIGHT)

        # Treeview로 변경
        list_frame = tk.Frame(dup_window, bg='#FFFFFF')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 15))

        columns = ('선택', '그룹', '파일명', '경로', '크기', '수정일')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                           selectmode='extended', height=25)

        tree.heading('선택', text='✓')
        tree.heading('그룹', text='그룹', command=lambda: self.sort_treeview(tree, '그룹', False))
        tree.heading('파일명', text='파일명', command=lambda: self.sort_treeview(tree, '파일명', False))
        tree.heading('경로', text='경로', command=lambda: self.sort_treeview(tree, '경로', False))
        tree.heading('크기', text='크기', command=lambda: self.sort_treeview(tree, '크기', False))
        tree.heading('수정일', text='수정일', command=lambda: self.sort_treeview(tree, '수정일', False))

        tree.column('선택', width=40, anchor='center')
        tree.column('그룹', width=80, anchor='center')
        tree.column('파일명', width=300)
        tree.column('경로', width=350)
        tree.column('크기', width=100, anchor='e')
        tree.column('수정일', width=100, anchor='center')

        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar_y.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 선택 상태 저장
        selected_items = set()

        # 그룹별 색상 설정
        tree.tag_configure('group_even', background='#FFFFFF')
        tree.tag_configure('group_odd', background='#F8F9FA')
        tree.tag_configure('selected', background='#E3F2FD')

        def toggle_selection(event):
            """클릭으로 선택 토글"""
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                col = tree.identify_column(event.x)
                if col == '#1':  # 선택 컬럼
                    item = tree.identify_row(event.y)
                    if item:
                        current_values = list(tree.item(item, 'values'))
                        if current_values[0] == '☑':
                            current_values[0] = '☐'
                            selected_items.discard(item)
                        else:
                            current_values[0] = '☑'
                            selected_items.add(item)
                        tree.item(item, values=current_values)
                        update_selection_count()

        tree.bind('<Button-1>', toggle_selection)
        tree.bind('<Double-Button-1>', lambda e: self.open_file_from_tree(tree))
        tree.bind('<Button-3>', lambda e: self.show_duplicate_context_menu_tree(e, tree))

        # 배치 로딩으로 데이터 추가
        sorted_groups = sorted(duplicates.items(), key=lambda x: sum(d['size'] for d in x[1]), reverse=True)
        all_items = []
        for group_idx, (group_name, dup_list) in enumerate(sorted_groups[:500]):  # 최대 500 그룹
            for dup in dup_list:
                all_items.append({
                    'group_idx': group_idx + 1,
                    'group_name': group_name,
                    'file': dup
                })

        def load_duplicates_batch():
            """배치로 중복 파일 로드"""
            total = len(all_items)
            loaded = [0]

            def load_batch():
                if not dup_window.winfo_exists():
                    return

                batch_end = min(loaded[0] + BATCH_SIZE, total)

                for i in range(loaded[0], batch_end):
                    item = all_items[i]
                    dup = item['file']
                    group_idx = item['group_idx']

                    modified_date = datetime.datetime.fromtimestamp(dup['modified']).strftime('%Y-%m-%d')
                    tag = 'group_even' if group_idx % 2 == 0 else 'group_odd'

                    tree.insert('', 'end', values=(
                        '☐',
                        f"#{group_idx}",
                        dup['name'],
                        str(Path(dup['path']).parent),
                        self.format_bytes(dup['size']),
                        modified_date
                    ), tags=(dup['path'], tag))

                loaded[0] = batch_end

                if loaded[0] < total:
                    loading_label.config(text=f"로딩 중... {loaded[0]:,}/{total:,}")
                    dup_window.after(BATCH_DELAY, load_batch)
                else:
                    loading_label.config(text="")

            load_batch()

        load_duplicates_batch()

        # 하단 버튼 영역
        bottom_frame = tk.Frame(dup_window, bg=self.bg_color)
        bottom_frame.pack(fill=tk.X, padx=25, pady=(5, 20))

        selection_label = tk.Label(bottom_frame, text="선택된 파일: 0개",
                                   font=('맑은 고딕', 10),
                                   bg=self.bg_color, fg='#666666')
        selection_label.pack(side=tk.LEFT)

        def update_selection_count():
            count = len(selected_items)
            total_size = 0
            for item in selected_items:
                try:
                    path = tree.item(item)['tags'][0]
                    # 파일 크기 찾기
                    size_str = tree.item(item)['values'][4]
                    # 크기 문자열을 바이트로 변환
                    total_size += self.parse_size_string(size_str)
                except:
                    pass
            selection_label.config(text=f"선택된 파일: {count}개 · {self.format_bytes(total_size)}")

        def select_all_duplicates():
            """복사본만 모두 선택 (첫 번째 파일 제외)"""
            selected_items.clear()
            current_group = None
            first_in_group = True

            for item in tree.get_children():
                values = list(tree.item(item, 'values'))
                group = values[1]

                if group != current_group:
                    current_group = group
                    first_in_group = True
                    values[0] = '☐'
                else:
                    if first_in_group:
                        first_in_group = False
                        values[0] = '☐'
                    else:
                        values[0] = '☑'
                        selected_items.add(item)

                tree.item(item, values=values)

            update_selection_count()

        def deselect_all():
            selected_items.clear()
            for item in tree.get_children():
                values = list(tree.item(item, 'values'))
                values[0] = '☐'
                tree.item(item, values=values)
            update_selection_count()

        select_dup_btn = tk.Button(bottom_frame, text="복사본만 선택",
                                   command=select_all_duplicates,
                                   bg='#E3F2FD', fg='#1976D2',
                                   font=('맑은 고딕', 9),
                                   relief='flat', padx=15, pady=5,
                                   cursor="hand2")
        select_dup_btn.pack(side=tk.RIGHT, padx=5)

        deselect_btn = tk.Button(bottom_frame, text="선택 해제",
                                 command=deselect_all,
                                 bg='#F5F5F5', fg='#666666',
                                 font=('맑은 고딕', 9),
                                 relief='flat', padx=15, pady=5,
                                 cursor="hand2")
        deselect_btn.pack(side=tk.RIGHT, padx=5)

        def delete_selected_duplicates():
            if not selected_items:
                messagebox.showinfo("알림", "삭제할 파일을 선택해주세요.")
                return

            result = messagebox.askyesno("확인",
                                        f"{len(selected_items)}개 파일을 휴지통으로 이동하시겠습니까?")
            if result:
                deleted_count = 0
                deleted_files_info = []

                for item in list(selected_items):
                    try:
                        file_path = tree.item(item)['tags'][0]
                        file_p = Path(file_path)
                        if file_p.exists():
                            file_info = {
                                'path': file_path,
                                'name': file_p.name,
                                'size': file_p.stat().st_size,
                                'type': file_p.suffix.upper()[1:] if file_p.suffix else '파일'
                            }

                            if self.move_to_trash(file_path):
                                deleted_files_info.append(file_info)
                                deleted_count += 1
                                tree.delete(item)
                                selected_items.discard(item)
                    except:
                        pass

                if deleted_files_info:
                    self.add_to_delete_history(deleted_files_info, "휴지통으로 이동")

                self.update_action_buttons()
                update_selection_count()
                messagebox.showinfo("완료", f"{deleted_count}개 파일을 휴지통으로 이동했습니다.")

        delete_btn = tk.Button(bottom_frame, text="🗑 선택 삭제",
                              command=delete_selected_duplicates,
                              bg='#FF6B6B', fg='white',
                              font=('맑은 고딕', 10, 'bold'),
                              relief='flat', padx=20, pady=8,
                              cursor="hand2")
        delete_btn.pack(side=tk.RIGHT, padx=(10, 5))

    def parse_size_string(self, size_str):
        """크기 문자열을 바이트로 변환"""
        try:
            parts = size_str.split()
            if len(parts) != 2:
                return 0
            num = float(parts[0])
            unit = parts[1]
            multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
            return int(num * multipliers.get(unit, 1))
        except:
            return 0

    def show_duplicate_context_menu_tree(self, event, tree):
        """Treeview용 중복 파일 컨텍스트 메뉴"""
        item = tree.identify_row(event.y)
        if item:
            if item not in tree.selection():
                tree.selection_set(item)

            file_path = tree.item(item)['tags'][0]

            context_menu = tk.Menu(tree, tearoff=0)
            context_menu.add_command(label="파일 열기",
                                    command=lambda: self.open_file_by_path(file_path))
            context_menu.add_command(label="파일 위치 열기",
                                    command=lambda: self.open_folder_by_path(file_path))
            context_menu.add_separator()
            context_menu.add_command(label="삭제",
                                    command=lambda: self.delete_file_by_path(file_path))

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def show_large_files(self):
        """큰 파일 보기"""
        if 'large_files' in self.analysis_result:
            self.show_file_list_window("용량이 큰 파일",
                                      self.analysis_result['large_files'])
        else:
            messagebox.showinfo("알림", "먼저 드라이브 분석을 실행해주세요.")

    def get_trash_files(self):
        """휴지통 파일 목록 가져오기"""
        trash_info = self.load_trash_info()
        files = []

        for trash_filename, info in trash_info.items():
            trash_file_path = self.trash_dir / trash_filename
            if trash_file_path.exists():
                actual_size = trash_file_path.stat().st_size
            else:
                actual_size = info.get('size', 0)

            files.append({
                'name': Path(info['original_path']).name,
                'path': info['original_path'],
                'size': actual_size,
                'modified': 0
            })

        return files

    def show_file_list_window(self, title, files, show_restore=False):
        """파일 목록 창 표시 (배치 로딩)"""
        list_window = tk.Toplevel(self.root)
        list_window.title(title)
        list_window.geometry("1300x750")
        list_window.configure(bg=self.bg_color)

        list_window.focus_force()
        list_window.bind('<Escape>', lambda e: list_window.destroy())

        # 헤더
        header = tk.Frame(list_window, bg=self.bg_color)
        header.pack(fill=tk.X, padx=20, pady=20)

        title_label = tk.Label(header, text=title, font=('맑은 고딕', 16, 'bold'),
                              bg=self.bg_color, fg='#2C3E50')
        title_label.pack(side=tk.LEFT)

        total_size = sum(f['size'] for f in files)
        info_label = tk.Label(header, text=f"{len(files)}개 파일 · {self.format_bytes(total_size)}",
                             font=('맑은 고딕', 11), bg=self.bg_color, fg='#666666')
        info_label.pack(side=tk.LEFT, padx=20)

        # 로딩 표시
        loading_label = tk.Label(header, text="",
                                font=('맑은 고딕', 10), bg=self.bg_color, fg='#5B8DEF')
        loading_label.pack(side=tk.LEFT, padx=10)

        # 버튼 프레임
        btn_frame_top = tk.Frame(header, bg=self.bg_color)
        btn_frame_top.pack(side=tk.RIGHT)

        select_all_btn = tk.Button(btn_frame_top, text="모두 선택",
                                   command=lambda: self.select_all_tree_items(tree),
                                   bg='#5B8DEF', fg='white',
                                   font=('맑은 고딕', 9),
                                   relief='flat', padx=10, pady=3,
                                   cursor="hand2")
        select_all_btn.pack(side=tk.LEFT, padx=5)

        # 검색 프레임
        search_frame = tk.Frame(list_window, bg=self.bg_color)
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        search_label = tk.Label(search_frame, text="🔍 검색:", font=('맑은 고딕', 10),
                               bg=self.bg_color, fg='#666666')
        search_label.pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                               font=('맑은 고딕', 10), width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        filter_label = tk.Label(search_frame, text="유형 필터:", font=('맑은 고딕', 10),
                               bg=self.bg_color, fg='#666666')
        filter_label.pack(side=tk.LEFT, padx=(20, 5))

        # 파일 유형 목록 추출
        file_types_set = set()
        for file_info in files[:500]:  # 샘플링으로 유형 추출
            file_path = Path(file_info['path'])
            file_ext = file_path.suffix.upper()[1:] if file_path.suffix else '파일'
            file_types_set.add(file_ext)

        type_filter_var = tk.StringVar(value="전체")
        type_filter = ttk.Combobox(search_frame, textvariable=type_filter_var,
                                   values=["전체"] + sorted(list(file_types_set)),
                                   state='readonly', width=15, font=('맑은 고딕', 9))
        type_filter.pack(side=tk.LEFT, padx=5)

        # 파일 목록 (Treeview)
        list_frame = tk.Frame(list_window, bg='#FFFFFF')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ('이름', '수정한 날짜', '유형', '크기', '경로')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                           selectmode='extended', height=20)

        tree.heading('이름', text='이름', command=lambda: self.sort_treeview(tree, '이름', False))
        tree.heading('수정한 날짜', text='수정한 날짜', command=lambda: self.sort_treeview(tree, '수정한 날짜', False))
        tree.heading('유형', text='유형', command=lambda: self.sort_treeview(tree, '유형', False))
        tree.heading('크기', text='크기', command=lambda: self.sort_treeview(tree, '크기', False))
        tree.heading('경로', text='경로', command=lambda: self.sort_treeview(tree, '경로', False))

        tree.column('이름', width=250)
        tree.column('수정한 날짜', width=150)
        tree.column('유형', width=80)
        tree.column('크기', width=100)
        tree.column('경로', width=300)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree.bind('<Double-Button-1>', lambda e: self.open_file_from_tree(tree))
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, tree, files, list_window))

        # 모든 파일 데이터 준비
        all_files_data = []
        for file_info in files:
            file_path = Path(file_info['path'])
            if file_info.get('modified', 0) > 0:
                modified_date = datetime.datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
            else:
                modified_date = '-'
            file_ext = file_path.suffix.upper()[1:] if file_path.suffix else '파일'

            all_files_data.append({
                'name': file_info['name'],
                'modified': modified_date,
                'type': file_ext,
                'size': self.format_bytes(file_info['size']),
                'size_bytes': file_info['size'],
                'path': str(file_path.parent),
                'full_path': file_info['path']
            })

        # 배치 로딩으로 파일 추가
        def load_files_batch():
            total = len(all_files_data)
            loaded = [0]

            def load_batch():
                if not list_window.winfo_exists():
                    return

                batch_end = min(loaded[0] + BATCH_SIZE, total)

                for i in range(loaded[0], batch_end):
                    file_data = all_files_data[i]
                    tree.insert('', 'end', values=(
                        file_data['name'],
                        file_data['modified'],
                        file_data['type'],
                        file_data['size'],
                        file_data['path']
                    ), tags=(file_data['full_path'],))

                loaded[0] = batch_end

                if loaded[0] < total:
                    loading_label.config(text=f"로딩 중... {loaded[0]:,}/{total:,}")
                    list_window.after(BATCH_DELAY, load_batch)
                else:
                    loading_label.config(text="")

            load_batch()

        load_files_batch()

        # 검색 필터링 함수 (최적화)
        def apply_filter(*args):
            search_text = search_var.get().lower()
            type_filter_text = type_filter_var.get()

            # 트리뷰 초기화
            for item in tree.get_children():
                tree.delete(item)

            loading_label.config(text="필터링 중...")

            # 필터링된 파일 목록 추가 (배치로)
            filtered_data = []
            for file_data in all_files_data:
                name_match = search_text in file_data['name'].lower() or search_text in file_data['path'].lower()
                type_match = type_filter_text == "전체" or file_data['type'] == type_filter_text

                if name_match and type_match:
                    filtered_data.append(file_data)

            def load_filtered_batch():
                total = len(filtered_data)
                loaded = [0]

                def batch():
                    if not list_window.winfo_exists():
                        return

                    batch_end = min(loaded[0] + BATCH_SIZE, total)

                    for i in range(loaded[0], batch_end):
                        file_data = filtered_data[i]
                        tree.insert('', 'end', values=(
                            file_data['name'],
                            file_data['modified'],
                            file_data['type'],
                            file_data['size'],
                            file_data['path']
                        ), tags=(file_data['full_path'],))

                    loaded[0] = batch_end

                    if loaded[0] < total:
                        loading_label.config(text=f"필터링 중... {loaded[0]:,}/{total:,}")
                        list_window.after(BATCH_DELAY, batch)
                    else:
                        loading_label.config(text="")
                        # 정보 레이블 업데이트
                        if search_text or type_filter_text != "전체":
                            info_label.config(text=f"{len(filtered_data)}개 파일 (전체 {len(files)}개 중)")
                        else:
                            info_label.config(text=f"{len(files)}개 파일 · {self.format_bytes(total_size)}")

                batch()

            load_filtered_batch()

        # 검색어 변경 시 필터링 (디바운스 적용)
        filter_timer = [None]

        def debounced_filter(*args):
            if filter_timer[0]:
                list_window.after_cancel(filter_timer[0])
            filter_timer[0] = list_window.after(300, apply_filter)

        search_var.trace('w', debounced_filter)
        type_filter_var.trace('w', debounced_filter)

        # 하단 버튼
        btn_frame = tk.Frame(list_window, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        if show_restore:
            restore_btn = tk.Button(btn_frame, text="선택 항목 복원",
                                   command=lambda: self.restore_selected_from_tree(tree, list_window),
                                   bg='#52C41A', fg='white', font=('맑은 고딕', 11, 'bold'),
                                   relief='flat', pady=10, cursor="hand2")
            restore_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

            delete_btn = tk.Button(btn_frame, text="선택 항목 영구 삭제",
                                  command=lambda: self.permanent_delete_from_tree(tree, list_window),
                                  bg='#FF6B6B', fg='white', font=('맑은 고딕', 11, 'bold'),
                                  relief='flat', pady=10, cursor="hand2")
            delete_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            delete_btn = tk.Button(btn_frame, text="선택 항목 삭제",
                                  command=lambda: self.delete_selected_from_tree(tree, files, list_window),
                                  bg='#FF6B6B', fg='white', font=('맑은 고딕', 11, 'bold'),
                                  relief='flat', pady=10, cursor="hand2")
            delete_btn.pack(fill=tk.X)

    def open_file_from_tree(self, tree):
        """트리뷰에서 선택한 파일 열기"""
        selected_items = tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        tags = tree.item(item)['tags']
        if not tags:
            return
        file_path = tags[0]

        try:
            if os.path.exists(file_path):
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{file_path}"')
                else:
                    os.system(f'xdg-open "{file_path}"')
            else:
                messagebox.showwarning("경고", "파일을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 열 수 없습니다: {str(e)}")

    def open_file_location(self, tree):
        """파일이 있는 폴더 열기"""
        selected_items = tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        tags = tree.item(item)['tags']
        if not tags:
            return
        file_path = tags[0]

        try:
            if os.path.exists(file_path):
                folder_path = str(Path(file_path).parent)
                if platform.system() == 'Windows':
                    os.system(f'explorer /select,"{file_path}"')
                elif platform.system() == 'Darwin':
                    os.system(f'open -R "{file_path}"')
                else:
                    os.system(f'xdg-open "{folder_path}"')
            else:
                messagebox.showwarning("경고", "파일을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"폴더를 열 수 없습니다: {str(e)}")

    def delete_single_file_from_context(self, tree, files, window):
        """컨텍스트 메뉴에서 단일 파일 삭제"""
        selected_items = tree.selection()
        if not selected_items:
            return

        self.delete_selected_from_tree(tree, files, window)

    def show_duplicate_context_menu(self, event, file_path):
        """중복 파일에서 오른쪽 클릭 컨텍스트 메뉴 표시"""
        context_menu = tk.Menu(event.widget, tearoff=0)
        context_menu.add_command(label="파일 열기",
                                command=lambda: self.open_file_by_path(file_path))
        context_menu.add_command(label="파일 위치 열기",
                                command=lambda: self.open_folder_by_path(file_path))
        context_menu.add_separator()
        context_menu.add_command(label="삭제",
                                command=lambda: self.delete_file_by_path(file_path))

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def open_file_by_path(self, file_path):
        """파일 경로로 파일 열기"""
        try:
            if os.path.exists(file_path):
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{file_path}"')
                else:
                    os.system(f'xdg-open "{file_path}"')
            else:
                messagebox.showwarning("경고", "파일을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"파일을 열 수 없습니다: {str(e)}")

    def open_folder_by_path(self, file_path):
        """파일 경로로 폴더 열기"""
        try:
            if os.path.exists(file_path):
                folder_path = str(Path(file_path).parent)
                if platform.system() == 'Windows':
                    os.system(f'explorer /select,"{file_path}"')
                elif platform.system() == 'Darwin':
                    os.system(f'open -R "{file_path}"')
                else:
                    os.system(f'xdg-open "{folder_path}"')
            else:
                messagebox.showwarning("경고", "파일을 찾을 수 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"폴더를 열 수 없습니다: {str(e)}")

    def delete_file_by_path(self, file_path):
        """파일 경로로 파일 삭제"""
        result = messagebox.askyesno("확인", "이 파일을 휴지통으로 이동하시겠습니까?")
        if result:
            try:
                file_p = Path(file_path)
                if file_p.exists():
                    file_info = {
                        'path': file_path,
                        'name': file_p.name,
                        'size': file_p.stat().st_size,
                        'type': file_p.suffix.upper()[1:] if file_p.suffix else '파일'
                    }

                    if self.move_to_trash(file_path):
                        self.add_to_delete_history([file_info], "휴지통으로 이동")
                        self.update_action_buttons()
                        messagebox.showinfo("완료", "파일을 휴지통으로 이동했습니다.")
                    else:
                        messagebox.showerror("오류", "파일 삭제에 실패했습니다.")
                else:
                    messagebox.showwarning("경고", "파일을 찾을 수 없습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"파일 삭제 중 오류 발생: {str(e)}")

    def show_context_menu(self, event, tree, files, window):
        """오른쪽 클릭 컨텍스트 메뉴 표시"""
        item = tree.identify_row(event.y)
        if item:
            if item not in tree.selection():
                tree.selection_set(item)

            context_menu = tk.Menu(tree, tearoff=0)
            context_menu.add_command(label="파일 열기",
                                    command=lambda: self.open_file_from_tree(tree))
            context_menu.add_command(label="파일 위치 열기",
                                    command=lambda: self.open_file_location(tree))
            context_menu.add_separator()
            context_menu.add_command(label="삭제",
                                    command=lambda: self.delete_single_file_from_context(tree, files, window))

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

    def select_all_tree_items(self, tree):
        """트리뷰의 모든 항목 선택"""
        children = tree.get_children()
        tree.selection_set(children)

    def sort_treeview(self, tree, col, reverse):
        """트리뷰 정렬"""
        items = [(tree.set(item, col), item) for item in tree.get_children('')]

        if col == '크기':
            def parse_size(size_str):
                if 'B' not in size_str:
                    return 0
                try:
                    num = float(size_str.split()[0])
                    unit = size_str.split()[1]
                    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
                    return num * multipliers.get(unit, 1)
                except:
                    return 0

            items.sort(key=lambda x: parse_size(x[0]), reverse=reverse)
        elif col == '수정한 날짜':
            items.sort(key=lambda x: x[0] if x[0] != '-' else '', reverse=reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)

        for index, (val, item) in enumerate(items):
            tree.move(item, '', index)

        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))

    def delete_selected_from_tree(self, tree, files, window):
        """트리뷰에서 선택한 파일 삭제"""
        selected_items = tree.selection()

        if not selected_items:
            messagebox.showinfo("알림", "삭제할 파일을 선택해주세요.")
            return

        result = messagebox.askyesno("확인",
                                    f"{len(selected_items)}개 파일을 휴지통으로 이동하시겠습니까?")
        if result:
            deleted_count = 0
            deleted_files_info = []

            for item in selected_items:
                tags = tree.item(item)['tags']
                if not tags:
                    continue
                file_path = tags[0]

                try:
                    file_p = Path(file_path)
                    if file_p.exists():
                        file_info = {
                            'path': file_path,
                            'name': file_p.name,
                            'size': file_p.stat().st_size,
                            'type': file_p.suffix.upper()[1:] if file_p.suffix else '파일'
                        }

                        if self.move_to_trash(file_path):
                            deleted_files_info.append(file_info)
                            deleted_count += 1
                except:
                    pass

            if deleted_files_info:
                self.add_to_delete_history(deleted_files_info, "휴지통으로 이동")

            self.update_action_buttons()

            messagebox.showinfo("완료", f"{deleted_count}개 파일이 휴지통으로 이동되었습니다.")
            window.destroy()

    def restore_selected_from_tree(self, tree, window):
        """트리뷰에서 선택한 파일 복원"""
        selected_items = tree.selection()

        if not selected_items:
            messagebox.showinfo("알림", "복원할 파일을 선택해주세요.")
            return

        result = messagebox.askyesno("확인",
                                    f"{len(selected_items)}개 파일을 복원하시겠습니까?")
        if result:
            trash_info = self.load_trash_info()
            restored_count = 0

            for item in selected_items:
                tags = tree.item(item)['tags']
                if not tags:
                    continue
                original_path = tags[0]

                for trash_filename, info in trash_info.items():
                    if info['original_path'] == original_path:
                        trash_path = self.trash_dir / trash_filename
                        if trash_path.exists():
                            try:
                                target_path = Path(original_path)
                                target_path.parent.mkdir(parents=True, exist_ok=True)

                                if target_path.exists():
                                    base_name = target_path.stem
                                    extension = target_path.suffix
                                    counter = 1
                                    while target_path.exists():
                                        target_path = target_path.parent / f"{base_name}_복원{counter}{extension}"
                                        counter += 1

                                shutil.move(str(trash_path), str(target_path))
                                del trash_info[trash_filename]
                                restored_count += 1
                            except Exception as e:
                                pass
                        break

            self.save_trash_info(trash_info)
            self.update_action_buttons()

            messagebox.showinfo("완료", f"{restored_count}개 파일이 복원되었습니다.")
            window.destroy()

    def permanent_delete_from_tree(self, tree, window):
        """트리뷰에서 선택한 파일 영구 삭제"""
        selected_items = tree.selection()

        if not selected_items:
            messagebox.showinfo("알림", "삭제할 파일을 선택해주세요.")
            return

        result = messagebox.askyesno("경고",
                                    f"{len(selected_items)}개 파일을 영구 삭제하시겠습니까?\n"
                                    "이 작업은 되돌릴 수 없습니다.")
        if result:
            trash_info = self.load_trash_info()
            deleted_count = 0
            deleted_files_info = []

            for item in selected_items:
                tags = tree.item(item)['tags']
                if not tags:
                    continue
                original_path = tags[0]

                for trash_filename, info in trash_info.items():
                    if info['original_path'] == original_path:
                        trash_path = self.trash_dir / trash_filename
                        if trash_path.exists():
                            try:
                                file_size = trash_path.stat().st_size
                                file_info = {
                                    'path': original_path,
                                    'name': Path(original_path).name,
                                    'size': file_size,
                                    'type': Path(original_path).suffix.upper()[1:] if Path(original_path).suffix else '파일'
                                }

                                trash_path.unlink()
                                del trash_info[trash_filename]
                                deleted_files_info.append(file_info)
                                deleted_count += 1
                            except Exception as e:
                                pass
                        break

            if deleted_files_info:
                self.add_to_delete_history(deleted_files_info, "영구 삭제")

            self.save_trash_info(trash_info)
            self.update_action_buttons()

            messagebox.showinfo("완료", f"{deleted_count}개 파일이 영구 삭제되었습니다.")
            window.destroy()

    def move_to_trash(self, file_path):
        """파일을 휴지통으로 이동"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False

            file_size = source_path.stat().st_size

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            trash_filename = f"{timestamp}_{source_path.name}"
            trash_path = self.trash_dir / trash_filename

            shutil.move(str(source_path), str(trash_path))

            trash_info = self.load_trash_info()
            trash_info[trash_filename] = {
                'original_path': str(source_path),
                'deleted_date': datetime.datetime.now().isoformat(),
                'auto_delete_date': (datetime.datetime.now() +
                                    datetime.timedelta(days=30)).isoformat(),
                'size': file_size
            }
            self.save_trash_info(trash_info)

            return True
        except Exception:
            return False

    def load_trash_info(self):
        """휴지통 정보 로드"""
        if self.trash_info_file.exists():
            try:
                with open(self.trash_info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_trash_info(self, trash_info):
        """휴지통 정보 저장"""
        with open(self.trash_info_file, 'w', encoding='utf-8') as f:
            json.dump(trash_info, f, ensure_ascii=False, indent=2)

    def load_delete_history(self):
        """삭제 히스토리 로드"""
        if self.delete_history_file.exists():
            try:
                with open(self.delete_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_delete_history(self, history):
        """삭제 히스토리 저장"""
        with open(self.delete_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def add_to_delete_history(self, files_info, operation_type="삭제"):
        """삭제 히스토리에 추가"""
        history = self.load_delete_history()

        total_size = sum(f['size'] for f in files_info)

        before_free = after_free = 0
        if self.selected_drive:
            try:
                _, _, free = shutil.disk_usage(Path(self.selected_drive))
                after_free = free
                before_free = free - total_size
            except:
                pass

        record = {
            'timestamp': datetime.datetime.now().isoformat(),
            'operation_type': operation_type,
            'drive': self.selected_drive,
            'file_count': len(files_info),
            'total_size': total_size,
            'before_free_space': before_free,
            'after_free_space': after_free,
            'files': files_info
        }

        history.append(record)
        self.save_delete_history(history)

    def generate_report(self):
        """삭제 히스토리 보고서 생성"""
        delete_history = self.load_delete_history()

        if not delete_history:
            messagebox.showinfo("알림", "삭제 히스토리가 없습니다.\n파일을 삭제한 후 보고서를 생성할 수 있습니다.")
            return

        permanent_deletes = [record for record in delete_history if record.get('operation_type') == '영구 삭제']
        trash_moves = [record for record in delete_history if record.get('operation_type') != '영구 삭제']

        if not permanent_deletes and not trash_moves:
            messagebox.showinfo("알림", "삭제 히스토리가 없습니다.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML 파일", "*.html"), ("모든 파일", "*.*")],
            initialfile=f"삭제_히스토리_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        if not file_path:
            return

        try:
            html_content = self.create_delete_history_html_report(permanent_deletes, trash_moves)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            messagebox.showinfo("완료", f"HTML 보고서가 생성되었습니다.")

            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"보고서 생성 중 오류 발생: {str(e)}")

    def create_delete_history_html_report(self, permanent_deletes, trash_moves):
        """삭제 히스토리 HTML 보고서 생성"""
        perm_deleted_files = sum(record['file_count'] for record in permanent_deletes) if permanent_deletes else 0
        perm_freed_space = sum(record['total_size'] for record in permanent_deletes) if permanent_deletes else 0

        trash_moved_files = sum(record['file_count'] for record in trash_moves) if trash_moves else 0
        trash_moved_space = sum(record['total_size'] for record in trash_moves) if trash_moves else 0

        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>삭제 히스토리 보고서</title>
    <style>
        body {{
            font-family: '맑은 고딕', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #F5F7FA;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2C3E50;
            font-size: 28px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #2C3E50;
            font-size: 20px;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #5B8DEF;
            padding-bottom: 10px;
        }}
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: inline-block;
            margin: 10px 30px 10px 0;
        }}
        .summary-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary-value {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .history-record {{
            background: #F8F9FA;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #5B8DEF;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .history-record:hover {{
            background: #E8EAF0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .record-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .record-time {{
            font-size: 16px;
            font-weight: bold;
            color: #2C3E50;
        }}
        .record-type {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            color: white;
            font-size: 12px;
            background: #5B8DEF;
        }}
        .record-stats {{
            color: #666;
            margin: 5px 0;
        }}
        .file-list {{
            margin-top: 15px;
            display: none;
        }}
        .file-list.show {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            background: white;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #E8E8E8;
            font-size: 13px;
        }}
        th {{
            background-color: #FFFFFF;
            color: #2C3E50;
            font-weight: 600;
            border-bottom: 2px solid #5B8DEF;
        }}
        tr:hover {{
            background-color: #F8F9FA;
        }}
        .freed-space {{
            color: #52C41A;
            font-weight: bold;
        }}
    </style>
    <script>
        function toggleFileList(id) {{
            var element = document.getElementById('files-' + id);
            element.classList.toggle('show');
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>삭제 히스토리 보고서</h1>

        <div class="summary-box">
            <div class="summary-item">
                <div class="summary-label">영구 삭제</div>
                <div class="summary-value">{perm_deleted_files:,}개 파일</div>
                <div class="summary-label" style="margin-top: 5px;">{self.format_bytes(perm_freed_space)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">휴지통 이동</div>
                <div class="summary-value">{trash_moved_files:,}개 파일</div>
                <div class="summary-label" style="margin-top: 5px;">{self.format_bytes(trash_moved_space)}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">총 확보 공간</div>
                <div class="summary-value">{self.format_bytes(perm_freed_space)}</div>
                <div class="summary-label" style="margin-top: 5px; font-size: 11px;">(영구 삭제 기준)</div>
            </div>
        </div>
"""

        if permanent_deletes:
            html += f"""
        <h2>영구 삭제 기록 ({len(permanent_deletes)}건)</h2>
        <p style="color: #FF6B6B; font-weight: bold;">실제로 저장 공간을 확보한 기록입니다</p>
"""
            for idx, record in enumerate(reversed(permanent_deletes)):
                timestamp = datetime.datetime.fromisoformat(record['timestamp'])
                time_str = timestamp.strftime('%Y년 %m월 %d일 %H:%M:%S')

                operation_type = record.get('operation_type', '삭제')
                file_count = record.get('file_count', 0)
                total_size = record.get('total_size', 0)
                drive = record.get('drive', '알 수 없음')
                before_free = record.get('before_free_space', 0)
                after_free = record.get('after_free_space', 0)

                space_change = ""
                if before_free > 0 and after_free > 0:
                    space_change = f"<br><span class='freed-space'>여유 공간: {self.format_bytes(before_free)} → {self.format_bytes(after_free)}</span>"

                html += f"""
        <div class="history-record" onclick="toggleFileList({idx})">
            <div class="record-header">
                <span class="record-time">{time_str}</span>
                <span class="record-type" style="background: #FF6B6B;">{operation_type}</span>
            </div>
            <div class="record-stats">
                드라이브: {drive} |
                파일 수: {file_count:,}개 |
                용량: <span class="freed-space">{self.format_bytes(total_size)}</span>
                {space_change}
            </div>
            <div class="file-list" id="files-{idx}">
                <table>
                    <tr>
                        <th>파일명</th>
                        <th>유형</th>
                        <th>크기</th>
                        <th>경로</th>
                    </tr>
"""

                for file_info in record.get('files', []):
                    file_name = file_info.get('name', '알 수 없음')
                    file_type = file_info.get('type', '-')
                    file_size = self.format_bytes(file_info.get('size', 0))
                    file_path = file_info.get('path', '')
                    file_dir = str(Path(file_path).parent) if file_path else '-'

                    html += f"""
                    <tr>
                        <td>{file_name}</td>
                        <td>{file_type}</td>
                        <td>{file_size}</td>
                        <td style="font-size: 11px; color: #999;">{file_dir}</td>
                    </tr>
"""

                html += """
                </table>
            </div>
        </div>
"""

        if trash_moves:
            html += f"""
        <h2>휴지통 이동 기록 ({len(trash_moves)}건)</h2>
        <p style="color: #999; font-size: 14px;">아직 영구삭제 되지 않아 저장 공간은 확보되지 않은 상태입니다</p>
"""
            offset = len(permanent_deletes)
            for idx, record in enumerate(reversed(trash_moves)):
                timestamp = datetime.datetime.fromisoformat(record['timestamp'])
                time_str = timestamp.strftime('%Y년 %m월 %d일 %H:%M:%S')

                operation_type = record.get('operation_type', '삭제')
                file_count = record.get('file_count', 0)
                total_size = record.get('total_size', 0)
                drive = record.get('drive', '알 수 없음')

                actual_idx = offset + idx

                html += f"""
        <div class="history-record" onclick="toggleFileList({actual_idx})" style="opacity: 0.7;">
            <div class="record-header">
                <span class="record-time">{time_str}</span>
                <span class="record-type" style="background: #95DE64;">{operation_type}</span>
            </div>
            <div class="record-stats">
                드라이브: {drive} |
                파일 수: {file_count:,}개 |
                용량: {self.format_bytes(total_size)}
            </div>
            <div class="file-list" id="files-{actual_idx}">
                <table>
                    <tr>
                        <th>파일명</th>
                        <th>유형</th>
                        <th>크기</th>
                        <th>경로</th>
                    </tr>
"""

                for file_info in record.get('files', []):
                    file_name = file_info.get('name', '알 수 없음')
                    file_type = file_info.get('type', '-')
                    file_size = self.format_bytes(file_info.get('size', 0))
                    file_path = file_info.get('path', '')
                    file_dir = str(Path(file_path).parent) if file_path else '-'

                    html += f"""
                    <tr>
                        <td>{file_name}</td>
                        <td>{file_type}</td>
                        <td>{file_size}</td>
                        <td style="font-size: 11px; color: #999;">{file_dir}</td>
                    </tr>
"""

                html += """
                </table>
            </div>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""
        return html

    def format_bytes(self, bytes_value):
        """바이트를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"


def main():
    """메인 함수"""
    root = tk.Tk()
    app = DiskSpaceManager(root)

    # 초기 프로그레스 바 그리기
    root.after(200, app.draw_progress_bar)

    root.mainloop()


if __name__ == "__main__":
    main()
