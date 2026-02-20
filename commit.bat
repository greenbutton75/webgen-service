@echo off
setlocal

:: ============================================================
:: WebGen — git commit & push helper
:: Usage: commit.bat "your commit message here"
:: ============================================================

set "REPO_URL=https://github.com/greenbutton75/webgen-service.git"
set "BRANCH=main"
set "WEBGEN_DIR=%~dp0"

cd /d "%WEBGEN_DIR%"

:: Init repo if not yet a git repo
if not exist ".git" (
    echo [INIT] Initializing git repo...
    git init
    git remote add origin "%REPO_URL%"
)

:: Check remote exists, add if missing
git remote get-url origin >nul 2>&1 || git remote add origin "%REPO_URL%"

:: Get commit message from arg or prompt
set "MSG=%~1"
if "%MSG%"=="" (
    set /p MSG="Commit message: "
)
if "%MSG%"=="" (
    echo ERROR: Commit message is required.
    exit /b 1
)

:: Stage all changes
git add -A

:: Show what's staged
echo.
echo [STAGED CHANGES]
git status --short
echo.

:: Commit
git commit -m "%MSG%"

:: Push — try normal push first, force-with-lease on conflict
git push origin %BRANCH% 2>nul || (
    echo [WARN] Normal push failed, retrying with --force-with-lease ...
    git push --force-with-lease origin %BRANCH%
)

echo.
echo [OK] Pushed to %BRANCH%
endlocal
