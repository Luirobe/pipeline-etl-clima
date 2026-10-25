@echo off
rem Ejecuta el pipeline de clima. Lo usa el Programador de tareas de Windows.

rem Ir a la carpeta donde está este archivo (importante para que encuentre data/ y logs/)
cd /d "%~dp0"

if not exist logs mkdir logs

python main.py >> logs\tarea_programada.log 2>&1
