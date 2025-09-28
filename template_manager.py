import json
import os
from datetime import datetime
from PyQt5.QtCore import QSettings

class TemplateManager:
    def __init__(self, templates_dir="templates"):
        self.templates_dir = templates_dir
        self.templates_file = os.path.join(templates_dir, "watermark_templates.json")
        self.settings = QSettings("WatermarkApp", "Templates")
        
        # 确保模板目录存在
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # 确保模板文件存在
        if not os.path.exists(self.templates_file):
            self._create_default_template_file()
    
    def _create_default_template_file(self):
        """创建默认模板文件"""
        default_templates = {
            "templates": {},
            "last_modified": datetime.now().isoformat()
        }
        self._save_templates(default_templates)
    
    def _load_templates(self):
        """加载模板数据"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"templates": {}, "last_modified": datetime.now().isoformat()}
    
    def _save_templates(self, templates_data):
        """保存模板数据"""
        templates_data["last_modified"] = datetime.now().isoformat()
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, indent=2, ensure_ascii=False)
    
    def save_template(self, template_name, template_data):
        """保存模板"""
        templates_data = self._load_templates()
        templates_data["templates"][template_name] = {
            "data": template_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_templates(templates_data)
        return True
    
    def load_template(self, template_name):
        """加载模板"""
        templates_data = self._load_templates()
        if template_name in templates_data["templates"]:
            return templates_data["templates"][template_name]["data"]
        return None
    
    def delete_template(self, template_name):
        """删除模板"""
        templates_data = self._load_templates()
        if template_name in templates_data["templates"]:
            del templates_data["templates"][template_name]
            self._save_templates(templates_data)
            return True
        return False
    
    def get_template_list(self):
        """获取模板列表"""
        templates_data = self._load_templates()
        templates = []
        for name, template_info in templates_data["templates"].items():
            templates.append({
                "name": name,
                "created_at": template_info.get("created_at", ""),
                "updated_at": template_info.get("updated_at", ""),
                "watermark_type": template_info["data"].get("watermark_type", "text")
            })
        return sorted(templates, key=lambda x: x["updated_at"], reverse=True)
    
    def template_exists(self, template_name):
        """检查模板是否存在"""
        templates_data = self._load_templates()
        return template_name in templates_data["templates"]
    
    def save_last_used_template(self, template_name):
        """保存最后使用的模板"""
        self.settings.setValue("last_used_template", template_name)
    
    def load_last_used_template(self):
        """加载最后使用的模板"""
        return self.settings.value("last_used_template", "")
    
    def save_current_settings(self, settings_data):
        """保存当前设置（用于程序启动时恢复）"""
        self.settings.setValue("current_settings", json.dumps(settings_data))
    
    def load_current_settings(self):
        """加载当前设置"""
        settings_json = self.settings.value("current_settings", "")
        if settings_json:
            return json.loads(settings_json)
        return None

def create_template_data_from_app(app_instance):
    """从应用实例创建模板数据"""
    template_data = {
        "watermark_type": app_instance.watermark_type,
        "text_content": app_instance.text_edit.text().strip() if hasattr(app_instance, 'text_edit') else "watermark",
        "font_name": app_instance.font_combo.currentText() if hasattr(app_instance, 'font_combo') else "Arial",
        "font_size": int(app_instance.font_size_spin.currentText()) if hasattr(app_instance, 'font_size_spin') else 96,
        "bold": app_instance.bold_check.isChecked() if hasattr(app_instance, 'bold_check') else False,
        "italic": app_instance.italic_check.isChecked() if hasattr(app_instance, 'italic_check') else False,
        "text_color": [
            app_instance.text_color.red(),
            app_instance.text_color.green(), 
            app_instance.text_color.blue(),
            app_instance.text_color.alpha()
        ] if hasattr(app_instance, 'text_color') else [255, 255, 255, 255],
        "opacity": app_instance.opacity_slider.value() if hasattr(app_instance, 'opacity_slider') else 80,
        "position": [app_instance.drag_position.x(), app_instance.drag_position.y()],
        "rotation": app_instance.rotate_slider.value() if hasattr(app_instance, 'rotate_slider') else 0,
        "scale": app_instance.scale_slider.value() if hasattr(app_instance, 'scale_slider') else 200,
        "shadow_enabled": app_instance.shadow_check.isChecked() if hasattr(app_instance, 'shadow_check') else False,
        "stroke_enabled": app_instance.stroke_check.isChecked() if hasattr(app_instance, 'stroke_check') else False,
        "grid_position": app_instance.grid_combo.currentIndex() if hasattr(app_instance, 'grid_combo') else 4,
        "image_path": app_instance.watermark_image_path if hasattr(app_instance, 'watermark_image_path') else "",
        "image_opacity": app_instance.image_opacity_slider.value() if hasattr(app_instance, 'image_opacity_slider') else 80,
        "image_scale": app_instance.image_scale_slider.value() if hasattr(app_instance, 'image_scale_slider') else 100
    }
    return template_data

def apply_template_to_app(template_data, app_instance):
    """将模板数据应用到应用实例"""
    # 首先设置水印类型并更新界面显示
    if template_data["watermark_type"] == "text":
        app_instance.watermark_type = "text"
        if hasattr(app_instance, 'text_radio'):
            app_instance.text_radio.setChecked(True)
        if hasattr(app_instance, 'image_radio'):
            app_instance.image_radio.setChecked(False)
        # 调用切换方法确保界面正确更新
        if hasattr(app_instance, 'toggle_watermark_type'):
            app_instance.toggle_watermark_type()
    else:
        app_instance.watermark_type = "image"
        if hasattr(app_instance, 'text_radio'):
            app_instance.text_radio.setChecked(False)
        if hasattr(app_instance, 'image_radio'):
            app_instance.image_radio.setChecked(True)
        # 调用切换方法确保界面正确更新
        if hasattr(app_instance, 'toggle_watermark_type'):
            app_instance.toggle_watermark_type()
    
    # 确保内部状态变量正确设置
    app_instance.current_text = template_data["text_content"] if hasattr(app_instance, 'current_text') else template_data["text_content"]
    app_instance.current_font_name = template_data["font_name"] if hasattr(app_instance, 'current_font_name') else template_data["font_name"]
    app_instance.current_font_size = template_data["font_size"] if hasattr(app_instance, 'current_font_size') else template_data["font_size"]
    app_instance.current_bold = template_data["bold"] if hasattr(app_instance, 'current_bold') else template_data["bold"]
    app_instance.current_italic = template_data["italic"] if hasattr(app_instance, 'current_italic') else template_data["italic"]
    app_instance.current_opacity = template_data["opacity"] if hasattr(app_instance, 'current_opacity') else template_data["opacity"]
    app_instance.current_rotation = template_data["rotation"] if hasattr(app_instance, 'current_rotation') else template_data["rotation"]
    app_instance.current_scale = template_data["scale"] if hasattr(app_instance, 'current_scale') else template_data["scale"]
    
    # 设置文本水印参数
    if hasattr(app_instance, 'text_edit'):
        app_instance.text_edit.setText(template_data["text_content"])
        # 手动触发文本变化信号
        app_instance.text_edit.textChanged.emit(template_data["text_content"])
    
    if hasattr(app_instance, 'font_combo'):
        # 设置字体并确保触发更新
        font_index = app_instance.font_combo.findText(template_data["font_name"])
        if font_index >= 0:
            app_instance.font_combo.setCurrentIndex(font_index)
        else:
            app_instance.font_combo.setCurrentText(template_data["font_name"])
        # 直接调用更新预览方法
        if hasattr(app_instance, 'update_preview'):
            app_instance.update_preview()
    
    if hasattr(app_instance, 'font_size_spin'):
        # 设置字号并确保触发更新
        size_text = str(template_data["font_size"])
        size_index = app_instance.font_size_spin.findText(size_text)
        if size_index >= 0:
            app_instance.font_size_spin.setCurrentIndex(size_index)
        else:
            app_instance.font_size_spin.setCurrentText(size_text)
        # 直接调用更新预览方法
        if hasattr(app_instance, 'update_preview'):
            app_instance.update_preview()
    
    if hasattr(app_instance, 'bold_check'):
        app_instance.bold_check.setChecked(template_data["bold"])
        # 手动触发粗体变化信号
        app_instance.bold_check.toggled.emit(template_data["bold"])
    
    if hasattr(app_instance, 'italic_check'):
        app_instance.italic_check.setChecked(template_data["italic"])
        # 手动触发斜体变化信号
        app_instance.italic_check.toggled.emit(template_data["italic"])
    
    if hasattr(app_instance, 'text_color'):
        color = template_data["text_color"]
        app_instance.text_color = app_instance.text_color.__class__(color[0], color[1], color[2], color[3])
        app_instance.color_label.setStyleSheet(f"background-color: rgba({color[0]}, {color[1]}, {color[2]}, {color[3]}); border: 1px solid black;")
    
    if hasattr(app_instance, 'opacity_slider'):
        app_instance.opacity_slider.setValue(template_data["opacity"])
        # 手动触发透明度变化信号
        app_instance.opacity_slider.valueChanged.emit(template_data["opacity"])
    
    if hasattr(app_instance, 'drag_position'):
        app_instance.drag_position = app_instance.drag_position.__class__(template_data["position"][0], template_data["position"][1])
    
    if hasattr(app_instance, 'rotate_slider'):
        app_instance.rotate_slider.setValue(template_data["rotation"])
        # 手动触发旋转变化信号
        app_instance.rotate_slider.valueChanged.emit(template_data["rotation"])
    
    if hasattr(app_instance, 'scale_slider'):
        app_instance.scale_slider.setValue(template_data["scale"])
        # 手动触发缩放变化信号
        app_instance.scale_slider.valueChanged.emit(template_data["scale"])
    
    if hasattr(app_instance, 'shadow_check'):
        app_instance.shadow_check.setChecked(template_data["shadow_enabled"])
        # 手动触发阴影变化信号
        app_instance.shadow_check.toggled.emit(template_data["shadow_enabled"])
    
    if hasattr(app_instance, 'stroke_check'):
        app_instance.stroke_check.setChecked(template_data["stroke_enabled"])
        # 手动触发描边变化信号
        app_instance.stroke_check.toggled.emit(template_data["stroke_enabled"])
    
    if hasattr(app_instance, 'grid_combo'):
        app_instance.grid_combo.setCurrentIndex(template_data["grid_position"])
        # 手动触发网格位置变化信号
        app_instance.grid_combo.currentIndexChanged.emit(template_data["grid_position"])
    
    # 设置图片水印参数
    if hasattr(app_instance, 'image_opacity_slider'):
        app_instance.image_opacity_slider.setValue(template_data["image_opacity"])
        # 手动触发图片透明度变化信号
        app_instance.image_opacity_slider.valueChanged.emit(template_data["image_opacity"])
    
    if hasattr(app_instance, 'image_scale_slider'):
        app_instance.image_scale_slider.setValue(template_data["image_scale"])
        # 手动触发图片缩放变化信号
        app_instance.image_scale_slider.valueChanged.emit(template_data["image_scale"])
    
    # 加载图片水印
    if template_data["image_path"] and os.path.exists(template_data["image_path"]):
        app_instance.watermark_image_path = template_data["image_path"]
        if hasattr(app_instance, 'image_path_label'):
            app_instance.image_path_label.setText(os.path.basename(template_data["image_path"]))
        try:
            from PIL import Image
            app_instance.watermark_image = Image.open(template_data["image_path"]).convert('RGBA')
        except:
            app_instance.watermark_image = None
    
    # 强制更新预览
    if hasattr(app_instance, 'update_preview'):
        app_instance.update_preview()