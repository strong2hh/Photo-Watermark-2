import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

class ImageItem(QListWidgetItem):
    def __init__(self, image_path):
        super().__init__(os.path.basename(image_path))
        self.image_path = image_path

class PhotoWatermarkApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('图片导入工具')
        self.resize(700, 500)
        self.image_list = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题和说明
        title_label = QLabel('图片导入工具')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; margin: 10px;')
        layout.addWidget(title_label)
        
        desc_label = QLabel('支持拖拽单张图片或批量导入文件夹，支持格式: JPEG, PNG, BMP, TIFF')
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet('color: #666; margin-bottom: 10px;')
        layout.addWidget(desc_label)

        # 导入按钮区域
        import_layout = QHBoxLayout()
        self.import_btn = QPushButton('导入图片')
        self.import_btn.clicked.connect(self.import_images)
        self.import_folder_btn = QPushButton('导入文件夹')
        self.import_folder_btn.clicked.connect(self.import_folder)
        import_layout.addWidget(self.import_btn)
        import_layout.addWidget(self.import_folder_btn)
        layout.addLayout(import_layout)

        # 图片列表
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(100, 100))
        self.list_widget.setSpacing(10)
        layout.addWidget(QLabel('已导入图片列表:'))
        layout.addWidget(self.list_widget)

        # 底部按钮
        button_layout = QHBoxLayout()
        self.clear_btn = QPushButton('清空列表')
        self.clear_btn.clicked.connect(self.clear_images)
        self.close_btn = QPushButton('完成导入')
        self.close_btn.clicked.connect(self.close_and_sync)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 支持拖拽
        self.setAcceptDrops(True)
        
    def close_and_sync(self):
        # 关闭窗口并返回接受结果
        self.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                # 导入整个文件夹
                for root, _, fs in os.walk(path):
                    for f in fs:
                        fpath = os.path.join(root, f)
                        if self.is_supported_image(fpath):
                            files.append(fpath)
            elif self.is_supported_image(path):
                # 导入单张图片
                files.append(path)
        
        if files:
            self.add_images(files)

    def is_supported_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_FORMATS

    def import_images(self):
        # 弹出文件选择器，支持多选
        files, _ = QFileDialog.getOpenFileNames(self, '选择图片', '',
                                                '图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)')
        if files:
            self.add_images(files)

    def import_folder(self):
        # 选择文件夹
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if folder:
            files = []
            for root, _, fs in os.walk(folder):
                for f in fs:
                    path = os.path.join(root, f)
                    if self.is_supported_image(path):
                        files.append(path)
            if files:
                self.add_images(files)

    def add_images(self, files):
        for f in files:
            if os.path.isfile(f) and self.is_supported_image(f) and f not in self.image_list:
                self.add_image(f)

    def add_image(self, path):
        item = ImageItem(path)
        pixmap = QPixmap(path)
        icon = QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        item.setIcon(icon)
        self.list_widget.addItem(item)
        self.image_list.append(path)

    def clear_images(self):
        self.list_widget.clear()
        self.image_list.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoWatermarkApp()
    window.show()
    sys.exit(app.exec_())
