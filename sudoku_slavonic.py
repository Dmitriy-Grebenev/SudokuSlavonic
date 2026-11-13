import sys
import random
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QMessageBox,
    QFrame
)
from PyQt6.QtGui import QFontDatabase, QFont, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression

# ======================================================================
# НАСТРОЙКИ ВНЕШНЕГО ВИДА
# ======================================================================
FONT_FAMILY = "Driagwa"
CELL_SIZE = 80
FONT_SIZE_CELL = 46
FONT_SIZE_TITLE = 72
FONT_SIZE_UI = 36

# ----------------------------------------------------------------------
# 1. Логика генерации судоку
# ----------------------------------------------------------------------
def is_valid(board, row, col, num):
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                return False
    return True

def solve_sudoku(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve_sudoku(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def generate_puzzle(difficulty="medium"):
    board = [[0] * 9 for _ in range(9)]
    solve_sudoku(board)
    
    cells_to_keep = {"easy": 40, "medium": 32, "hard": 26}
    keep = cells_to_keep.get(difficulty, 32)
    
    puzzle = [row[:] for row in board]
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    
    for r, c in cells:
        if keep <= 0:
            break
        puzzle[r][c] = 0
        keep -= 1
    return puzzle, board

# ----------------------------------------------------------------------
# 2. Преобразование чисел в церковнославянскую цифирь и обратно
# ----------------------------------------------------------------------
UNITS = {1: "а҃", 2: "в҃", 3: "г҃", 4: "д҃", 5: "є҃",
         6: "ѕ҃", 7: "з҃", 8: "и҃", 9: "ѳ҃"}
TENS = {10: "і҃", 20: "к҃", 30: "л҃", 40: "м҃", 50: "н҃",
        60: "ѯ҃", 70: "ѻ҃", 80: "п҃", 90: "ч҃"}
HUNDREDS = {100: "р҃", 200: "с҃", 300: "т҃", 400: "у҃",
            500: "ф҃", 600: "х҃", 700: "ѱ҃", 800: "ѿ҃", 900: "ц҃"}

def arabic_to_slavonic(num):
    if num == 0: return ""
    if 1 <= num <= 9: return UNITS[num]
    if 10 <= num <= 19: return UNITS[num % 10] + TENS[10]
    if 20 <= num <= 99:
        tens = (num // 10) * 10
        units = num % 10
        return TENS[tens] + (UNITS[units] if units else "")
    return str(num)

def slavonic_to_arabic(text):
    text = text.strip()
    if not text: return None
    if text in "123456789": return int(text)
    for n, letter in UNITS.items():
        if letter == text or letter.replace("҃", "") == text.replace("҃", ""):
            return n
    return None

# ----------------------------------------------------------------------
# 3. Графический интерфейс и Темы
# ----------------------------------------------------------------------
THEMES = {
    "light": {
        "bg_main": "#F4EBD0", "bg_frame": "#FFF8E7",
        "bg_cell_1": "#FFF8E7", "bg_cell_2": "#F0E3C8",
        "bg_fixed": "#E8D5B5", "bg_focus": "#FFE4B5",
        "text": "#2B1F1C", "text_fixed": "#1A1413",
        "border_thin": "#D2B48C", "border_thick": "#8B1E1E",
        "btn_bg": "#8B1E1E", "btn_text": "#F4EBD0", "btn_hover": "#A52A2A",
        "combo_bg": "#FFF8E7", "combo_text": "#2B1F1C"
    },
    "dark": {
        "bg_main": "#1A1413", "bg_frame": "#2B1F1C",
        "bg_cell_1": "#2B1F1C", "bg_cell_2": "#1F1615",
        "bg_fixed": "#15100F", "bg_focus": "#3E2723",
        "text": "#E6D5B8", "text_fixed": "#D4AF37",
        "border_thin": "#4A3B38", "border_thick": "#D4AF37",
        "btn_bg": "#D4AF37", "btn_text": "#1A1413", "btn_hover": "#E6C65C",
        "combo_bg": "#2B1F1C", "combo_text": "#E6D5B8"
    }
}

class SudokuCell(QLineEdit):
    def __init__(self, row, col, is_fixed=False, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.is_fixed = is_fixed
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMaxLength(2) 
        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        
        regex = QRegularExpression("[1-9а-ѳА-Ѳ҃]")
        self.setValidator(QRegularExpressionValidator(regex, self))
        self.setFont(QFont(FONT_FAMILY, FONT_SIZE_CELL))
        self.textChanged.connect(self.on_text_changed)

    def on_text_changed(self, text):
        if self.isReadOnly(): return
        if len(text) == 1 and text in "123456789":
            num = int(text)
            self.blockSignals(True)
            self.setText(arabic_to_slavonic(num))
            self.blockSignals(False)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if len(self.text()) > 0:
                self.clear()
                event.accept()
                return
        super().keyPressEvent(event)

class SudokuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Судоку · Славянская цифирь")
        self.setFixedSize(850, 1000)
        
        self.current_theme = "light"
        self.solution_board = None
        
        self.font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        self.load_fonts()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 20, 30, 30)
        self.main_layout.setSpacing(15)
        
        # --- Верхняя панель с кнопкой темы в правом углу ---
        self.top_bar = QHBoxLayout()
        self.top_bar.addStretch()
        
        self.theme_btn = QPushButton("🌙 Тёмная тема")
        self.theme_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setFixedHeight(50)
        self.top_bar.addWidget(self.theme_btn)
        
        self.main_layout.addLayout(self.top_bar)
        
        # --- Заголовок ---
        self.title_label = QLabel("СУДОКУ")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_TITLE, QFont.Weight.Bold))
        self.main_layout.addWidget(self.title_label)
        
        # --- Панель управления ---
        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(15)
        
        self.difficulty_label = QLabel("Сложность:")
        self.difficulty_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Лёгкий", "Средний", "Сложный"])
        self.difficulty_combo.setCurrentText("Средний")
        self.difficulty_combo.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        
        self.new_game_btn = QPushButton("Новая игра")
        self.new_game_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        self.new_game_btn.clicked.connect(self.new_game)
        
        self.check_btn = QPushButton("Проверить")
        self.check_btn.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        self.check_btn.clicked.connect(self.check_solution)
        
        self.control_layout.addWidget(self.difficulty_label)
        self.control_layout.addWidget(self.difficulty_combo)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.new_game_btn)
        self.control_layout.addWidget(self.check_btn)
        self.main_layout.addLayout(self.control_layout)
        
        # --- Сетка ---
        self.grid_frame = QFrame()
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(15, 15, 15, 15) 
        
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        for r in range(9):
            for c in range(9):
                cell = SudokuCell(r, c)
                self.grid_layout.addWidget(cell, r, c)
                self.cells[r][c] = cell
        
        self.main_layout.addWidget(self.grid_frame)
        
        self.apply_theme()
        self.new_game()

    def load_fonts(self):
        if not os.path.exists(self.font_dir):
            os.makedirs(self.font_dir)
            print(f"Папка {self.font_dir} создана. Поместите в неё шрифт {FONT_FAMILY}.otf.")
            return
        
        for font_file in os.listdir(self.font_dir):
            if font_file.lower().endswith(('.ttf', '.otf')):
                font_path = os.path.join(self.font_dir, font_file)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    print(f"Не удалось загрузить шрифт: {font_path}")
                else:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"Загружен шрифт: {font_file} -> {families}")

    def toggle_theme(self):
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_btn.setText("☀️ Светлая тема")
        else:
            self.current_theme = "light"
            self.theme_btn.setText("🌙 Тёмная тема")
        self.apply_theme()

    def show_message(self, icon, title, text):
        t = THEMES[self.current_theme]
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        msg_box.setFont(QFont(FONT_FAMILY, FONT_SIZE_UI))
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {t['bg_main']};
                font-family: '{FONT_FAMILY}';
            }}
            QLabel {{
                color: {t['text']};
                font-size: {FONT_SIZE_UI}px;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton {{
                background-color: {t['btn_bg']};
                color: {t['btn_text']};
                border: 2px solid {t['border_thick']};
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: {FONT_SIZE_UI}px;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton:hover {{
                background-color: {t['btn_hover']};
            }}
        """)
        msg_box.exec()

    def apply_theme(self):
        t = THEMES[self.current_theme]
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {t['bg_main']}; }}
            QLabel {{ color: {t['text']}; background-color: transparent; }}
            
            QComboBox {{
                background-color: {t['combo_bg']}; color: {t['combo_text']};
                border: 2px solid {t['border_thick']}; border-radius: 6px;
                padding: 4px 8px; font-size: {FONT_SIZE_UI}px;
            }}
            QComboBox::drop-down {{ border: none; }}
            
            /* СТИЛИ ДЛЯ ВЫПАДАЮЩЕГО СПИСКА */
            QComboBox QAbstractItemView {{
                background-color: {t['combo_bg']};
                color: {t['combo_text']};
                border: 2px solid {t['border_thick']};
                selection-background-color: {t['btn_bg']};
                selection-color: {t['btn_text']};
                font-size: {FONT_SIZE_UI}px;
                font-family: '{FONT_FAMILY}';
                outline: none;
            }}
            
            QPushButton {{
                background-color: {t['btn_bg']}; color: {t['btn_text']};
                border: 2px solid {t['border_thick']}; border-radius: 6px;
                padding: 8px 16px; font-weight: bold; font-size: {FONT_SIZE_UI}px;
            }}
            QPushButton:hover {{ background-color: {t['btn_hover']}; }}
        """)
        
        self.title_label.setStyleSheet(f"color: {t['border_thick']}; margin-bottom: 10px; font-size: {FONT_SIZE_TITLE}px;")
        
        self.grid_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t['bg_frame']};
                border: 5px solid {t['border_thick']};
                border-radius: 10px;
            }}
        """)
        
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                
                top = 5 if r % 3 == 0 else 1
                left = 5 if c % 3 == 0 else 1
                bottom = 5 if r == 8 else 1
                right = 5 if c == 8 else 1
                
                block_idx = (r // 3) * 3 + (c // 3)
                bg = t['bg_cell_1'] if block_idx % 2 == 0 else t['bg_cell_2']
                
                if cell.is_fixed:
                    bg = t['bg_fixed']
                    text_color = t['text_fixed']
                else:
                    text_color = t['text']
                
                b_color_thick = t['border_thick']
                b_color_thin = t['border_thin']
                
                cell.setStyleSheet(f"""
                    QLineEdit {{
                        background-color: {bg};
                        color: {text_color};
                        border-top: {top}px solid {b_color_thick if top > 1 else b_color_thin};
                        border-left: {left}px solid {b_color_thick if left > 1 else b_color_thin};
                        border-bottom: {bottom}px solid {b_color_thick if bottom > 1 else b_color_thin};
                        border-right: {right}px solid {b_color_thick if right > 1 else b_color_thin};
                        font-size: {FONT_SIZE_CELL}px;
                    }}
                    QLineEdit:focus {{
                        background-color: {t['bg_focus']};
                    }}
                """)

    def new_game(self):
        difficulty_map = {"Лёгкий": "easy", "Средний": "medium", "Сложный": "hard"}
        diff = difficulty_map.get(self.difficulty_combo.currentText(), "medium")
        puzzle, solution = generate_puzzle(diff)
        self.solution_board = solution
        
        for r in range(9):
            for c in range(9):
                cell = self.cells[r][c]
                val = puzzle[r][c]
                if val != 0:
                    cell.setText(arabic_to_slavonic(val))
                    cell.setReadOnly(True)
                    cell.is_fixed = True
                else:
                    cell.setText("")
                    cell.setReadOnly(False)
                    cell.is_fixed = False
        self.apply_theme()

    def check_solution(self):
        if self.solution_board is None:
            return
        
        user_board = [[0] * 9 for _ in range(9)]
        empty_cells = []
        for r in range(9):
            for c in range(9):
                text = self.cells[r][c].text().strip()
                if not text:
                    empty_cells.append((r, c))
                    continue
                
                num = slavonic_to_arabic(text)
                if num is None:
                    self.show_message(QMessageBox.Icon.Warning, "Ошибка", f"Некорректный символ в ячейке ({r+1}, {c+1})!")
                    return
                user_board[r][c] = num
        
        if empty_cells:
            self.show_message(QMessageBox.Icon.Information, "Проверка", f"Заполнено не всё. Осталось ячеек: {len(empty_cells)}")
            return
        
        for r in range(9):
            for c in range(9):
                if user_board[r][c] != self.solution_board[r][c]:
                    self.show_message(QMessageBox.Icon.Warning, "Проверка", f"Ошибка в ячейке ({r+1}, {c+1})!")
                    return
        
        self.show_message(QMessageBox.Icon.Information, "Поздравляем!", "Судоку решено верно! 🎉")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SudokuWindow()
    window.show()
    sys.exit(app.exec())