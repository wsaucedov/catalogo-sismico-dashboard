@echo off
REM ==============================================================
REM  Ejecuta el dashboard en un contenedor Docker (Windows).
REM  Requiere Docker Desktop iniciado. No requiere Python.
REM ==============================================================
chcp 65001 >nul
cd /d "%~dp0"
where docker >nul 2>nul || ( echo [ERROR] Docker no esta instalado o no esta en el PATH. & pause & exit /b 1 )
docker info >nul 2>nul || ( echo [ERROR] Inicie Docker Desktop y vuelva a intentar. & pause & exit /b 1 )

echo Construyendo e iniciando el contenedor (la primera vez tarda unos minutos) ...
docker compose up -d --build || ( echo [ERROR] No se pudo iniciar el contenedor. & pause & exit /b 1 )
echo Esperando a que la app responda ...
timeout /t 8 /nobreak >nul
start "" http://localhost:8501
echo.
echo Dashboard disponible en http://localhost:8501
echo Para detenerlo:  docker compose down
pause
