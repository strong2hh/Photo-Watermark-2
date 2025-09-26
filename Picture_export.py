import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QSlider, QSpinBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PIL import Image

class PictureProcessingDialog(QDialog):
    def __init__(self, image_list, watermarked_images=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图片导出设置')
        self.resize(500, 400)
        self.image_list = image_list
        self.watermarked_images = watermarked_images
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel('水印图片导出设置')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; margin: 10px;')
        layout.addWidget(title_label)
        
        # 输出文件夹设置
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel('输出文件夹:'))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText('选择输出文件夹...')
        self.output_folder_btn = QPushButton('选择')
        self.output_folder_btn.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(self.output_folder_edit)
        folder_layout.addWidget(self.output_folder_btn)
        layout.addLayout(folder_layout)
        
        # 命名规则
        naming_layout = QVBoxLayout()
        naming_layout.addWidget(QLabel('命名规则:'))
        
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel('前缀:'))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText('如: wm_')
        prefix_layout.addWidget(self.prefix_edit)
        naming_layout.addLayout(prefix_layout)
        
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel('后缀:'))
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText('如: _watermarked')
        suffix_layout.addWidget(self.suffix_edit)
        naming_layout.addLayout(suffix_layout)
        
        layout.addLayout(naming_layout)
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('输出格式:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPEG', 'PNG'])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # JPEG质量调节
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel('JPEG质量 (0-100):'))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(90)
        self.quality_slider.setTickInterval(10)
        self.quality_label = QLabel('90')
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        layout.addLayout(quality_layout)
        
        # 尺寸调整
        resize_layout = QVBoxLayout()
        resize_layout.addWidget(QLabel('尺寸调整:'))
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel('宽度:'))
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(0)
        self.width_spin.setMaximum(10000)
        self.width_spin.setValue(0)
        self.width_spin.setSpecialValueText('保持原尺寸')
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel('高度:'))
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(0)
        self.height_spin.setMaximum(10000)
        self.height_spin.setValue(0)
        self.height_spin.setSpecialValueText('保持原尺寸')
        size_layout.addWidget(self.height_spin)
        resize_layout.addLayout(size_layout)
        
        percent_layout = QHBoxLayout()
        percent_layout.addWidget(QLabel('百分比缩放:'))
        self.percent_spin = QSpinBox()
        self.percent_spin.setMinimum(1)
        self.percent_spin.setMaximum(500)
        self.percent_spin.setValue(100)
        self.percent_spin.setSuffix('%')
        percent_layout.addWidget(self.percent_spin)
        resize_layout.addLayout(percent_layout)
        
        layout.addLayout(resize_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        self.export_btn = QPushButton('开始导出')
        self.export_btn.clicked.connect(self.export_images)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 初始化状态
        self.on_format_changed('JPEG')

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择输出文件夹')
        if folder:
            self.output_folder_edit.setText(folder)

    def on_format_changed(self, format_text):
        # 根据格式显示/隐藏质量调节
        if format_text == 'JPEG':
            self.quality_slider.setEnabled(True)
            self.quality_label.setEnabled(True)
        else:
            self.quality_slider.setEnabled(False)
            self.quality_label.setEnabled(False)

    def on_quality_changed(self, value):
        self.quality_label.setText(str(value))

    def export_images(self):
        output_folder = self.output_folder_edit.text().strip()
        if not output_folder:
            QMessageBox.warning(self, '警告', '请选择输出文件夹！')
            return
            
        # 检查是否导出到原文件夹
        for img_path in self.image_list:
            if os.path.dirname(img_path) == output_folder:
                QMessageBox.warning(self, '警告', '禁止导出到原文件夹！请选择其他输出文件夹。')
                return
        
        prefix = self.prefix_edit.text().strip()
        suffix = self.suffix_edit.text().strip()
        fmt = self.format_combo.currentText()
        quality = self.quality_slider.value()
        width = self.width_spin.value()
        height = self.height_spin.value()
        percent = self.percent_spin.value()
        
        success_count = 0
        error_count = 0
        
        for i, img_path in enumerate(self.image_list):
            try:
                # 如果有带水印的图片数据，使用它；否则打开原始图片
                if self.watermarked_images and i < len(self.watermarked_images):
                    img = self.watermarked_images[i]
                else:
                    img = Image.open(img_path)
                
                # 尺寸调整
                if percent != 100:
                    # 百分比缩放
                    w, h = img.size
                    new_width = int(w * percent / 100)
                    new_height = int(h * percent / 100)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                elif width > 0 and height > 0:
                    # 指定宽高
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                elif width > 0:
                    # 仅指定宽度，保持宽高比
                    w, h = img.size
                    new_height = int(h * width / w)
                    img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                elif height > 0:
                    # 仅指定高度，保持宽高比
                    w, h = img.size
                    new_width = int(w * height / h)
                    img = img.resize((new_width, height), Image.Resampling.LANCZOS)
                
                # 命名规则
                base_name = os.path.basename(img_path)
                name, ext = os.path.splitext(base_name)
                new_name = f"{prefix}{name}{suffix}.{fmt.lower()}"
                output_path = os.path.join(output_folder, new_name)
                
                # 保存图片
                if fmt == 'JPEG':
                    # JPEG格式需要转换为RGB模式
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(output_path, 'JPEG', quality=quality, optimize=True)
                else:
                    # PNG格式保持原模式
                    img.save(output_path, 'PNG', optimize=True)
                
                success_count += 1
                
            except Exception as e:
                print(f"导出图片失败: {img_path}, 错误: {e}")
                error_count += 1
        
        # 显示导出结果
        if error_count == 0:
            QMessageBox.information(self, '导出完成', 
                                   f'成功导出 {success_count} 张图片到:\n{output_folder}')
            self.accept()
        else:
            QMessageBox.warning(self, '导出结果', 
                              f'成功导出 {success_count} 张图片\n失败 {error_count} 张图片')

def show_export_dialog(image_list, watermarked_images=None, parent=None):
    """显示导出对话框的便捷函数"""
    dialog = PictureProcessingDialog(image_list, watermarked_images, parent)
    return dialog.exec()

if __name__ == '__main__':
    # 测试代码
    app = QApplication(sys.argv)
    # 模拟图片列表
    test_images = ['test1.jpg', 'test2.png']
    dialog = PictureProcessingDialog(test_images)
    result = dialog.exec()
    sys.exit(0)