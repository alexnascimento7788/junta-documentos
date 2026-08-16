"""Folha de estilos (QSS) para o tema dark moderno do aplicativo."""

COLOR_BG = "#1e1f29"
COLOR_PANEL = "#262837"
COLOR_PANEL_ALT = "#2d3044"
COLOR_ACCENT = "#7c5cff"
COLOR_ACCENT_HOVER = "#9075ff"
COLOR_ACCENT_PRESSED = "#6647e6"
COLOR_TEXT = "#e8e8f0"
COLOR_TEXT_MUTED = "#9a9cb5"
COLOR_BORDER = "#3a3d54"
COLOR_SUCCESS = "#3ddc97"
COLOR_DANGER = "#ff6b81"

STYLE_SHEET = f"""
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

#TopBar {{
    background-color: {COLOR_PANEL};
    border-bottom: 1px solid {COLOR_BORDER};
}}

#TitleLabel {{
    font-size: 18px;
    font-weight: 600;
    color: {COLOR_TEXT};
}}

#SubtitleLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 12px;
}}

#LeftPanel {{
    background-color: {COLOR_PANEL};
    border-right: 1px solid {COLOR_BORDER};
}}

#RightPanel {{
    background-color: {COLOR_BG};
}}

QLabel#SectionLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding-top: 6px;
}}

QLabel#PathLabel {{
    color: {COLOR_TEXT};
    background-color: {COLOR_PANEL_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 10px;
}}

QPushButton {{
    background-color: {COLOR_PANEL_ALT};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #363a52;
    border-color: {COLOR_ACCENT};
}}

QPushButton:pressed {{
    background-color: #2a2c40;
}}

QPushButton:disabled {{
    color: {COLOR_TEXT_MUTED};
    background-color: {COLOR_PANEL};
    border-color: {COLOR_BORDER};
}}

QPushButton#PrimaryButton {{
    background-color: {COLOR_ACCENT};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {COLOR_ACCENT_PRESSED};
}}

QPushButton#PrimaryButton:disabled {{
    background-color: #3a3d54;
    color: {COLOR_TEXT_MUTED};
}}

QPushButton#IconButton {{
    padding: 6px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
}}

QListWidget {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 6px;
    outline: none;
}}

QListWidget::item {{
    background-color: {COLOR_PANEL_ALT};
    border-radius: 8px;
    margin: 4px 2px;
    padding: 0px;
}}

QListWidget::item:selected {{
    background-color: #3a3660;
    border: 1px solid {COLOR_ACCENT};
}}

QListWidget::item:hover {{
    background-color: #33364a;
}}

QProgressBar {{
    background-color: {COLOR_PANEL_ALT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    text-align: center;
    color: {COLOR_TEXT};
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {COLOR_ACCENT};
    border-radius: 7px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLOR_BORDER};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

#EmptyStateLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 13px;
}}
"""
