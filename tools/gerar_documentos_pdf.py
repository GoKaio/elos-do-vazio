# -*- coding: utf-8 -*-
"""
Gerador Editorial de Documentação PDF — Elos do Vazio & GoZygrid Studios (`gerar_documentos_pdf.py`).

Gera dois documentos PDF vetoriais A4 via ReportLab + Pillow diretamente na raiz do projeto:
  1. `elos_do_vazio_exposicao.pdf`: Pôster e ficha técnica Dark Fantasy para mostras, eventos e estandes.
  2. `elos_do_vazio_guia_github.pdf`: Manual técnico de instalação (Releases/EXE e código-fonte Python).

Carrega automaticamente:
  - Logo oficial da GoZygrid Studios (`assets/logo_gozygrid.png`, downloads ou uploads).
  - Logo oficial de Elos do Vazio (`assets/logo_jogo.png`, `assets/titulo_elos_do_vazio.png`, `assets/ui/logo_elos_do_vazio.png`).
  - Sprites do protagonista (`Final/Assets/Character_Sprite_Sheet.png` ou `assets/Hero/*.png`).
  - Fundos e atlas (`Background_1.png`, `Background_2.png`, `Assets.png` ou `assets/final_pack/*` e `.zip`).

Caso qualquer imagem externa não esteja presente, renderiza placeholders vetoriais elegantes
com moldura dourada `#D97706` sem interromper a geração dos PDFs.
"""

import glob
import io
import math
import os
import sys
import zipfile

try:
    from PIL import Image as PILImage, ImageDraw as PILDraw
except ImportError as exc:
    raise SystemExit(
        "Dependência ausente: instale Pillow com `pip install pillow` para processar imagens nos PDFs."
    ) from exc

try:
    from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String, Circle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Flowable,
        Image as RLImage,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:
    raise SystemExit(
        "Dependência ausente: instale ReportLab com `pip install reportlab` para gerar os PDFs."
    ) from exc


DIR_TOOLS = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(DIR_TOOLS)
DIR_SRC = os.path.join(RAIZ, "src")
for _p in (DIR_SRC, RAIZ):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Paleta Editorial Dark Fantasy — Elos do Vazio
HEX_FUNDO = "#0B0F19"
HEX_PAINEL = "#13192B"
HEX_PAINEL_ALT = "#1A2238"
HEX_OURO = "#D97706"
HEX_OURO_CLARO = "#FDE68A"
HEX_OURO_ESCURO = "#92400E"
HEX_MARFIM = "#F8FAFC"
HEX_PRATA = "#CBD5E1"
HEX_CINZA = "#94A3B8"
HEX_CIANO = "#38BDF8"
HEX_CIANO_ESCURO = "#0369A1"

C_FUNDO = colors.HexColor(HEX_FUNDO)
C_PAINEL = colors.HexColor(HEX_PAINEL)
C_PAINEL_ALT = colors.HexColor(HEX_PAINEL_ALT)
C_OURO = colors.HexColor(HEX_OURO)
C_OURO_CLARO = colors.HexColor(HEX_OURO_CLARO)
C_OURO_ESCURO = colors.HexColor(HEX_OURO_ESCURO)
C_MARFIM = colors.HexColor(HEX_MARFIM)
C_PRATA = colors.HexColor(HEX_PRATA)
C_CINZA = colors.HexColor(HEX_CINZA)
C_CIANO = colors.HexColor(HEX_CIANO)
C_CIANO_ESCURO = colors.HexColor(HEX_CIANO_ESCURO)
C_ESCURO_TXT = colors.HexColor("#0F172A")
C_PAPEL_CLARO = colors.HexColor("#F8FAFC")
C_LINHA_CLARA = colors.HexColor("#CBD5E1")


# ==============================================================================
# 1. LOCALIZADOR E PROCESSADOR DE IMAGENS (SEM DISTORÇÃO + FALLBACK SEGURO)
# ==============================================================================
def _abrir_pil_de_disco_ou_zip(caminhos_rel_ou_abs, nome_zip_alvo=None):
    """Tenta abrir uma imagem via PIL a partir de caminhos em disco ou dentro de `Legacy-Dungeon*.zip`."""
    for cand in caminhos_rel_ou_abs:
        p_abs = cand if os.path.isabs(cand) else os.path.join(RAIZ, cand)
        if os.path.isfile(p_abs):
            try:
                img = PILImage.open(p_abs)
                img.load()
                return img.convert("RGBA"), p_abs
            except Exception:
                pass

    if nome_zip_alvo:
        alvo_low = nome_zip_alvo.lower()
        zips = []
        for pad in (
            os.path.join(RAIZ, "Legacy-Dungeon*.zip"),
            os.path.join(RAIZ, "assets", "Legacy-Dungeon*.zip"),
            os.path.join(RAIZ, "*.zip"),
        ):
            zips.extend(glob.glob(pad))
        for zp in zips:
            try:
                with zipfile.ZipFile(zp, "r") as zf:
                    membros = [
                        n for n in zf.namelist()
                        if n.lower().endswith("/" + alvo_low) or n.lower() == alvo_low
                    ]
                    if membros:
                        membros.sort(key=lambda s: (0 if "final/assets" in s.lower() else 1, len(s)))
                        dados = zf.read(membros[0])
                        img = PILImage.open(io.BytesIO(dados))
                        img.load()
                        return img.convert("RGBA"), f"{zp}!{membros[0]}"
            except Exception:
                pass
    return None, None


def _pil_para_rl_image(pil_img, max_w, max_h):
    """Converte PIL.Image para `reportlab.platypus.Image` preservando exatamente a razão de aspecto."""
    iw, ih = max(1, pil_img.width), max(1, pil_img.height)
    escala = min(float(max_w) / float(iw), float(max_h) / float(ih))
    dw = max(4.0, iw * escala)
    dh = max(4.0, ih * escala)
    # Limita a 300 DPI equivalentes para manter PDFs leves e nítidos no GitHub
    px_max_w = max(240, int(round(dw * 300.0 / 72.0)))
    px_max_h = max(120, int(round(dh * 300.0 / 72.0)))
    img_otim = pil_img
    if iw > px_max_w or ih > px_max_h:
        img_otim = pil_img.copy()
        img_otim.thumbnail((px_max_w, px_max_h), PILImage.Resampling.LANCZOS)
    buf = io.BytesIO()
    img_otim.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return RLImage(buf, width=dw, height=dh)


def _recortar_borda_escura(pil_img, limiar=38):
    """Funde suavemente margens escuras uniformes ao fundo e recorta a caixa útil da logo."""
    if pil_img is None:
        return None
    w, h = pil_img.size
    if w < 16 or h < 16:
        return pil_img
    rgba = pil_img.convert("RGBA")
    r, g, b, a = rgba.split()
    lum = rgba.convert("L")
    # Pixels abaixo de 24 viram transparentes; transição suave entre 24 e `limiar`
    denom = float(max(1, limiar - 22))
    lut = [0 if i <= 22 else (255 if i >= limiar else int(255.0 * (i - 22) / denom)) for i in range(256)]
    alpha_mask = lum.point(lut)
    # Preserva pixels já opacos do miolo usando ImageChops.darker com o alfa original
    from PIL import ImageChops
    rgba.putalpha(ImageChops.darker(a, alpha_mask))
    bbox = rgba.split()[-1].getbbox()
    if bbox:
        pad = 8
        rgba = rgba.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
    return rgba


class PlaceholderEmblema(Flowable):
    """Bloco vetorial elegante com moldura dourada caso algum arquivo visual esteja ausente."""

    def __init__(self, largura, altura, titulo, subtitulo=""):
        super().__init__()
        self.width = float(largura)
        self.height = float(altura)
        self.titulo = str(titulo)
        self.subtitulo = str(subtitulo)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(C_PAINEL)
        c.setStrokeColor(C_OURO)
        c.setLineWidth(1.4)
        c.roundRect(0, 0, self.width, self.height, 4, stroke=1, fill=1)
        c.setStrokeColor(C_OURO_ESCURO)
        c.setLineWidth(0.6)
        c.roundRect(3, 3, max(4, self.width - 6), max(4, self.height - 6), 3, stroke=1, fill=0)

        # Cantoneiras
        c.setStrokeColor(C_OURO_CLARO)
        c.setLineWidth(1.1)
        arm = min(9.0, self.width * 0.12, self.height * 0.22)
        for px, py, dx, dy in (
            (1, 1, 1, 1),
            (self.width - 1, 1, -1, 1),
            (1, self.height - 1, 1, -1),
            (self.width - 1, self.height - 1, -1, -1),
        ):
            c.line(px, py, px + arm * dx, py)
            c.line(px, py, px, py + arm * dy)

        c.setFillColor(C_OURO_CLARO)
        c.setFont("Helvetica-Bold", 11 if self.height > 46 else 9)
        c.drawCentredString(self.width / 2.0, self.height / 2.0 + (4 if self.subtitulo else -3), self.titulo)
        if self.subtitulo:
            c.setFillColor(C_CINZA)
            c.setFont("Helvetica", 8)
            c.drawCentredString(self.width / 2.0, self.height / 2.0 - 11, self.subtitulo)
        c.restoreState()


def _construir_banner_vetorial_jogo(largura, altura):
    """Banner vetorial Dark Fantasy para 'ELOS DO VAZIO' se a imagem PNG não existir."""
    d = Drawing(largura, altura)
    d.add(Rect(0, 0, largura, altura, fillColor=C_PAINEL, strokeColor=C_OURO, strokeWidth=1.8, rx=4, ry=4))
    d.add(Rect(4, 4, largura - 8, altura - 8, fillColor=None, strokeColor=C_OURO_ESCURO, strokeWidth=0.8, rx=3, ry=3))
    cx = largura / 2.0
    cy = altura / 2.0
    d.add(Circle(cx, cy, min(altura * 0.40, 26), fillColor=None, strokeColor=C_CIANO, strokeWidth=1.4))
    d.add(String(cx, cy - 6, "ELOS DO VAZIO", fontName="Times-Bold", fontSize=24, fillColor=C_OURO_CLARO, textAnchor="middle"))
    d.add(String(cx, 10, "DARK FANTASY · AÇÃO E PLATAFORMA 2D", fontName="Helvetica-Bold", fontSize=7, fillColor=C_CIANO, textAnchor="middle"))
    return d


def _construir_emblema_vetorial_gozygrid(largura, altura):
    """Emblema vetorial com 'Z' hexagonal e coroa caso `logo_gozygrid.png` esteja ausente."""
    d = Drawing(largura, altura)
    d.add(Rect(0, 0, largura, altura, fillColor=C_PAINEL, strokeColor=C_OURO, strokeWidth=1.3, rx=4, ry=4))
    cx = largura / 2.0
    cy = altura * 0.58
    r = min(largura, altura) * 0.26
    pts = []
    for k in range(6):
        ang = math.radians(60 * k - 90)
        pts.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])
    d.add(Polygon(pts, fillColor=C_FUNDO, strokeColor=C_OURO, strokeWidth=1.6))
    d.add(String(cx, cy - 7, "Z", fontName="Times-Bold", fontSize=18, fillColor=C_CIANO, textAnchor="middle"))
    d.add(String(cx, 8, "GoZygrid STUDIOS", fontName="Helvetica-Bold", fontSize=8, fillColor=C_OURO_CLARO, textAnchor="middle"))
    return d


def carregar_logo_gozygrid(max_w, max_h):
    candidatos = [
        "assets/logo_gozygrid.png",
        "assets/ui/logo_gozygrid.png",
        "assets/ui/logo_gozygrid_studios.jpg",
        "assets/logo_gozygrid.jpg",
        "assets/logo_gozygrid.jfif",
    ]
    img, orig = _abrir_pil_de_disco_ou_zip(candidatos)
    if img is not None:
        if orig and orig.lower().endswith(".png"):
            return _pil_para_rl_image(img, max_w, max_h)
        return _pil_para_rl_image(_recortar_borda_escura(img), max_w, max_h)
    return _construir_emblema_vetorial_gozygrid(max_w, max_h)


def carregar_logo_jogo(max_w, max_h):
    candidatos = [
        "assets/logo_jogo.png",
        "assets/titulo_elos_do_vazio.png",
        "assets/ui/logo_elos_do_vazio.png",
    ]
    img, _ = _abrir_pil_de_disco_ou_zip(candidatos)
    if img is not None:
        return _pil_para_rl_image(img, max_w, max_h)
    return _construir_banner_vetorial_jogo(max_w, max_h)


# ==============================================================================
# 2. CAPTURA DIRETA DE TELAS REAIS DO JOGO (4 BIOMAS, COMBATE 2.5D E MENU)
# ==============================================================================
def _emoldurar_captura_pil(pil_img):
    """Adiciona borda fina dourada (#D97706) às capturas reais do jogo."""
    img = pil_img.convert("RGBA")
    draw = PILDraw.Draw(img)
    w, h = img.size
    draw.rectangle((0, 0, w - 1, h - 1), outline=(217, 119, 6, 255), width=3)
    return img


def capturar_telas_reais_do_jogo():
    """
    Renderiza capturas autênticas diretamente pelo motor do jogo (`cenarios.py`,
    `main.py`, `menu.py`, `combate.py`) para compor o pôster oficial de exposição.
    """
    capturas = {}
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("HEADLESS", "1")

    try:
        import pygame
        if not pygame.get_init():
            pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((960, 540))

        import cenarios
        import main
        from progresso import Progresso
        from menu import MenuInicial
        from combate import CombateExpedition33

        prog = Progresso()
        prog.nome_heroi = "Viajante"
        salas = main.criar_entidades_das_salas(prog)

        def _surf_para_pil(surf):
            raw = pygame.image.tobytes(surf, "RGB")
            return _emoldurar_captura_pil(PILImage.frombytes("RGB", surf.get_size(), raw))

        def _render_sala(mapa_idx, cam_offset_dx=180, foco_boss=False):
            surf = pygame.Surface((960, 540))
            mapa = cenarios.DADOS_MAPAS[mapa_idx]
            grupo = salas[mapa_idx]
            boss_atual = grupo["boss"]
            if foco_boss:
                boss_atual.vivo = True
                boss_atual.hp = boss_atual.max_hp
                boss_atual.x = 640
                hx, hy = 130, boss_atual.y + 32
            else:
                sp = mapa.get("spawn_heroi", (120, cenarios.LIMITE_SUBSOLO - 56))
                hx, hy = sp[0] + cam_offset_dx, sp[1]

            jog = main.JogadorMapa(hx, hy)
            jog.progresso_ref = prog
            jog.mapa_idx = mapa_idx
            jog.update(0.05, mapa, grupo)

            cam = main.CameraMapa()
            foco_x = 480 if foco_boss else jog.x + 120
            cam.focar_instantaneo(
                foco_x,
                jog.y,
                mapa.get("largura", cenarios.LARGURA_MUNDO),
                mapa.get("altura", cenarios.ALTURA_MUNDO),
            )

            tempo = 1.8
            cenarios.atualizar_salas(mapa_idx, 0.05, tempo)
            off_x, off_y = cam.offset_x, cam.offset_y

            cenarios.desenhar_fundo_sala(surf, mapa_idx, offset_x=off_x, offset_y=off_y)
            cenarios.desenhar_decoracoes(surf, mapa_idx, off_x, camera_y=off_y)
            cenarios.desenhar_estruturas_organicas(surf, mapa_idx, off_x, camera_y=off_y, tempo=tempo)
            cenarios.desenhar_terreno(surf, mapa_idx, off_x, camera_y=off_y)
            cenarios.desenhar_armadilhas(surf, mapa_idx, off_x, tempo, camera_y=off_y)

            larg_m = float(mapa.get("largura", cenarios.LARGURA_MUNDO))
            portal_pos = mapa.get("portal_saida", (larg_m - 140, 960))
            cenarios.desenhar_saida(surf, off_x, boss_atual.vivo, tempo, camera_y=off_y, portal_pos=portal_pos)
            cenarios.desenhar_portoes(surf, grupo, off_x, off_y, tempo)
            cenarios.desenhar_alavancas(surf, grupo, off_x, off_y, tempo)
            cenarios.desenhar_chaves(surf, grupo, off_x, off_y, tempo)
            cenarios.desenhar_baus(surf, grupo, off_x, off_y, tempo)

            for inim in grupo["inimigos"]:
                inim.draw(surf, cam)
            boss_atual.draw(surf, cam)
            jog.draw(surf, cam)

            if mapa_idx == 6:
                main.desenhar_runas_puzzle(surf, off_x, jog, tempo, camera_offset_y=off_y)

            cenarios.desenhar_atmosfera_camada(surf, mapa_idx, off_y, jog.y, tempo)
            return _surf_para_pil(surf), jog

        capturas["bioma_0"], jog_s1 = _render_sala(0, cam_offset_dx=180, foco_boss=False)
        capturas["bioma_1"], _ = _render_sala(3, cam_offset_dx=420, foco_boss=False)
        capturas["bioma_2"], _ = _render_sala(4, cam_offset_dx=340, foco_boss=False)
        capturas["bioma_3"], _ = _render_sala(6, foco_boss=True)

        # Menu Principal real
        surf_menu = pygame.Surface((960, 540))
        menu = MenuInicial(prog)
        for _ in range(25):
            menu.update(0.05)
        menu.draw(surf_menu)
        capturas["menu"] = _surf_para_pil(surf_menu)

        # Combate Tático 2.5D real (sem inimigos removidos)
        surf_comb = pygame.Surface((960, 540))
        inim_grupo = salas[0]["inimigos"][:2]
        alvo0 = inim_grupo[0] if inim_grupo else salas[0]["boss"]
        comb = CombateExpedition33(jog_s1, alvo0, vantagem="JOGADOR", sala_idx=0, alvos_disponiveis=inim_grupo, sala_atual=0)
        for _ in range(30):
            comb.update(0.04)
        comb.draw(surf_comb)
        capturas["combate"] = _surf_para_pil(surf_comb)
    except Exception as exc:
        print(f"[pdf] Aviso na captura ao vivo: {exc}")

    # Fallback para capturas já exportadas em docs/screenshots/, caso necessário
    for chave, arq in (
        ("menu", "docs/screenshots/01_menu_principal.png"),
        ("bioma_0", "docs/screenshots/02_exploracao_sala1.png"),
        ("combate", "docs/screenshots/03_combate_25d.png"),
    ):
        if chave not in capturas:
            img, _ = _abrir_pil_de_disco_ou_zip([arq])
            if img is not None:
                capturas[chave] = _emoldurar_captura_pil(img)

    return capturas


# ==============================================================================
# 3. MOLDURAS DE PÁGINA DARK FANTASY E CABEÇALHOS REPORTLAB
# ==============================================================================
def _desenhar_fundo_pagina_escura(canvas, doc, rodape_texto="GoZygrid Studios  ·  Elos do Vazio"):
    canvas.saveState()
    pw, ph = A4
    canvas.setFillColor(C_FUNDO)
    canvas.rect(0, 0, pw, ph, stroke=0, fill=1)

    # Moldura dupla em ouro velho #D97706
    m = 10 * mm
    canvas.setStrokeColor(C_OURO)
    canvas.setLineWidth(1.5)
    canvas.rect(m, m, pw - 2 * m, ph - 2 * m, stroke=1, fill=0)
    canvas.setStrokeColor(C_OURO_ESCURO)
    canvas.setLineWidth(0.6)
    canvas.rect(m + 3, m + 3, pw - 2 * m - 6, ph - 2 * m - 6, stroke=1, fill=0)

    # Cantoneiras decorativas em ouro vivo
    canvas.setStrokeColor(C_OURO_CLARO)
    canvas.setLineWidth(1.6)
    arm = 6 * mm
    for cx, cy, dx, dy in (
        (m, m, 1, 1),
        (pw - m, m, -1, 1),
        (m, ph - m, 1, -1),
        (pw - m, ph - m, -1, -1),
    ):
        canvas.line(cx, cy, cx + arm * dx, cy)
        canvas.line(cx, cy, cx, cy + arm * dy)

    canvas.setFillColor(C_CINZA)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(pw / 2.0, m + 4.5, f"{rodape_texto}   |   Página {doc.page}")
    canvas.restoreState()


def _desenhar_borda_guia_claro(canvas, doc):
    canvas.saveState()
    pw, ph = A4
    canvas.setFillColor(C_PAPEL_CLARO)
    canvas.rect(0, 0, pw, ph, stroke=0, fill=1)
    m = 10 * mm
    canvas.setStrokeColor(C_OURO)
    canvas.setLineWidth(1.0)
    canvas.rect(m, m, pw - 2 * m, ph - 2 * m, stroke=1, fill=0)
    canvas.setFillColor(C_ESCURO_TXT)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(pw / 2.0, m + 4.5, f"GoZygrid Studios  ·  Manual Técnico GitHub & Instalação  |  Página {doc.page}")
    canvas.restoreState()


def _divisor_ouro(largura=170 * mm):
    d = Drawing(largura, 8)
    d.add(Line(0, 4, largura, 4, strokeColor=C_OURO, strokeWidth=1.0))
    cx = largura / 2.0
    d.add(Polygon([cx, 7.5, cx + 4.5, 4, cx, 0.5, cx - 4.5, 4], fillColor=C_OURO_CLARO, strokeColor=C_OURO, strokeWidth=0.6))
    return d


# ==============================================================================
# 4. PDF 1: PAINEL EDITORIAL DE EXPOSIÇÃO (`elos_do_vazio_exposicao.pdf`)
# ==============================================================================
def gerar_pdf_exposicao(destino_pdf):
    doc = SimpleDocTemplate(
        destino_pdf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=10 * mm,
        bottomMargin=11 * mm,
        title="Elos do Vazio — Painel Editorial de Exposição (GoZygrid Studios)",
        author="GoZygrid Studios",
    )

    st_sub = ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=9.4, leading=11.5, textColor=C_CIANO, alignment=TA_CENTER)
    st_sec = ParagraphStyle("sec", fontName="Times-Bold", fontSize=11.5, leading=13.5, textColor=C_OURO_CLARO, spaceBefore=2.5, spaceAfter=2.0)
    st_body = ParagraphStyle("body", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=C_MARFIM, alignment=TA_JUSTIFY)
    st_cell_k = ParagraphStyle("ck", fontName="Helvetica-Bold", fontSize=8.1, leading=10.2, textColor=C_OURO_CLARO)
    st_cell_v = ParagraphStyle("cv", fontName="Helvetica", fontSize=8.1, leading=10.2, textColor=C_MARFIM)
    st_cap = ParagraphStyle("cap", fontName="Helvetica-Bold", fontSize=7.9, leading=10.0, textColor=C_OURO_CLARO, alignment=TA_CENTER)
    st_cap_sub = ParagraphStyle("caps", fontName="Helvetica", fontSize=7.0, leading=9.0, textColor=C_PRATA, alignment=TA_CENTER)

    larg_util = A4[0] - 30 * mm
    telas = capturar_telas_reais_do_jogo()
    story = []

    # --- CABEÇALHO DUPLO DE IDENTIDADE (GoZygrid Studios + Logo Oficial Elos do Vazio) ---
    logo_estudio = carregar_logo_gozygrid(40 * mm, 22 * mm)
    logo_jogo = carregar_logo_jogo(112 * mm, 24 * mm)

    cabecalho = Table(
        [[logo_estudio, logo_jogo]],
        colWidths=[46 * mm, larg_util - 46 * mm],
    )
    cabecalho.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, -1), C_PAINEL),
        ("BOX", (0, 0), (-1, -1), 1.2, C_OURO),
        ("LINEAFTER", (0, 0), (0, 0), 0.8, C_OURO_ESCURO),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(cabecalho)
    story.append(Spacer(1, 1.8 * mm))
    story.append(Paragraph("Plataforma 2D & Combate Tático 2.5D em Dark Fantasy Medieval", st_sub))
    story.append(Spacer(1, 1.2 * mm))
    story.append(_divisor_ouro(larg_util))
    story.append(Spacer(1, 1.2 * mm))

    # --- SINOPSE DO JOGO ---
    story.append(Paragraph("SINOPSE E DIREÇÃO DE ARTE", st_sec))
    story.append(Paragraph(
        "Em <b>Elos do Vazio</b>, o Viajante desperta sob o luar de uma cidadela em ruínas para atravessar sete "
        "câmaras interconectadas e derrotar os guardiões que selam o coração do Éter. Unindo travessia ágil em "
        "plataforma 2D com combate tático 2.5D de reação em tempo real — onde <i>Parry Perfeito</i> [X], esquiva [C], "
        "salto defensivo [ESPAÇO] e QTE ofensivo [Z] definem cada confronto — o projeto combina cantaria em pixel art e áudio atmosférico.",
        st_body,
    ))
    story.append(Spacer(1, 1.5 * mm))

    # --- FICHA TÉCNICA EDITORIAL ---
    story.append(Paragraph("FICHA TÉCNICA DO PROJETO", st_sec))
    dados_ficha = [
        [Paragraph("Desenvolvedor / Estúdio", st_cell_k), Paragraph("GoZygrid Studios (desenvolvido com auxílio de Inteligência Artificial)", st_cell_v)],
        [Paragraph("Motor / Tecnologia", st_cell_k), Paragraph("Python 3.10+ & pygame-ce (960x540 SCALED 16:9)", st_cell_v)],
        [Paragraph("Gênero", st_cell_k), Paragraph("Plataforma 2D / Combate Tático 2.5D / Dark Fantasy", st_cell_v)],
        [Paragraph("Modos & Controles", st_cell_k), Paragraph("Campanha (7 Salas), Boss Rush, Modo Bot [F2] • Teclado & Controle USB (Xbox/PS)", st_cell_v)],
    ]
    tb_ficha = Table(dados_ficha, colWidths=[46 * mm, larg_util - 46 * mm])
    tb_ficha.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PAINEL),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_PAINEL, C_PAINEL_ALT]),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("GRID", (0, 0), (-1, -1), 0.5, C_OURO_ESCURO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
    ]))
    story.append(tb_ficha)
    story.append(Spacer(1, 1.5 * mm))

    # --- PAINEL DAS 7 SALAS DA MASMORRA (4 CAPTURAS REAIS DO JOGO) ---
    story.append(Paragraph("AS 7 SALAS E OS 4 BIOMAS DA MASMORRA (CAPTURAS REAIS)", st_sec))
    infos_biomas = [
        (0, "Salas 1 e 2 — Ameias e Pátio Superior", "Céu noturno, lua cheia, mastros com bandeiras, baús e emboscadas com Demon Carmesim e Orc."),
        (1, "Salas 3 e 4 — Galerias das Torres de Vigia", "Torres em paralaxe, passarelas suspensas por correntes, chaves douradas e alavancas de portão."),
        (2, "Salas 5 e 6 — Cripta e Catacumbas", "Teto fechado em cantaria escura, grades de ferro, lápides, tochas frias e plataformas móveis."),
        (3, "Sala 7 — Santuário do Guardião (Boss Final)", "Arena monumental com 3 Relíquias Arcanas de Éter frente ao Bibliotecário do Vazio."),
    ]
    w_cel = (larg_util - 3 * mm) / 2.0
    cards_bioma = []
    for b_idx, tit_b, desc_b in infos_biomas:
        img_real = telas.get(f"bioma_{b_idx}")
        if img_real is not None:
            rl_prev = _pil_para_rl_image(img_real, w_cel - 5 * mm, 36 * mm)
        else:
            rl_prev = PlaceholderEmblema(w_cel - 5 * mm, 35 * mm, tit_b)
        sub_tab = Table(
            [[rl_prev], [Paragraph(tit_b, st_cap)], [Paragraph(desc_b, st_cap_sub)]],
            colWidths=[w_cel - 2 * mm],
        )
        sub_tab.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ]))
        cards_bioma.append(sub_tab)

    tb_biomas = Table(
        [[cards_bioma[0], cards_bioma[1]], [cards_bioma[2], cards_bioma[3]]],
        colWidths=[w_cel, w_cel],
    )
    tb_biomas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PAINEL),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, C_OURO_ESCURO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tb_biomas)
    story.append(Spacer(1, 1.5 * mm))

    # --- PAINEL DE COMBATE 2.5D E MENU PRINCIPAL (CAPTURAS REAIS) ---
    story.append(Paragraph("COMBATE TÁTICO 2.5D & INTERFACE DO JOGO", st_sec))
    img_menu = telas.get("menu")
    img_comb = telas.get("combate")
    rl_menu = _pil_para_rl_image(img_menu, w_cel - 5 * mm, 36 * mm) if img_menu is not None else PlaceholderEmblema(w_cel - 5 * mm, 35 * mm, "MENU PRINCIPAL")
    rl_comb = _pil_para_rl_image(img_comb, w_cel - 5 * mm, 36 * mm) if img_comb is not None else PlaceholderEmblema(w_cel - 5 * mm, 35 * mm, "COMBATE 2.5D")

    tb_comb = Table(
        [
            [rl_menu, rl_comb],
            [
                Paragraph("<b>Menu Principal & Modos:</b> Acesso à Campanha, Seleção de Salas, Boss Rush e Ranque.", st_cap_sub),
                Paragraph("<b>Combate 2.5D:</b> Ordem de turnos, Parry [X] com hitstop, Esquiva [C] e Salto [ESPAÇO].", st_cap_sub),
            ],
        ],
        colWidths=[w_cel, w_cel],
    )
    tb_comb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PAINEL),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, C_OURO_ESCURO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tb_comb)

    doc.build(
        story,
        onFirstPage=lambda c, d: _desenhar_fundo_pagina_escura(c, d, "GoZygrid Studios  ·  Elos do Vazio (Desenvolvido com auxílio de IA)"),
        onLaterPages=lambda c, d: _desenhar_fundo_pagina_escura(c, d, "GoZygrid Studios  ·  Elos do Vazio (Desenvolvido com auxílio de IA)"),
    )


# ==============================================================================
# 5. PDF 2: GUIA DE INSTALAÇÃO & GITHUB (`elos_do_vazio_guia_github.pdf`)
# ==============================================================================
def gerar_pdf_guia_github(destino_pdf):
    doc = SimpleDocTemplate(
        destino_pdf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=11 * mm,
        bottomMargin=12 * mm,
        title="Elos do Vazio — Guia de Instalação & GitHub (GoZygrid Studios)",
        author="GoZygrid Studios",
    )

    st_banner_tit = ParagraphStyle("bt", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=C_OURO_CLARO, alignment=TA_CENTER)
    st_banner_sub = ParagraphStyle("bs", fontName="Helvetica", fontSize=8.0, leading=10.5, textColor=C_MARFIM, alignment=TA_CENTER)
    st_h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=11.0, leading=14, textColor=C_ESCURO_TXT, spaceBefore=3.5, spaceAfter=2)
    st_p = ParagraphStyle("p", fontName="Helvetica", fontSize=8.7, leading=11.8, textColor=C_ESCURO_TXT, alignment=TA_JUSTIFY, spaceAfter=2.5)
    st_step_k = ParagraphStyle("sk", fontName="Helvetica-Bold", fontSize=8.2, leading=10.8, textColor=C_OURO_ESCURO)
    st_step_v = ParagraphStyle("sv", fontName="Helvetica", fontSize=8.2, leading=10.8, textColor=C_ESCURO_TXT)
    st_code = ParagraphStyle("code", fontName="Courier", fontSize=8.0, leading=10.5, textColor=C_OURO_CLARO)
    st_tree_k = ParagraphStyle("tk", fontName="Courier-Bold", fontSize=8.0, leading=10.5, textColor=C_CIANO_ESCURO)

    larg_util = A4[0] - 30 * mm
    story = []

    # Cabeçalho técnico limpo mantendo as duas logos lado a lado em destaque Dark Fantasy
    logo_estudio = carregar_logo_gozygrid(40 * mm, 21 * mm)
    logo_jogo = carregar_logo_jogo(112 * mm, 22 * mm)
    tb_header = Table(
        [
            [logo_estudio, logo_jogo],
            [Paragraph("GUIA DE INSTALAÇÃO, RELEASES E CÓDIGO-FONTE (GITHUB)", st_banner_tit), ""],
            [Paragraph("GoZygrid Studios  ·  Manual Técnico — Elos do Vazio (Desenvolvido com auxílio de IA)", st_banner_sub), ""],
        ],
        colWidths=[48 * mm, larg_util - 48 * mm],
    )
    tb_header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_FUNDO),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 2), (1, 2)),
        ("BOX", (0, 0), (-1, -1), 1.4, C_OURO),
        ("LINEBELOW", (0, 0), (1, 0), 0.7, C_OURO_ESCURO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]))
    story.append(tb_header)
    story.append(Spacer(1, 2.5 * mm))

    # --- SEÇÃO 1: MODO JOGADOR (EXECUTÁVEL VIA GITHUB RELEASES) ---
    story.append(Paragraph("SEÇÃO 1 — COMO BAIXAR O EXECUTÁVEL PRONTO (MODO JOGADOR)", st_h1))
    story.append(Paragraph(
        "Para jogar diretamente no Windows sem precisar configurar Python ou bibliotecas externas:<br/>"
        "<b>1.</b> Acesse a aba <b>Releases</b> no repositório oficial do GitHub: "
        "<font color='#0369A1'><u>https://github.com/GoKaio/elos-do-vazio/releases</u></font><br/>"
        "<b>2.</b> Baixe o arquivo <b>Instalador_Elos_do_Vazio.exe</b> e execute-o com dois cliques.<br/>"
        "<b>3.</b> Siga as <b>4 etapas do instalador gótico</b> detalhadas abaixo:",
        st_p,
    ))

    etapas_inst = [
        [Paragraph("Etapa 1 · Boas-Vindas", st_step_k),
         Paragraph("Apresenta a moldura Dark Fantasy, versão e controle de música ambiente em loop; clique em <b>AVANÇAR &gt;</b>.", st_step_v)],
        [Paragraph("Etapa 2 · Diretório & Opções", st_step_k),
         Paragraph("Permite editar o caminho padrão (<b>C:\\Jogos\\Elos do Vazio</b>), procurar outra pasta e marcar criação de atalhos.", st_step_v)],
        [Paragraph("Etapa 3 · Instalação Ativa", st_step_k),
         Paragraph("Descompacta o jogo em <i>thread</i> separada com barra segmentada em ciano de Éter, mantendo a música tema e badalo nos 100%.", st_step_v)],
        [Paragraph("Etapa 4 · Conclusão & Atalhos", st_step_k),
         Paragraph("Cria atalhos <b>.lnk</b> automáticos na Área de Trabalho e Menu Iniciar e libera o botão <b>JOGAR AGORA</b>.", st_step_v)],
    ]
    tb_inst = Table(etapas_inst, colWidths=[45 * mm, larg_util - 45 * mm])
    tb_inst.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F1F5F9")]),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("GRID", (0, 0), (-1, -1), 0.5, C_LINHA_CLARA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tb_inst)
    story.append(Spacer(1, 2 * mm))

    # --- SEÇÃO 2: MODO DESENVOLVEDOR (CÓDIGO-FONTE & PYTHON) ---
    story.append(Paragraph("SEÇÃO 2 — COMO BAIXAR E RODAR VIA CÓDIGO-FONTE (MODO DESENVOLVEDOR)", st_h1))
    story.append(Paragraph(
        "Requer <b>Python 3.10+</b> (recomendado <b>Python 3.12</b>) e Git instalados no Windows. "
        "Execute os comandos abaixo no PowerShell ou Prompt de Comando:",
        st_p,
    ))

    bloco_cmd = Paragraph(
        "# 1. Clonar o repositório e entrar na pasta<br/>"
        "git clone https://github.com/GoKaio/elos-do-vazio.git<br/>"
        "cd elos-do-vazio<br/><br/>"
        "# 2. Criar/ativar ambiente virtual e instalar dependências<br/>"
        "python -m venv venv<br/>"
        "venv\\Scripts\\activate<br/>"
        "pip install -r requirements.txt<br/><br/>"
        "# 3. Executar o jogo (ou .\\tools\\build_tudo.bat para compilar o .exe)<br/>"
        "python main.py",
        st_code,
    )
    tb_code = Table([[bloco_cmd]], colWidths=[larg_util])
    tb_code.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_FUNDO),
        ("BOX", (0, 0), (-1, -1), 1.0, C_CIANO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tb_code)
    story.append(Spacer(1, 2 * mm))

    # --- SEÇÃO 3: MAPA DA ESTRUTURA DE ARQUIVOS DO REPOSITÓRIO ---
    story.append(Paragraph("SEÇÃO 3 — MAPA DA ESTRUTURA DE ARQUIVOS DO REPOSITÓRIO", st_h1))
    arvore = [
        [Paragraph("elos-do-vazio/", st_tree_k), Paragraph("Raiz enxuta: main.py, JOGAR.bat, INSTALAR_DEPENDENCIAS.bat e README.md", st_step_v)],
        [Paragraph("|-- src/", st_tree_k), Paragraph("Núcleo do jogo: menu, cenarios, gerenciador_salas, combate 2.5D, player, inimigos e sprites.", st_step_v)],
        [Paragraph("|-- docs/", st_tree_k), Paragraph("Guias (LEIA-ME.txt, COMO_JOGAR.txt, bosses), PDFs editoriais e screenshots/ reais.", st_step_v)],
        [Paragraph("|-- tools/", st_tree_k), Paragraph("Instalador gótico (instalador_gui.py), build_instalador.py, gerar_trailer.py e PDFs.", st_step_v)],
        [Paragraph("|-- assets/", st_tree_k), Paragraph("Logos, sprites do herói/inimigos, sons/músicas e recursos visuais (Legacy-Dungeon).", st_step_v)],
        [Paragraph("+-- .github/", st_tree_k), Paragraph("Workflows CI automáticos no GitHub Actions e templates de Issue / Pull Request.", st_step_v)],
    ]
    tb_tree = Table(arvore, colWidths=[66 * mm, larg_util - 66 * mm])
    tb_tree.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F1F5F9"), colors.HexColor("#FFFFFF")]),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("GRID", (0, 0), (-1, -1), 0.4, C_LINHA_CLARA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tb_tree)

    doc.build(story, onFirstPage=_desenhar_borda_guia_claro, onLaterPages=_desenhar_borda_guia_claro)


def main():
    docs_dir = os.path.join(RAIZ, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    out_exposicao = os.path.join(docs_dir, "elos_do_vazio_exposicao.pdf")
    out_guia = os.path.join(docs_dir, "elos_do_vazio_guia_github.pdf")
    gerar_pdf_exposicao(out_exposicao)
    print(f"[OK] PDF de Exposição gerado: {out_exposicao}")
    gerar_pdf_guia_github(out_guia)
    print(f"[OK] PDF Guia GitHub gerado: {out_guia}")


if __name__ == "__main__":
    main()
