"""Paleta de cores e folha de estilos (QSS) — identidade visual CEASAMINAS."""

# Paleta extraída da marca CEASAMINAS (losango verde/dourado + tipografia preta/verde).
COLOR_GREEN = "#1C7C3E"          # verde principal da marca
COLOR_GREEN_DARK = "#0F5C2E"     # verde escuro (hover/pressed, texto "MINAS")
COLOR_GREEN_LIGHT = "#E6F4EA"    # verde clarinho (fundo de seleção/hover)
COLOR_GOLD = "#F5A623"           # dourado da marca (seta direita do losango)
COLOR_GOLD_DARK = "#C98A00"      # dourado escuro (hover sobre dourado)

COLOR_BG = "#F5F6F5"
COLOR_PANEL = "#FFFFFF"
COLOR_PANEL_ALT = "#F0F2F0"
COLOR_BORDER = "#E1E4E1"
COLOR_TEXT = "#1A1A1A"
COLOR_TEXT_MUTED = "#6B7280"

COLOR_SUCCESS = COLOR_GREEN
COLOR_WARNING = COLOR_GOLD
COLOR_DANGER = "#D64545"

# Cores de identificação usadas nos avatares circulares da lista de PDFs —
# variações dentro da mesma família verde/dourada da marca, para manter a coesão visual.
AVATAR_PALETTE = [
    COLOR_GREEN, COLOR_GOLD, COLOR_GREEN_DARK, "#2F9E63",
    "#C9A227", "#4C7A3E", "#B76E00", "#3D8361",
]

STYLE_SHEET = f"""
QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

#TopBar {{
    background-color: {COLOR_PANEL};
    border-bottom: 2px solid {COLOR_GREEN};
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

#FooterBar {{
    background-color: {COLOR_PANEL};
    border-top: 1px solid {COLOR_BORDER};
}}

#FooterLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
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
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLOR_GREEN_LIGHT};
    border-color: {COLOR_GREEN};
}}

QPushButton:pressed {{
    background-color: #d9ecdf;
}}

QPushButton:disabled {{
    color: {COLOR_TEXT_MUTED};
    background-color: {COLOR_PANEL_ALT};
    border-color: {COLOR_BORDER};
}}

QPushButton#PrimaryButton {{
    background-color: {COLOR_GREEN};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {COLOR_GREEN_DARK};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: #0a441f;
}}

QPushButton#PrimaryButton:disabled {{
    background-color: #b7c9bd;
    color: #eef3ef;
}}

QPushButton#IconButton {{
    padding: 6px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
}}

QLineEdit {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {COLOR_GREEN_LIGHT};
    selection-color: {COLOR_TEXT};
}}

QLineEdit:focus {{
    border-color: {COLOR_GREEN};
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
    background-color: {COLOR_GREEN_LIGHT};
    border: 1px solid {COLOR_GREEN};
}}

QListWidget::item:hover {{
    background-color: #e8ebe8;
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
    background: {COLOR_GREEN};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

#EmptyStateLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 13px;
}}
"""
