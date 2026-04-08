<div align="center"> <img width="128" height="128" alt="charmap" src="https://github.com/user-attachments/assets/2dbfd417-1e98-4613-9d14-ec740572756e" /> <div>


### 字符映射表NG版
微软字符映射表 (charmap.exe) 的开源复刻

# <div align="left"> 来源 <div>
<div align="left"> 本人心血来潮，觉得字符映射表这款软件很有趣，于是就复刻并开源了。NG的意思是该软件可以在Windows、MacOS和Linux下编译运行 <div>

# <div align="left"> 用法 <div>
<div align="left"> 类似Windows原版charmap.exe，选择字体可查看该字体在映射表的分布，支持分组查看，能选择多个字符并复制，还能通过搜索查找文字和Unicode <div>

# <div align="left"> 截图 <div>
<div align="center"> <img width="276" height="346" alt="2026-04-08_225844" src="https://github.com/user-attachments/assets/7d60e99e-08ce-4922-993e-be4f23e7317d" /> <img width="274" height="350" alt="截图_charamap-ng py_20260408230903" src="https://github.com/user-attachments/assets/551b295d-29e7-41be-a820-14593d086771" /> <div>

# <div align="left"> 编译 <div>
老规矩，pip安装下列模块：
`pip3 install pyqt6 nuitka`

nuitka编译：
`nuitka --onefile --standalone --windows-console-mode=disable --show-progress --lto=yes --jobs=4 --enable-plugins=pyqt6 --include-data-dir=./ui=./ui charmap-ng.py`

# <div align="left"> 开源许可 <div>
本软件以GPLv3许可证开源
