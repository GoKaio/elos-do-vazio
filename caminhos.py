# -*- coding: utf-8 -*-
"""
ELOS DO VAZIO - Módulo de Auditoria, Caminhos e Registro de Erros (Logging Global).

Garante:
  1. Captura global de exceções não tratadas (sys.excepthook e threading.excepthook).
  2. Gravação de logs com data/hora, especificações do sistema e tracebacks em "jogo_erro.log".
  3. Resolução robusta de caminhos tanto em execução direta (script) quanto congelada (.exe via PyInstaller).
  4. Exibição de diálogo nativo amigável no Windows se o jogo encontrar uma falha fatal.
"""
import sys
import os
import traceback
import datetime
import platform

# Garante suporte a UTF-8 completo no terminal e console do Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def obter_dir_base():
    """Retorna o diretório base da aplicação (diretório do .exe se congelado, ou do script)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    """Resolve caminhos de recursos tanto em execução direta quanto empacotada via PyInstaller."""
    bases = []
    if hasattr(sys, "_MEIPASS"):
        bases.append(sys._MEIPASS)
    bases.append(obter_dir_base())
    bases.append(os.path.abspath("."))
    for base in bases:
        candidato = os.path.join(base, relative_path)
        if os.path.exists(candidato):
            return candidato
    base_padrao = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_padrao, relative_path)


obter_caminho_recurso = resource_path

_DIR_DADOS_CACHE = None


def obter_dir_dados():
    """
    Retorna o diretório gravável para saves, perfis, rankings e logs.
    Usa a pasta do aplicativo se gravável; caso esteja em diretório protegido
    (ex.: Program Files sem privilégios de administrador), utiliza %LOCALAPPDATA%\\Elos do Vazio.
    """
    global _DIR_DADOS_CACHE
    if _DIR_DADOS_CACHE is not None:
        return _DIR_DADOS_CACHE

    base = obter_dir_base()
    if not getattr(sys, "frozen", False):
        _DIR_DADOS_CACHE = base
        return base

    # Verifica permissão real de escrita no diretório do executável
    teste = os.path.join(base, ".write_probe.tmp")
    try:
        with open(teste, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(teste)
        _DIR_DADOS_CACHE = base
        return base
    except Exception:
        pass

    local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    destino = os.path.join(local_app, "Elos do Vazio")
    try:
        os.makedirs(destino, exist_ok=True)
    except Exception:
        destino = os.path.abspath(".")
    _DIR_DADOS_CACHE = destino
    return destino


def obter_caminho_save():
    """Caminho absoluto para o arquivo de save do jogo."""
    dir_dados = obter_dir_dados()
    novo = os.path.join(dir_dados, "elos_do_vazio_save.json")
    antigo = os.path.join(dir_dados, "endbound_save.json")
    if not os.path.exists(novo) and os.path.exists(antigo):
        try:
            os.replace(antigo, novo)
        except Exception:
            pass
    return novo


def obter_caminho_log():
    """Caminho absoluto para o arquivo de log de erros e eventos."""
    return os.path.join(obter_dir_dados(), "jogo_erro.log")


def registrar_log(nivel, mensagem, exc_info=None):
    """Grava uma entrada formatada no arquivo jogo_erro.log e no terminal."""
    caminho = obter_caminho_log()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] [{nivel.upper()}] {mensagem}\n"
    if exc_info is not None:
        if isinstance(exc_info, BaseException):
            tb = "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
        else:
            tb = traceback.format_exc()
        linha += tb + "\n"
    try:
        with open(caminho, "a", encoding="utf-8-sig") as f:
            f.write(linha)
            f.flush()
    except Exception:
        pass
    try:
        print(linha, end="")
    except Exception:
        pass


def log_info(msg):
    registrar_log("INFO", msg)


def log_aviso(msg):
    registrar_log("AVISO", msg)


def log_erro(msg, exc_info=None):
    registrar_log("ERRO", msg, exc_info=exc_info)


def _excepthook(exc_type, exc_value, exc_traceback):
    """Gancho global de captura de exceções não tratadas."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    info_sistema = (
        f"Sistema Operacional: {platform.system()} {platform.release()} ({sys.platform})\n"
        f"Versão Python: {sys.version.split()[0]} | Arquitetura: {platform.architecture()[0]}\n"
        f"Modo Executável (Frozen): {getattr(sys, 'frozen', False)}\n"
        f"Diretório Base: {obter_dir_base()}\n"
        f"Diretório de Trabalho (CWD): {os.getcwd()}"
    )
    relatorio = f"FALHA CRÍTICA INESPERADA:\n{info_sistema}\n\nExceção: {exc_type.__name__}: {exc_value}\n\nTraceback completo:\n{tb_str}"
    registrar_log("FATAL", relatorio)

    # Exibe caixa de mensagem explicativa no Windows se em ambiente com GUI
    if sys.platform == "win32" and os.environ.get("SDL_VIDEODRIVER") != "dummy" and not os.environ.get("HEADLESS"):
        try:
            import ctypes
            titulo = "ELOS DO VAZIO — Falha Inesperada"
            corpo = (
                f"Ocorreu um erro inesperado e o jogo precisou ser interrompido:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Um relatório detalhado foi registrado em:\n"
                f"{obter_caminho_log()}\n\n"
                f"Por favor, verifique o arquivo para mais detalhes técnicos."
            )
            # MB_ICONERROR | MB_OK | MB_TASKMODAL
            ctypes.windll.user32.MessageBoxW(0, corpo, titulo, 0x10 | 0x0 | 0x2000)
        except Exception:
            pass


def instalar_tratador_excecoes():
    """Registra os hooks de captura no sys e threading."""
    sys.excepthook = _excepthook
    try:
        import threading
        if hasattr(threading, "excepthook"):
            def _thread_hook(args):
                _excepthook(args.exc_type, args.exc_value, args.exc_traceback)
            threading.excepthook = _thread_hook
    except Exception:
        pass
    log_info("Sistema de captura de erros e logging inicializado com sucesso.")
