@echo off
:: TRIBALs PC — lanzador del cliente de escritorio
:: Doble clic: abre la app con el buscador de tribu.
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "TRIBALs PC" pythonw "%~dp0tribal_pc.py"
) else (
    python "%~dp0tribal_pc.py"
)
