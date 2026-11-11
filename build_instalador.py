# -*- coding: utf-8 -*-
"""
Script Dedicado de Empacotamento e Build do Instalador (`build_instalador.py`).

Orquestra:
  1. Verificação e descompactação opcional de `Legacy-Dungeon_V0.2_vacaroxa.zip` caso presente na raiz.
  2. Geração do ícone multi-resolução `.ico` do jogo (`assets/icone_jogo.ico` e `icon.ico`).
  3. Compilação do executável principal `dist/Elos_do_Vazio/Elos_do_Vazio.exe` (via `--all` ou se ausente).
  4. Empacotamento do payload ZIP e compilação de `dist_installer/Instalador_Elos_do_Vazio.exe`
     com áudio, ícone e GUI gótica (`instalador_gui.py`).
"""

import argparse
import os
import sys
import zipfile

import build_exe


RAIZ = os.path.dirname(os.path.abspath(__file__))


def extrair_assets_legacy_dungeon_se_presente():
    """Se `Legacy-Dungeon_V0.2_vacaroxa.zip` existir no projeto, extrai `Final/Assets` automaticamente."""
    alvo_assets = os.path.join(RAIZ, "assets", "Legacy-Dungeon")
    marcador = os.path.join(alvo_assets, "Final", "Assets", "Background_1.png")
    if os.path.isfile(marcador):
        return

    candidatos_zip = [
        os.path.join(RAIZ, "Legacy-Dungeon_V0.2_vacaroxa.zip"),
        os.path.join(RAIZ, "assets", "Legacy-Dungeon_V0.2_vacaroxa.zip"),
    ]
    for zip_path in candidatos_zip:
        if os.path.isfile(zip_path):
            print(f"[build_instalador] Extraindo assets góticos de '{zip_path}'...")
            os.makedirs(alvo_assets, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    rel_norm = os.path.normpath(info.filename).lstrip("\\/")
                    dest = os.path.abspath(os.path.join(alvo_assets, rel_norm))
                    if not (dest == os.path.abspath(alvo_assets) or dest.startswith(os.path.abspath(alvo_assets) + os.sep)):
                        continue
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with zf.open(info, "r") as src, open(dest, "wb") as dst:
                        dst.write(src.read())
            print(f"[build_instalador] Assets extraídos em: {alvo_assets}")
            return


def main():
    parser = argparse.ArgumentParser(description="Build completo e instalador Windows — Elos do Vazio")
    parser.add_argument("--all", action="store_true", help="Compila o jogo principal e em seguida gera o instalador (padrão).")
    parser.add_argument("--reuse-dist", action="store_true", help="Reutiliza dist/Elos_do_Vazio existente ao empacotar o instalador.")
    parser.add_argument("--only-installer", action="store_true", help="Gera apenas o instalador usando o dist/Elos_do_Vazio atual.")
    parser.add_argument("--onefile", action="store_true", help="Compila o jogo em modo --onefile antes de empacotar.")
    args = parser.parse_args()

    extrair_assets_legacy_dungeon_se_presente()
    build_exe.garantir_icone_jogo()

    exe_jogo = os.path.join(build_exe.DIST_JOGO, "Elos_do_Vazio.exe")
    deve_compilar_jogo = args.all or (not args.only_installer and (not args.reuse_dist or not os.path.isfile(exe_jogo)))

    if deve_compilar_jogo:
        build_exe.compilar_jogo(onefile=args.onefile)
        if args.onefile:
            os.makedirs(build_exe.DIST_JOGO, exist_ok=True)
            import shutil
            shutil.copy2(
                os.path.join(RAIZ, "dist", "Elos_do_Vazio.exe"),
                exe_jogo,
            )

    build_exe.criar_payload_zip()
    out_installer = build_exe.compilar_instalador()
    print(f"[build_instalador] Pacote final pronto em: {out_installer}")


if __name__ == "__main__":
    main()

