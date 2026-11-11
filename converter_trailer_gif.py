# -*- coding: utf-8 -*-
"""
Conversor Otimizado de Trecho do Trailer para GIF — Elos do Vazio (`converter_trailer_gif.py`).

Extrai os 6 segundos mais intensos de combate do arquivo `trailer_elos_do_vazio.mp4`
(por padrão o intervalo de Esquiva + Parry Perfeito 2.5D com Hitstop + Contra-ataque)
e exporta um GIF em loop contínuo otimizado para GitHub (`assets/trailer_preview.gif`,
largura de 640px, controle automático de peso abaixo do teto definido).

Também garante que `assets/logo_gozygrid.png` esteja disponível a partir dos recursos
locais caso o arquivo ainda não tenha sido copiado para `assets/`.
"""

import argparse
import os
import shutil
import subprocess
import sys


RAIZ = os.path.dirname(os.path.abspath(__file__))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

MP4_PADRAO = os.path.join(RAIZ, "trailer_elos_do_vazio.mp4")
GIF_PADRAO = os.path.join(RAIZ, "assets", "trailer_preview.gif")
LARGURA_GIF = 640
INICIO_COMBATE_PADRAO = 17.5
DURACAO_TRECHO_PADRAO = 6.0
FPS_GIF_PADRAO = 18
LIMITE_MB_PADRAO = 8.5


def garantir_dependencias_gif(permitir_instalar=True):
    """Verifica/instala bibliotecas opcionais para manipulação de vídeo e imagem."""
    faltantes = []
    for mod, pkg in (("PIL", "pillow"), ("imageio_ffmpeg", "imageio-ffmpeg"), ("imageio", "imageio")):
        try:
            __import__(mod)
        except ImportError:
            faltantes.append(pkg)

    if faltantes and permitir_instalar:
        print(f"[gif] Instalando dependências: {', '.join(faltantes)} ...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *faltantes])
        except Exception as exc:
            print(f"[gif] Aviso ao instalar via pip ({exc}). Continuando com backends presentes.")


def garantir_logo_gozygrid_assets():
    """Garante `assets/logo_gozygrid.png` para exibição no README.md do GitHub."""
    destino = os.path.join(RAIZ, "assets", "logo_gozygrid.png")
    if os.path.isfile(destino):
        return destino

    candidatos = [
        os.path.join(RAIZ, "assets", "ui", "logo_gozygrid.png"),
        os.path.join(RAIZ, "assets", "ui", "logo_gozygrid_studios.jpg"),
        os.path.join(RAIZ, "assets", "logo_gozygrid.jpg"),
        os.path.join(RAIZ, "assets", "logo_gozygrid.jfif"),
    ]
    for orig in candidatos:
        if not os.path.isfile(orig):
            continue
        try:
            from PIL import Image
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            img = Image.open(orig).convert("RGBA")
            img.save(destino, format="PNG", optimize=True)
            print(f"[assets] Logo GoZygrid Studios salva em: {destino}")
            return destino
        except Exception:
            pass
    return None


def _encontrar_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _converter_via_ffmpeg(mp4_path, gif_path, inicio, duracao, largura, fps, cores, ffmpeg_exe):
    """Converte MP4 -> GIF em 2 passes com `palettegen` + `paletteuse` para máxima nitidez e baixo peso."""
    filtro = (
        f"fps={fps},scale={largura}:-1:flags=lanczos,"
        f"split[s0][s1];"
        f"[s0]palettegen=max_colors={cores}:stats_mode=diff[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
    )
    cmd = [
        ffmpeg_exe, "-y",
        "-ss", f"{inicio:.2f}",
        "-t", f"{duracao:.2f}",
        "-i", mp4_path,
        "-vf", filtro,
        "-loop", "0",
        gif_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg falhou ({proc.returncode}): {proc.stderr[-300:]}")


def _converter_via_moviepy_ou_cv2(mp4_path, gif_path, inicio, duracao, largura, fps, cores):
    """Fallback usando MoviePy ou OpenCV + Pillow quando `ffmpeg` direto não está acessível."""
    from PIL import Image

    quadros_pil = []
    fim = inicio + duracao

    try:
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            from moviepy import VideoFileClip

        clip = VideoFileClip(mp4_path)
        sub = clip.subclipped(inicio, min(clip.duration, fim)) if hasattr(clip, "subclipped") else clip.subclip(inicio, min(clip.duration, fim))
        passo = 1.0 / float(max(1, fps))
        t_cur = 0.0
        while t_cur < sub.duration:
            arr = sub.get_frame(t_cur)
            im = Image.fromarray(arr).convert("RGB")
            alt = max(1, int(round(im.height * (largura / float(max(1, im.width))))))
            im = im.resize((largura, alt), Image.Resampling.LANCZOS)
            quadros_pil.append(im.quantize(colors=cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG))
            t_cur += passo
        sub.close()
        clip.close()
    except Exception:
        import cv2
        cap = cv2.VideoCapture(mp4_path)
        if not cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir o vídeo: {mp4_path}")
        fps_orig = cap.get(cv2.CAP_PROP_FPS) or 60.0
        step_frames = max(1, int(round(fps_orig / float(max(1, fps)))))
        idx_ini = int(round(inicio * fps_orig))
        idx_fim = int(round(fim * fps_orig))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx_ini)
        idx = idx_ini
        while idx <= idx_fim:
            ok, bgr = cap.read()
            if not ok:
                break
            if (idx - idx_ini) % step_frames == 0:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(rgb)
                alt = max(1, int(round(im.height * (largura / float(max(1, im.width))))))
                im = im.resize((largura, alt), Image.Resampling.LANCZOS)
                quadros_pil.append(im.quantize(colors=cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG))
            idx += 1
        cap.release()

    if not quadros_pil:
        raise RuntimeError("Nenhum quadro pôde ser extraído do vídeo para gerar o GIF.")

    dur_ms = max(20, int(round(1000.0 / float(max(1, fps)))))
    quadros_pil[0].save(
        gif_path,
        format="GIF",
        save_all=True,
        append_images=quadros_pil[1:],
        duration=dur_ms,
        loop=0,
        optimize=True,
    )


def converter_trailer_para_gif(
    mp4_path=MP4_PADRAO,
    gif_path=GIF_PADRAO,
    inicio=INICIO_COMBATE_PADRAO,
    duracao=DURACAO_TRECHO_PADRAO,
    largura=LARGURA_GIF,
    fps=FPS_GIF_PADRAO,
    limite_mb=LIMITE_MB_PADRAO,
    permitir_instalar=True,
):
    garantir_dependencias_gif(permitir_instalar=permitir_instalar)
    garantir_logo_gozygrid_assets()

    if not os.path.isfile(mp4_path):
        raise FileNotFoundError(
            f"Trailer não encontrado em '{mp4_path}'. Execute antes `python gerar_trailer.py`."
        )

    os.makedirs(os.path.dirname(os.path.abspath(gif_path)), exist_ok=True)
    ffmpeg_exe = _encontrar_ffmpeg()

    # Tentativas progressivas caso o arquivo inicial fique acima de `limite_mb`
    perfis = [
        (fps, 128),
        (max(12, fps - 4), 96),
        (max(10, fps - 6), 64),
    ]
    for idx, (fps_atual, max_cores) in enumerate(perfis):
        print(f"[gif] Extraindo {duracao:.1f}s ({inicio:.1f}s -> {inicio + duracao:.1f}s) | {largura}px @ {fps_atual} FPS ({max_cores} cores)...")
        if ffmpeg_exe:
            _converter_via_ffmpeg(mp4_path, gif_path, inicio, duracao, largura, fps_atual, max_cores, ffmpeg_exe)
        else:
            _converter_via_moviepy_ou_cv2(mp4_path, gif_path, inicio, duracao, largura, fps_atual, max_cores)

        tam_mb = os.path.getsize(gif_path) / (1024.0 * 1024.0)
        print(f"[gif] Tamanho gerado: {tam_mb:.2f} MB (limite alvo: {limite_mb:.1f} MB)")
        if tam_mb <= limite_mb or idx == len(perfis) - 1:
            print(f"[OK] GIF otimizado salvo em: {gif_path}")
            return gif_path

    return gif_path


def main():
    parser = argparse.ArgumentParser(description="Extrai trecho de combate de trailer_elos_do_vazio.mp4 para GIF otimizado.")
    parser.add_argument("--entrada", default=MP4_PADRAO, help="Caminho do vídeo .mp4 de origem.")
    parser.add_argument("--saida", default=GIF_PADRAO, help="Caminho do .gif otimizado de saída.")
    parser.add_argument("--inicio", type=float, default=INICIO_COMBATE_PADRAO, help="Segundo inicial do corte de combate.")
    parser.add_argument("--duracao", type=float, default=DURACAO_TRECHO_PADRAO, help="Duração em segundos (padrão: 6.0).")
    parser.add_argument("--largura", type=int, default=LARGURA_GIF, help="Largura final em pixels (padrão: 640).")
    parser.add_argument("--fps", type=int, default=FPS_GIF_PADRAO, help="Taxa de quadros do GIF (padrão: 18).")
    parser.add_argument("--limite-mb", type=float, default=LIMITE_MB_PADRAO, help="Peso máximo desejado em MB.")
    parser.add_argument("--no-install", action="store_true", help="Não instalar dependências ausentes.")
    args = parser.parse_args()

    converter_trailer_para_gif(
        mp4_path=args.entrada,
        gif_path=args.saida,
        inicio=max(0.0, args.inicio),
        duracao=max(1.0, args.duracao),
        largura=max(160, args.largura),
        fps=max(8, args.fps),
        limite_mb=max(1.0, args.limite_mb),
        permitir_instalar=not args.no_install,
    )


if __name__ == "__main__":
    main()

