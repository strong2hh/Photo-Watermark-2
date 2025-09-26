import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLineEdit, QComboBox, QSlider, QDialog
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QMouseEvent
from PyQt5.QtCore import Qt, QSize, QPoint
from PIL import Image, ImageDraw, ImageFont
from Picture_import import PhotoWatermarkApp
from Picture_export import show_export_dialog

class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('添加水印工具')
        self.resize(800, 600)
        self.image_list = []
        self.current_image_path = None
        self.drag_position = QPoint(100, 100)  # 拖拽位置
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
        
        # 预览区（支持拖拽）
        self.preview_label = QLabel('预览区')
        self.preview_label.setFixedSize(500, 400)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        self.preview_label.mousePressEvent = self.preview_mouse_press
        self.preview_label.mouseMoveEvent = self.preview_mouse_move
        self.preview_label.mouseReleaseEvent = self.preview_mouse_release
        right_layout.addWidget(self.preview_label)

        # 文本水印设置
        text_layout = QHBoxLayout()
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText('输入水印文本')
        self.text_edit.setText('水印文本')
        self.text_edit.textChanged.connect(self.update_preview)
        text_layout.addWidget(QLabel('水印文本:'))
        text_layout.addWidget(self.text_edit)
        right_layout.addLayout(text_layout)

        # 九宫格布局
        grid_layout = QHBoxLayout()
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(['左上', '上中', '右上', '左中', '中心', '右中', '左下', '下中', '右下'])
        self.grid_combo.currentIndexChanged.connect(self.update_preview)
        grid_layout.addWidget(QLabel('预设位置:'))
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
        
        # 初始化预览
        self.update_preview()

    def import_images(self):
        # 创建并显示 Picture_import 的弹出窗口
        self.pp_window = PhotoWatermarkApp()
        self.pp_window.setWindowModality(Qt.ApplicationModal)
        self.pp_window.setWindowTitle('导入图片 - 选择完成后点击"完成导入"')
        
        result = self.pp_window.exec()
        
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
                self.drag_position = QPoint(100, 100)  # 重置拖拽位置
                self.update_preview()

    def is_supported_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

    def on_image_selected(self, item):
        idx = self.list_widget.row(item)
        self.current_image_path = self.image_list[idx]
        self.drag_position = QPoint(100, 100)  # 重置拖拽位置
        self.update_preview()

    # 移除颜色选择功能

    def get_grid_position(self, img_size, wm_size):
        """获取九宫格位置"""
        w, h = img_size
        ww, wh = wm_size
        pos_map = {
            0: (0, 0),  # 左上
            1: ((w - ww)//2, 0),  # 上中
            2: (w - ww, 0),  # 右上
            3: (0, (h - wh)//2),  # 左中
            4: ((w - ww)//2, (h - wh)//2),  # 中心
            5: (w - ww, (h - wh)//2),  # 右中
            6: (0, h - wh),  # 左下
            7: ((w - ww)//2, h - wh),  # 下中
            8: (w - ww, h - wh),  # 右下
        }
        idx = self.grid_combo.currentIndex()
        return pos_map.get(idx, (0, 0))

    def get_drag_position(self, img_size, wm_size):
        """获取拖拽位置"""
        w, h = img_size
        ww, wh = wm_size
        # 确保水印在图片范围内
        x = max(0, min(self.drag_position.x(), w - ww))
        y = max(0, min(self.drag_position.y(), h - wh))
        return (x, y)

    # 鼠标事件处理 - 拖拽功能
    def preview_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()
            self.dragging = True

    def preview_mouse_move(self, event: QMouseEvent):
        if hasattr(self, 'dragging') and self.dragging:
            # 更新拖拽位置
            delta = event.pos() - self.drag_start
            self.drag_position += delta
            self.drag_start = event.pos()
            self.update_preview()

    def preview_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def update_preview(self):
        if not self.current_image_path:
            self.preview_label.clear()
            self.preview_label.setText('请先导入图片')
            return
            
        img = Image.open(self.current_image_path).convert('RGBA')
        preview = img.copy()
        
        # 获取水印文本
        text = self.text_edit.text().strip()
        if not text:
            text = "水印文本"
            
        # 使用默认字体设置
        try:
            # 尝试加载系统字体，设置合适的大小
            font = ImageFont.truetype("arial.ttf", 128)  # 使用128号字体
        except:
            # 如果失败，使用默认字体但设置更大尺寸
            font = ImageFont.load_default()
            # 对于默认字体，我们需要使用更大的尺寸
        opacity = 0.8  # 默认透明度80%
        color = (255, 255, 255, int(255 * opacity))  # 默认白色
            
        # 计算文本尺寸
        # 先创建一个临时图像来计算文本尺寸
        temp_img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # 获取位置
        if hasattr(self, 'dragging') and self.dragging:
            # 使用拖拽位置
            pos = self.get_drag_position(preview.size, (w, h))
        else:
            # 使用九宫格位置
            pos = self.get_grid_position(preview.size, (w, h))
            # 同步拖拽位置到九宫格位置
            self.drag_position = QPoint(pos[0], pos[1])
        
        # 旋转
        angle = self.rotate_slider.value()
        
        # 创建水印图层（包含文本的完整尺寸）
        txt_img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_img)
        
        # 绘制文本到水印图层（考虑基线偏移）
        draw.text((-bbox[0], -bbox[1]), text, font=font, fill=color)
        
        # 应用旋转（围绕水印自身中心）
        if angle != 0:
            txt_img = txt_img.rotate(angle, expand=1, center=(w//2, h//2))
        
        # 将旋转后的水印放置到正确位置
        final_img = Image.new('RGBA', preview.size, (255, 255, 255, 0))
        final_img.paste(txt_img, pos, txt_img)
        txt_img = final_img
        
        # 合成图片
        preview = Image.alpha_composite(preview, txt_img)
        
        # 显示预览
        qimg = QImage(preview.tobytes(), preview.size[0], preview.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio))

    def apply_watermark_to_image(self, image_path):
        """为单张图片添加水印"""
        img = Image.open(image_path).convert('RGBA')
        
        # 获取水印文本
        text = self.text_edit.text().strip()
        if not text:
            text = "水印文本"
            
        # 使用默认字体设置
        try:
            # 尝试加载系统字体，设置合适的大小
            font = ImageFont.truetype("arial.ttf", 128)  # 使用128号字体
        except:
            # 如果失败，使用默认字体但设置更大尺寸
            font = ImageFont.load_default()
            # 对于默认字体，我们需要使用更大的尺寸
        opacity = 0.8  # 默认透明度80%
        color = (255, 255, 255, int(255 * opacity))  # 默认白色
            
        # 计算文本尺寸
        temp_img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # 获取位置（使用当前拖拽位置）
        pos = self.get_drag_position(img.size, (w, h))
        
        # 旋转
        angle = self.rotate_slider.value()
        
        # 创建水印图层（包含文本的完整尺寸）
        txt_img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_img)
        
        # 绘制文本到水印图层（考虑基线偏移）
        draw.text((-bbox[0], -bbox[1]), text, font=font, fill=color)
        
        # 应用旋转（围绕水印自身中心）
        if angle != 0:
            txt_img = txt_img.rotate(angle, expand=1, center=(w//2, h//2))
        
        # 将旋转后的水印放置到正确位置
        final_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
        final_img.paste(txt_img, pos, txt_img)
        txt_img = final_img
        
        # 合成图片
        img = Image.alpha_composite(img, txt_img)
        
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