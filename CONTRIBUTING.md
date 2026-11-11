# Contribuindo com Elos do Vazio

Obrigado pelo interesse em contribuir com **Elos do Vazio** (**GoZygrid Studios**)!

## Ambiente de Desenvolvimento

1. Faça um **fork** e clone o repositório:
   ```powershell
   git clone https://github.com/GoKaio/elos-do-vazio.git
   cd elos-do-vazio
   ```
2. Crie um ambiente virtual e instale a dependência principal:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Execute o jogo localmente:
   ```powershell
   python main.py
   ```

## Verificações Antes de Enviar um Pull Request

Execute a compilação de sintaxe e uma inicialização rápida em modo *headless*:

```powershell
python -m compileall -q .
python -c "import os, sys; sys.path.insert(0, os.path.abspath('src')); os.environ.update({'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','HEADLESS':'1'}); import pygame; pygame.init(); pygame.display.set_mode((960,540)); from splash_estudio import AnimacaoAberturaEstudio; s=AnimacaoAberturaEstudio(); s.update(0.1); print('OK')"
```

## Boas Práticas
- Mantenha funções focadas e preserve docstrings/comentários existentes.
- Não versione arquivos `.zip`, logs (`*.log`), saves locais (`progresso*.json`, `ranking*.json`, `perfis/`) ou pastas de build (`build/`, `dist/`, `dist_installer/`).
- Ao alterar mecânicas ou telas principais, atualize o [README.md](README.md) ou os scripts de documentação se aplicável.
