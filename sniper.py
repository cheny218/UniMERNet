from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QGuiApplication
from PIL import Image
import io

class ScreenSnipper(QWidget):
    snip_captured = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setStyleSheet("background:transparent;")
        self.setCursor(Qt.CrossCursor)

        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.is_snipping = False
        self.full_screen_pixmap = None

    def start_snip(self):
        screen = QGuiApplication.primaryScreen()
        if screen:
            self.full_screen_pixmap = screen.grabWindow(0)
            self.setGeometry(screen.geometry())
            self.showFullScreen()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_snipping = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_snipping:
            self.is_snipping = False
            self.hide()
            
            rect = QRect(self.start_pos, self.end_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                cropped_pixmap = self.full_screen_pixmap.copy(rect)
                buffer = io.BytesIO()
                cropped_pixmap.save(buffer, "PNG")
                buffer.seek(0)
                img = Image.open(buffer).convert("RGB")
                self.snip_captured.emit(img)

    def paintEvent(self, event):
        if not self.full_screen_pixmap:
            return
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.full_screen_pixmap)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self.is_snipping:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.drawPixmap(rect, self.full_screen_pixmap, rect)
            pen = QPen(QColor(0, 150, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()