import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLineEdit, QComboBox, QSlider, QCheckBox, QSpinBox
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QSize
from PIL import Image
import shutil

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

class ImageItem(QListWidgetItem):
    def __init__(self, image_path):
        super().__init__(os.path.basename(image_path))
        self.image_path = image_path

class PhotoWatermarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('图片批量处理工具')
        self.resize(900, 600)
        self.image_list = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # 导入图片按钮
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
        layout.addWidget(QLabel('已导入图片列表：'))
        layout.addWidget(self.list_widget)

        # 导出设置
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel('输出文件夹:'))
        self.output_folder_edit = QLineEdit()
        self.output_folder_btn = QPushButton('选择')
        self.output_folder_btn.clicked.connect(self.select_output_folder)
        export_layout.addWidget(self.output_folder_edit)
        export_layout.addWidget(self.output_folder_btn)
        layout.addLayout(export_layout)

        # 命名规则
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel('命名规则:'))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText('前缀 (如 wm_)')
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText('后缀 (如 _watermarked)')
        naming_layout.addWidget(self.prefix_edit)
        naming_layout.addWidget(self.suffix_edit)
        layout.addLayout(naming_layout)

        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('输出格式:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPEG', 'PNG'])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # JPEG质量调节
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(90)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        layout.addWidget(QLabel('JPEG质量调节 (仅JPEG有效):'))
        layout.addWidget(self.quality_slider)

        # 尺寸调整
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel('宽度:'))
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(0)
        self.width_spin.setMaximum(10000)
        self.width_spin.setValue(0)
        resize_layout.addWidget(self.width_spin)
        resize_layout.addWidget(QLabel('高度:'))
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(0)
        self.height_spin.setMaximum(10000)
        self.height_spin.setValue(0)
        resize_layout.addWidget(self.height_spin)
        resize_layout.addWidget(QLabel('百分比缩放:'))
        self.percent_spin = QSpinBox()
        self.percent_spin.setMinimum(0)
        self.percent_spin.setMaximum(100)
        self.percent_spin.setValue(100)
        resize_layout.addWidget(self.percent_spin)
        layout.addLayout(resize_layout)

        # 导出按钮
        self.export_btn = QPushButton('导出图片')
        self.export_btn.clicked.connect(self.export_images)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)

        # 支持拖拽
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.import_folder(path)
            elif self.is_supported_image(path):
                self.add_image(path)

    def is_supported_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_FORMATS

    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, '选择图片', '',
                                                '图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff)')
        for f in files:
            if self.is_supported_image(f):
                self.add_image(f)

    def import_folder(self, folder=None):
        if not folder:
            folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            for root, _, files in os.walk(folder):
                for f in files:
                    path = os.path.join(root, f)
                    if self.is_supported_image(path):
                        self.add_image(path)

    def add_image(self, path):
        if path not in self.image_list:
            item = ImageItem(path)
            pixmap = QPixmap(path)
            icon = QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            item.setIcon(icon)
            self.list_widget.addItem(item)
            self.image_list.append(path)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择输出文件夹')
        if folder:
            self.output_folder_edit.setText(folder)

    def export_images(self):
        output_folder = self.output_folder_edit.text().strip()
        if not output_folder:
            self.show_message('请先选择输出文件夹')
            return
        # 禁止导出到原文件夹
        for img_path in self.image_list:
            if os.path.dirname(img_path) == output_folder:
                self.show_message('禁止导出到原文件夹！')
                return
        prefix = self.prefix_edit.text().strip()
        suffix = self.suffix_edit.text().strip()
        fmt = self.format_combo.currentText()
        quality = self.quality_slider.value()
        width = self.width_spin.value()
        height = self.height_spin.value()
        percent = self.percent_spin.value()
        for img_path in self.image_list:
            img = Image.open(img_path)
            # PNG透明通道支持
            if fmt == 'PNG' and img.mode in ('RGBA', 'LA'):
                pass
            # 尺寸调整
            if percent != 100:
                w, h = img.size
                img = img.resize((int(w * percent / 100), int(h * percent / 100)), Image.Resampling.LANCZOS)
            elif width > 0 and height > 0:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            # 命名规则
            base, ext = os.path.splitext(os.path.basename(img_path))
            new_name = f"{prefix}{base}{suffix}.{fmt.lower()}"
            out_path = os.path.join(output_folder, new_name)
            if fmt == 'JPEG':
                img = img.convert('RGB')
                img.save(out_path, 'JPEG', quality=quality)
            else:
                img.save(out_path, 'PNG')
        self.show_message('导出完成！')

    def show_message(self, msg):
        dlg = QLabel(msg)
        dlg.setWindowTitle('提示')
        dlg.setAlignment(Qt.AlignCenter)
        dlg.setFixedSize(200, 100)
        dlg.show()
        # 自动关闭
        # QTimer 需导入
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, dlg.close)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoWatermarkApp()
    window.show()
    sys.exit(app.exec_())
