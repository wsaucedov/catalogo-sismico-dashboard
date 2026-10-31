@echo off
REM ==============================================================
REM  Dashboard Catalogo Sismico del Peru 1960-2025
REM  Doble clic para ejecutar en Windows (requiere Python 3.10+).
REM  La primera vez instala dependencias (2-4 min, con internet).
REM ==============================================================
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo [ERROR] No se encontro Python. Instalelo desde https://www.python.org/downloads/
  echo         marcando la opcion "Add python.exe to PATH", y vuelva a ejecutar este archivo.
  echo         Alternativa sin Python: ejecutar_docker.bat (requiere Docker Desktop^).
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual .venv ...
  %PY% -m venv .venv || ( echo [ERROR] No se pudo crear el entorno virtual. & pause & exit /b 1 )
  echo Instalando dependencias ...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || ( echo [ERROR] Fallo la instalacion. & pause & exit /b 1 )
)

echo.
echo Iniciando el dashboard en http://localhost:8501
echo (Cierre esta ventana o presione Ctrl+C para detenerlo.)
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false
pause
