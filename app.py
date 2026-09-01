import os
import sys
from PIL import Image, ImageGrab
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QFileDialog, QStatusBar, QSplitter, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView

from sniper import ScreenSnipper
from inference_engine import UniMERNetEngine


class ModelInitWorker(QThread):
    loaded = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            engine = UniMERNetEngine()
            self.loaded.emit(engine)
        except Exception as e:
            self.failed.emit(str(e))


class InferenceWorker(QThread):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, engine, image):
        super().__init__()
        self.engine = engine
        self.image = image

    def run(self):
        try:
            latex = self.engine.predict(self.image)
            self.finished.emit(latex)
        except Exception as e:
            self.failed.emit(str(e))


class LaTeXApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UniMERNet 智能公式识别桌面版")
        self.resize(920, 700)
        self.engine = None

        self.init_ui()
        self.snipper = ScreenSnipper()
        self.snipper.snip_captured.connect(self.process_image)

        # 注册 F4 全局/窗口截图快捷键
        self.shortcut_snip = QShortcut(QKeySequence("F4"), self)
        self.shortcut_snip.activated.connect(self.start_screen_snip)

        # 后台异步加载模型
        self.status_bar.showMessage("正在加载 UniMERNet 模型，请稍候...")
        self.set_controls_enabled(False)
        self.init_worker = ModelInitWorker()
        self.init_worker.loaded.connect(self.on_model_loaded)
        self.init_worker.failed.connect(self.on_model_init_failed)
        self.init_worker.start()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # 顶部操作栏
        toolbar_group = QGroupBox("输入方式")
        toolbar_layout = QHBoxLayout(toolbar_group)

        self.btn_snip = QPushButton("📷 快捷截图识别 (F4)")
        self.btn_paste = QPushButton("📋 从剪贴板识别")
        self.btn_open = QPushButton("📁 打开本地图片...")

        self.btn_snip.clicked.connect(self.start_screen_snip)
        self.btn_paste.clicked.connect(self.recognize_from_clipboard)
        self.btn_open.clicked.connect(self.open_image_file)

        toolbar_layout.addWidget(self.btn_snip)
        toolbar_layout.addWidget(self.btn_paste)
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar_group)

        # 中间分割区
        splitter = QSplitter(Qt.Vertical)

        # 上半部分：LaTeX 源码与复制
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        code_layout.setContentsMargins(0, 4, 0, 4)

        lbl_code = QLabel("<b>LaTeX 源码（支持编辑修改）：</b>")
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("公式识别成功后，此处将显示 LaTeX 源码...")
        self.text_editor.textChanged.connect(self.on_code_edited)

        copy_layout = QHBoxLayout()
        self.btn_copy_raw = QPushButton("复制纯代码")
        self.btn_copy_inline = QPushButton("复制行内公式 $...$")
        self.btn_copy_block = QPushButton("复制独立公式 $$...$$")

        self.btn_copy_raw.clicked.connect(lambda: self.copy_to_clipboard(self.text_editor.toPlainText()))
        self.btn_copy_inline.clicked.connect(lambda: self.copy_to_clipboard(f"${self.text_editor.toPlainText().strip()}$"))
        self.btn_copy_block.clicked.connect(lambda: self.copy_to_clipboard(f"$${self.text_editor.toPlainText().strip()}$$\n"))

        copy_layout.addWidget(self.btn_copy_raw)
        copy_layout.addWidget(self.btn_copy_inline)
        copy_layout.addWidget(self.btn_copy_block)
        copy_layout.addStretch()

        code_layout.addWidget(lbl_code)
        code_layout.addWidget(self.text_editor)
        code_layout.addLayout(copy_layout)
        splitter.addWidget(code_widget)

        # 下半部分：KaTeX 渲染效果
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 4, 0, 4)

        lbl_preview = QLabel("<b>公式实时渲染预览：</b>")
        self.web_view = QWebEngineView()
        
        html_file = os.path.join(os.path.dirname(__file__), "katex_template.html")
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                self.web_view.setHtml(f.read())

        preview_layout.addWidget(lbl_preview)
        preview_layout.addWidget(self.web_view)
        splitter.addWidget(preview_widget)

        main_layout.addWidget(splitter)

        # 底部状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(central_widget)

    def set_controls_enabled(self, enabled: bool):
        self.btn_snip.setEnabled(enabled)
        self.btn_paste.setEnabled(enabled)
        self.btn_open.setEnabled(enabled)

    def on_model_loaded(self, engine):
        self.engine = engine
        self.set_controls_enabled(True)
        self.status_bar.showMessage(f"就绪 (运行模式: {self.engine.device.upper()})", 6000)

    def on_model_init_failed(self, err_msg):
        QMessageBox.critical(self, "模型初始化失败", f"无法加载 UniMERNet 模型：\n{err_msg}")
        self.status_bar.showMessage("模型加载失败。")

    def start_screen_snip(self):
        self.snipper.start_snip()

    def recognize_from_clipboard(self):
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            self.process_image(img)
        else:
            QMessageBox.information(self, "提示", "剪贴板中未发现有效图片。")

    def open_image_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择公式图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            try:
                img = Image.open(path)
                self.process_image(img)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开图片：{e}")

    def process_image(self, image: Image.Image):
        if not self.engine:
            QMessageBox.warning(self, "提示", "模型仍在加载中...")
            return

        self.status_bar.showMessage("正在识别中...")
        self.set_controls_enabled(False)

        self.worker = InferenceWorker(self.engine, image)
        self.worker.finished.connect(self.on_inference_success)
        self.worker.failed.connect(self.on_inference_failed)
        self.worker.start()

    def on_inference_success(self, latex: str):
        self.set_controls_enabled(True)
        self.text_editor.setPlainText(latex)
        self.status_bar.showMessage("识别成功！已生成 LaTeX 与预览效果。", 5000)

    def on_inference_failed(self, err: str):
        self.set_controls_enabled(True)
        QMessageBox.warning(self, "识别出错", f"推理异常：\n{err}")
        self.status_bar.showMessage("识别失败。")

    def on_code_edited(self):
        latex = self.text_editor.toPlainText()
        js_code = f"renderFormula({repr(latex)});"
        self.web_view.page().runJavaScript(js_code)

    def copy_to_clipboard(self, text: str):
        if not text.strip():
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_bar.showMessage("已复制到剪贴板！", 2500)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LaTeXApp()
    window.show()
    sys.exit(app.exec())