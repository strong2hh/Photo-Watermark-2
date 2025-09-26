import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLineEdit, QComboBox, QSlider, QColorDialog, QSpinBox, QGraphicsView, QGraphicsScene, QDialog
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont
from PyQt5.QtCore import Qt, QSize, QPointF
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
# 导入图片处理模块
from Picture_import import PhotoWatermarkApp
from Picture_export import show_export_dialog

class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('添加水印工具')
        self.resize(1000, 700)
        self.image_list = []
        self.current_image_path = None
        self.watermark_type = 'text'  # 'text' or 'image'
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        # 左侧图片列表
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(80, 80))
        self.list_widget.itemClicked.connect(self.on_image_selected)
        left_layout.addWidget(QLabel('图片列表'))
        left_layout.addWidget(self.list_widget)
        self.import_btn = QPushButton('导入图片')
        self.import_btn.clicked.connect(self.import_images)
        left_layout.addWidget(self.import_btn)
        layout.addLayout(left_layout)

        # 右侧主区域
        right_layout = QVBoxLayout()
        # 预览区
        self.preview_label = QLabel('预览区')
        self.preview_label.setFixedSize(600, 400)
        self.preview_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.preview_label)

        # 水印类型选择
        type_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(['文本水印', '图片水印'])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(QLabel('水印类型:'))
        type_layout.addWidget(self.type_combo)
        right_layout.addLayout(type_layout)

        # 文本水印设置
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText('输入水印文本')
        self.text_edit.textChanged.connect(self.update_preview)
        self.font_combo = QComboBox()
        self.font_combo.addItems(['Arial', 'SimSun', 'SimHei'])
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 100)
        self.font_size_spin.setValue(32)
        self.font_size_spin.valueChanged.connect(self.update_preview)
        self.color_btn = QPushButton('选择颜色')
        self.color_btn.clicked.connect(self.choose_color)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(80)
        self.opacity_slider.valueChanged.connect(self.update_preview)
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel('文本:'))
        text_layout.addWidget(self.text_edit)
        text_layout.addWidget(QLabel('字体:'))
        text_layout.addWidget(self.font_combo)
        text_layout.addWidget(QLabel('字号:'))
        text_layout.addWidget(self.font_size_spin)
        text_layout.addWidget(self.color_btn)
        text_layout.addWidget(QLabel('透明度:'))
        text_layout.addWidget(self.opacity_slider)
        right_layout.addLayout(text_layout)

        # 图片水印设置
        self.image_wm_btn = QPushButton('选择水印图片')
        self.image_wm_btn.clicked.connect(self.choose_watermark_image)
        self.image_wm_path = None
        self.image_wm_scale_slider = QSlider(Qt.Horizontal)
        self.image_wm_scale_slider.setRange(10, 200)
        self.image_wm_scale_slider.setValue(100)
        self.image_wm_scale_slider.valueChanged.connect(self.update_preview)
        self.image_wm_opacity_slider = QSlider(Qt.Horizontal)
        self.image_wm_opacity_slider.setRange(0, 100)
        self.image_wm_opacity_slider.setValue(80)
        self.image_wm_opacity_slider.valueChanged.connect(self.update_preview)
        img_layout = QHBoxLayout()
        img_layout.addWidget(self.image_wm_btn)
        img_layout.addWidget(QLabel('缩放:'))
        img_layout.addWidget(self.image_wm_scale_slider)
        img_layout.addWidget(QLabel('透明度:'))
        img_layout.addWidget(self.image_wm_opacity_slider)
        right_layout.addLayout(img_layout)
        # 默认只显示文本水印设置
        self.toggle_watermark_settings()

        # 九宫格布局
        grid_layout = QHBoxLayout()
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(['左上', '上中', '右上', '左中', '中心', '右中', '左下', '下中', '右下'])
        self.grid_combo.currentIndexChanged.connect(self.update_preview)
        grid_layout.addWidget(QLabel('水印位置:'))
        grid_layout.addWidget(self.grid_combo)
        right_layout.addLayout(grid_layout)

        # 旋转
        rotate_layout = QHBoxLayout()
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(0, 360)
        self.rotate_slider.setValue(0)
        self.rotate_slider.valueChanged.connect(self.update_preview)
        rotate_layout.addWidget(QLabel('旋转角度:'))
        rotate_layout.addWidget(self.rotate_slider)
        right_layout.addLayout(rotate_layout)

        # 导出按钮
        self.export_btn = QPushButton('导出水印图片')
        self.export_btn.clicked.connect(self.export_image)
        right_layout.addWidget(self.export_btn)

        layout.addLayout(right_layout)
        self.setLayout(layout)
        # 默认颜色
        self.wm_color = QColor(255, 255, 255)
        
        # 设置默认水印文本
        self.text_edit.setText('水印文本')
        
        # 初始化预览
        self.update_preview()

    def import_images(self):
        # 创建并显示 Picture_processing 的弹出窗口
        self.pp_window = PhotoWatermarkApp()
        self.pp_window.setWindowModality(Qt.ApplicationModal)  # 设置为模态窗口
        self.pp_window.setWindowTitle('导入图片 - 选择完成后点击"完成导入"')
        
        # 使用 exec() 方法显示模态对话框，这样会阻塞直到窗口关闭
        result = self.pp_window.exec()
        
        # 窗口关闭后同步图片列表（只有当用户点击"完成导入"时才同步）
        if result == QDialog.Accepted and hasattr(self.pp_window, 'image_list'):
            self.image_list = self.pp_window.image_list.copy()
            self.list_widget.clear()
            for f in self.image_list:
                item = QListWidgetItem(os.path.basename(f))
                icon = QIcon(QPixmap(f).scaled(80, 80, Qt.KeepAspectRatio))
                item.setIcon(icon)
                self.list_widget.addItem(item)
            if self.image_list:
                self.current_image_path = self.image_list[0]
                self.update_preview()

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
                for root, _, fs in os.walk(path):
                    for f in fs:
                        fpath = os.path.join(root, f)
                        if self.is_supported_image(fpath):
                            files.append(fpath)
            elif self.is_supported_image(path):
                files.append(path)
        self.image_list = []
        self.list_widget.clear()
        for f in files:
            item = QListWidgetItem(os.path.basename(f))
            icon = QIcon(QPixmap(f).scaled(80, 80, Qt.KeepAspectRatio))
            item.setIcon(icon)
            self.list_widget.addItem(item)
            self.image_list.append(f)
        if self.image_list:
            self.current_image_path = self.image_list[0]
            self.update_preview()

    def is_supported_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

    def on_image_selected(self, item):
        idx = self.list_widget.row(item)
        self.current_image_path = self.image_list[idx]
        self.update_preview()

    def on_type_changed(self, idx):
        self.watermark_type = 'text' if idx == 0 else 'image'
        self.toggle_watermark_settings()
        self.update_preview()

    def toggle_watermark_settings(self):
        # 控制文本/图片水印设置显示
        show_text = self.watermark_type == 'text'
        self.text_edit.setVisible(show_text)
        self.font_combo.setVisible(show_text)
        self.font_size_spin.setVisible(show_text)
        self.color_btn.setVisible(show_text)
        self.opacity_slider.setVisible(show_text)
        self.image_wm_btn.setVisible(not show_text)
        self.image_wm_scale_slider.setVisible(not show_text)
        self.image_wm_opacity_slider.setVisible(not show_text)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.wm_color = color
            self.update_preview()

    def choose_watermark_image(self):
        file, _ = QFileDialog.getOpenFileName(self, '选择水印图片', '', '图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff)')
        if file:
            self.image_wm_path = file
            self.update_preview()

    def get_grid_position(self, img_size, wm_size):
        # 九宫格位置计算
        w, h = img_size
        ww, wh = wm_size
        pos_map = {
            0: (0, 0),  # 左上
            1: ((w - ww)//2, 0),  # 上中
            2: (w - ww, 0),  # 右上
            3: (0, (h - wh)//2),  # 左中
            4: ((w - ww)//2, (h - wh)//2),  # 中
            5: (w - ww, (h - wh)//2),  # 右中
            6: (0, h - wh),  # 左下
            7: ((w - ww)//2, h - wh),  # 下中
            8: (w - ww, h - wh),  # 右下
        }
        idx = self.grid_combo.currentIndex()
        return pos_map.get(idx, (0, 0))

    def update_preview(self):
        if not self.current_image_path:
            self.preview_label.clear()
            self.preview_label.setText('请先导入图片')
            return
        img = Image.open(self.current_image_path).convert('RGBA')
        preview = img.copy()
        if self.watermark_type == 'text':
            text = self.text_edit.text().strip()
            if not text:  # 如果文本为空，使用默认文本
                text = "水印文本"
            font_name = self.font_combo.currentText()
            font_size = self.font_size_spin.value()
            opacity = self.opacity_slider.value() / 100.0
            color = self.wm_color
            # 字体路径（简化，实际可遍历系统字体）
            try:
                font = ImageFont.truetype(font_name + '.ttf', font_size)
            except:
                font = ImageFont.load_default()
            txt_img = Image.new('RGBA', preview.size, (255,255,255,0))
            draw = ImageDraw.Draw(txt_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = self.get_grid_position(preview.size, (w, h))
            # 旋转
            angle = self.rotate_slider.value()
            # 透明度
            fill = (color.red(), color.green(), color.blue(), int(255 * opacity))
            draw.text(pos, text, font=font, fill=fill)
            if angle != 0:
                txt_img = txt_img.rotate(angle, expand=1)
                # 确保旋转后的图像尺寸与预览图像匹配
                if txt_img.size != preview.size:
                    # 创建一个与预览图像相同尺寸的新图像
                    new_txt_img = Image.new('RGBA', preview.size, (255, 255, 255, 0))
                    # 将旋转后的文本图像居中放置
                    x = (preview.size[0] - txt_img.size[0]) // 2
                    y = (preview.size[1] - txt_img.size[1]) // 2
                    new_txt_img.paste(txt_img, (x, y), txt_img)
                    txt_img = new_txt_img
            preview = Image.alpha_composite(preview, txt_img)
        else:
            if self.image_wm_path:
                wm_img = Image.open(self.image_wm_path).convert('RGBA')
                scale = self.image_wm_scale_slider.value() / 100.0
                opacity = self.image_wm_opacity_slider.value() / 100.0
                w, h = wm_img.size
                wm_img = wm_img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
                # 透明度
                alpha = wm_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                wm_img.putalpha(alpha)
                pos = self.get_grid_position(preview.size, wm_img.size)
                angle = self.rotate_slider.value()
                if angle != 0:
                    wm_img = wm_img.rotate(angle, expand=1)
                    # 确保旋转后的水印图片尺寸与预览图像匹配
                    if wm_img.size != preview.size:
                        # 创建一个与预览图像相同尺寸的新图像
                        new_wm_img = Image.new('RGBA', preview.size, (255, 255, 255, 0))
                        # 将旋转后的水印图片居中放置
                        x = (preview.size[0] - wm_img.size[0]) // 2
                        y = (preview.size[1] - wm_img.size[1]) // 2
                        new_wm_img.paste(wm_img, (x, y), wm_img)
                        wm_img = new_wm_img
                tmp = Image.new('RGBA', preview.size, (255,255,255,0))
                tmp.paste(wm_img, pos, wm_img)
                preview = Image.alpha_composite(preview, tmp)
        # 显示预览
        qimg = QImage(preview.tobytes(), preview.size[0], preview.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio))

    def apply_watermark_to_image(self, image_path):
        """为单张图片添加水印"""
        img = Image.open(image_path).convert('RGBA')
        
        # 应用水印
        if self.watermark_type == 'text':
            text = self.text_edit.text().strip()
            if not text:  # 如果文本为空，使用默认文本
                text = "水印文本"
            font_name = self.font_combo.currentText()
            font_size = self.font_size_spin.value()
            opacity = self.opacity_slider.value() / 100.0
            color = self.wm_color
            
            try:
                font = ImageFont.truetype(font_name + '.ttf', font_size)
            except:
                font = ImageFont.load_default()
                
            txt_img = Image.new('RGBA', img.size, (255,255,255,0))
            draw = ImageDraw.Draw(txt_img)
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = self.get_grid_position(img.size, (w, h))
            
            angle = self.rotate_slider.value()
            fill = (color.red(), color.green(), color.blue(), int(255 * opacity))
            draw.text(pos, text, font=font, fill=fill)
            
            if angle != 0:
                txt_img = txt_img.rotate(angle, expand=1)
                if txt_img.size != img.size:
                    new_txt_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
                    x = (img.size[0] - txt_img.size[0]) // 2
                    y = (img.size[1] - txt_img.size[1]) // 2
                    new_txt_img.paste(txt_img, (x, y), txt_img)
                    txt_img = new_txt_img
            
            img = Image.alpha_composite(img, txt_img)
        else:
            if self.image_wm_path:
                wm_img = Image.open(self.image_wm_path).convert('RGBA')
                scale = self.image_wm_scale_slider.value() / 100.0
                opacity = self.image_wm_opacity_slider.value() / 100.0
                w, h = wm_img.size
                wm_img = wm_img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
                
                alpha = wm_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                wm_img.putalpha(alpha)
                
                pos = self.get_grid_position(img.size, wm_img.size)
                angle = self.rotate_slider.value()
                
                if angle != 0:
                    wm_img = wm_img.rotate(angle, expand=1)
                    if wm_img.size != img.size:
                        new_wm_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
                        x = (img.size[0] - wm_img.size[0]) // 2
                        y = (img.size[1] - wm_img.size[1]) // 2
                        new_wm_img.paste(wm_img, (x, y), wm_img)
                        wm_img = new_wm_img
                
                tmp = Image.new('RGBA', img.size, (255,255,255,0))
                tmp.paste(wm_img, pos, wm_img)
                img = Image.alpha_composite(img, tmp)
        
        return img

    def export_image(self):
        if not self.image_list:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, '警告', '请先导入图片！')
            return
        
        # 为所有图片添加水印
        watermarked_images = []
        for image_path in self.image_list:
            watermarked_img = self.apply_watermark_to_image(image_path)
            watermarked_images.append(watermarked_img)
        
        # 使用导出对话框保存图片
        result = show_export_dialog(self.image_list, watermarked_images, self)
        if result == QDialog.Accepted:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, '完成', '水印图片导出成功！')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec_())
