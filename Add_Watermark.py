import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLineEdit, QComboBox, QSlider, QDialog, QCheckBox, QColorDialog, QInputDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QMouseEvent
from PyQt5.QtCore import Qt, QSize, QPoint
from PIL import Image, ImageDraw, ImageFont
from Picture_import import PhotoWatermarkApp
from Picture_export import show_export_dialog
from template_manager import TemplateManager, create_template_data_from_app, apply_template_to_app

class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('添加水印工具')
        self.resize(800, 600)
        self.image_list = []
        self.current_image_path = None
        self.drag_position = QPoint(100, 100)  # 拖拽位置
        self.text_color = QColor(255, 255, 255)  # 默认白色
        self.scale_factor = 1.0  # 缩放因子
        self.template_manager = TemplateManager()  # 模板管理器
        self.init_ui()
        self.load_last_settings()  # 加载上次设置
        
        # 初始化内部状态变量
        self.current_text = "watermark"
        self.current_font_name = "Arial"
        self.current_font_size = 96
        self.current_bold = False
        self.current_italic = False
        self.current_opacity = 80
        self.current_rotation = 0
        self.current_scale = 200
        self.current_shadow_enabled = False
        self.current_stroke_enabled = False
        self.current_grid_position = 4
        self.current_image_opacity = 80
        self.current_image_scale = 100

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

        # 水印类型选择
        type_layout = QHBoxLayout()
        self.watermark_type = 'text'  # 默认文本水印
        self.text_radio = QCheckBox('文本水印')
        self.text_radio.setChecked(True)
        self.text_radio.toggled.connect(self.toggle_watermark_type)
        type_layout.addWidget(self.text_radio)
        
        self.image_radio = QCheckBox('图片水印')
        self.image_radio.toggled.connect(self.toggle_watermark_type)
        type_layout.addWidget(self.image_radio)
        right_layout.addLayout(type_layout)

        # 文本水印设置容器
        self.text_settings_widget = QWidget()
        self.text_settings = QVBoxLayout(self.text_settings_widget)
        text_layout = QHBoxLayout()
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText('输入水印文本')
        self.text_edit.setText('watermark')
        self.text_edit.textChanged.connect(self.update_preview)
        text_layout.addWidget(QLabel('水印文本:'))
        text_layout.addWidget(self.text_edit)
        self.text_settings.addLayout(text_layout)

        # 图片水印设置容器
        self.image_settings_widget = QWidget()
        self.image_settings = QVBoxLayout(self.image_settings_widget)
        image_select_layout = QHBoxLayout()
        self.image_path_label = QLabel('未选择图片')
        self.select_image_btn = QPushButton('选择图片')
        self.select_image_btn.clicked.connect(self.select_watermark_image)
        image_select_layout.addWidget(QLabel('水印图片:'))
        image_select_layout.addWidget(self.image_path_label)
        image_select_layout.addWidget(self.select_image_btn)
        self.image_settings.addLayout(image_select_layout)

        # 图片水印透明度
        image_opacity_layout = QHBoxLayout()
        self.image_opacity_slider = QSlider(Qt.Horizontal)
        self.image_opacity_slider.setRange(0, 100)
        self.image_opacity_slider.setValue(80)
        self.image_opacity_slider.valueChanged.connect(self.update_preview)
        image_opacity_layout.addWidget(QLabel('图片透明度:'))
        image_opacity_layout.addWidget(self.image_opacity_slider)
        self.image_opacity_label = QLabel('80%')
        image_opacity_layout.addWidget(self.image_opacity_label)
        self.image_settings.addLayout(image_opacity_layout)

        # 图片水印缩放
        image_scale_layout = QHBoxLayout()
        self.image_scale_slider = QSlider(Qt.Horizontal)
        self.image_scale_slider.setRange(10, 500)  # 10% 到 500%
        self.image_scale_slider.setValue(100)
        self.image_scale_slider.valueChanged.connect(self.update_preview)
        image_scale_layout.addWidget(QLabel('图片缩放:'))
        image_scale_layout.addWidget(self.image_scale_slider)
        self.image_scale_label = QLabel('100%')
        image_scale_layout.addWidget(self.image_scale_label)
        self.image_settings.addLayout(image_scale_layout)

        right_layout.addWidget(self.text_settings_widget)
        right_layout.addWidget(self.image_settings_widget)
        self.image_settings_widget.setVisible(False)  # 默认隐藏图片水印设置

        # 字体设置
        font_layout = QHBoxLayout()
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Times New Roman", "SimHei", "Microsoft YaHei", "SimSun"])
        self.font_combo.currentIndexChanged.connect(self.update_preview)
        font_layout.addWidget(QLabel('字体:'))
        font_layout.addWidget(self.font_combo)
        
        self.font_size_spin = QComboBox()
        self.font_size_spin.addItems(["96", "128", "160", "192", "256", "320", "480", "640"])
        self.font_size_spin.setCurrentText("96")
        self.font_size_spin.currentIndexChanged.connect(self.update_preview)
        font_layout.addWidget(QLabel('字号:'))
        font_layout.addWidget(self.font_size_spin)
        
        self.bold_check = QCheckBox('粗体')
        self.bold_check.stateChanged.connect(self.update_preview)
        font_layout.addWidget(self.bold_check)
        
        self.italic_check = QCheckBox('斜体')
        self.italic_check.stateChanged.connect(self.update_preview)
        font_layout.addWidget(self.italic_check)
        
        right_layout.addLayout(font_layout)

        # 颜色和透明度
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton('选择颜色')
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(QLabel('颜色:'))
        color_layout.addWidget(self.color_btn)
        
        self.color_label = QLabel()
        self.color_label.setFixedSize(30, 30)
        self.color_label.setStyleSheet("background-color: white; border: 1px solid black;")
        color_layout.addWidget(self.color_label)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(80)
        self.opacity_slider.valueChanged.connect(self.update_preview)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        color_layout.addWidget(QLabel('透明度:'))
        color_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel('80%')
        color_layout.addWidget(self.opacity_label)
        
        right_layout.addLayout(color_layout)

        # 阴影和描边效果
        effect_layout = QHBoxLayout()
        self.shadow_check = QCheckBox('阴影效果')
        self.shadow_check.stateChanged.connect(self.update_preview)
        effect_layout.addWidget(self.shadow_check)
        
        self.stroke_check = QCheckBox('描边效果')
        self.stroke_check.stateChanged.connect(self.update_preview)
        effect_layout.addWidget(self.stroke_check)
        
        right_layout.addLayout(effect_layout)

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

        # 缩放控制
        scale_layout = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 1000)  # 50% 到 1000%
        self.scale_slider.setValue(200)
        self.scale_slider.valueChanged.connect(self.update_preview)
        self.scale_slider.valueChanged.connect(self.update_scale_label)
        scale_layout.addWidget(QLabel('缩放比例:'))
        scale_layout.addWidget(self.scale_slider)
        
        self.scale_label = QLabel('200%')
        scale_layout.addWidget(self.scale_label)
        right_layout.addLayout(scale_layout)

        # 模板管理区域
        template_layout = QHBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(150)
        self.template_combo.currentTextChanged.connect(self.on_template_selected)
        template_layout.addWidget(QLabel('模板:'))
        template_layout.addWidget(self.template_combo)
        
        self.save_template_btn = QPushButton('保存模板')
        self.save_template_btn.clicked.connect(self.save_template)
        template_layout.addWidget(self.save_template_btn)
        
        self.load_template_btn = QPushButton('加载模板')
        self.load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(self.load_template_btn)
        
        self.delete_template_btn = QPushButton('删除模板')
        self.delete_template_btn.clicked.connect(self.delete_template)
        template_layout.addWidget(self.delete_template_btn)
        
        right_layout.addLayout(template_layout)

        # 导出按钮
        self.export_btn = QPushButton('导出水印图片')
        self.export_btn.clicked.connect(self.export_image)
        right_layout.addWidget(self.export_btn)

        layout.addLayout(right_layout)
        self.setLayout(layout)
        
        # 初始化图片水印相关变量
        self.watermark_image_path = None
        self.watermark_image = None
        
        # 加载模板列表
        self.refresh_template_list()

    def toggle_watermark_type(self):
        """切换水印类型"""
        if self.text_radio.isChecked():
            self.watermark_type = 'text'
            self.text_settings_widget.setVisible(True)
            self.image_settings_widget.setVisible(False)
        elif self.image_radio.isChecked():
            self.watermark_type = 'image'
            self.text_settings_widget.setVisible(False)
            self.image_settings_widget.setVisible(True)
        # 强制更新预览
        self.update_preview()

    def select_watermark_image(self):
        """选择水印图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择水印图片', '', 
            '图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;PNG文件 (*.png)'
        )
        if file_path:
            self.watermark_image_path = file_path
            self.image_path_label.setText(os.path.basename(file_path))
            try:
                # 加载水印图片
                self.watermark_image = Image.open(file_path).convert('RGBA')
                self.update_preview()
            except Exception as e:
                self.image_path_label.setText('加载失败')
                self.update_preview()

    def refresh_template_list(self):
        """刷新模板列表"""
        self.template_combo.clear()
        templates = self.template_manager.get_template_list()
        self.template_combo.addItem("-- 选择模板 --", "")
        for template in templates:
            self.template_combo.addItem(template["name"], template["name"])
        
        # 设置最后使用的模板
        last_used = self.template_manager.load_last_used_template()
        if last_used and self.template_manager.template_exists(last_used):
            index = self.template_combo.findData(last_used)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)

    def on_template_selected(self, template_name):
        """模板选择事件"""
        if template_name and template_name != "-- 选择模板 --":
            self.load_template_by_name(template_name)

    def save_template(self):
        """保存模板"""
        template_name, ok = QInputDialog.getText(
            self, '保存模板', '请输入模板名称:',
            text=f"模板_{len(self.template_manager.get_template_list()) + 1}"
        )
        
        if ok and template_name:
            if self.template_manager.template_exists(template_name):
                reply = QMessageBox.question(
                    self, '模板已存在', 
                    f'模板 "{template_name}" 已存在，是否覆盖？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # 创建模板数据
            template_data = create_template_data_from_app(self)
            self.template_manager.save_template(template_name, template_data)
            self.template_manager.save_last_used_template(template_name)
            
            # 刷新模板列表
            self.refresh_template_list()
            QMessageBox.information(self, '成功', f'模板 "{template_name}" 保存成功！')

    def load_template(self):
        """加载模板"""
        current_template = self.template_combo.currentData()
        if current_template:
            self.load_template_by_name(current_template)
        else:
            QMessageBox.warning(self, '警告', '请先选择一个模板！')

    def load_template_by_name(self, template_name):
        """根据名称加载模板"""
        template_data = self.template_manager.load_template(template_name)
        if template_data:
            # 应用模板数据
            apply_template_to_app(template_data, self)
            
            # 更新内部状态变量
            self.current_text = template_data["text_content"]
            self.current_font_name = template_data["font_name"]
            self.current_font_size = template_data["font_size"]
            self.current_bold = template_data["bold"]
            self.current_italic = template_data["italic"]
            self.current_opacity = template_data["opacity"]
            self.current_rotation = template_data["rotation"]
            self.current_scale = template_data["scale"]
            self.current_shadow_enabled = template_data["shadow_enabled"]
            self.current_stroke_enabled = template_data["stroke_enabled"]
            self.current_grid_position = template_data["grid_position"]
            self.current_image_opacity = template_data["image_opacity"]
            self.current_image_scale = template_data["image_scale"]
            
            self.template_manager.save_last_used_template(template_name)
            self.update_preview()
            QMessageBox.information(self, '成功', f'模板 "{template_name}" 加载成功！')
        else:
            QMessageBox.warning(self, '错误', f'模板 "{template_name}" 加载失败！')

    def delete_template(self):
        """删除模板"""
        template_name = self.template_combo.currentData()
        if not template_name:
            QMessageBox.warning(self, '警告', '请先选择一个模板！')
            return
        
        reply = QMessageBox.question(
            self, '确认删除', 
            f'确定要删除模板 "{template_name}" 吗？',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.template_manager.delete_template(template_name):
                self.refresh_template_list()
                QMessageBox.information(self, '成功', f'模板 "{template_name}" 删除成功！')
            else:
                QMessageBox.warning(self, '错误', f'模板 "{template_name}" 删除失败！')

    def load_last_settings(self):
        """加载上次设置"""
        # 尝试加载最后使用的模板
        last_template = self.template_manager.load_last_used_template()
        if last_template and self.template_manager.template_exists(last_template):
            template_data = self.template_manager.load_template(last_template)
            if template_data:
                apply_template_to_app(template_data, self)
                return
        
        # 如果没有模板，加载当前设置
        current_settings = self.template_manager.load_current_settings()
        if current_settings:
            apply_template_to_app(current_settings, self)

    def closeEvent(self, event):
        """程序关闭事件 - 保存当前设置"""
        template_data = create_template_data_from_app(self)
        self.template_manager.save_current_settings(template_data)
        event.accept()

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

    # 鼠标事件处理 - 拖拽和缩放功能
    def preview_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start = event.pos()
            self.dragging = True
        elif event.button() == Qt.RightButton:
            self.scale_start = event.pos()
            self.scaling = True

    def preview_mouse_move(self, event: QMouseEvent):
        if hasattr(self, 'dragging') and self.dragging:
            # 更新拖拽位置
            delta = event.pos() - self.drag_start
            self.drag_position += delta
            self.drag_start = event.pos()
            self.update_preview()
        elif hasattr(self, 'scaling') and self.scaling:
            # 更新缩放比例（右键拖拽垂直方向）
            delta_y = event.pos().y() - self.scale_start.y()
            scale_change = delta_y / 10.0  # 每10像素改变1%
            new_scale = max(50, min(1000, self.scale_slider.value() - scale_change))
            self.scale_slider.setValue(int(new_scale))
            self.scale_start = event.pos()

    def preview_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
        elif event.button() == Qt.RightButton:
            self.scaling = False

    def choose_color(self):
        color = QColorDialog.getColor(self.text_color, self, "选择水印颜色")
        if color.isValid():
            self.text_color = color
            self.color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            self.update_preview()

    def update_opacity_label(self, value):
        self.opacity_label.setText(f"{value}%")

    def update_scale_label(self, value):
        self.scale_label.setText(f"{value}%")

    def get_font_style(self):
        """获取字体样式设置"""
        # 优先使用控件的当前值，确保实时更新
        font_name = self.font_combo.currentText()
        font_size = int(self.font_size_spin.currentText())
        
        # 构建字体样式字符串
        style = ""
        bold = self.bold_check.isChecked()
        italic = self.italic_check.isChecked()
        
        if bold:
            style += "bold "
        if italic:
            style += "italic "
        
        return font_name, font_size, style.strip()

    def apply_text_effects(self, draw, text, position, font, color):
        """应用文本效果（阴影、描边和斜体）"""
        if self.shadow_check.isChecked():
            # 添加阴影效果
            shadow_color = (0, 0, 0, color[3])  # 黑色阴影
            shadow_offset = 2
            draw.text((position[0] + shadow_offset, position[1] + shadow_offset), 
                     text, font=font, fill=shadow_color)
        
        if self.stroke_check.isChecked():
            # 添加描边效果
            stroke_color = (0, 0, 0, color[3])  # 黑色描边
            stroke_width = 2
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((position[0] + dx, position[1] + dy), 
                                 text, font=font, fill=stroke_color)
        
        # 绘制主文本
        if self.italic_check.isChecked():
            # 使用简单的斜体模拟 - 在多个位置绘制文本创建倾斜效果
            base_x, base_y = position
            # 绘制多个轻微偏移的文本来模拟斜体
            for offset in range(3):
                # 每个偏移位置的透明度逐渐降低
                alpha_factor = 1.0 - (offset * 0.2)
                italic_alpha = int(color[3] * alpha_factor)
                italic_color = (color[0], color[1], color[2], italic_alpha)
                draw.text((base_x + offset, base_y), text, font=font, fill=italic_color)
        else:
            # 正常绘制文本
            draw.text(position, text, font=font, fill=color)

    def update_preview(self):
        if not self.current_image_path:
            self.preview_label.clear()
            self.preview_label.setText('请先导入图片')
            return
            
        img = Image.open(self.current_image_path).convert('RGBA')
        preview = img.copy()
        
        if self.watermark_type == 'text':
            # 文本水印处理
            text = self.text_edit.text().strip()
            if not text:
                text = "watermark"
                
            # 使用用户设置的字体、颜色和透明度
            font_name, font_size, font_style = self.get_font_style()
            opacity = self.opacity_slider.value() / 100.0  # 透明度百分比转小数
            color = (self.text_color.red(), self.text_color.green(), self.text_color.blue(), int(255 * opacity))
            scale_factor = self.scale_slider.value() / 100.0  # 缩放因子
            
            # 尝试加载用户选择的字体（应用缩放，使用更高质量）
            scaled_font_size = max(10, int(font_size * scale_factor))
            
            # 字体名称映射，将常见的中文字体名称映射到系统字体文件
            font_mapping = {
                "SimHei": "simhei.ttf",  # 黑体
                "Microsoft YaHei": "msyh.ttc",  # 微软雅黑
                "SimSun": "simsun.ttc",  # 宋体
                "Arial": "arial.ttf",
                "Times New Roman": "times.ttf"
            }
            
            # 获取对应的字体文件名
            font_file = font_mapping.get(font_name, font_name)
            
            try:
                # 首先尝试直接加载字体文件
                font = ImageFont.truetype(font_file, scaled_font_size, encoding="unic")
                
                # 应用粗体和斜体效果
                if self.bold_check.isChecked() and self.italic_check.isChecked():
                    # 粗体+斜体 - 尝试加载粗斜体版本
                    try:
                        font = ImageFont.truetype(font_file, scaled_font_size, encoding="unic", index=3)
                    except:
                        # 如果失败，使用更大的字号模拟粗体效果
                        font = ImageFont.truetype(font_file, int(scaled_font_size * 1.2), encoding="unic")
                elif self.bold_check.isChecked():
                    # 仅粗体 - 尝试加载粗体版本
                    try:
                        font = ImageFont.truetype(font_file, scaled_font_size, encoding="unic", index=1)
                    except:
                        # 如果失败，使用更大的字号模拟粗体效果
                        font = ImageFont.truetype(font_file, int(scaled_font_size * 1.1), encoding="unic")
                elif self.italic_check.isChecked():
                    # 仅斜体 - 使用倾斜变换来模拟斜体效果
                    font = ImageFont.truetype(font_file, scaled_font_size, encoding="unic")
                    # 斜体效果将在后续的文本绘制中处理
                    
            except Exception as e:
                # 如果加载失败，尝试使用系统默认字体
                try:
                    font = ImageFont.truetype("arial.ttf", scaled_font_size, encoding="unic")
                except:
                    # 如果都失败，使用默认字体但设置更大的尺寸
                    font = ImageFont.load_default()
                    # 对于默认字体，我们需要使用更大的尺寸
                    scaled_font_size = max(10, int(font_size * scale_factor * 3))  # 默认字体三倍大小
                
            # 计算文本尺寸
            temp_img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            # 获取位置
            if hasattr(self, 'dragging') and self.dragging:
                pos = self.get_drag_position(preview.size, (w, h))
            else:
                pos = self.get_grid_position(preview.size, (w, h))
                self.drag_position = QPoint(pos[0], pos[1])
            
            # 旋转
            angle = self.rotate_slider.value()
            
            # 创建水印图层
            txt_img = Image.new('RGBA', (w, h), (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_img)
            
            # 绘制文本到水印图层
            self.apply_text_effects(draw, text, (-bbox[0], -bbox[1]), font, color)
            
            # 应用旋转
            if angle != 0:
                txt_img = txt_img.rotate(angle, expand=1, center=(w//2, h//2))
                w, h = txt_img.size
                if hasattr(self, 'dragging') and self.dragging:
                    pos = self.get_drag_position(preview.size, (w, h))
                else:
                    pos = self.get_grid_position(preview.size, (w, h))
            
            # 应用额外的图像缩放
            if scale_factor > 1.0:
                additional_scale = min(3.0, scale_factor)
                new_width = int(w * additional_scale)
                new_height = int(h * additional_scale)
                txt_img = txt_img.resize((new_width, new_height), Image.LANCZOS)
                w, h = new_width, new_height
                if hasattr(self, 'dragging') and self.dragging:
                    pos = self.get_drag_position(preview.size, (w, h))
                else:
                    pos = self.get_grid_position(preview.size, (w, h))
            
            # 将水印放置到正确位置
            final_img = Image.new('RGBA', preview.size, (255, 255, 255, 0))
            final_img.paste(txt_img, pos, txt_img)
            preview = Image.alpha_composite(preview, final_img)
            
        elif self.watermark_type == 'image' and self.watermark_image:
            # 图片水印处理
            watermark_img = self.watermark_image.copy()
            
            # 应用图片透明度
            image_opacity = self.image_opacity_slider.value() / 100.0
            if image_opacity < 1.0:
                # 创建透明水印
                alpha = watermark_img.split()[3]
                alpha = alpha.point(lambda p: p * image_opacity)
                watermark_img.putalpha(alpha)
            
            # 应用图片缩放
            image_scale = self.image_scale_slider.value() / 100.0
            if image_scale != 1.0:
                new_width = int(watermark_img.width * image_scale)
                new_height = int(watermark_img.height * image_scale)
                watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
            
            w, h = watermark_img.size
            
            # 获取位置
            if hasattr(self, 'dragging') and self.dragging:
                pos = self.get_drag_position(preview.size, (w, h))
            else:
                pos = self.get_grid_position(preview.size, (w, h))
                self.drag_position = QPoint(pos[0], pos[1])
            
            # 应用旋转
            angle = self.rotate_slider.value()
            if angle != 0:
                watermark_img = watermark_img.rotate(angle, expand=1, center=(w//2, h//2))
                w, h = watermark_img.size
                if hasattr(self, 'dragging') and self.dragging:
                    pos = self.get_drag_position(preview.size, (w, h))
                else:
                    pos = self.get_grid_position(preview.size, (w, h))
            
            # 将图片水印放置到正确位置
            final_img = Image.new('RGBA', preview.size, (255, 255, 255, 0))
            final_img.paste(watermark_img, pos, watermark_img)
            preview = Image.alpha_composite(preview, final_img)
        
        # 显示预览
        qimg = QImage(preview.tobytes(), preview.size[0], preview.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio))

    def apply_watermark_to_image(self, image_path):
        """为单张图片添加水印"""
        img = Image.open(image_path).convert('RGBA')
        
        if self.watermark_type == 'text':
            # 文本水印处理
            text = self.text_edit.text().strip()
            if not text:
                text = "watermark"
                
            # 使用用户设置的字体、颜色和透明度
            font_name, font_size, font_style = self.get_font_style()
            opacity = self.opacity_slider.value() / 100.0  # 透明度百分比转小数
            color = (self.text_color.red(), self.text_color.green(), self.text_color.blue(), int(255 * opacity))
            scale_factor = self.scale_slider.value() / 100.0  # 缩放因子
            
            try:
                # 尝试加载用户选择的字体（应用缩放，使用更高质量）
                scaled_font_size = max(10, int(font_size * scale_factor))
                # 使用更高质量的字体加载方式
                font = ImageFont.truetype(font_name, scaled_font_size, encoding="unic")
            except:
                # 如果失败，尝试使用其他字体
                try:
                    # 尝试使用Arial字体
                    font = ImageFont.truetype("arial.ttf", scaled_font_size, encoding="unic")
                except:
                    # 如果都失败，使用默认字体但设置更大的尺寸
                    font = ImageFont.load_default()
                    # 对于默认字体，我们需要使用更大的尺寸
                    scaled_font_size = max(10, int(font_size * scale_factor * 3))  # 默认字体三倍大小
                
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
            
            # 绘制文本到水印图层（考虑基线偏移，并应用效果）
            self.apply_text_effects(draw, text, (-bbox[0], -bbox[1]), font, color)
            
            # 应用旋转（围绕水印自身中心）
            if angle != 0:
                txt_img = txt_img.rotate(angle, expand=1, center=(w//2, h//2))
                # 旋转后水印尺寸可能变化，需要重新计算位置
                w, h = txt_img.size
                pos = self.get_drag_position(img.size, (w, h))
            
            # 应用额外的图像缩放来获得更大的水印
            if scale_factor > 1.0:
                # 如果缩放因子大于1，使用图像缩放来进一步放大
                additional_scale = min(3.0, scale_factor)  # 最大额外缩放3倍
                new_width = int(w * additional_scale)
                new_height = int(h * additional_scale)
                txt_img = txt_img.resize((new_width, new_height), Image.LANCZOS)
                w, h = new_width, new_height
                # 重新计算位置
                pos = self.get_drag_position(img.size, (w, h))
            
            # 将旋转后的水印放置到正确位置
            final_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
            final_img.paste(txt_img, pos, txt_img)
            txt_img = final_img
            
            # 合成图片
            img = Image.alpha_composite(img, txt_img)
            
        elif self.watermark_type == 'image' and self.watermark_image:
            # 图片水印处理
            watermark_img = self.watermark_image.copy()
            
            # 应用图片透明度
            image_opacity = self.image_opacity_slider.value() / 100.0
            if image_opacity < 1.0:
                # 创建透明水印
                alpha = watermark_img.split()[3]
                alpha = alpha.point(lambda p: p * image_opacity)
                watermark_img.putalpha(alpha)
            
            # 应用图片缩放
            image_scale = self.image_scale_slider.value() / 100.0
            if image_scale != 1.0:
                new_width = int(watermark_img.width * image_scale)
                new_height = int(watermark_img.height * image_scale)
                watermark_img = watermark_img.resize((new_width, new_height), Image.LANCZOS)
            
            w, h = watermark_img.size
            
            # 获取位置
            pos = self.get_drag_position(img.size, (w, h))
            
            # 应用旋转
            angle = self.rotate_slider.value()
            if angle != 0:
                watermark_img = watermark_img.rotate(angle, expand=1, center=(w//2, h//2))
                w, h = watermark_img.size
                pos = self.get_drag_position(img.size, (w, h))
            
            # 将图片水印放置到正确位置
            final_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
            final_img.paste(watermark_img, pos, watermark_img)
            img = Image.alpha_composite(img, final_img)
        
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