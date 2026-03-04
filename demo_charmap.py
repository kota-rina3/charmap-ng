#!/usr/bin/env python3
"""
字符映射表 - 演示版
用于演示核心功能逻辑
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QComboBox, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import fontTools.ttLib


class DemoCharMapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_files = []
        self.current_font_path = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("字符映射表 - 演示版")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 上方工具栏
        toolbar_layout = QHBoxLayout()
        
        # 导入字体按钮
        import_btn = QLabel("导入字体:")
        self.import_button = QLabel("[点击选择字体文件]")
        self.import_button.setStyleSheet("color: blue; text-decoration: underline; padding-left: 5px;")
        self.import_button.mousePressEvent = self.import_font
        
        toolbar_layout.addWidget(import_btn)
        toolbar_layout.addWidget(self.import_button)
        toolbar_layout.addStretch()
        
        # 字体选择下拉框
        font_label = QLabel("选择字体:")
        self.font_combo = QComboBox()
        self.font_combo.setMinimumWidth(200)
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
        self.status_bar.showMessage("请导入字体文件")
    
    def import_font(self, event):
        """导入字体文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择字体文件", 
            "", 
            "字体文件 (*.ttf *.otf);;所有文件 (*)"
        )
        
        if file_path and os.path.exists(file_path):
            # 检查是否已存在
            if file_path not in self.font_files:
                self.font_files.append(file_path)
                self.font_combo.addItem(os.path.basename(file_path), userData=file_path)
                
                # 自动选中新添加的字体
                self.font_combo.setCurrentText(os.path.basename(file_path))
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
                    if isinstance(code, int) and code >= 0 and code < 0x10000:  # 限制在基本多文种平面
                        char_codes.add(code)
            
            # 转换为排序后的列表
            sorted_chars = sorted(list(char_codes))
            
            font.close()
            return sorted_chars[:512]  # 限制数量以便演示
            
        except Exception as e:
            print(f"无法读取字体文件: {str(e)}")
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
                
                # 设置字体大小以确保可见性
                font = QFont()
                font.setPointSize(14)
                item.setFont(font)
                
                self.table.setItem(row, col, item)
            except ValueError:
                # 如果无法转换为字符，则跳过
                continue
    
    def on_font_changed(self, font_name):
        """字体选择变化时的处理"""
        if not font_name:
            return
            
        font_path = self.font_combo.currentData()
        if font_path:
            self.current_font_path = font_path
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
            
            # 复制到剪贴板（如果可用）
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(char)
                self.status_bar.showMessage(f"字符 '{char}' 已复制到剪贴板 | {status_text}", 5000)
            except:
                self.status_bar.showMessage(f"字符 '{char}' | {status_text}")
    
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
            (0x1000, 0x109F, "缅甸文"),
            (0x1100, 0x11FF, "谚文"),
            (0x1E00, 0x1EFF, "拉丁文扩展附加"),
            (0x1F00, 0x1FFF, "希腊文扩展"),
            (0x2000, 0x206F, "常用标点"),
            (0x2070, 0x209F, "上标和下标"),
            (0x20A0, 0x20CF, "货币符号"),
            (0x2100, 0x214F, "字母式符号"),
            (0x2150, 0x218F, "数字形式"),
            (0x2190, 0x21FF, "箭头"),
            (0x2200, 0x22FF, "数学运算符号"),
            (0x2300, 0x23FF, "杂项技术符号"),
            (0x2400, 0x243F, "控制图片"),
            (0x2460, 0x24FF, "封闭式字母数字"),
            (0x2500, 0x257F, "制表符"),
            (0x2580, 0x259F, "块元素"),
            (0x25A0, 0x25FF, "几何形状"),
            (0x2600, 0x26FF, "杂项符号"),
            (0x2700, 0x27BF, "印刷符号"),
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
            (0x4E00, 0x9FFF, "CJK统一汉字"),
            (0xAC00, 0xD7AF, "谚文音节"),
            (0xE000, 0xF8FF, "私人使用区-A"),
            (0xF900, 0xFAFF, "CJK兼容汉字"),
            (0xFE00, 0xFE0F, "变体选择符"),
            (0xFF00, 0xFFEF, "半角和全角形式"),
        ]
        
        for start, end, name in partitions:
            if start <= code_point <= end:
                return name
        
        return "其他"
    

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("字符映射表 - 演示版")
    
    window = DemoCharMapApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()