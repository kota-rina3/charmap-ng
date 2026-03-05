#!/usr/bin/env python3
"""
字符映射表软件
功能：
- 读取或导入字体文件
- 下拉框控件选择字体文件
- 在表格控件中显示该字体所有字符
- 点击任意方格复制某字符
- statusbar控件显示UTF-8编码及字符分区
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QHeaderView, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import fontTools.ttLib


class CharMapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_files = {}  # 存储字体名和路径的字典
        self.current_font_path = None
        self.current_font_name = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("字符映射表")
        self.setGeometry(100, 100, 1000, 700)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 上方工具栏
        toolbar_layout = QHBoxLayout()

        # 导入字体按钮
        self.import_button = QPushButton("导入字体")
        self.import_button.clicked.connect(self.import_font)

        toolbar_layout.addWidget(self.import_button)
        toolbar_layout.addStretch()

        # 字体选择下拉框
        font_label = QLabel("选择字体:")
        self.font_combo = QComboBox()
        self.font_combo.setMinimumWidth(300)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)

        toolbar_layout.addWidget(font_label)
        toolbar_layout.addWidget(self.font_combo)

        main_layout.addLayout(toolbar_layout)

        # 表格控件显示字符
        self.table = QTableWidget()
        self.table.setColumnCount(16)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 连接单元格点击事件
        self.table.cellClicked.connect(self.on_cell_clicked)

        main_layout.addWidget(self.table)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("请选择或导入字体文件")

    def import_font(self):
        """导入字体文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字体文件",
            "",
            "字体文件 (*.ttf *.otf *.woff *.woff2);;所有文件 (*)"
        )

        if file_path and os.path.exists(file_path):
            font_name = os.path.basename(file_path)
            
            # 检查是否已存在
            if font_name not in self.font_files.values():
                self.font_files[font_name] = file_path
                self.font_combo.addItem(font_name, file_path)

                # 自动选中新添加的字体
                index = self.font_combo.findText(font_name)
                if index >= 0:
                    self.font_combo.setCurrentIndex(index)
            else:
                QMessageBox.information(self, "提示", "该字体文件已存在")

    def load_font_data(self, font_path):
        """加载字体文件中的字符数据"""
        try:
            font = fontTools.ttLib.TTFont(font_path)

            # 获取字体中的字符编码
            char_codes = set()
            for table in font['cmap'].tables:
                for code, name in table.cmap.items():
                    if isinstance(code, int) and code >= 0:
                        char_codes.add(code)

            # 转换为排序后的列表
            sorted_chars = sorted(list(char_codes))

            font.close()
            return sorted_chars

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取字体文件: {str(e)}")
            return []

    def display_characters(self, char_codes):
        """在表格中显示字符"""
        if not char_codes:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(16)
            return

        # 计算需要多少行
        rows = (len(char_codes) + 15) // 16  # 每行16个字符

        self.table.setRowCount(rows)
        self.table.setColumnCount(16)

        # 填充表格
        for i, code in enumerate(char_codes):
            row = i // 16
            col = i % 16

            # 尝试转换为字符
            try:
                char = chr(code)
                item = QTableWidgetItem(char)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 设置当前字体以确保字符按选定字体文件渲染
                if self.current_font_path:
                    font = QFont()
                    font.setFamily(self.current_font_name or os.path.basename(self.current_font_path))
                    font.setPointSize(16)
                    item.setFont(font)

                self.table.setItem(row, col, item)
            except ValueError:
                # 如果无法转换为字符，则跳过
                continue

    def on_font_changed(self, font_name):
        """字体选择变化时的处理"""
        if not font_name:
            return

        font_path = self.font_files.get(font_name)
        if font_path:
            self.current_font_path = font_path
            self.current_font_name = font_name
            self.load_and_display_font(font_path)

    def load_and_display_font(self, font_path):
        """加载并显示字体"""
        self.status_bar.showMessage(f"正在加载字体: {os.path.basename(font_path)}...")
        QApplication.processEvents()  # 更新界面

        char_codes = self.load_font_data(font_path)
        self.display_characters(char_codes)

        if char_codes:
            self.status_bar.showMessage(f"字体: {os.path.basename(font_path)}, 字符数: {len(char_codes)}")
        else:
            self.status_bar.showMessage(f"无法加载字体: {os.path.basename(font_path)}")

    def on_cell_clicked(self, row, column):
        """单元格点击事件 - 复制字符到剪贴板"""
        item = self.table.item(row, column)
        if item and item.text():
            char = item.text()

            # 获取字符的UTF-8编码
            utf8_bytes = char.encode('utf-8')
            utf8_hex = ' '.join([f'{b:02X}' for b in utf8_bytes])

            # 获取Unicode码点
            unicode_code = ord(char)
            unicode_hex = f'{unicode_code:04X}'

            # 获取字符分区信息
            partition = self.get_unicode_partition(unicode_code)

            # 显示状态信息
            status_text = f"字符: '{char}' | Unicode: U+{unicode_hex} | UTF-8: {utf8_hex} | 分区: {partition}"
            self.status_bar.showMessage(status_text)

            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(char)

            # 给用户反馈
            self.status_bar.showMessage(f"字符 '{char}' 已复制到剪贴板 | {status_text}", 5000)

    def get_unicode_partition(self, code_point):
        """获取字符所属的Unicode分区"""
        partitions = [
            (0x0000, 0x007F, "基本拉丁文"),
            (0x0080, 0x00FF, "拉丁文补充"),
            (0x0100, 0x017F, "拉丁文扩展-A"),
            (0x0180, 0x024F, "拉丁文扩展-B"),
            (0x0250, 0x02AF, "国际音标扩展"),
            (0x02B0, 0x02FF, "空白修饰字母"),
            (0x0300, 0x036F, "组合变音标记"),
            (0x0370, 0x03FF, "希腊文和科普特文"),
            (0x0400, 0x04FF, "西里尔文"),
            (0x0500, 0x052F, "西里尔文补充"),
            (0x0530, 0x058F, "亚美尼亚文"),
            (0x0590, 0x05FF, "希伯来文"),
            (0x0600, 0x06FF, "阿拉伯文"),
            (0x0700, 0x074F, "叙利亚文"),
            (0x0750, 0x077F, "阿拉伯文补充"),
            (0x0780, 0x07BF, "马尔代夫文"),
            (0x07C0, 0x07FF, "非洲文字"),
            (0x0800, 0x083F, "Samaritan "),
            (0x0840, 0x085F, "Mandaic"),
            (0x08A0, 0x08FF, "阿拉伯文扩展-A"),
            (0x0900, 0x097F, "天城文"),
            (0x0980, 0x09FF, "孟加拉文"),
            (0x0A00, 0x0A7F, "果鲁穆奇文"),
            (0x0A80, 0x0AFF, "古吉拉特文"),
            (0x0B00, 0x0B7F, "奥里亚文"),
            (0x0B80, 0x0BFF, "泰米尔文"),
            (0x0C00, 0x0C7F, "泰卢固文"),
            (0x0C80, 0x0CFF, "卡纳达文"),
            (0x0D00, 0x0D7F, "马拉雅拉姆文"),
            (0x0D80, 0x0DFF, "僧伽罗文"),
            (0x0E00, 0x0E7F, "泰文"),
            (0x0E80, 0x0EFF, "老挝文"),
            (0x0F00, 0x0FFF, "藏文"),
            (0x1000, 0x109F, "缅甸文"),
            (0x10A0, 0x10FF, "格鲁吉亚文"),
            (0x1100, 0x11FF, "谚文"),
            (0x1200, 0x137F, "埃塞俄比亚文"),
            (0x1380, 0x139F, "埃塞俄比亚补充"),
            (0x13A0, 0x13FF, "切罗基文"),
            (0x1400, 0x167F, "统一加拿大原住民音节文字"),
            (0x1680, 0x169F, "欧甘文"),
            (0x16A0, 0x16FF, "如尼文"),
            (0x1700, 0x171F, "他加禄文"),
            (0x1720, 0x173F, "哈努诺文"),
            (0x1740, 0x175F, "布希德文"),
            (0x1760, 0x177F, "塔格班瓦文"),
            (0x1780, 0x17FF, "高棉文"),
            (0x1800, 0x18AF, "蒙古文"),
            (0x18B0, 0x18FF, "加拿大原住民统一音节扩展"),
            (0x1900, 0x194F, "林布文"),
            (0x1950, 0x197F, "德宏泰文"),
            (0x1980, 0x19DF, "新傣仂文"),
            (0x19E0, 0x19FF, "高棉符号"),
            (0x1A00, 0x1A1F, "布吉文"),
            (0x1A20, 0x1AAF, "老挝文扩展"),
            (0x1B00, 0x1B7F, "巴厘文"),
            (0x1B80, 0x1BBF, "巽他文"),
            (0x1BC0, 0x1BFF, "巴塔克文"),
            (0x1C00, 0x1C4F, "雷布查文"),
            (0x1C50, 0x1C7F, "奥利奇基文"),
            (0x1CC0, 0x1CCF, "巽他文补充"),
            (0x1CD0, 0x1CFF, "吠陀扩展"),
            (0x1D00, 0x1D7F, "语音学扩展"),
            (0x1D80, 0x1DBF, "语音学扩展补充"),
            (0x1DC0, 0x1DFF, "组合变音标记补充"),
            (0x1E00, 0x1EFF, "拉丁文扩展附加"),
            (0x1F00, 0x1FFF, "希腊文扩展"),
            (0x2000, 0x206F, "常用标点"),
            (0x2070, 0x209F, "上标和下标"),
            (0x20A0, 0x20CF, "货币符号"),
            (0x20D0, 0x20FF, "组合变音标记补充"),
            (0x2100, 0x214F, "字母式符号"),
            (0x2150, 0x218F, "数字形式"),
            (0x2190, 0x21FF, "箭头"),
            (0x2200, 0x22FF, "数学运算符号"),
            (0x2300, 0x23FF, "杂项技术符号"),
            (0x2400, 0x243F, "控制图片"),
            (0x2440, 0x245F, "光学字符识别"),
            (0x2460, 0x24FF, "封闭式字母数字"),
            (0x2500, 0x257F, "制表符"),
            (0x2580, 0x259F, "块元素"),
            (0x25A0, 0x25FF, "几何形状"),
            (0x2600, 0x26FF, "杂项符号"),
            (0x2700, 0x27BF, "印刷符号"),
            (0x27C0, 0x27EF, "杂项数学符号-A"),
            (0x27F0, 0x27FF, "追加箭头-A"),
            (0x2800, 0x28FF, "盲文模式"),
            (0x2900, 0x297F, "追加箭头-B"),
            (0x2980, 0x29FF, "杂项数学符号-B"),
            (0x2A00, 0x2AFF, "追加数学运算符"),
            (0x2B00, 0x2BFF, "杂项符号和箭头"),
            (0x2C00, 0x2C5F, "格拉哥里文"),
            (0x2C60, 0x2C7F, "拉丁文扩展-C"),
            (0x2C80, 0x2CFF, "科普特文"),
            (0x2D00, 0x2D2F, "格鲁吉亚文补充"),
            (0x2D30, 0x2D7F, "提非纳文"),
            (0x2D80, 0x2DDF, "埃塞俄比亚扩展"),
            (0x2DE0, 0x2DFF, "西里尔文扩展-A"),
            (0x2E00, 0x2E7F, "追加标点"),
            (0x2E80, 0x2EFF, "中文部首补充"),
            (0x2F00, 0x2FDF, "康熙字典部首"),
            (0x2FF0, 0x2FFF, "表意文字描述符"),
            (0x3000, 0x303F, "CJK符号和标点"),
            (0x3040, 0x309F, "平假名"),
            (0x30A0, 0x30FF, "片假名"),
            (0x3100, 0x312F, "注音符号"),
            (0x3130, 0x318F, "谚文兼容字母"),
            (0x3190, 0x319F, "象形字注释标志"),
            (0x31A0, 0x31BF, "注音符号扩展"),
            (0x31C0, 0x31EF, "CJK笔画"),
            (0x31F0, 0x31FF, "片假名扩展"),
            (0x3200, 0x32FF, "封闭式CJK字母和月份"),
            (0x3300, 0x33FF, "CJK兼容"),
            (0x3400, 0x4DBF, "CJK扩展A"),
            (0x4DC0, 0x4DFF, "易经六十四卦"),
            (0x4E00, 0x9FFF, "CJK统一汉字"),
            (0x9FC0, 0x9FFF, "CJK统一汉字扩展A"),
            (0xA000, 0xA48F, "彝文"),
            (0xA490, 0xA4CF, "彝文补充"),
            (0xA4D0, 0xA4FF, "越南傣文"),
            (0xA500, 0xA63F, "瓦伊文"),
            (0xA640, 0xA69F, "西里尔文扩展-B"),
            (0xA6A0, 0xA6FF, "巴姆穆文"),
            (0xA700, 0xA71F, "语音学扩展补充"),
            (0xA720, 0xA7FF, "拉丁文扩展-D"),
            (0xA800, 0xA82F, "锡尔赫特文"),
            (0xA830, 0xA83F, "印度数字形式"),
            (0xA840, 0xA87F, "八思巴文"),
            (0xA880, 0xA8DF, "索拉什特拉文"),
            (0xA8E0, 0xA8FF, "天城文扩展"),
            (0xA900, 0xA92F, "克耶文"),
            (0xA930, 0xA95F, "勒姜文"),
            (0xA960, 0xA97F, "谚文扩展-A"),
            (0xA980, 0xA9DF, "爪哇文"),
            (0xAA00, 0xAA5F, "占文"),
            (0xAA60, 0xAA7F, "缅甸文扩展-A"),
            (0xAA80, 0xAADF, "泰国文"),
            (0xAAE0, 0xAAFF, "老挝文扩展"),
            (0xAB00, 0xAB2F, "格鲁吉亚文扩展"),
            (0xAB30, 0xAB6F, "拉丁文扩展-E"),
            (0xAB70, 0xABBF, "谚文音节"),
            (0xABC0, 0xABFF, "阿洪姆文"),
            (0xAC00, 0xD7AF, "谚文音节"),
            (0xD7B0, 0xD7FF, "谚文扩展-B"),
            (0xD800, 0xDB7F, "高半区"),
            (0xDB80, 0xDBFF, "高半区专用子区"),
            (0xDC00, 0xDFFF, "低半区"),
            (0xE000, 0xF8FF, "私人使用区-A"),
            (0xF900, 0xFAFF, "CJK兼容汉字"),
            (0xFB00, 0xFB4F, "字母表达形式"),
            (0xFB50, 0xFDFF, "阿拉伯文表达形式-A"),
            (0xFE00, 0xFE0F, "变体选择符"),
            (0xFE10, 0xFE1F, "竖排形式"),
            (0xFE20, 0xFE2F, "组合半符号"),
            (0xFE30, 0xFE4F, "CJK兼容形式"),
            (0xFE50, 0xFE6F, "小型变体形式"),
            (0xFE70, 0xFEFF, "阿拉伯文表达形式-B"),
            (0xFF00, 0xFFEF, "半角和全角形式"),
            (0xFFF0, 0xFFFF, "特殊区域"),
        ]

        for start, end, name in partitions:
            if start <= code_point <= end:
                return name

        return "未知分区"


def main():
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("字符映射表")
    app.setOrganizationName("PyQt6")

    window = CharMapApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()