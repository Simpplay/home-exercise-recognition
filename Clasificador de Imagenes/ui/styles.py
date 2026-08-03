"""Hoja de estilos (QSS) para dar a la aplicación una apariencia moderna y oscura."""
from __future__ import annotations

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1f26;
    color: #e6e6ea;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #1a1b21;
}

QLabel#TopBarTitle {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 600;
    color: #9a9db0;
    padding: 4px 2px;
    text-transform: uppercase;
}

QFrame#TopBar {
    background-color: #23242c;
    border-bottom: 1px solid #303240;
}

QFrame#BottomControls {
    background-color: #23242c;
    border-top: 1px solid #303240;
}

QFrame#Sidebar, QFrame#ThumbnailsPanel {
    background-color: #20212a;
    border-right: 1px solid #303240;
}

QFrame#ThumbnailsPanel {
    border-right: none;
    border-left: 1px solid #303240;
}

QFrame#SegmentsPanel {
    background-color: #20212a;
    border-right: 1px solid #303240;
    border-top: 1px solid #303240;
}

QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 6px;
    border-radius: 6px;
    margin: 2px 4px;
}

QListWidget::item:selected {
    background-color: #3a5fd9;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #2b2d38;
}

QPushButton {
    background-color: #2b2d38;
    border: 1px solid #3a3c4a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e6e6ea;
}

QPushButton:hover {
    background-color: #363845;
    border-color: #4a4d5e;
}

QPushButton:pressed {
    background-color: #2a5fd9;
    border-color: #2a5fd9;
}

QPushButton:disabled {
    color: #62636e;
    background-color: #232430;
}

QPushButton#PrimaryButton {
    background-color: #3a5fd9;
    border-color: #3a5fd9;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #4a6ef0;
}

QPushButton#IconButton {
    padding: 6px 10px;
    font-weight: 600;
}

QPushButton:checkable:checked {
    background-color: #3a5fd9;
    border-color: #3a5fd9;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #303240;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3a5fd9;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QGraphicsView {
    background-color: #101116;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #3a3c4a;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #4a4d5e;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background: #3a3c4a;
    border-radius: 5px;
    min-width: 24px;
}

QStatusBar {
    background-color: #23242c;
    color: #9a9db0;
    border-top: 1px solid #303240;
}

QLineEdit, QComboBox {
    background-color: #2b2d38;
    border: 1px solid #3a3c4a;
    border-radius: 5px;
    padding: 5px 8px;
    color: #e6e6ea;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #3a5fd9;
}

QComboBox::drop-down {
    border: none;
}

QCheckBox {
    spacing: 8px;
}

QToolTip {
    background-color: #2b2d38;
    color: #e6e6ea;
    border: 1px solid #3a3c4a;
    padding: 4px;
}
"""
