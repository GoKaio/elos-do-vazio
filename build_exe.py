# -*- coding: utf-8 -*-
"""
Script Automatizado de Empacotamento Windows (build_exe.py)
Gera:
  1. Ícone multi-resolução Windows (assets/icone_jogo.ico e icon.ico) via Pillow.
  2. Executável autônomo do jogo em dist/Elos_do_Vazio/Elos_do_Vazio.exe via PyInstaller.
  3. Pacote comprimido do jogo + instalador gótico autônomo em
     dist_installer/Instalador_Elos_do_Vazio.exe.
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile


RAIZ = os.path.dirname(os.path.abspath(__file__))
ICONE_REL = os.path.join("assets", "icone_jogo.ico")
ICONE_ABS = os.path.join(RAIZ, ICONE_REL)
ICONE_RAIZ = os.path.join(RAIZ, "icon.ico")
PAYLOAD_DIR = os.path.join(RAIZ, "build_payload")
PAYLOAD_ZIP = os.path.join(PAYLOAD_DIR, "elos_do_vazio_payload.zip")
DIST_JOGO = os.path.join(RAIZ, "dist", "Elos_do_Vazio")
DIST_INSTALLER = os.path.join(RAIZ, "dist_installer")


def garantir_icone_jogo():
    """
    Garante que assets/icone_jogo.ico e icon.ico sejam arquivos Windows ICO válidos
    multi-resolução (16..256px RGBA), evitando falha no compilador de recursos do PyInstaller.
    """
    from PIL import Image, ImageDraw

    os.makedirs(os.path.dirname(ICONE_ABS), exist_ok=True)
    precisa_gerar = not os.path.exists(ICONE_ABS)
    if os.path.exists(ICONE_ABS):
        try:
            with Image.open(ICONE_ABS) as chk:
                if chk.format != "ICO":
                    precisa_gerar = True
        except Exception:
            precisa_gerar = True

    raiz_invalido = True
    if os.path.exists(ICONE_RAIZ):
        try:
            with Image.open(ICONE_RAIZ) as chk2:
                if chk2.format == "ICO":
                    raiz_invalido = False
        except Exception:
            raiz_invalido = True

    if precisa_gerar or raiz_invalido:
        fonte_logo = os.path.join(RAIZ, "assets", "ui", "logo_elos_do_vazio.png")
        if os.path.exists(fonte_logo):
            src = Image.open(fonte_logo).convert("RGBA")
        elif os.path.exists(ICONE_RAIZ):
            src = Image.open(ICONE_RAIZ).convert("RGBA")
        else:
            src = Image.new("RGBA", (512, 512), (15, 15, 26, 255))

        # Recorta o medalhão central (círculo rúnico ciano + anel dourado) em proporção 1:1
        lado = min(src.width, src.height)
        crop_side = int(lado * 0.92)
        cx, cy = src.width // 2, src.height // 2
        box = (
            max(0, cx - crop_side // 2),
            max(0, cy - crop_side // 2),
            min(src.width, cx + crop_side // 2),
            min(src.height, cy + crop_side // 2),
        )
        emblema = src.crop(box).resize((476, 476), Image.Resampling.LANCZOS)

        # Base ébano com moldura dourada chanfrada para destaque nítido na Barra de Tarefas
        tela_ico = Image.new("RGBA", (512, 512), (15, 15, 26, 255))
        tela_ico.paste(emblema, (18, 18), emblema)
        draw = ImageDraw.Draw(tela_ico)
        draw.rounded_rectangle((6, 6, 505, 505), radius=54, outline=(245, 158, 11, 255), width=10)
        draw.rounded_rectangle((18, 18, 493, 493), radius=42, outline=(253, 230, 138, 220), width=4)

        tamanhos = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        tela_ico.save(ICONE_ABS, format="ICO", sizes=tamanhos)
        tela_ico.save(ICONE_RAIZ, format="ICO", sizes=tamanhos)
        print(f"[build_exe] Ícone multi-resolução gerado com sucesso: {ICONE_ABS}")
    else:
        print(f"[build_exe] Ícone válido detectado: {ICONE_ABS}")

    return ICONE_ABS


def _coletar_datas_jogo():
    """Coleta pastas e arquivos de runtime existentes no projeto."""
    datas = []
    for pasta in ("assets", "fontes", "sons", "Final"):
        p_abs = os.path.join(RAIZ, pasta)
        if os.path.isdir(p_abs):
            datas.append((p_abs, pasta))

    # Inclui tools apenas se houver scripts/assets diretos (ignorando repositórios de referência git)
    tools_abs = os.path.join(RAIZ, "tools")
    if os.path.isdir(tools_abs):
        for nome in os.listdir(tools_abs):
            if nome in ("repos_ref", "__pycache__"):
                continue
            item = os.path.join(tools_abs, nome)
            if os.path.isfile(item) and not item.endswith(".pyc"):
                datas.append((item, "tools"))

    for arq in ("elos_do_vazio_ui_positions.json", "LEIA-ME.txt", "COMO_JOGAR.txt", "icon.ico"):
        arq_abs = os.path.join(RAIZ, arq)
        if os.path.isfile(arq_abs):
            datas.append((arq_abs, "."))
    return datas


def _verificar_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        print("[build_exe] ERRO: PyInstaller não encontrado. Instale com: pip install pyinstaller", file=sys.stderr)
        return False


def compilar_jogo(onefile=False):
    """Compila main.py para dist/Elos_do_Vazio/Elos_do_Vazio.exe (ou executável único)."""
    if not _verificar_pyinstaller():
        raise SystemExit(1)

    icone = garantir_icone_jogo()
    datas = _coletar_datas_jogo()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile" if onefile else "--onedir",
        "--windowed",
        "--noconsole",
        "--name", "Elos_do_Vazio",
        "--icon", icone,
        "--collect-all", "pygame",
        "--collect-all", "pygame_ce",
        "--hidden-import", "pygame",
        "--hidden-import", "caminhos",
        "--hidden-import", "progresso",
        "--hidden-import", "ranking",
        "--hidden-import", "ui",
        "--hidden-import", "ui_procedural",
        "--hidden-import", "ui_medieval",
        "--hidden-import", "ui_assets",
        "--hidden-import", "ui_configurador",
        "--hidden-import", "combate",
        "--hidden-import", "combate_ui",
        "--hidden-import", "cenarios",
        "--hidden-import", "gerenciador_salas",
        "--hidden-import", "cenario_combate_25d",
        "--hidden-import", "dados_combatentes",
        "--hidden-import", "sprites",
        "--hidden-import", "audio",
        "--hidden-import", "menu",
        "--hidden-import", "splash_estudio",
        "--hidden-import", "intro",
        "--hidden-import", "cutscene",
        "--hidden-import", "cutscenes",
        "--hidden-import", "bot_autonomo",
        "--hidden-import", "procedural_gen",
    ]
    for src, dst in datas:
        cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
    cmd.append(os.path.join(RAIZ, "main.py"))

    print("[build_exe] Executando PyInstaller para o jogo principal...")
    res = subprocess.run(cmd, cwd=RAIZ)
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller falhou ao compilar o jogo (código {res.returncode}).")

    exe_esperado = os.path.join(RAIZ, "dist", "Elos_do_Vazio.exe" if onefile else os.path.join("Elos_do_Vazio", "Elos_do_Vazio.exe"))
    if not os.path.isfile(exe_esperado):
        raise FileNotFoundError(f"Executável esperado não encontrado: {exe_esperado}")
    print(f"[build_exe] Jogo compilado com sucesso: {exe_esperado}")
    return exe_esperado


def criar_payload_zip():
    """Empacota dist/Elos_do_Vazio em build_payload/elos_do_vazio_payload.zip para o instalador."""
    if not os.path.isdir(DIST_JOGO):
        raise FileNotFoundError(f"Diretório de build '{DIST_JOGO}' não encontrado para empacotar.")

    os.makedirs(PAYLOAD_DIR, exist_ok=True)
    if os.path.exists(PAYLOAD_ZIP):
        os.remove(PAYLOAD_ZIP)

    total = 0
    with zipfile.ZipFile(PAYLOAD_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for raiz, _, arqs in os.walk(DIST_JOGO):
            for arq in arqs:
                caminho = os.path.join(raiz, arq)
                rel = os.path.relpath(caminho, DIST_JOGO)
                zf.write(caminho, rel)
                total += 1
    tamanho_mb = os.path.getsize(PAYLOAD_ZIP) / (1024.0 * 1024.0)
    print(f"[build_exe] Payload gerado: {PAYLOAD_ZIP} ({total} arquivos, {tamanho_mb:.2f} MB)")
    return PAYLOAD_ZIP


def compilar_instalador():
    """Compila instalador_gui.py em dist_installer/Instalador_Elos_do_Vazio.exe."""
    if not _verificar_pyinstaller():
        raise SystemExit(1)

    icone = garantir_icone_jogo()
    if not os.path.isfile(PAYLOAD_ZIP):
        criar_payload_zip()

    os.makedirs(DIST_INSTALLER, exist_ok=True)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--noconsole",
        "--name", "Instalador_Elos_do_Vazio",
        "--distpath", DIST_INSTALLER,
        "--workpath", os.path.join(RAIZ, "build_installer_work"),
        "--specpath", os.path.join(RAIZ, "build_installer_work"),
        "--icon", icone,
        "--collect-all", "pygame",
        "--hidden-import", "ui_procedural",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "--add-data", f"{PAYLOAD_ZIP}{os.pathsep}payload",
        "--add-data", f"{icone}{os.pathsep}assets",
    ]
    sons_dir = os.path.join(RAIZ, "assets", "sons")
    if os.path.isdir(sons_dir):
        cmd.extend(["--add-data", f"{sons_dir}{os.pathsep}{os.path.join('assets', 'sons')}"])
    for bg_nome in ("Background_0.png", "Background_1.png"):
        bg_path = os.path.join(RAIZ, "assets", "final_pack", bg_nome)
        if os.path.isfile(bg_path):
            cmd.extend(["--add-data", f"{bg_path}{os.pathsep}{os.path.join('assets', 'final_pack')}"])
    cmd.append(os.path.join(RAIZ, "instalador_gui.py"))

    print("[build_exe] Compilando Instalador_Elos_do_Vazio.exe...")
    res = subprocess.run(cmd, cwd=RAIZ)
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller falhou ao compilar o instalador (código {res.returncode}).")

    out_exe = os.path.join(DIST_INSTALLER, "Instalador_Elos_do_Vazio.exe")
    if not os.path.isfile(out_exe):
        raise FileNotFoundError(f"Instalador não encontrado após compilação: {out_exe}")
    print(f"[build_exe] Instalador compilado com sucesso: {out_exe}")
    return out_exe


def main():
    parser = argparse.ArgumentParser(description="Build e Empacotamento Windows para Elos do Vazio")
    parser.add_argument("--onefile", action="store_true", help="Compila o jogo em arquivo único em vez de --onedir.")
    parser.add_argument("--installer", action="store_true", help="Compila também o instalador gótico em dist_installer/.")
    parser.add_argument("--only-installer", action="store_true", help="Recompila apenas o instalador (usa dist/Elos_do_Vazio existente).")
    args = parser.parse_args()

    garantir_icone_jogo()
    if args.only_installer:
        criar_payload_zip()
        compilar_instalador()
        return

    compilar_jogo(onefile=args.onefile)
    if args.installer:
        if args.onefile:
            os.makedirs(DIST_JOGO, exist_ok=True)
            shutil.copy2(os.path.join(RAIZ, "dist", "Elos_do_Vazio.exe"), os.path.join(DIST_JOGO, "Elos_do_Vazio.exe"))
        criar_payload_zip()
        compilar_instalador()


if __name__ == "__main__":
    main()
