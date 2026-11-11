$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot

Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "  ELOS DO VAZIO — CRIAR REPOSITÓRIO E PUBLICAR NO GITHUB (GoKaio)" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRO] Git não encontrado no PATH. Instale em https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

$gitUser = (git config user.name)
if ([string]::IsNullOrWhiteSpace($gitUser)) { $gitUser = "GoKaio" }
Write-Host "[Git] Conta configurada: $gitUser" -ForegroundColor Cyan

# 1) Garante PDFs, trailer MP4, GIF de prévia e logo PNG para o README.md
if (-not (Test-Path "assets\trailer_preview.gif") -or -not (Test-Path "assets\logo_gozygrid.png")) {
    if (-not (Test-Path "trailer_elos_do_vazio.mp4")) {
        Write-Host "[1/4] Gerando trailer oficial (trailer_elos_do_vazio.mp4)..." -ForegroundColor Cyan
        python gerar_trailer.py
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    Write-Host "[2/4] Extraindo prévia GIF (640px) e logo GoZygrid Studios para assets/..." -ForegroundColor Cyan
    python converter_trailer_gif.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "[3/4] Atualizando PDFs de documentação (página única)..." -ForegroundColor Cyan
python gerar_documentos_pdf.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2) Inicializa repositório local na branch main
if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

git add -A
$pendentes = git status --porcelain
if ($pendentes) {
    git commit -m "Versão inicial completa: Elos do Vazio (GoZygrid Studios)"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "[Git] Nenhuma alteração pendente para novo commit." -ForegroundColor Gray
}

# 3) Cria repositório remoto e envia via GitHub CLI (`gh`) ou `git push`
$temGh = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)
$ghLogado = $false
if ($temGh) {
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    gh auth status | Out-Null
    $ghLogado = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevPref
}

if ($ghLogado) {
    Write-Host "[4/4] Criando/enviando repositório público '$gitUser/elos-do-vazio' via GitHub CLI..." -ForegroundColor Green
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    gh repo view "$gitUser/elos-do-vazio" | Out-Null
    $repoExiste = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevPref

    $temRemote = git remote | Where-Object { $_ -eq "origin" }
    if (-not $repoExiste) {
        if ($temRemote) { git remote remove origin }
        gh repo create elos-do-vazio --public --source=. --remote=origin --push
    } else {
        if (-not $temRemote) { git remote add origin "https://github.com/$gitUser/elos-do-vazio.git" }
        git push -u origin main
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if (Test-Path "dist_installer\Instalador_Elos_do_Vazio.exe") {
        Write-Host "[Release] Publicando Instalador_Elos_do_Vazio.exe em v1.0..." -ForegroundColor Cyan
        $prevPref = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        gh release view v1.0 | Out-Null
        $temRelease = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $prevPref
        if ($temRelease) {
            gh release upload v1.0 "dist_installer\Instalador_Elos_do_Vazio.exe" --clobber
        } else {
            gh release create v1.0 "dist_installer\Instalador_Elos_do_Vazio.exe" --title "Elos do Vazio v1.0" --notes "Instalador oficial Windows (GoZygrid Studios)"
        }
    }
    Write-Host "[OK] Projeto publicado no GitHub com sucesso!" -ForegroundColor Green
} else {
    $urlRepo = "https://github.com/$gitUser/elos-do-vazio.git"
    $temRemote = git remote | Where-Object { $_ -eq "origin" }
    if (-not $temRemote) {
        git remote add origin $urlRepo
    }
    Write-Host ""
    Write-Host "[AÇÃO NECESSÁRIA] GitHub CLI ('gh') não encontrado ou não autenticado." -ForegroundColor Yellow
    Write-Host "1. Crie um repositório vazio chamado 'elos-do-vazio' em: https://github.com/new"
    Write-Host "   (sem marcar README/.gitignore, pois já foram criados localmente)"
    Read-Host "2. Depois de criar no navegador, pressione [ENTER] aqui para enviar (git push)"
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "[OK] Código enviado para $urlRepo!" -ForegroundColor Green
}
