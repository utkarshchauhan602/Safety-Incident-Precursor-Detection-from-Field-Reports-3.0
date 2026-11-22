"""Theme tokens and accessible CSS for the Streamlit user interface."""
from __future__ import annotations

THEMES = {
    "Light": {"bg":"#f4f7fb", "surface":"#ffffff", "surface_alt":"#edf3fa", "text":"#172338", "muted":"#61718a", "border":"#dce5f0", "accent":"#1769d2", "accent_soft":"#e7f1ff", "sidebar":"#eaf0f7"},
    "Dark": {"bg":"#0b1220", "surface":"#111c2e", "surface_alt":"#17243a", "text":"#e8eef8", "muted":"#a5b4c8", "border":"#29384f", "accent":"#5ba8ff", "accent_soft":"#142c49", "sidebar":"#0e192a"},
}

def tokens(name: str) -> dict[str, str]:
    return dict(THEMES.get(name, THEMES["Light"]))

def css(name: str) -> str:
    p = tokens(name)
    return f"""
    <style>
    :root {{ color-scheme: {'dark' if name == 'Dark' else 'light'}; }}
    html, body, .stApp, [data-testid='stAppViewContainer'] {{ background:{p['bg']} !important; color:{p['text']} !important; font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif; }}
    .block-container {{ max-width:1480px; padding-top:1.35rem; padding-bottom:2.5rem; }}
    [data-testid='stSidebar'] {{ background:{p['sidebar']} !important; border-right:1px solid {p['border']}; }}
    [data-testid='stMetric'] {{ background:{p['surface']} !important; border:1px solid {p['border']}; border-radius:16px; padding:14px 16px; box-shadow:0 5px 18px rgba(20,40,70,.06); }}
    [data-testid='stChatMessageContent'] {{ background:{p['surface']} !important; border:1px solid {p['border']}; border-radius:18px; padding:1rem 1.1rem; box-shadow:0 4px 14px rgba(20,40,70,.06); }}
    [data-testid='stChatMessage'] {{ gap:.8rem; padding:.35rem 0; }}
    [data-testid='stChatInput'] {{ border:1px solid {p['border']}; border-radius:16px; background:{p['surface']}; }}
    [data-testid='stChatInput'] textarea {{ line-height:1.55; }}
    div.stButton>button, div.stDownloadButton>button {{ border-radius:11px; font-weight:650; min-height:2.55rem; transition:transform .15s ease,box-shadow .15s ease; }}
    div.stButton>button:hover {{ transform:translateY(-1px); box-shadow:0 5px 14px rgba(20,40,70,.12); }}
    [data-testid='stForm'] {{ background:{p['surface']}; border:1px solid {p['border']}; border-radius:16px; padding:1rem; }}
    .spi-chat-intro {{ background:linear-gradient(115deg,{p['surface']},{p['surface_alt']}); border:1px solid {p['border']}; border-radius:20px; padding:1.2rem 1.35rem; margin:.4rem 0 1.1rem; }}
    .spi-chat-intro p {{ color:{p['muted']}; margin:.35rem 0 0; line-height:1.65; }}
    .spi-chip {{ display:inline-block; border:1px solid {p['border']}; background:{p['surface_alt']}; color:{p['text']}; border-radius:999px; padding:.28rem .65rem; font-size:.76rem; margin:.15rem .2rem .15rem 0; }}
    .spi-alert {{ border-left:4px solid #dc2626; padding:.75rem 1rem; border-radius:9px; background:rgba(220,38,38,.08); margin:.5rem 0; }}
    @media(max-width:700px) {{ .block-container {{padding-left:1rem;padding-right:1rem;}} }}
    @media(prefers-reduced-motion:reduce) {{*,*::before,*::after {{animation-duration:.01ms!important;transition-duration:.01ms!important;}}}}
    </style>
    """
