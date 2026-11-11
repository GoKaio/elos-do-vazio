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


RAIZ = os.path.dirname(os.path.abspath(__file__))

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
# 2. COMPOSITOR VISUAL DE SPRITES E MINIATURAS DOS 4 BIOMAS + ATLAS
# ==============================================================================
def _abrir_asset_legacy(nome_arquivo):
    cands = [
        os.path.join("Final", "Assets", nome_arquivo),
        os.path.join("assets", "Legacy-Dungeon", "Final", "Assets", nome_arquivo),
        os.path.join("assets", "legacy_dungeon", "Final", "Assets", nome_arquivo),
        os.path.join("assets", "Final", "Assets", nome_arquivo),
        os.path.join("assets", "final_pack", nome_arquivo),
    ]
    img, _ = _abrir_pil_de_disco_ou_zip(cands, nome_zip_alvo=nome_arquivo)
    return img


def carregar_faixa_sprites_protagonista(max_w, max_h):
    """Extrai quadros em ação de `Character_Sprite_Sheet.png` ou fallback de `assets/Hero/*.png`."""
    frames = []
    sheet = _abrir_asset_legacy("Character_Sprite_Sheet.png")
    if sheet is not None:
        sw, sh = sheet.size
        # Fatiamento adaptativo: grade quadrada baseada na menor dimensão ou fileiras de 8 colunas
        tam = sh if sh <= 96 else max(16, sh // max(1, round(sh / 32)))
        if sw >= tam * 3:
            cols = min(6, sw // tam)
            for c in range(cols):
                crop = sheet.crop((c * tam, 0, (c + 1) * tam, min(sh, tam)))
                if crop.getbbox():
                    frames.append(crop)

    if not frames:
        # Tenta sprites modulares Tiny RPG do projeto (`Hero-Idle.png`, `Hero-Attack01.png`, `Hero-Attack02.png`, `Hero-Walk.png`)
        for rel, quadro_idx in (
            ("assets/Hero/Hero-Idle.png", 0),
            ("assets/Hero/Hero-Walk.png", 2),
            ("assets/Hero/Hero-Attack01.png", 3),
            ("assets/Hero/Hero-Attack02.png", 3),
        ):
            img, _ = _abrir_pil_de_disco_ou_zip([rel])
            if img is not None:
                iw, ih = img.size
                cell = ih if iw >= ih else iw
                n_frames = max(1, iw // max(1, cell))
                idx = min(n_frames - 1, quadro_idx)
                q = img.crop((idx * cell, 0, (idx + 1) * cell, ih))
                bbox = (q.split()[-1].getbbox() if q.mode == "RGBA" else None) or q.getbbox()
                if bbox:
                    pad = 6
                    box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(q.width, bbox[2] + pad), min(q.height, bbox[3] + pad))
                    frames.append(q.crop(box))

    if not frames:
        return PlaceholderEmblema(max_w, max_h, "SPRITES DO PROTAGONISTA", "Character_Sprite_Sheet.png não localizado")

    # Monta vitrine com 4 quadros em estantes góticas iluminadas por Éter
    w_tot, h_tot = 520, 118
    canvas = PILImage.new("RGBA", (w_tot, h_tot), (13, 18, 32, 255))
    draw = PILDraw.Draw(canvas)
    draw.rectangle((0, 0, w_tot - 1, h_tot - 1), outline=(217, 119, 6, 255), width=2)
    legenda = ("Vigília", "Avanço", "Corte / Parry", "Golpe de Éter")
    n = min(4, len(frames))
    larg_slot = w_tot // max(1, n)

    from PIL import ImageFont
    fonte_leg = None
    for fn_font in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            fonte_leg = ImageFont.truetype(fn_font, 11)
            break
        except Exception:
            pass

    for i in range(n):
        fr = frames[i]
        sx0 = i * larg_slot + 8
        sy0 = 8
        sw_s = larg_slot - 16
        sh_s = h_tot - 26
        draw.rectangle((sx0, sy0, sx0 + sw_s, sy0 + sh_s), fill=(19, 25, 43, 255), outline=(56, 189, 248, 120), width=1)
        esc = min((sw_s - 10) / float(max(1, fr.width)), (sh_s - 12) / float(max(1, fr.height)))
        nw = max(1, int(fr.width * esc))
        nh = max(1, int(fr.height * esc))
        fr_sc = fr.resize((nw, nh), PILImage.Resampling.NEAREST)
        canvas.paste(fr_sc, (sx0 + (sw_s - nw) // 2, sy0 + sh_s - nh - 4), fr_sc)
        txt = legenda[i] if i < len(legenda) else f"Quadro {i + 1}"
        if fonte_leg is not None:
            draw.text((sx0 + 6, h_tot - 17), txt, font=fonte_leg, fill=(253, 230, 138, 255))
        else:
            txt_ascii = txt.replace("í", "i").replace("ç", "c").replace("É", "E")
            draw.text((sx0 + 6, h_tot - 16), txt_ascii, fill=(253, 230, 138, 255))

    return _pil_para_rl_image(canvas, max_w, max_h)


def _desenhar_miniatura_bioma(bioma_idx, w=320, h=140):
    """
    Compõe em Pillow uma prévia fiel de cada um dos 4 biomas integrando `Background_1.png`,
    `Background_2.png`, `Background_0.png`, `Tiles.png` e `Assets.png` quando disponíveis.
    """
    img = PILImage.new("RGBA", (w, h), (11, 15, 25, 255))
    draw = PILDraw.Draw(img)

    bg0 = _abrir_asset_legacy("Background_0.png")
    bg1 = _abrir_asset_legacy("Background_1.png")
    bg2 = _abrir_asset_legacy("Background_2.png")
    atlas = _abrir_asset_legacy("Assets.png") or _abrir_asset_legacy("Tiles.png")

    if bioma_idx == 0:
        # Bioma 1: Ameias e Pátio Superior (`Background_1.png` + lua + tochas + bandeira)
        if bg0 is not None:
            cam0 = bg0.resize((w, h), PILImage.Resampling.BILINEAR)
            img.paste(cam0, (0, 0), cam0)
        if bg1 is not None:
            cam1 = bg1.resize((w, h), PILImage.Resampling.BILINEAR)
            img.paste(cam1, (0, 0), cam1)
        draw.ellipse((w - 64, 14, w - 24, 54), fill=(226, 232, 240, 240))
        # Ameias, mastro e tochas
        draw.rectangle((0, h - 26, w, h), fill=(34, 41, 56, 255), outline=(71, 85, 105, 255))
        draw.line((46, h - 26, 46, h - 92), fill=(148, 163, 184, 255), width=2)
        draw.polygon([(47, h - 90), (84, h - 82), (47, h - 72)], fill=(153, 27, 27, 255), outline=(245, 158, 11, 255))
        for tx in (128, 224):
            draw.ellipse((tx - 14, h - 66, tx + 14, h - 38), fill=(249, 115, 22, 65))
            draw.polygon([(tx - 4, h - 46), (tx, h - 62), (tx + 4, h - 46)], fill=(254, 240, 138, 255))

    elif bioma_idx == 1:
        # Bioma 2: Galerias das Torres de Vigia (`Background_2.png`, plataformas suspensas e correntes)
        if bg0 is not None:
            cam0 = bg0.resize((w, h), PILImage.Resampling.BILINEAR)
            img.paste(cam0, (0, 0), cam0)
        if bg2 is not None:
            cam2 = bg2.resize((w, h), PILImage.Resampling.BILINEAR)
            img.paste(cam2, (0, 0), cam2)
        else:
            for tx, tw, th in ((24, 34, 90), (140, 42, 110), (244, 38, 95)):
                draw.rectangle((tx, h - th, tx + tw, h), fill=(20, 26, 44, 235), outline=(51, 65, 85, 255))
        # Plataforma suspensa com correntes de ferro verticais + degraus
        draw.rectangle((0, h - 44, 72, h), fill=(39, 48, 67, 255), outline=(100, 116, 139, 255))
        draw.rectangle((w - 84, h - 38, w, h), fill=(39, 48, 67, 255), outline=(100, 116, 139, 255))
        for px, py, pw in ((98, 64, 74), (186, 48, 68)):
            draw.line((px + 10, 0, px + 10, py), fill=(148, 163, 184, 255), width=2)
            draw.line((px + pw - 10, 0, px + pw - 10, py), fill=(148, 163, 184, 255), width=2)
            draw.rectangle((px, py, px + pw, py + 12), fill=(51, 65, 85, 255), outline=(148, 163, 184, 255))

    elif bioma_idx == 2:
        # Bioma 3: Catacumbas Subterrâneas (teto fechado, arcos, grades, lápides e tochas frias)
        draw.rectangle((0, 0, w, h), fill=(12, 14, 24, 255))
        draw.rectangle((0, 0, w, 22), fill=(24, 28, 44, 255), outline=(71, 85, 105, 255))
        draw.rectangle((0, h - 22, w, h), fill=(24, 28, 44, 255), outline=(71, 85, 105, 255))
        for ax in (32, 128, 224):
            draw.arc((ax, 22, ax + 68, 92), 180, 360, fill=(71, 85, 105, 255), width=2)
            draw.rectangle((ax + 12, 54, ax + 56, h - 22), fill=(5, 7, 13, 255), outline=(51, 65, 85, 255))
            for bx in range(ax + 20, ax + 54, 10):
                draw.line((bx, 56, bx, h - 22), fill=(100, 116, 139, 255), width=2)
        for tx in (86, 200):
            draw.ellipse((tx - 12, 52, tx + 12, 76), fill=(56, 189, 248, 65))
            draw.polygon([(tx - 4, 70), (tx, 54), (tx + 4, 70)], fill=(168, 85, 247, 255))
        for lx in (106, 212):
            draw.rounded_rectangle((lx - 8, h - 42, lx + 8, h - 22), radius=4, fill=(51, 65, 85, 255), outline=(15, 23, 42, 255))

    else:
        # Bioma 4: Santuário do Guardião (arena ampla 960px, pilares com gárgulas e portão titânico)
        draw.rectangle((0, 0, w, h), fill=(10, 13, 26, 255))
        draw.rectangle((0, 0, w, 16), fill=(28, 32, 52, 255), outline=(217, 119, 6, 255))
        draw.rectangle((0, h - 22, w, h), fill=(28, 36, 62, 255), outline=(56, 189, 248, 255))
        for gx in (58, 214):
            draw.rectangle((gx - 12, h - 86, gx + 12, h - 22), fill=(68, 72, 92, 255), outline=(148, 163, 184, 255))
            draw.polygon([(gx - 16, h - 86), (gx, h - 108), (gx + 16, h - 86)], fill=(100, 116, 139, 255))
        # Portão titânico à direita com runa ciano/ouro
        draw.rectangle((w - 54, h - 98, w - 18, h - 22), fill=(20, 24, 38, 255), outline=(217, 119, 6, 255), width=2)
        for bx in range(w - 48, w - 20, 8):
            draw.line((bx, h - 96, bx, h - 24), fill=(148, 163, 184, 255), width=2)
        draw.ellipse((w - 44, h - 68, w - 28, h - 52), outline=(56, 189, 248, 255), width=2)

    # Recorte de amostra do atlas de cantaria no canto se disponível
    if atlas is not None and bioma_idx in (0, 2):
        aw, ah = atlas.size
        sw_c = min(44, aw)
        sh_c = min(32, ah)
        rec = atlas.crop((0, 0, sw_c, sh_c)).resize((36, 26), PILImage.Resampling.NEAREST)
        img.paste(rec, (6, 6), rec)
        draw.rectangle((5, 5, 43, 33), outline=(217, 119, 6, 255), width=1)

    draw.rectangle((0, 0, w - 1, h - 1), outline=(217, 119, 6, 255), width=2)
    return img


def carregar_amostra_atlas_cantaria(max_w, max_h):
    """Carrega recorte ilustrativo de `Assets.png` (ou `Tiles.png`) para a ficha de cenários."""
    atlas = _abrir_asset_legacy("Assets.png") or _abrir_asset_legacy("Tiles.png")
    if atlas is None:
        return PlaceholderEmblema(max_w, max_h, "ATLAS DE CANTARIA", "Final/Assets/Assets.png")
    aw, ah = atlas.size
    rec = atlas.crop((0, 0, min(aw, 280), min(ah, 180)))
    return _pil_para_rl_image(rec, max_w, max_h)


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
        topMargin=11 * mm,
        bottomMargin=12 * mm,
        title="Elos do Vazio — Painel Editorial de Exposição (GoZygrid Studios)",
        author="GoZygrid Studios",
    )

    st_sub = ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=9.6, leading=12, textColor=C_CIANO, alignment=TA_CENTER)
    st_sec = ParagraphStyle("sec", fontName="Times-Bold", fontSize=12, leading=14.5, textColor=C_OURO_CLARO, spaceBefore=3, spaceAfter=2.5)
    st_body = ParagraphStyle("body", fontName="Helvetica", fontSize=8.9, leading=12.2, textColor=C_MARFIM, alignment=TA_JUSTIFY)
    st_cell_k = ParagraphStyle("ck", fontName="Helvetica-Bold", fontSize=8.4, leading=11, textColor=C_OURO_CLARO)
    st_cell_v = ParagraphStyle("cv", fontName="Helvetica", fontSize=8.4, leading=11, textColor=C_MARFIM)
    st_cap = ParagraphStyle("cap", fontName="Helvetica-Bold", fontSize=8.0, leading=10.2, textColor=C_OURO_CLARO, alignment=TA_CENTER)
    st_cap_sub = ParagraphStyle("caps", fontName="Helvetica", fontSize=7.3, leading=9.5, textColor=C_PRATA, alignment=TA_CENTER)

    larg_util = A4[0] - 30 * mm
    story = []

    # --- CABEÇALHO DUPLO DE IDENTIDADE (GoZygrid Studios + Logo Oficial Elos do Vazio) ---
    logo_estudio = carregar_logo_gozygrid(40 * mm, 24 * mm)
    logo_jogo = carregar_logo_jogo(114 * mm, 26 * mm)

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
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(cabecalho)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Ação, Plataforma 2D e Combate de Precisão em Dark Fantasy", st_sub))
    story.append(Spacer(1, 1.5 * mm))
    story.append(_divisor_ouro(larg_util))
    story.append(Spacer(1, 1.5 * mm))

    # --- SINOPSE DO JOGO ---
    story.append(Paragraph("SINOPSE E DIREÇÃO DE ARTE", st_sec))
    story.append(Paragraph(
        "Em <b>Elos do Vazio</b>, o último expedicionário desperta sob a luz pálida de uma cidadela partida para atravessar "
        "sete câmaras interconectadas e enfrentar os guardiões que selam o coração do Éter. Combinando travessia ágil em "
        "plataforma 2D com confrontos táticos de precisão — onde cada <i>parry</i>, esquiva e contra-ataque rúnico define a "
        "sobrevivência — o título une arquitetura gótica em pixel art, iluminação volumétrica e trilha atmosférica.",
        st_body,
    ))
    story.append(Spacer(1, 2 * mm))

    # --- FICHA TÉCNICA EDITORIAL ---
    story.append(Paragraph("FICHA TÉCNICA DO PROJETO", st_sec))
    dados_ficha = [
        [Paragraph("Desenvolvedor / Estúdio", st_cell_k), Paragraph("GoZygrid Studios", st_cell_v)],
        [Paragraph("Motor / Tecnologia", st_cell_k), Paragraph("Python 3.12 & pygame-ce", st_cell_v)],
        [Paragraph("Gênero", st_cell_k), Paragraph("Plataforma 2D / Ação / Dark Fantasy Medieval", st_cell_v)],
        [Paragraph("Modos de Jogo", st_cell_k), Paragraph("Solo e Cooperativo Local (2 Jogadores com instâncias de controle isoladas)", st_cell_v)],
        [Paragraph("Resolução Base", st_cell_k), Paragraph("960x540 com escala proporcional para Full HD e 4K", st_cell_v)],
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
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tb_ficha)
    story.append(Spacer(1, 2 * mm))

    # --- PAINEL DAS 7 SALAS DA MASMORRA (4 BIOMAS COM CAPTURAS REAIS) ---
    story.append(Paragraph("AS 7 SALAS E OS 4 BIOMAS DA MASMORRA", st_sec))
    infos_biomas = [
        (0, "Salas 1 e 2 — Ameias e Pátio Superior", "Exterior noturno (Background_1.png), lua cheia, tochas de parede, mastros e saltos verticais em 3 alturas."),
        (1, "Salas 3 e 4 — Galerias das Torres de Vigia", "Torres em paralaxe (Background_2.png), degraus rebaixados com portão ao solo e passarelas suspensas por correntes."),
        (2, "Salas 5 e 6 — Catacumbas Subterrâneas", "Interior fechado em cantaria escura, grades de ferro, arcos, lápides, tochas frias e plataformas móveis."),
        (3, "Sala 7 — Santuário do Guardião (Boss Room)", "Arena monumental de 960 px, pilares com gárgulas e portão de ferro titânico com fechadura rúnica."),
    ]
    w_cel = (larg_util - 4 * mm) / 2.0
    cards_bioma = []
    for b_idx, tit_b, desc_b in infos_biomas:
        prev_pil = _desenhar_miniatura_bioma(b_idx, w=340, h=126)
        rl_prev = _pil_para_rl_image(prev_pil, w_cel - 8 * mm, 22 * mm)
        sub_tab = Table(
            [[rl_prev], [Paragraph(tit_b, st_cap)], [Paragraph(desc_b, st_cap_sub)]],
            colWidths=[w_cel - 2 * mm],
        )
        sub_tab.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
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
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tb_biomas)
    story.append(Spacer(1, 2 * mm))

    # --- PAINEL DE COMBATE, MECÂNICAS E SPRITES DO PROTAGONISTA ---
    story.append(Paragraph("COMBATE DE PRECISÃO, ÉTER E DIREÇÃO VISUAL", st_sec))
    faixa_sprites = carregar_faixa_sprites_protagonista(114 * mm, 21 * mm)
    amostra_atlas = carregar_amostra_atlas_cantaria(54 * mm, 21 * mm)

    txt_combate = Paragraph(
        "<b>Parry Refinado & Hitstop:</b> Defesas cronometradas anulam golpes titânicos com congelamento de impacto, "
        "faíscas de aço e contra-ataques imediatos.<br/>"
        "<b>Impulsos Aéreos & Magias de Éter:</b> Saltos responsivos, corte aéreo e consumo estratégico de gemas de Éter "
        "para desencadear habilidades em área como a <i>Dança do Éter</i>.",
        st_body,
    )
    tb_comb = Table(
        [
            [faixa_sprites, amostra_atlas],
            [txt_combate, Paragraph("<b>Atlas Gótico de Cantaria</b><br/>Tiles procedurais e peças de Final/Assets.", st_cap_sub)],
        ],
        colWidths=[116 * mm, larg_util - 116 * mm],
    )
    tb_comb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PAINEL),
        ("BOX", (0, 0), (-1, -1), 1.0, C_OURO),
        ("GRID", (0, 0), (-1, -1), 0.5, C_OURO_ESCURO),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tb_comb)

    doc.build(
        story,
        onFirstPage=lambda c, d: _desenhar_fundo_pagina_escura(c, d, "GoZygrid Studios  ·  Exposição Oficial — Elos do Vazio"),
        onLaterPages=lambda c, d: _desenhar_fundo_pagina_escura(c, d, "GoZygrid Studios  ·  Exposição Oficial — Elos do Vazio"),
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
            [Paragraph("GoZygrid Studios  ·  Manual Técnico do Repositório Oficial — Elos do Vazio", st_banner_sub), ""],
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
        "# 3. Executar o jogo (ou .\\build_tudo.bat para compilar o .exe)<br/>"
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
        [Paragraph("elos-do-vazio/", st_tree_k), Paragraph("Diretório raiz do projeto distribuído pela GoZygrid Studios", st_step_v)],
        [Paragraph("|-- main.py", st_tree_k), Paragraph("Loop principal (960x540 virtual), câmera, física 2D, controle/teclado e máquina de estados.", st_step_v)],
        [Paragraph("|-- cenarios.py", st_tree_k), Paragraph("Renderizador de cenários, tileset 32x32 PixelArray, fundos em paralaxe, tochas e portões.", st_step_v)],
        [Paragraph("|-- gerenciador_salas.py", st_tree_k), Paragraph("Construtores das 7 salas em 4 biomas e loader automático do pacote Legacy-Dungeon (Final/Assets).", st_step_v)],
        [Paragraph("|-- sprites.py / config.py", st_tree_k), Paragraph("Loader modular de sprites (Hero/Inimigos/Chefes) e balanceamento global do jogo.", st_step_v)],
        [Paragraph("|-- combate.py / cenario_combate_25d.py", st_tree_k), Paragraph("Sistema tático de turnos com parry, QTE ofensivo, hitstop e arenas 2.5D por sala.", st_step_v)],
        [Paragraph("|-- instalador_gui.py / build_instalador.py", st_tree_k), Paragraph("Instalador gráfico 800x500 com música tema, atalhos Windows e empacotamento PyInstaller.", st_step_v)],
        [Paragraph("+-- assets/", st_tree_k), Paragraph("Logos, sprites do herói/inimigos, sons/músicas e recursos visuais (Legacy-Dungeon).", st_step_v)],
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
    out_exposicao = os.path.join(RAIZ, "elos_do_vazio_exposicao.pdf")
    out_guia = os.path.join(RAIZ, "elos_do_vazio_guia_github.pdf")
    gerar_pdf_exposicao(out_exposicao)
    print(f"[OK] PDF de Exposição gerado: {out_exposicao}")
    gerar_pdf_guia_github(out_guia)
    print(f"[OK] PDF Guia GitHub gerado: {out_guia}")


if __name__ == "__main__":
    main()
