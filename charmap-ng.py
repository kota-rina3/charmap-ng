#!/usr/bin/env python

from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMessageBox
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QGuiApplication, QDesktopServices
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.uic import loadUi
import sys,os,unicodedata

UNICODE_BLOCKS = [
        ("全部", 0x0000, 0xF8FF),
        ("基本拉丁字母", 0x0000, 0x007F),
        ("拉丁字母补充", 0x0080, 0x00FF),
        ("拉丁字母扩展-A", 0x0100, 0x017F),
        ("拉丁字母扩展-B", 0x0180, 0x024F),
        ("国际音标扩展", 0x0250, 0x02AF),
        ("希腊字母和科普特字母", 0x0370, 0x03FF),
        ("西里尔字母", 0x0400, 0x04FF),
        ("中文标点", 0x3000, 0x303F),
        ("平假名", 0x3040, 0x309F),
        ("片假名", 0x30A0, 0x30FF),
        ("注音符号", 0x3100, 0x312F),
        ("中日韩统一表意文字", 0x4E00, 0x9FFF),
        ("中日韩统一表意文字扩展-B", 0x20000, 0x2A6DF),
        ("半角及全角字符", 0xFF00, 0xFFEF),
        ("箭头", 0x2190, 0x21FF),
        ("数学运算符", 0x2200, 0x22FF),
        ("几何形状", 0x25A0, 0x25FF),
        ("表情符号", 0x2600, 0x26FF),
        ("表情符号扩展", 0x1F600, 0x1F64F),
        ("杂项符号和图案", 0x1F300, 0x1F5FF),
        ("私人使用区", 0xE000, 0xF8FF),
    ]

class CharMapNG(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("./ui/NGmain.ui", self)
        self.setWindowTitle("字符映射表")
        self.setWindowIcon(QIcon("./ui/charmap.png"))
        self.setFixedSize(550, 660)

        self.populate_fonts()
        self.fontChoice.currentTextChanged.connect(self.on_font_changed)

        QTimer.singleShot(0, self.load_characters)

        self.fonts.setText("字体(F):")

        self.fontChoice.setEditable(False)

        self.help.setText("帮助(H)")
        self.help.clicked.connect(self.jump_help)

        self.fontMap.setColumnCount(int(10)) # 创建字符表格
        self.fontMap.setRowCount(0)
        self.fontMap.horizontalHeader().setVisible(False)
        self.fontMap.verticalHeader().setVisible(False)
        self.fontMap.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.fontMap.cellClicked.connect(self.on_cell_clicked)
        self.fontMap.verticalHeader().setDefaultSectionSize(30) # 设置表格单元格大小
        self.fontMap.horizontalHeader().setDefaultSectionSize(30)

        self.textShow.setText(" ")
        self.textShow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.textShow.setStyleSheet("color: black; font-size: 70px; border: 2px solid #0078D7; padding: 10px; background-color: #F0F0F0;")

        self.texts.setText("选择多个字符：")

        self.anyText.setPlaceholderText("输入多个字符")

        self.choseTexts.setText("选择")
        self.choseTexts.clicked.connect(self.addChars)

        
        self.copyTexts.setText("复制上面的字符")
        self.copyTexts.clicked.connect(self.copyChars)

        self.clearTexts.setText("清除")
        self.clearTexts.clicked.connect(self.anyText.clear)


        self.tectCopy.setText("复制单字符(A):")

        self.copyText.setText("复制选中的字符") # 复制按钮
        self.copyText.clicked.connect(self.copy_char)

        self.coptUni.setText("复制选中的Unicode") # 复制按钮
        self.coptUni.clicked.connect(self.copy_code)

        self.group.setText("分组依据(G):")

        for blocks, start, end in UNICODE_BLOCKS:   # 分组依据
            self.choseGroup.addItem(f"{blocks} (U+{start:04X}-U+{end:04X})", (start, end))
        self.choseGroup.setCurrentIndex(0)
        self.choseGroup.currentIndexChanged.connect(self.on_block_changed)
        self.choseGroup.setMinimumWidth(250)

        self.search.setText("搜索(E):")

        self.textSch.setPlaceholderText("输入字符（如：酸）或Unicode（如：U+9178）")
        self.textSch.textChanged.connect(self.on_search_changed)

        self.clearSch.setText("清除")
        self.clearSch.clicked.connect(self.textSch.clear)
        
        self.msg.showMessage("就绪")  # 状态栏

        self.current_char = None
        self.current_code_point = None

        default_font = QFont(self.fontChoice.currentText(), 16)
        self.fontMap.setFont(default_font)

    def jump_help(self):
        QDesktopServices.openUrl(QUrl("https://github.com/kota-rina3/charmap-ng"))

    def populate_fonts(self):
        """填充字体列表"""
        families = QFontDatabase.families()
        self.fontChoice.addItems(sorted(families))

    def load_characters(self):
        index = self.choseGroup.currentIndex()
        if index < 0:
            return
        start_code, end_code = self.choseGroup.itemData(index)
        columns = 10
        total_chars = end_code - start_code + 1
        rows = (total_chars + columns - 1) // columns

        # 重置表格
        self.fontMap.setRowCount(rows)
        self.fontMap.setColumnCount(columns)
        self.fontMap.clearContents()
        # 预设行列尺寸（可选）
        for col in range(columns):
            self.fontMap.setColumnWidth(col, 49)
        for row in range(rows):
            self.fontMap.setRowHeight(row, 49)

        self._load_batch(start_code, end_code, start_code, columns)

    def _load_batch(self, start_code, end_code, current, columns):
        """每次处理 200 个字符，避免阻塞"""
        BATCH_SIZE = 300
        batch_end = min(current + BATCH_SIZE - 1, end_code)

        for code in range(current, batch_end + 1):
            offset = code - start_code
            row = offset // columns
            col = offset % columns
            try:
                char = chr(code)
                item = QTableWidgetItem(char)
                item.setData(Qt.ItemDataRole.UserRole, code)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setToolTip(f"U+{code:04X}")
                self.fontMap.setItem(row, col, item)
            except:
                pass

        # 还有剩余字符 → 继续下一批
        if batch_end < end_code:
            QTimer.singleShot(1, lambda: self._load_batch(start_code, end_code, batch_end + 1, columns))
        else:
            self.msg.showMessage(f"已加载区块: {self.choseGroup.currentText()}")

    def update_font(self):
        """优化版：只需更新整个表格的字体，无需遍历单元格"""
        font_family = self.fontChoice.currentText()
        font_size = 16
        font = QFont(font_family, font_size)
        self.fontMap.setFont(font)

        # 同时更新预览字符字体
        if self.current_char:
            self.textShow.setFont(font)

    def on_font_changed(self):
        self.update_font()

    def on_block_changed(self):
        self.load_characters()

    def on_cell_clicked(self, row, col):
        """表格单元格点击事件"""
        item = self.fontMap.item(row, col)
        if not item:
            return
        
        char = item.text()
        code_point = item.data(Qt.ItemDataRole.UserRole)
        
        # 保存当前选中
        self.current_char = char
        self.current_code_point = code_point
        
        # 显示字符信息
        self.textShow.setText(char)

        # 更新预览字体
        font_family = self.fontChoice.currentText()
        font_size = int(20)
        font = QFont(font_family, font_size)
        self.textShow.setFont(font)

        # 状态栏
        self.msg.showMessage(f"{char} (U+{code_point:04X})")

    def get_char_name(self, code_point):
        """获取字符名称"""
        try:
            char = chr(code_point)
            name = unicodedata.name(char, "未知")
            return name
        except:
            return "未知"
        
    def get_char_category(self, code_point):
        """获取字符类别"""
        try:
            char = chr(code_point)
            category = unicodedata.category(char)
            return category
        except:
            return "未知"

    def addChars(self):
        if self.current_char: 
            self.anyText.insert(self.current_char) # 累加多个字符
        else:
            QMessageBox.warning(self, "警告", "请至少选择一个字符")

    def copy_char(self):
        """复制当前选中的字符到剪贴板"""
        if self.current_char:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.current_char)
            self.msg.showMessage(f"已复制字符: {self.current_char}")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个字符")

    def copyChars(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.anyText.text())
        self.msg.showMessage("已复制多个文本")
        
    def copy_code(self):
        """复制当前选中字符的Unicode代码到剪贴板"""
        if self.current_code_point is not None:
            code_str = f"U+{self.current_code_point:04X}"
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(code_str)
            self.msg.showMessage(f"已复制Unicode代码: {code_str}")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个字符")

    def on_search_changed(self):
        """搜索字符"""
        text = self.textSch.text().strip().upper()
        if not text:
            return
        
        # 检查是否是U+格式的Unicode代码
        if text.startswith("U+") and len(text) <= 7:
            try:
                code_point = int(text[2:], 16)
                self.search_by_code_point(code_point)
                return
            except:
                pass
        
        # 搜索字符
        for row in range(self.fontMap.rowCount()):
            for col in range(self.fontMap.columnCount()):
                item = self.fontMap.item(row, col)
                if item and item.text() == text:
                    self.fontMap.setCurrentCell(row, col)
                    self.fontMap.scrollToItem(item)
                    self.on_cell_clicked(row, col)
                    return
        
        # 搜索字符名称
        for row in range(self.fontMap.rowCount()):
            for col in range(self.fontMap.columnCount()):
                item = self.fontMap.item(row, col)
                if item:
                    code_point = item.data(Qt.ItemDataRole.UserRole)
                    name = self.get_char_name(code_point).upper()
                    if text in name:
                        self.fontMap.setCurrentCell(row, col)
                        self.fontMap.scrollToItem(item)
                        self.on_cell_clicked(row, col)
                        return
        
        self.msg.showMessage(f"未找到匹配的字符: {text}")

    def search_by_code_point(self, code_point):
        """通过代码点搜索字符"""
        for row in range(self.fontMap.rowCount()):
            for col in range(self.fontMap.columnCount()):
                item = self.fontMap.item(row, col)
                if item and item.data(Qt.ItemDataRole.UserRole) == code_point:
                    self.fontMap.setCurrentCell(row, col)
                    self.fontMap.scrollToItem(item)
                    self.on_cell_clicked(row, col)
                    self.msg.showMessage(f"找到字符: U+{code_point:04X}")
                    return
        
        # 如果当前区块没有，尝试切换到包含该代码点的区块
        for idx, (blocks, start, end) in enumerate(UNICODE_BLOCKS):
            if start <= code_point <= end:
                self.choseGroup.setCurrentIndex(idx)
                QTimer.singleShot(100, lambda: self.search_by_code_point(code_point))
                return
        
        self.msg.showMessage(f"未找到字符: U+{code_point:04X}")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ['QT_QPA_PLATFORM'] = 'xcb' 
    app = QApplication(sys.argv)
    window = CharMapNG()
    window.show()
    sys.exit(app.exec())