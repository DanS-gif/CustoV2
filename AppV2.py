"""
ObraCalc - Sistema Inteligente e Paramétrico para Cálculo e Orçamento de Obras
===============================================================================
MVP v2.0  |  Stack: Streamlit · Pandas · st-aggrid · Matplotlib · fpdf2 · JSON

Arquitetura em blocos lógicos:
  [A] Imports e Configuração de Página
  [B] CSS Blueprint Dark Theme
  [C] Constantes e Dados-Padrão
  [D] Gestão do sugestoes_mercado.json
  [E] Inicialização do Session State
  [F] Algoritmo Heurístico de Layout de Planta (Matplotlib + ABNT)
  [G] Gráfico Comparativo de Perfis (Matplotlib)
  [H] Geração de Proposta em PDF (fpdf2)
  [I] Helpers de AgGrid e Cálculo de Custo
  [J] Abas da Interface Streamlit
  [K] Ponto de Entrada (main)
"""

# ═══════════════════════════════════════════════════════════════════════════
# [A] IMPORTS E CONFIGURAÇÃO DE PÁGINA
# ═══════════════════════════════════════════════════════════════════════════

import io
import json
import math
import os
from typing import Optional

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import streamlit as st
from fpdf import FPDF
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode

st.set_page_config(
    page_title="ObraCalc · Orçamento Paramétrico",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════
# [B] CSS - BLUEPRINT DARK THEME
# ═══════════════════════════════════════════════════════════════════════════

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne+Mono&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #060d18; color: #b8ccdc; }

/* ── Header ── */
.oc-header {
    background: linear-gradient(160deg,#091524 0%,#0f2035 60%,#091524 100%);
    border:1px solid #183554; border-radius:14px;
    padding:26px 36px; margin-bottom:22px; position:relative; overflow:hidden;
}
.oc-header::after {
    content:''; position:absolute; inset:0; pointer-events:none;
    background:
        repeating-linear-gradient(0deg,transparent,transparent 29px,
            rgba(24,80,140,.07) 29px,rgba(24,80,140,.07) 30px),
        repeating-linear-gradient(90deg,transparent,transparent 29px,
            rgba(24,80,140,.07) 29px,rgba(24,80,140,.07) 30px);
}
.oc-header h1 {
    font-family:'Syne Mono',monospace; font-size:2rem; color:#4d9fd6;
    letter-spacing:3px; margin:0; text-shadow:0 0 24px rgba(77,159,214,.35);
}
.oc-header p { color:#547a96; margin:5px 0 0; font-size:.9rem; letter-spacing:.5px; }

/* ── Metric cards ── */
.oc-card {
    background:linear-gradient(145deg,#0c1e30,#132840);
    border:1px solid #1a3d60; border-left:4px solid #4d9fd6;
    border-radius:10px; padding:18px 22px; margin:6px 0;
}
.oc-card .lbl { font-family:'Syne Mono',monospace; font-size:.72rem;
    color:#506e86; text-transform:uppercase; letter-spacing:1.8px; }
.oc-card .val { font-family:'Syne Mono',monospace; font-size:1.9rem;
    font-weight:700; color:#4d9fd6; line-height:1.15; }
.oc-card .sub { font-size:.78rem; color:#3d8a5a; margin-top:3px; }

/* ── Suggestion cards ── */
.sug-card {
    background:#0c1e30; border:1px solid #1a3d60; border-radius:10px;
    padding:18px; height:100%;
}
.sug-card h4 { font-family:'Syne Mono',monospace; color:#4d9fd6;
    margin:0 0 10px; font-size:.95rem; }
.sug-card .badge {
    display:inline-block; background:#0f2a1a; border:1px solid #1e5c32;
    color:#4caf70; border-radius:20px; padding:2px 10px;
    font-size:.72rem; margin:3px 2px 0;
}
.sug-card p { color:#8eb0c8; font-size:.84rem; line-height:1.55; margin:8px 0 6px; }

/* ── Abas ── */
.stTabs [data-baseweb="tab-list"] {
    background:#060d18; border-bottom:2px solid #183554; gap:3px;
}
.stTabs [data-baseweb="tab"] {
    background:transparent; color:#506e86; border:1px solid transparent;
    border-radius:8px 8px 0 0; padding:10px 20px;
    font-family:'Syne Mono',monospace; font-size:.85rem; letter-spacing:.4px;
}
.stTabs [aria-selected="true"] {
    background:#0f2035 !important; color:#4d9fd6 !important;
    border-color:#1a3d60 !important; border-bottom-color:#0f2035 !important;
}

/* ── Inputs ── */
.stNumberInput input, .stTextInput input, .stSelectbox select {
    background:#0c1e30 !important; border:1px solid #1a3d60 !important;
    color:#b8ccdc !important; border-radius:6px !important;
}
/* ── Buttons ── */
.stDownloadButton button, .stButton button {
    background:linear-gradient(135deg,#122640,#1a3a60) !important;
    color:#4d9fd6 !important; border:1px solid #1a3d60 !important;
    border-radius:8px !important; font-family:'Syne Mono',monospace !important;
    letter-spacing:.4px !important; transition:all .2s !important;
}
.stDownloadButton button:hover, .stButton button:hover {
    background:linear-gradient(135deg,#1a3a60,#1e5080) !important;
    border-color:#4d9fd6 !important;
    box-shadow:0 0 14px rgba(77,159,214,.25) !important;
}
/* ── Expander ── */
.streamlit-expanderHeader {
    background:#0c1e30 !important; border:1px solid #1a3d60 !important;
    border-radius:8px !important; color:#4d9fd6 !important;
    font-family:'Syne Mono',monospace !important;
}
/* ── Data editor / table ── */
.stDataFrame, .stDataEditor { border:1px solid #1a3d60 !important;
    border-radius:8px !important; }
/* ── Divider ── */
hr { border-color:#183554 !important; margin:24px 0 !important; }
/* ── Scrollbar ── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#060d18; }
::-webkit-scrollbar-thumb { background:#1a3d60; border-radius:3px; }
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════
# [C] CONSTANTES E DADOS-PADRÃO
# ═══════════════════════════════════════════════════════════════════════════

JSON_PATH: str = "sugestoes_mercado.json"

TIPOS_APLICACAO: list[str] = ["Piso/Fundação", "Alvenaria/Reboco", "Ambos"]

COLUNAS_INSUMOS: list[str] = [
    "Insumo",
    "Unidade",
    "Custo Unitário (R$)",
    "Tipo de Aplicação",
    "Índice Técnico / m²",
]

# Projeto-exemplo para cold start
COMODOS_PADRAO: list[dict] = [
    {"Nome": "Sala",            "Largura (m)": 4.0, "Comprimento (m)": 4.0},
    {"Nome": "Quarto Principal","Largura (m)": 3.0, "Comprimento (m)": 3.0},
    {"Nome": "Cozinha",         "Largura (m)": 3.0, "Comprimento (m)": 2.5},
    {"Nome": "Banheiro",        "Largura (m)": 2.0, "Comprimento (m)": 1.5},
]

# Tabela de insumos-base (perfil Intermediário por padrão)
INSUMOS_PADRAO: list[dict] = [
    {"Insumo": "Mão de Obra - Piso",      "Unidade": "hora",    "Custo Unitário (R$)": 65.00, "Tipo de Aplicação": "Piso/Fundação",    "Índice Técnico / m²": 3.0},
    {"Insumo": "Mão de Obra - Alvenaria", "Unidade": "hora",    "Custo Unitário (R$)": 65.00, "Tipo de Aplicação": "Alvenaria/Reboco", "Índice Técnico / m²": 6.0},
    {"Insumo": "Cimento CP II",           "Unidade": "kg",      "Custo Unitário (R$)": 0.85,  "Tipo de Aplicação": "Ambos",            "Índice Técnico / m²": 12.0},
    {"Insumo": "Areia Média Lavada",      "Unidade": "m³",      "Custo Unitário (R$)": 110.00,"Tipo de Aplicação": "Ambos",            "Índice Técnico / m²": 0.04},
    {"Insumo": "Brita 1",                 "Unidade": "m³",      "Custo Unitário (R$)": 130.00,"Tipo de Aplicação": "Piso/Fundação",    "Índice Técnico / m²": 0.03},
    {"Insumo": "Blocos Cerâmicos",        "Unidade": "unidade", "Custo Unitário (R$)": 1.40,  "Tipo de Aplicação": "Alvenaria/Reboco", "Índice Técnico / m²": 18.0},
]

SUGESTOES_PADRAO: dict = {
    "versao": "1.0",
    "descricao": "Sugestões de materiais sustentáveis e tendências de mercado para ObraCalc.",
    "sugestoes": [
        {
            "categoria": "Sustentabilidade",
            "icone": "🌿",
            "titulo": "Bloco de Concreto com Agregado Reciclado",
            "descricao": (
                "Substitui o bloco cerâmico convencional. Fabricado com resíduos de construção "
                "e demolição (RCD), reduz a extração de argila e pode diminuir o custo em até 12%."
            ),
            "economia_estimada": "10–15%",
            "tags": ["reciclado", "estrutural", "ABNT NBR 15270"],
        },
        {
            "categoria": "Eficiência Energética",
            "icone": "⚡",
            "titulo": "Argamassa Térmica com Perlita",
            "descricao": (
                "Argamassa leve com perlita expandida oferece isolamento térmico superior "
                "ao reboco comum, reduzindo gastos com climatização artificial em até 20%."
            ),
            "economia_estimada": "15–20% (energia)",
            "tags": ["isolante", "leve", "conforto térmico"],
        },
        {
            "categoria": "Custo-Benefício",
            "icone": "💡",
            "titulo": "Steel Frame para Vedação",
            "descricao": (
                "Estrutura de perfis de aço galvanizado substitui a alvenaria de vedação. "
                "Reduz peso, tempo de obra e desperdício de argamassa em até 30%."
            ),
            "economia_estimada": "20–30% (tempo + mão de obra)",
            "tags": ["seco", "rápido", "leve"],
        },
        {
            "categoria": "Revestimentos",
            "icone": "🔲",
            "titulo": "Porcelanato Técnico Retificado 120×60",
            "descricao": (
                "Formato grande reduz o número de rejuntes, facilita limpeza e oferece "
                "aparência premium. Indicado para ambientes comerciais e residências de alto padrão."
            ),
            "economia_estimada": "-",
            "tags": ["premium", "durável", "baixa manutenção"],
        },
        {
            "categoria": "Impermeabilização",
            "icone": "💧",
            "titulo": "Manta EPDM Autoadesiva",
            "descricao": (
                "Alternativa às mantas asfálticas tradicionais, com maior durabilidade "
                "(vida útil +25 anos) e instalação simplificada sem maçarico."
            ),
            "economia_estimada": "8–12% (mão de obra)",
            "tags": ["durável", "fácil aplicação", "sustentável"],
        },
        {
            "categoria": "Tendência 2025",
            "icone": "🏡",
            "titulo": "Concreto Aparente Polido - Microcimento",
            "descricao": (
                "Microcimento sobre base existente elimina demolição de revestimentos antigos. "
                "Reduz entulho, cria estética contemporânea e é aplicável em piso e parede."
            ),
            "economia_estimada": "Reduz demolição em 100%",
            "tags": ["contemporâneo", "sem demolição", "multissuperfície"],
        },
    ],
}

# Paleta de cores para cômodos (blueprint estilizado)
CORES_COMODOS: list[str] = [
    "#0d2e50", "#0d3b30", "#2e1a40",
    "#3b1a10", "#1a3b10", "#2e2e10",
    "#10253b", "#3b1030", "#1a2e10",
]

# ═══════════════════════════════════════════════════════════════════════════
# [D] GESTÃO DO sugestoes_mercado.json
# ═══════════════════════════════════════════════════════════════════════════


def garantir_json_sugestoes() -> dict:
    """
    Garante a existência do arquivo sugestoes_mercado.json.
    Se não existir, cria-o com o conteúdo padrão de sustentabilidade.

    Retorna
    -------
    dict
        Conteúdo do JSON carregado.
    """
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(SUGESTOES_PADRAO, f, ensure_ascii=False, indent=2)
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return SUGESTOES_PADRAO


def salvar_json_sugestoes(dados: dict) -> bool:
    """
    Persiste o dicionário de sugestões no arquivo JSON.

    Parâmetros
    ----------
    dados : dict
        Dicionário com estrutura de sugestões validada.

    Retorna
    -------
    bool
        True se a gravação foi bem-sucedida, False em caso de erro.
    """
    try:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# [E] INICIALIZAÇÃO DO SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════


def inicializar_estado() -> None:
    """
    Inicializa todas as variáveis persistentes do Streamlit session_state.
    Garante o "Projeto Exemplo" no cold start, sem sobrescrever edições.
    """
    defaults: dict = {
        "comodos": pd.DataFrame(COMODOS_PADRAO),
        "df_insumos": pd.DataFrame(INSUMOS_PADRAO),
        "pe_direito": 2.80,
        "desperdicio_pct": 10,
        "nome_projeto": "Projeto Residencial - Exemplo",
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


# ═══════════════════════════════════════════════════════════════════════════
# [F] ALGORITMO HEURÍSTICO DE LAYOUT + PLANTA ABNT (MATPLOTLIB)
# ═══════════════════════════════════════════════════════════════════════════


def _calcular_posicoes(comodos: list[dict], gap: float = 0.35) -> list[dict]:
    """
    Algoritmo heurístico simples para dispor cômodos em grid adjacente.

    Estratégia: distribui os cômodos em ceil(sqrt(n)) colunas,
    calculando largura de cada coluna e altura de cada linha a partir
    das dimensões reais. Sem Bin Packing complexo - zero risco de IndexError.

    Parâmetros
    ----------
    comodos : list[dict]
        Lista com chaves 'Nome', 'Largura (m)', 'Comprimento (m)'.
    gap : float
        Espaço entre cômodos em metros.

    Retorna
    -------
    list[dict]
        Lista com as chaves originais acrescidas de 'x' e 'y' (posição de origem).
    """
    n = len(comodos)
    if n == 0:
        return []

    n_cols = max(1, math.ceil(math.sqrt(n)))
    n_rows = math.ceil(n / n_cols)

    # Largura máxima por coluna e altura máxima por linha
    col_widths: list[float] = [0.0] * n_cols
    row_heights: list[float] = [0.0] * n_rows

    for idx, c in enumerate(comodos):
        col = idx % n_cols
        row = idx // n_cols
        col_widths[col] = max(col_widths[col], float(c.get("Largura (m)", 1.0)))
        row_heights[row] = max(row_heights[row], float(c.get("Comprimento (m)", 1.0)))

    # Posições acumuladas (origem de cada coluna/linha)
    x_starts: list[float] = []
    acc = 0.0
    for w in col_widths:
        x_starts.append(acc)
        acc += w + gap

    y_starts: list[float] = []
    acc = 0.0
    for h in row_heights:
        y_starts.append(acc)
        acc += h + gap

    resultado: list[dict] = []
    for idx, c in enumerate(comodos):
        col = idx % n_cols
        row = idx // n_cols
        resultado.append({**c, "x": x_starts[col], "y": y_starts[row]})

    return resultado


def _desenhar_cota_horizontal(
    ax: plt.Axes,
    x0: float, x1: float, y_cota: float,
    valor: float, fontsize: float,
    cor: str = "#4d9fd6",
) -> None:
    """
    Desenha uma linha de cota horizontal no estilo ABNT (traço oblíquo a 45°).
    """
    tick = 0.12
    # Linha principal da cota
    ax.annotate(
        "", xy=(x1, y_cota), xytext=(x0, y_cota),
        arrowprops=dict(arrowstyle="<->", color=cor, lw=0.9),
        zorder=6,
    )
    # Traços oblíquos de limite
    for xp in (x0, x1):
        ax.plot([xp - tick / 2, xp + tick / 2],
                [y_cota - tick / 2, y_cota + tick / 2],
                color=cor, lw=1.0, zorder=7)
    ax.text(
        (x0 + x1) / 2, y_cota - 0.28,
        f"{valor:.2f} m",
        ha="center", va="top",
        fontsize=fontsize, color="#7bbde0",
        fontfamily="monospace", fontweight="bold", zorder=7,
    )


def _desenhar_cota_vertical(
    ax: plt.Axes,
    y0: float, y1: float, x_cota: float,
    valor: float, fontsize: float,
    cor: str = "#4d9fd6",
) -> None:
    """
    Desenha uma linha de cota vertical no estilo ABNT (traço oblíquo a 45°).
    """
    tick = 0.12
    ax.annotate(
        "", xy=(x_cota, y1), xytext=(x_cota, y0),
        arrowprops=dict(arrowstyle="<->", color=cor, lw=0.9),
        zorder=6,
    )
    for yp in (y0, y1):
        ax.plot([x_cota - tick / 2, x_cota + tick / 2],
                [yp - tick / 2, yp + tick / 2],
                color=cor, lw=1.0, zorder=7)
    ax.text(
        x_cota - 0.28, (y0 + y1) / 2,
        f"{valor:.2f} m",
        ha="right", va="center",
        fontsize=fontsize, color="#7bbde0",
        fontfamily="monospace", fontweight="bold",
        rotation=90, zorder=7,
    )


def plotar_planta_esquematica(df_comodos: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Gera a planta baixa esquemática com layout heurístico em grid.

    Aplica:
    - Fundo escuro estilo blueprint com grade milimetrada
    - Cada cômodo renderizado com cor e label adaptivo
    - Cotas ABNT (horizontal + vertical) por cômodo, com anti-colisão de texto
    - Cotas do bounding box total

    Parâmetros
    ----------
    df_comodos : pd.DataFrame
        DataFrame com colunas 'Nome', 'Largura (m)', 'Comprimento (m)'.

    Retorna
    -------
    Optional[plt.Figure]
        Figura ou None se não houver cômodos válidos.
    """
    registros = df_comodos.dropna(subset=["Nome", "Largura (m)", "Comprimento (m)"]).to_dict("records")
    # Filtra dimensões inválidas
    registros = [
        r for r in registros
        if float(r.get("Largura (m)", 0)) > 0 and float(r.get("Comprimento (m)", 0)) > 0
    ]
    if not registros:
        return None

    posicoes = _calcular_posicoes(registros)

    # Bounding box total para dimensionar eixos
    max_x = max(p["x"] + float(p["Largura (m)"]) for p in posicoes)
    max_y = max(p["y"] + float(p["Comprimento (m)"]) for p in posicoes)

    margem = 1.8  # margem para cotas externas
    fig_w = min(12, max(7, max_x + 2 * margem + 1))
    fig_h = min(10, max(6, max_y + 2 * margem + 1))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("#030a15")
    ax.set_facecolor("#05111e")

    # ── Grade milimetrada ──────────────────────────────────────────────
    passo_grade = max(0.5, round(max(max_x, max_y) / 20, 1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(passo_grade / 5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(passo_grade / 5))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(passo_grade))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(passo_grade))
    ax.grid(which="major", color="#0c2235", lw=0.5, ls="-")
    ax.grid(which="minor", color="#071528", lw=0.25, ls="-")
    ax.set_axisbelow(True)

    ax.set_xlim(-margem, max_x + margem)
    ax.set_ylim(-margem, max_y + margem)
    ax.set_aspect("equal")

    # ── Renderização dos cômodos ───────────────────────────────────────
    for idx, pos in enumerate(posicoes):
        w = float(pos["Largura (m)"])
        h = float(pos["Comprimento (m)"])
        x, y = pos["x"], pos["y"]
        nome = str(pos.get("Nome", f"Cômodo {idx+1}"))
        cor_fundo = CORES_COMODOS[idx % len(CORES_COMODOS)]
        area_com = w * h

        # Retângulo do cômodo
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="square,pad=0",
            facecolor=cor_fundo, edgecolor="#3a7ab5",
            linewidth=2.2, zorder=3,
        )
        ax.add_patch(rect)

        # Hachura interna discreta
        rect_h = plt.Polygon(
            [(x, y), (x+w, y), (x+w, y+h), (x, y+h)],
            closed=True, fill=False, hatch="///",
            edgecolor="#0d2238", lw=0, zorder=2,
        )
        ax.add_patch(rect_h)

        # ── Labels adaptativos (anti-colisão) ─────────────────────────
        # Tamanho de fonte proporcional ao menor lado do cômodo
        min_dim = min(w, h)
        fs_nome = max(6.0, min(9.5, min_dim * 3.2))
        fs_dim  = max(5.5, min(8.5, min_dim * 2.8))

        # Nome do cômodo (linha 1)
        ax.text(
            x + w / 2, y + h / 2 + h * 0.12,
            nome,
            ha="center", va="center",
            fontsize=fs_nome, color="#9dd4f0",
            fontfamily="monospace", fontweight="bold",
            zorder=5,
            clip_on=True,
        )
        # Dimensões (linha 2)
        ax.text(
            x + w / 2, y + h / 2 - h * 0.14,
            f"{w:.1f}×{h:.1f} m  |  {area_com:.1f}m²",
            ha="center", va="center",
            fontsize=fs_dim, color="#5a8ab0",
            fontfamily="monospace",
            zorder=5,
            clip_on=True,
        )

        # ── Cotas ABNT por cômodo ─────────────────────────────────────
        offset_cota = 0.55
        # Determina se há espaço para cota inferior (evita sobreposição com bounding box)
        y_cota_inf = y - offset_cota
        _desenhar_cota_horizontal(ax, x, x + w, y_cota_inf, w,
                                   fontsize=max(5.5, fs_dim - 1.0))

        x_cota_esq = x - offset_cota
        _desenhar_cota_vertical(ax, y, y + h, x_cota_esq, h,
                                 fontsize=max(5.5, fs_dim - 1.0))

    # ── Bounding box total ─────────────────────────────────────────────
    bb_rect = plt.Polygon(
        [(0, 0), (max_x, 0), (max_x, max_y), (0, max_y)],
        closed=True, fill=False,
        edgecolor="#1e5a8c", linewidth=1.2,
        linestyle="--", zorder=1,
    )
    ax.add_patch(bb_rect)

    # Cotas do bounding box total (externas)
    offset_ext = margem * 0.65
    _desenhar_cota_horizontal(ax, 0, max_x, -offset_ext, max_x,
                               fontsize=8.5, cor="#2a7abf")
    _desenhar_cota_vertical(ax, 0, max_y, -offset_ext, max_y,
                             fontsize=8.5, cor="#2a7abf")

    # ── Títulos e rodapé ──────────────────────────────────────────────
    ax.set_title(
        "PLANTA BAIXA ESQUEMÁTICA - LAYOUT PARAMÉTRICO",
        color="#4d9fd6", fontfamily="monospace",
        fontsize=11, fontweight="bold", pad=12,
    )
    fig.text(
        0.5, 0.005,
        "ObraCalc v2.0  |  Algoritmo Heurístico Grid  |  ABNT NBR 6492  |  Escala: sem escala",
        ha="center", fontsize=7, color="#1a4060", fontfamily="monospace",
    )

    ax.tick_params(colors="#122a3d", labelsize=6.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("#0c2235")

    plt.tight_layout(pad=1.0)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# [G] GRÁFICO COMPARATIVO DE CUSTO (MATPLOTLIB)
# ═══════════════════════════════════════════════════════════════════════════


def plotar_grafico_custo_por_insumo(df_orcamento: pd.DataFrame) -> Optional[plt.Figure]:
    """
    Gera gráfico de barras horizontal mostrando o custo total por insumo.

    Parâmetros
    ----------
    df_orcamento : pd.DataFrame
        DataFrame com colunas 'Insumo' e 'Custo Total (R$)'.

    Retorna
    -------
    Optional[plt.Figure]
    """
    if df_orcamento.empty:
        return None

    df_plot = df_orcamento.sort_values("Custo Total (R$)", ascending=True).tail(12)
    n = len(df_plot)

    # Paleta degradê azul-teal
    cores = plt.cm.YlGnBu(np.linspace(0.35, 0.9, n))

    fig, ax = plt.subplots(figsize=(8, max(4, n * 0.55)))
    fig.patch.set_facecolor("#05111e")
    ax.set_facecolor("#05111e")

    barras = ax.barh(
        df_plot["Insumo"], df_plot["Custo Total (R$)"],
        color=cores, height=0.65, edgecolor="#030a15", linewidth=1.2, zorder=3,
    )

    for barra, val in zip(barras, df_plot["Custo Total (R$)"]):
        ax.text(
            val + max(df_plot["Custo Total (R$)"]) * 0.01,
            barra.get_y() + barra.get_height() / 2,
            f"R$ {val:,.0f}".replace(",", "."),
            va="center", ha="left",
            fontsize=8, color="#7bbde0", fontfamily="monospace",
        )

    ax.set_xlabel("Custo Total Estimado (R$)", color="#3a6a8a", fontsize=9,
                  fontfamily="monospace")
    ax.set_title("DISTRIBUIÇÃO DE CUSTOS POR INSUMO",
                 color="#4d9fd6", fontsize=10, fontfamily="monospace",
                 fontweight="bold", pad=10)
    ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda v, _: f"R$ {v:,.0f}".replace(",", "."))
    )
    ax.tick_params(axis="x", colors="#1a3a55", labelsize=7.5)
    ax.tick_params(axis="y", colors="#7bbde0", labelsize=8.5)
    ax.grid(axis="x", color="#0c2235", lw=0.7, ls="--", zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor("#0c2235")

    plt.tight_layout(pad=0.9)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# [H] GERAÇÃO DE PROPOSTA PDF (fpdf2)
# ═══════════════════════════════════════════════════════════════════════════


def _fig_para_bytes(fig: plt.Figure, dpi: int = 150) -> io.BytesIO:
    """Serializa uma figura Matplotlib para BytesIO PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf


def gerar_pdf(
    nome_projeto: str,
    metricas: dict,
    df_orcamento: pd.DataFrame,
    fig_planta: Optional[plt.Figure],
    fig_custos: Optional[plt.Figure],
) -> bytes:
    """
    Gera uma proposta técnica em PDF usando fpdf2.

    Estrutura do documento:
    - Capa com título e métricas
    - Planta baixa (se disponível)
    - Tabela de orçamento detalhado
    - Gráfico de distribuição de custos

    Parâmetros
    ----------
    nome_projeto : str
        Nome do projeto exibido no cabeçalho.
    metricas : dict
        Dicionário com chaves: area_piso, area_parede, perimetro,
        pe_direito, custo_total, desperdicio_pct.
    df_orcamento : pd.DataFrame
        Tabela consolidada de orçamento.
    fig_planta : Optional[plt.Figure]
        Figura da planta baixa para embed.
    fig_custos : Optional[plt.Figure]
        Figura do gráfico de custos para embed.

    Retorna
    -------
    bytes
        Conteúdo binário do PDF gerado.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)

    # ── Fonte padrão ──────────────────────────────────────────────────
    # fpdf2 usa fontes nativas; 'Helvetica' suporta ASCII+Latin
    # Para acentos brasileiros, substituímos caracteres problemáticos
    def tx(texto: str) -> str:
        """Sanitiza texto para compatibilidade com fpdf2 sem fontes externas."""
        substituicoes = {
            "ã": "a", "â": "a", "á": "a", "à": "a", "ä": "a",
            "ê": "e", "é": "e", "è": "e", "ë": "e",
            "í": "i", "î": "i", "ì": "i",
            "õ": "o", "ô": "o", "ó": "o", "ò": "o", "ö": "o",
            "ú": "u", "û": "u", "ù": "u", "ü": "u",
            "ç": "c", "ñ": "n",
            "Ã": "A", "Â": "A", "Á": "A", "À": "A",
            "Ê": "E", "É": "E",
            "Í": "I", "Î": "I",
            "Õ": "O", "Ô": "O", "Ó": "O",
            "Ú": "U", "Û": "U",
            "Ç": "C",
        }
        for orig, sub in substituicoes.items():
            texto = texto.replace(orig, sub)
        return texto

    # ── Página 1: Capa e Métricas ──────────────────────────────────────
    pdf.add_page()

    # Cabeçalho principal
    pdf.set_fill_color(6, 13, 24)
    pdf.rect(0, 0, 210, 45, "F")
    pdf.set_xy(15, 12)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(77, 159, 214)
    pdf.cell(0, 10, "ObraCalc - Proposta Tecnica", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(15, 24)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 110, 134)
    pdf.cell(0, 8, tx(nome_projeto), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(15, 34)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(40, 70, 100)
    pdf.cell(0, 6,
             "Sistema Inteligente para Calculo e Orcamento de Obras - MVP v2.0",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(12)

    # Linha separadora
    pdf.set_draw_color(26, 61, 96)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # Bloco de métricas
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(77, 159, 214)
    pdf.cell(0, 8, "METRICAS DO PROJETO", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    col_w = 87.5
    dados_metricas = [
        ("Area de Piso Total",      f"{metricas.get('area_piso', 0):.2f} m2"),
        ("Perimetro Interno Total", f"{metricas.get('perimetro', 0):.2f} m"),
        ("Pe-direito",              f"{metricas.get('pe_direito', 2.80):.2f} m"),
        ("Area de Parede Total",    f"{metricas.get('area_parede', 0):.2f} m2"),
        ("Margem de Desperdicio",   f"{metricas.get('desperdicio_pct', 10)}%"),
        ("CUSTO TOTAL ESTIMADO",    f"R$ {metricas.get('custo_total', 0):,.2f}".replace(",", ".")),
    ]

    for i, (lbl, val) in enumerate(dados_metricas):
        y_pos = pdf.get_y()
        col = i % 2
        x_pos = 15 + col * col_w

        fill = (12, 30, 48) if i % 2 == 0 else (9, 22, 37)
        pdf.set_fill_color(*fill)
        pdf.set_xy(x_pos, y_pos)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 110, 134)
        pdf.cell(col_w - 2, 5, tx(lbl), fill=True, new_x="RIGHT", new_y="TOP")

        pdf.set_xy(x_pos, y_pos + 5)
        pdf.set_font("Helvetica", "B", 11)
        is_custo = "CUSTO" in lbl
        pdf.set_text_color(77, 180, 77) if is_custo else pdf.set_text_color(180, 204, 220)
        pdf.cell(col_w - 2, 7, tx(val), fill=True, new_x="RIGHT", new_y="TOP")

        if col == 1 or i == len(dados_metricas) - 1:
            pdf.set_xy(15, y_pos + 13)

    pdf.ln(10)
    pdf.set_draw_color(26, 61, 96)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # ── Planta Baixa ──────────────────────────────────────────────────
    if fig_planta is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(77, 159, 214)
        pdf.cell(0, 8, "PLANTA BAIXA ESQUEMATICA", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        try:
            buf_planta = _fig_para_bytes(fig_planta, dpi=120)
            pdf.image(buf_planta, x=15, y=None, w=180)
        except Exception:
            pdf.set_text_color(160, 80, 80)
            pdf.cell(0, 8, "[Erro ao renderizar planta]", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

    # ── Página 2: Tabela de Orçamento ──────────────────────────────────
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(77, 159, 214)
    pdf.cell(0, 10, "ORCAMENTO DETALHADO", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if not df_orcamento.empty:
        # Cabeçalho da tabela
        colunas_pdf = ["Insumo", "Unid.", "Qtd. c/ Desp.", "Custo Unit.", "Custo Total"]
        larguras = [65, 18, 30, 32, 35]

        pdf.set_fill_color(9, 21, 38)
        pdf.set_text_color(77, 159, 214)
        pdf.set_font("Helvetica", "B", 8)
        for col_nome, larg in zip(colunas_pdf, larguras):
            pdf.cell(larg, 8, col_nome, border=1, align="C", fill=True)
        pdf.ln()

        # Linhas da tabela
        pdf.set_font("Helvetica", "", 7.5)
        for i, (_, row) in enumerate(df_orcamento.iterrows()):
            fill_color = (12, 30, 48) if i % 2 == 0 else (8, 18, 30)
            pdf.set_fill_color(*fill_color)
            pdf.set_text_color(184, 204, 220)

            insumo = tx(str(row.get("Insumo", "")))[:38]
            unid   = tx(str(row.get("Unidade", "")))[:8]
            qtd    = f"{row.get('Qtd. c/ Desperdicio', 0):.3f}"
            c_unit = f"R$ {row.get('Custo Unit. (R$)', 0):.2f}"
            c_tot  = f"R$ {row.get('Custo Total (R$)', 0):,.2f}".replace(",", ".")

            for val, larg, alg in zip(
                [insumo, unid, qtd, c_unit, c_tot],
                larguras,
                ["L", "C", "R", "R", "R"],
            ):
                pdf.cell(larg, 7, val, border=1, align=alg, fill=True)
            pdf.ln()

        # Totalizador
        total = df_orcamento["Custo Total (R$)"].sum()
        pdf.set_fill_color(6, 20, 40)
        pdf.set_text_color(77, 210, 100)
        pdf.set_font("Helvetica", "B", 9)
        soma_larguras = sum(larguras[:-1])
        pdf.cell(soma_larguras, 9, "TOTAL GERAL", border=1, align="R", fill=True)
        pdf.cell(larguras[-1], 9,
                 f"R$ {total:,.2f}".replace(",", "."),
                 border=1, align="R", fill=True)
        pdf.ln()

    pdf.ln(10)

    # ── Gráfico de Custos ──────────────────────────────────────────────
    if fig_custos is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(77, 159, 214)
        pdf.cell(0, 8, "DISTRIBUICAO DE CUSTOS POR INSUMO", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        try:
            buf_custos = _fig_para_bytes(fig_custos, dpi=110)
            espaco_restante = 297 - 15 - pdf.get_y()
            altura_img = min(120.0, max(60.0, float(espaco_restante) - 10.0))
            pdf.image(buf_custos, x=15, y=None, w=180, h=altura_img)
        except Exception:
            pass

    # ── Rodapé ────────────────────────────────────────────────────────
    pdf.set_y(-15)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(30, 64, 100)
    pdf.cell(
        0, 5,
        "ObraCalc MVP v2.0 - Valores estimados. Consulte profissional habilitado para validacao.",
        align="C",
    )

    return bytes(pdf.output())


# ═══════════════════════════════════════════════════════════════════════════
# [I] HELPERS DE AGGRID, CÁLCULO E CSV
# ═══════════════════════════════════════════════════════════════════════════


def construir_aggrid(df: pd.DataFrame, altura: int = 380) -> pd.DataFrame:
    """
    Configura e renderiza o AgGrid editável para a tabela de insumos.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame de insumos a ser exibido e editado.
    altura : int
        Altura em pixels do componente AgGrid.

    Retorna
    -------
    pd.DataFrame
        DataFrame atualizado com as edições do usuário.
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        editable=True,
        resizable=True,
        sortable=True,
        filter=True,
        min_width=80,
    )
    gb.configure_column(
        "Insumo", min_width=180, pinned="left",
        headerTooltip="Nome do material ou serviço",
    )
    gb.configure_column(
        "Unidade", width=100,
        headerTooltip="Unidade de medida (kg, m², hora...)",
    )
    gb.configure_column(
        "Custo Unitário (R$)", width=150, type=["numericColumn"],
        valueFormatter="'R$ ' + value.toFixed(2)",
        headerTooltip="Custo por unidade na sua região (sem desperdício)",
    )
    gb.configure_column(
        "Tipo de Aplicação", width=160,
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": TIPOS_APLICACAO},
        headerTooltip="Define se o índice se aplica ao piso, parede ou ambos",
    )
    gb.configure_column(
        "Índice Técnico / m²", width=160, type=["numericColumn"],
        headerTooltip="Quantidade teórica de insumo por m² de área de referência (TCPO/SINAPI)",
    )
    gb.configure_grid_options(stopEditingWhenCellsLoseFocus=True, rowHeight=34)

    grid_response = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
        theme="alpine",
        height=altura,
        allow_unsafe_jscode=True,
        key="aggrid_insumos",
    )
    df_ret = grid_response.get("data")
    if df_ret is None or (isinstance(df_ret, pd.DataFrame) and df_ret.empty):
        return df
    return pd.DataFrame(df_ret)


def calcular_metricas_geometricas(df_comodos: pd.DataFrame, pe_direito: float) -> dict:
    """
    Calcula métricas geométricas globais a partir da tabela de cômodos.

    Parâmetros
    ----------
    df_comodos : pd.DataFrame
        Cômodos com 'Largura (m)' e 'Comprimento (m)'.
    pe_direito : float
        Altura do pé-direito em metros.

    Retorna
    -------
    dict
        Dicionário com area_piso, perimetro, area_parede, pe_direito.
    """
    df_valido = df_comodos.dropna(subset=["Largura (m)", "Comprimento (m)"])
    df_valido = df_valido[
        (pd.to_numeric(df_valido["Largura (m)"], errors="coerce") > 0)
        & (pd.to_numeric(df_valido["Comprimento (m)"], errors="coerce") > 0)
    ].copy()

    df_valido["Largura (m)"]      = pd.to_numeric(df_valido["Largura (m)"])
    df_valido["Comprimento (m)"]  = pd.to_numeric(df_valido["Comprimento (m)"])
    df_valido["_area"]    = df_valido["Largura (m)"] * df_valido["Comprimento (m)"]
    df_valido["_perim"]   = 2 * (df_valido["Largura (m)"] + df_valido["Comprimento (m)"])

    area_piso  = float(df_valido["_area"].sum())
    perimetro  = float(df_valido["_perim"].sum())
    area_parede = perimetro * pe_direito

    return {
        "area_piso":   area_piso,
        "perimetro":   perimetro,
        "area_parede": area_parede,
        "pe_direito":  pe_direito,
    }


def calcular_orcamento(
    df_insumos: pd.DataFrame,
    metricas: dict,
    desperdicio_pct: int,
) -> pd.DataFrame:
    """
    Gera o orçamento cruzando índices técnicos, tipo de aplicação e preços.

    Regras de base de cálculo:
    - 'Piso/Fundação'    → usa area_piso
    - 'Alvenaria/Reboco' → usa area_parede (perímetro × pé-direito)
    - 'Ambos'            → usa area_piso + area_parede

    Parâmetros
    ----------
    df_insumos : pd.DataFrame
        Tabela de insumos com preços e índices.
    metricas : dict
        Saída de calcular_metricas_geometricas().
    desperdicio_pct : int
        Percentual de desperdício (5, 10 ou 15).

    Retorna
    -------
    pd.DataFrame
        Orçamento consolidado com quantidades e custos.
    """
    if df_insumos.empty or metricas["area_piso"] <= 0:
        return pd.DataFrame()

    fator = 1.0 + desperdicio_pct / 100.0
    area_piso   = metricas["area_piso"]
    area_parede = metricas["area_parede"]

    linhas: list[dict] = []
    for _, row in df_insumos.iterrows():
        tipo = str(row.get("Tipo de Aplicação", "Ambos"))
        if tipo == "Piso/Fundação":
            base = area_piso
        elif tipo == "Alvenaria/Reboco":
            base = area_parede
        else:  # Ambos
            base = area_piso + area_parede

        try:
            indice   = float(row.get("Índice Técnico / m²", 0))
            cu       = float(row.get("Custo Unitário (R$)", 0))
        except (ValueError, TypeError):
            continue

        if indice <= 0 or cu <= 0:
            continue

        qtd_teorica = base * indice
        qtd_desp    = qtd_teorica * fator
        custo_total = qtd_desp * cu

        linhas.append({
            "Insumo":              str(row.get("Insumo", "-")),
            "Unidade":             str(row.get("Unidade", "-")),
            "Tipo":                tipo,
            "Base de Cálculo (m²)": round(base, 2),
            "Qtd. Teórica":        round(qtd_teorica, 3),
            "Qtd. c/ Desperdicio": round(qtd_desp, 3),
            "Custo Unit. (R$)":    round(cu, 2),
            "Custo Total (R$)":    round(custo_total, 2),
        })

    return pd.DataFrame(linhas)


def carregar_csv_insumos(arquivo) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Importa CSV de insumos com tratamento de codificação e separador decimal.

    Parâmetros
    ----------
    arquivo : UploadedFile
        Arquivo CSV do st.file_uploader.

    Retorna
    -------
    tuple[Optional[pd.DataFrame], Optional[str]]
        (DataFrame, None) em sucesso ou (None, mensagem_erro).
    """
    conteudo = arquivo.read()
    df: Optional[pd.DataFrame] = None

    for enc in ("utf-8", "utf-8-sig", "latin1"):
        try:
            df = pd.read_csv(io.BytesIO(conteudo), encoding=enc,
                             sep=None, engine="python")
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue

    if df is None:
        return None, "❌ Não foi possível decodificar o arquivo. Use UTF-8 ou latin1."

    faltando = set(COLUNAS_INSUMOS) - set(df.columns)
    if faltando:
        return None, f"❌ Colunas ausentes: {', '.join(faltando)}"

    col = "Custo Unitário (R$)"
    if df[col].dtype == object:
        df[col] = (
            df[col].astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    col2 = "Índice Técnico / m²"
    if df[col2].dtype == object:
        df[col2] = (
            df[col2].astype(str)
            .str.replace(",", ".", regex=False)
        )
    df[col2] = pd.to_numeric(df[col2], errors="coerce").fillna(0.0)

    return df, None


# ═══════════════════════════════════════════════════════════════════════════
# [J] ABAS DA INTERFACE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

# ─── J.1  Header e Métricas Rápidas ────────────────────────────────────────


def renderizar_header() -> None:
    """Renderiza o cabeçalho principal com identidade visual blueprint."""
    st.markdown(
        f"""
        <div class="oc-header">
            <h1>🏗️ ObraCalc</h1>
            <p>Sistema Inteligente e Paramétrico para Cálculo e Orçamento de Obras · MVP v2.0</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_cards(metricas: dict, custo_total: float, desperdicio: int) -> None:
    """
    Exibe os cards de métricas rápidas no topo da tela de resultados.

    Parâmetros
    ----------
    metricas : dict
        Dicionário de métricas geométricas.
    custo_total : float
        Custo total estimado em R$.
    desperdicio : int
        Percentual de desperdício configurado.
    """
    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "📐 Área de Piso",    f"{metricas['area_piso']:.2f} m²",    "Soma das áreas dos cômodos"),
        (c2, "📏 Perímetro Total", f"{metricas['perimetro']:.2f} m",      "Soma dos perímetros internos"),
        (c3, "🧱 Área de Parede",  f"{metricas['area_parede']:.2f} m²",  f"Pé-direito: {metricas['pe_direito']:.2f} m"),
        (c4, "🔧 Desperdício",     f"{desperdicio}%",                      "Margem adicionada à quantidade teórica"),
        (c5, "💰 Custo Estimado",  f"R$ {custo_total:,.0f}".replace(",", "."), "Soma total com desperdício"),
    ]
    for col, lbl, val, sub in cards:
        with col:
            st.markdown(
                f"""<div class="oc-card">
                    <div class="lbl">{lbl}</div>
                    <div class="val">{val}</div>
                    <div class="sub">{sub}</div>
                </div>""",
                unsafe_allow_html=True,
            )


# ─── J.2  Aba 1: Gerenciador de Cômodos ───────────────────────────────────


def aba_gerenciador() -> None:
    """
    Aba 1 - Gerenciador Paramétrico de Cômodos.

    Permite adicionar/editar cômodos via st.data_editor com num_rows='dynamic'.
    Exibe a planta baixa gerada pelo algoritmo heurístico em tempo real.
    """
    st.markdown("### 📐 Gerenciador de Cômodos")
    st.caption(
        "Adicione, edite ou remova cômodos diretamente na tabela. "
        "A planta baixa e o orçamento são atualizados automaticamente."
    )

    col_cfg, col_plot = st.columns([1, 2], gap="large")

    with col_cfg:
        # ── Nome do projeto ──
        nome = st.text_input(
            "Nome do Projeto",
            value=st.session_state["nome_projeto"],
            help="Identificação do projeto, exibida na proposta PDF.",
        )
        st.session_state["nome_projeto"] = nome

        # ── Pé-direito ──
        pe = st.number_input(
            "Pé-direito (m)",
            min_value=2.0,
            max_value=6.0,
            value=float(st.session_state["pe_direito"]),
            step=0.05,
            format="%.2f",
            help=(
                "Altura do teto ao piso (padrão NBR: 2,50 m mínimo residencial). "
                "Afeta diretamente a área de parede para alvenaria e reboco."
            ),
        )
        st.session_state["pe_direito"] = pe

        st.markdown("---")
        st.markdown("**📋 Cômodos do Projeto**")
        st.caption(
            "Edite células, adicione linhas (+) ou exclua com a checkbox lateral. "
            "Dimensões mínimas: 0.5 m."
        )

        df_comodos_editado = st.data_editor(
            st.session_state["comodos"],
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Nome": st.column_config.TextColumn(
                    "Nome do Cômodo",
                    help="Ex: Sala, Quarto, Banheiro, Garagem.",
                    max_chars=40,
                ),
                "Largura (m)": st.column_config.NumberColumn(
                    "Largura (m)",
                    min_value=0.5,
                    max_value=99.0,
                    step=0.1,
                    format="%.2f",
                    help="Largura interna do cômodo em metros. Mínimo: 0,5 m.",
                ),
                "Comprimento (m)": st.column_config.NumberColumn(
                    "Comprimento (m)",
                    min_value=0.5,
                    max_value=99.0,
                    step=0.1,
                    format="%.2f",
                    help="Comprimento interno do cômodo em metros. Mínimo: 0,5 m.",
                ),
            },
            hide_index=True,
            height=320,
            key="editor_comodos",
        )

        # Persiste, filtrando linhas completamente vazias
        df_comodos_editado = df_comodos_editado.dropna(
            subset=["Nome", "Largura (m)", "Comprimento (m)"], how="all"
        )
        st.session_state["comodos"] = df_comodos_editado

        # ── Totais rápidos ──
        metricas = calcular_metricas_geometricas(df_comodos_editado, pe)
        n_comodos = len(
            df_comodos_editado.dropna(
                subset=["Largura (m)", "Comprimento (m)"]
            )
        )
        st.metric("Cômodos válidos",  n_comodos)
        st.metric("Área de Piso",     f"{metricas['area_piso']:.2f} m²")
        st.metric("Área de Parede",   f"{metricas['area_parede']:.2f} m²",
                  help="Perímetro × Pé-direito.")

    with col_plot:
        st.markdown("**🏠 Planta Baixa - Layout Heurístico Grid (ABNT)**")
        df_valido = st.session_state["comodos"].dropna(
            subset=["Nome", "Largura (m)", "Comprimento (m)"]
        )
        if df_valido.empty:
            st.info("ℹ️ Adicione ao menos um cômodo com dimensões válidas para exibir a planta.")
        else:
            with st.spinner("Renderizando planta..."):
                fig = plotar_planta_esquematica(df_valido)
            if fig is not None:
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                st.warning("⚠️ Não foi possível renderizar a planta. Verifique as dimensões.")


# ─── J.3  Aba 2: Tabela de Preços com AgGrid ──────────────────────────────


def aba_precos() -> None:
    """
    Aba 2 - Tabela de Preços Locais com AgGrid editável.

    Suporta importação/exportação CSV e seleção de margem de desperdício.
    """
    st.markdown("### 💲 Tabela de Preços Locais")
    st.caption(
        "Edite os valores diretamente na grid. "
        "Os índices técnicos seguem referências SINAPI/TCPO e podem ser ajustados."
    )

    # ── Controles superiores ──────────────────────────────────────────
    col_desp, col_imp, col_exp, col_tpl = st.columns([1, 1, 1, 1])

    with col_desp:
        desp = st.select_slider(
            "Margem de Desperdício",
            options=[5, 10, 15],
            value=st.session_state["desperdicio_pct"],
            format_func=lambda v: f"{v}%",
            help=(
                "Fator adicional aplicado sobre as quantidades teóricas. "
                "5% = obras simples; 10% = padrão; 15% = obras complexas ou remodelações."
            ),
        )
        st.session_state["desperdicio_pct"] = desp

    with col_tpl:
        tpl_bytes = st.session_state["df_insumos"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Template CSV",
            data=tpl_bytes,
            file_name="template_insumos_obra.csv",
            mime="text/csv",
            help="Baixe o modelo CSV para preencher com preços da sua região.",
            use_container_width=True,
        )

    with col_imp:
        arq = st.file_uploader(
            "📂 Importar CSV",
            type=["csv"],
            help="CSV com colunas: Insumo, Unidade, Custo Unitário (R$), Tipo de Aplicação, Índice Técnico / m².",
            label_visibility="collapsed",
        )
        if arq:
            df_imp, erro = carregar_csv_insumos(arq)
            if erro:
                st.error(erro)
            else:
                st.session_state["df_insumos"] = df_imp
                st.success(f"✅ {len(df_imp)} insumos importados.")

    with col_exp:
        exp_bytes = st.session_state["df_insumos"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "📤 Exportar CSV",
            data=exp_bytes,
            file_name="insumos_atualizados.csv",
            mime="text/csv",
            help="Salve a tabela atual (com suas edições) em CSV.",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown(
        "**💡 Dica:** Clique em qualquer célula para editar. "
        "Arraste o cabeçalho para reordenar colunas. "
        "Use o ícone de filtro para pesquisar insumos."
    )

    # ── AgGrid ───────────────────────────────────────────────────────
    df_atualizado = construir_aggrid(st.session_state["df_insumos"])
    if df_atualizado is not None and not df_atualizado.empty:
        # Garante que colunas numéricas sejam float após edição
        for col_num in ["Custo Unitário (R$)", "Índice Técnico / m²"]:
            if col_num in df_atualizado.columns:
                df_atualizado[col_num] = pd.to_numeric(
                    df_atualizado[col_num], errors="coerce"
                ).fillna(0.0)
        st.session_state["df_insumos"] = df_atualizado

    st.markdown("---")
    c_i1, c_i2, c_i3 = st.columns(3)
    c_i1.metric("Total de Insumos", len(st.session_state["df_insumos"]))
    c_i2.metric(
        "Piso/Fundação",
        len(st.session_state["df_insumos"][
            st.session_state["df_insumos"]["Tipo de Aplicação"] == "Piso/Fundação"
        ]),
    )
    c_i3.metric(
        "Alvenaria/Reboco",
        len(st.session_state["df_insumos"][
            st.session_state["df_insumos"]["Tipo de Aplicação"] == "Alvenaria/Reboco"
        ]),
    )


# ─── J.4  Aba 3: Resultados e Orçamento ───────────────────────────────────


def aba_resultados() -> None:
    """
    Aba 3 - Dashboard de Resultados.

    Exibe métricas, tabela de orçamento detalhada e
    gráfico de distribuição de custos por insumo.
    """
    st.markdown("### 📊 Resultados e Orçamento")

    metricas = calcular_metricas_geometricas(
        st.session_state["comodos"],
        st.session_state["pe_direito"],
    )

    if metricas["area_piso"] <= 0:
        st.warning(
            "⚠️ Nenhuma área válida calculada. "
            "Verifique os cômodos na aba **Gerenciador de Cômodos**.",
            icon="⚠️",
        )
        return

    df_orcamento = calcular_orcamento(
        st.session_state["df_insumos"],
        metricas,
        st.session_state["desperdicio_pct"],
    )
    custo_total = float(df_orcamento["Custo Total (R$)"].sum()) if not df_orcamento.empty else 0.0

    # ── Cards de métricas ─────────────────────────────────────────────
    renderizar_cards(metricas, custo_total, st.session_state["desperdicio_pct"])
    st.markdown("---")

    col_tab, col_graf = st.columns([3, 2], gap="large")

    with col_tab:
        st.markdown("#### 📋 Orçamento Detalhado")
        st.caption(
            f"Desperdício: {st.session_state['desperdicio_pct']}%  ·  "
            f"Área piso: {metricas['area_piso']:.2f} m²  ·  "
            f"Área parede: {metricas['area_parede']:.2f} m²"
        )

        if df_orcamento.empty:
            st.info(
                "ℹ️ O orçamento está vazio. "
                "Verifique se a tabela de preços possui insumos com custo e índice > 0."
            )
        else:
            # Tabela de exibição formatada
            df_exib = df_orcamento.copy()
            df_exib["Custo Unit. (R$)"] = df_exib["Custo Unit. (R$)"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", ".")
            )
            df_exib["Custo Total (R$)"] = df_exib["Custo Total (R$)"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", ".")
            )
            st.dataframe(
                df_exib,
                use_container_width=True,
                hide_index=True,
                height=420,
                column_config={
                    "Insumo":              st.column_config.TextColumn("Insumo", width="medium"),
                    "Tipo":                st.column_config.TextColumn("Tipo", width="small"),
                    "Qtd. Teórica":        st.column_config.NumberColumn("Qtd. Teórica", format="%.3f"),
                    "Qtd. c/ Desperdicio": st.column_config.NumberColumn("Qtd. c/ Desp.", format="%.3f"),
                },
            )

            # Custo total destacado
            st.markdown(
                f"""<div class="oc-card" style="border-left-color:#3db86c;margin-top:10px">
                    <div class="lbl">💰 Custo Total Consolidado</div>
                    <div class="val" style="color:#3db86c">
                        R$ {custo_total:,.2f}
                    </div>
                    <div class="sub">
                        R$ {(custo_total / metricas['area_piso']):.2f}/m²
                        (referência: SINAPI/PINI)
                    </div>
                </div>""".replace(",", "."),
                unsafe_allow_html=True,
            )

            # Exportar orçamento
            csv_orc = df_orcamento.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar Orçamento CSV",
                data=csv_orc,
                file_name=f"orcamento_{st.session_state['nome_projeto'].replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_graf:
        st.markdown("#### 📊 Distribuição por Insumo")
        if not df_orcamento.empty:
            fig_custo = plotar_grafico_custo_por_insumo(df_orcamento)
            if fig_custo:
                st.pyplot(fig_custo, use_container_width=True)
                plt.close(fig_custo)
        else:
            st.info("O gráfico aparecerá após o cálculo do orçamento.")

    # ── Sugestões do JSON ─────────────────────────────────────────────
    st.markdown("---")
    dados_json = garantir_json_sugestoes()
    sugestoes = dados_json.get("sugestoes", [])

    if sugestoes:
        st.markdown("#### 💡 Sugestões de Mercado e Sustentabilidade")
        st.caption("Dados carregados de `sugestoes_mercado.json` - editável na aba Proposta PDF.")
        cols = st.columns(min(3, len(sugestoes)))
        for i, sug in enumerate(sugestoes[:6]):
            with cols[i % len(cols)]:
                tags_html = "".join(
                    f'<span class="badge">{t}</span>'
                    for t in sug.get("tags", [])
                )
                st.markdown(
                    f"""<div class="sug-card">
                        <h4>{sug.get('icone','💡')} {sug.get('titulo','-')}</h4>
                        <span style="font-size:.72rem;color:#3a6a8a;
                            font-family:\'Syne Mono\',monospace;letter-spacing:1px;">
                            {sug.get('categoria','').upper()}
                        </span>
                        <p>{sug.get('descricao','')}</p>
                        <div style="font-size:.75rem;color:#4caf70;margin-bottom:6px;">
                            💰 Economia estimada: <b>{sug.get('economia_estimada','-')}</b>
                        </div>
                        {tags_html}
                    </div>""",
                    unsafe_allow_html=True,
                )


# ─── J.5  Aba 4: Proposta PDF + Admin JSON ────────────────────────────────
def tx(texto: str) -> str:
    """Sanitiza texto para compatibilidade com fpdf2 sem fontes externas."""
    texto = str(texto)
    substituicoes = {
        "ã": "a", "â": "a", "á": "a", "à": "a", "ä": "a",
        "ê": "e", "é": "e", "è": "e", "ë": "e",
        "í": "i", "î": "i", "ì": "i",
        "õ": "o", "ô": "o", "ó": "o", "ò": "o", "ö": "o",
        "ú": "u", "û": "u", "ù": "u", "ü": "u",
        "ç": "c", "ñ": "n",
        "Ã": "A", "Â": "A", "Á": "A", "À": "A",
        "Ê": "E", "É": "E",
        "Í": "I", "Î": "I",
        "Õ": "O", "Ô": "O", "Ó": "O",
        "Ú": "U", "Û": "U",
        "Ç": "C",
        "-": "-", "–": "-", "“": '"', "”": '"',
        "‘": "'", "’": "'", "•": "-", "²": "2",
        "³": "3", "º": ".", "ª": "."
    }
    for orig, sub in substituicoes.items():
        texto = texto.replace(orig, sub)
    return texto.encode('latin-1', 'ignore').decode('latin-1')

def aba_proposta_pdf() -> None:
    """
    Aba 4 - Geração de Proposta PDF e Área do Administrador (JSON).

    Gera documento PDF profissional com capa, planta, orçamento e gráficos.
    Inclui st.expander para edição direta do sugestoes_mercado.json.
    """
    st.markdown("### 📄 Proposta Técnica em PDF")
    st.caption(
        "Gere um documento profissional contendo as métricas, "
        "planta esquemática, tabela de orçamento e gráfico de custos."
    )

    metricas = calcular_metricas_geometricas(
        st.session_state["comodos"],
        st.session_state["pe_direito"],
    )

    if metricas["area_piso"] <= 0:
        st.warning(
            "⚠️ Adicione cômodos com dimensões válidas antes de gerar o PDF.",
            icon="⚠️",
        )
    else:
        df_orcamento = calcular_orcamento(
            st.session_state["df_insumos"],
            metricas,
            st.session_state["desperdicio_pct"],
        )
        custo_total = float(df_orcamento["Custo Total (R$)"].sum()) if not df_orcamento.empty else 0.0
        metricas["custo_total"] = custo_total
        metricas["desperdicio_pct"] = st.session_state["desperdicio_pct"]

        col_prev, col_btn = st.columns([3, 1])

        with col_prev:
            st.markdown(
                f"""<div class="oc-card">
                    <div class="lbl">📋 Resumo do Documento</div>
                    <div style="margin-top:8px;color:#8eb0c8;font-size:.88rem;line-height:1.7">
                        <b style="color:#4d9fd6">Projeto:</b>
                        {st.session_state['nome_projeto']}<br>
                        <b style="color:#4d9fd6">Cômodos:</b>
                        {len(st.session_state['comodos'].dropna(
                            subset=['Largura (m)','Comprimento (m)']
                        ))} ambientes<br>
                        <b style="color:#4d9fd6">Área de Piso:</b>
                        {metricas['area_piso']:.2f} m²  ·
                        <b style="color:#4d9fd6">Pé-direito:</b>
                        {metricas['pe_direito']:.2f} m<br>
                        <b style="color:#4d9fd6">Custo Estimado:</b>
                        R$ {custo_total:,.2f}
                    </div>
                </div>""".replace(",", "."),
                unsafe_allow_html=True,
            )

        with col_btn:
            gerar = st.button(
                "🔄 Gerar PDF",
                use_container_width=True,
                help=(
                    "Processa a planta, o orçamento e as métricas e compila "
                    "o documento PDF para download."
                ),
            )

        if gerar:
            with st.spinner("Compilando planta e gerando PDF... aguarde."):
                # Gera figuras para embed no PDF
                df_valido = st.session_state["comodos"].dropna(
                    subset=["Nome", "Largura (m)", "Comprimento (m)"]
                )
                fig_planta = plotar_planta_esquematica(df_valido) if not df_valido.empty else None
                fig_custos = plotar_grafico_custo_por_insumo(df_orcamento) if not df_orcamento.empty else None

                try:
                    pdf_bytes = gerar_pdf(
                        nome_projeto=st.session_state["nome_projeto"],
                        metricas=metricas,
                        df_orcamento=df_orcamento,
                        fig_planta=fig_planta,
                        fig_custos=fig_custos,
                    )
                    st.success("✅ PDF gerado com sucesso! Clique abaixo para baixar.")
                    nome_arq = (
                        st.session_state["nome_projeto"]
                        .replace(" ", "_")
                        .replace("/", "-")[:40]
                    )
                    st.download_button(
                        label="📥 Baixar Proposta PDF",
                        data=pdf_bytes,
                        file_name=f"proposta_{nome_arq}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao gerar PDF: {e}")
                finally:
                    if fig_planta:
                        plt.close(fig_planta)
                    if fig_custos:
                        plt.close(fig_custos)

    st.markdown("---")

    # ── Área do Administrador ─────────────────────────────────────────
    with st.expander("🔧 Área do Administrador - Editar sugestoes_mercado.json", expanded=False):
        st.caption(
            "Edite diretamente o JSON de sugestões de mercado. "
            "As alterações são salvas no arquivo `sugestoes_mercado.json` "
            "na pasta do projeto e refletidas imediatamente na aba Resultados."
        )
        dados_atuais = garantir_json_sugestoes()
        json_texto = st.text_area(
            "Conteúdo do JSON",
            value=json.dumps(dados_atuais, ensure_ascii=False, indent=2),
            height=420,
            help=(
                "Edite o JSON e clique em 'Salvar Alterações'. "
                "Estrutura obrigatória: objeto com chave 'sugestoes' (lista de objetos)."
            ),
        )

        col_salvar, col_reset = st.columns([1, 1])
        with col_salvar:
            if st.button("💾 Salvar Alterações", use_container_width=True):
                try:
                    dados_novos = json.loads(json_texto)
                    if "sugestoes" not in dados_novos:
                        st.error("❌ JSON inválido: chave 'sugestoes' não encontrada.")
                    elif not isinstance(dados_novos["sugestoes"], list):
                        st.error("❌ O campo 'sugestoes' deve ser uma lista.")
                    else:
                        ok = salvar_json_sugestoes(dados_novos)
                        if ok:
                            st.success(
                                f"✅ {len(dados_novos['sugestoes'])} sugestões salvas em "
                                f"`{JSON_PATH}`."
                            )
                        else:
                            st.error("❌ Erro ao gravar o arquivo JSON. Verifique permissões.")
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON inválido: {e}")

        with col_reset:
            if st.button("↩️ Restaurar Padrão", use_container_width=True):
                ok = salvar_json_sugestoes(SUGESTOES_PADRAO)
                if ok:
                    st.success("✅ JSON restaurado ao conteúdo padrão.")
                    st.rerun()

        st.markdown("**Estrutura esperada de cada item em `sugestoes`:**")
        st.code(
            json.dumps(
                {
                    "categoria": "Categoria",
                    "icone": "🔧",
                    "titulo": "Título da Sugestão",
                    "descricao": "Descrição técnica do material ou prática.",
                    "economia_estimada": "10–20%",
                    "tags": ["tag1", "tag2"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            language="json",
        )


# ═══════════════════════════════════════════════════════════════════════════
# [K] PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """
    Ponto de entrada principal da aplicação ObraCalc.

    Sequência de execução:
    1. Injeta CSS global
    2. Inicializa session_state (cold start com projeto-exemplo)
    3. Renderiza header
    4. Renderiza as 4 abas principais
    5. Renderiza rodapé técnico
    """
    # CSS global
    st.markdown(CSS, unsafe_allow_html=True)

    # Cold start - garante dados iniciais sem sobrescrever edições
    inicializar_estado()

    # Garante existência do JSON de sugestões
    garantir_json_sugestoes()

    # Header
    renderizar_header()

    # Abas
    aba1, aba2, aba3, aba4 = st.tabs([
        "📐  Gerenciador de Cômodos",
        "💲  Tabela de Preços",
        "📊  Resultados",
        "📄  Proposta PDF",
    ])

    with aba1:
        aba_gerenciador()

    with aba2:
        aba_precos()

    with aba3:
        aba_resultados()

    with aba4:
        aba_proposta_pdf()

    # Rodapé
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#1a3d5a;font-size:.75rem;"
        "font-family:\"Syne Mono\",monospace;'>"
        "ObraCalc MVP v2.0 · Streamlit · Pandas · st-aggrid · Matplotlib · fpdf2 · JSON  |  "
        "Índices de referência: SINAPI / TCPO / PINI  |  "
        "Valores são estimativas - consulte engenheiro ou arquiteto habilitado."
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
