# -*- coding: utf-8 -*-
"""Utilitário para clonar repositórios de referência procedural e projeção 2.5D."""

import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS_DIR = os.path.join(BASE_DIR, "tools", "repos_ref")

REPOSITORIOS = [
    ("https://github.com/Atman50/Procedural-Dungeon-Generation-Pygame.git", "bsp_dungeon",
     "https://github.com/jpyankel/PyBSP_Dungeon_Generator.git"),
    ("https://github.com/le-chartreux/pyprocgen.git", "pyprocgen", None),
    ("https://github.com/StanislavPetrovV/Mode7.git", "mode7_pygame",
     "https://github.com/Robomarchello/Mode7.git"),
]


def clonar_repositorios():
    os.makedirs(REPOS_DIR, exist_ok=True)
    for url, destino_nome, fallback_url in REPOSITORIOS:
        destino = os.path.join(REPOS_DIR, destino_nome)
        if os.path.isdir(destino) and os.listdir(destino):
            print(f"[OK] Já existe: {destino}")
            continue
        urls_tentar = [u for u in (url, fallback_url) if u]
        for tentativa_url in urls_tentar:
            print(f"[CLONE] {tentativa_url} -> {destino}")
            try:
                subprocess.run(["git", "clone", "--depth", "1", tentativa_url, destino], check=True)
                break
            except subprocess.CalledProcessError as exc:
                print(f"[AVISO] Falha ao clonar {tentativa_url}: {exc}")


if __name__ == "__main__":
    clonar_repositorios()
