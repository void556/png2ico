import sys
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QFrame
)


class DropArea(QFrame):
    """Custom widget handling file selection and drag-and-drop operations."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #3a3d4d;
                border-radius: 8px;
                background-color: #1e1e2e;
            }
            DropArea:hover {
                border-color: #89b4fa;
                background-color: #252538;
            }
        """)

        layout = QVBoxLayout(self)
        self.label = QLabel("Drag & Drop PNG files here\nor click to browse")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #a6adc8; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.label)

        self.on_files_dropped = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_files_dropped:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select PNG Images", "", "PNG Images (*.png)"
            )
            if files:
                self.on_files_dropped(files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith('.png'):
                file_paths.append(path)
        
        if file_paths and self.on_files_dropped:
            self.on_files_dropped(file_paths)


class PngToIcoConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PNG to ICO Converter")
        self.resize(550, 600)
        
        self.selected_files = []
        
        self.init_ui()

    def init_ui(self):
        # Central Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Drag & Drop Zone
        self.drop_area = DropArea()
        self.drop_area.setFixedHeight(120)
        self.drop_area.on_files_dropped = self.add_files
        main_layout.addWidget(self.drop_area)

        # File List Box
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #ffffff;
            }
        """)
        self.file_list.currentItemChanged.connect(self.update_preview)
        main_layout.addWidget(self.file_list)

        # Middle Control Panel (Preview + Options)
        control_layout = QHBoxLayout()

        # Image Preview Frame
        self.preview_label = QLabel("No Preview")
        self.preview_label.setFixedSize(128, 128)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid #313244;
                border-radius: 6px;
                background-color: #11111b;
                color: #6c7086;
            }
        """)
        control_layout.addWidget(self.preview_label)

        # Settings Options
        settings_layout = QVBoxLayout()
        
        size_label = QLabel("Select Target Icon Sizes:")
        size_label.setStyleSheet("font-weight: bold; color: #cdd6f4;")
        settings_layout.addWidget(size_label)

        self.size_dropdown = QComboBox()
        self.size_dropdown.addItems([
            "Multi-Size Standard (16, 32, 48, 64, 128, 256)",
            "Maximum Quality (256x256)",
            "Large (128x128)",
            "Medium (64x64)",
            "Standard Desktop (48x48)",
            "Small (32x32)",
            "Favicon / Taskbar (16x16)"
        ])
        self.size_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        settings_layout.addWidget(self.size_dropdown)

        # Clear Selection Button
        self.btn_clear = QPushButton("Clear Queue")
        self.btn_clear.clicked.connect(self.clear_queue)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        settings_layout.addWidget(self.btn_clear)
        settings_layout.addStretch()

        control_layout.addLayout(settings_layout)
        main_layout.addLayout(control_layout)

        # Conversion Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 4px;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Convert Action Button
        self.btn_convert = QPushButton("Convert to ICO")
        self.btn_convert.setFixedHeight(45)
        self.btn_convert.clicked.connect(self.convert_images)
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-size: 15px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)
        main_layout.addWidget(self.btn_convert)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Applies a uniform dark palette across the window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
        """)

    def add_files(self, paths):
        """Adds selected or dropped PNG file paths to the list."""
        for path in paths:
            if path not in self.selected_files:
                self.selected_files.append(path)
                self.file_list.addItem(Path(path).name)

        if self.selected_files and self.file_list.currentRow() == -1:
            self.file_list.setCurrentRow(0)

    def clear_queue(self):
        """Resets the queued file list and preview panel."""
        self.selected_files.clear()
        self.file_list.clear()
        self.preview_label.setText("No Preview")
        self.preview_label.setPixmap(QPixmap())
        self.progress_bar.setValue(0)

    def update_preview(self):
        """Updates the thumbnail preview frame when selecting list items."""
        row = self.file_list.currentRow()
        if row != -1 and row < len(self.selected_files):
            file_path = self.selected_files[row]
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                QSize(120, 120),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)

    def get_selected_sizes(self):
        """Maps dropdown choices to standard Pillow icon size tuples."""
        choice = self.size_dropdown.currentIndex()
        mapping = {
            0: [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            1: [(256, 256)],
            2: [(128, 128)],
            3: [(64, 64)],
            4: [(48, 48)],
            5: [(32, 32)],
            6: [(16, 16)]
        }
        return mapping.get(choice, [(256, 256)])

    def convert_images(self):
        """Performs Pillow conversion from PNG to ICO files."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please add at least one PNG file to convert.")
            return

        target_folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not target_folder:
            return

        sizes = self.get_selected_sizes()
        total_files = len(self.selected_files)
        self.progress_bar.setMaximum(total_files)

        converted_count = 0

        for i, file_path in enumerate(self.selected_files):
            try:
                img = Image.open(file_path)
                
                # Output filename configuration
                base_name = Path(file_path).stem
                output_path = Path(target_folder) / f"{base_name}.ico"

                # Save using Pillow ICO plugin
                img.save(output_path, format="ICO", sizes=sizes)
                converted_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to convert {Path(file_path).name}:\n{str(e)}")

            self.progress_bar.setValue(i + 1)

        QMessageBox.information(
            self,
            "Success",
            f"Successfully converted {converted_count} of {total_files} file(s) to ICO!"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PngToIcoConverter()
    window.show()
    sys.exit(app.exec())