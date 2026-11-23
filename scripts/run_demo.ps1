$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python' }
}
$pythonExe = (Resolve-Path '.venv\Scripts\python.exe').Path
& $pythonExe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Instalación fallida' }
docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'Abre Docker Desktop y espera a que el motor esté listo' }
& $pythonExe -m src.train
if ($LASTEXITCODE -ne 0) { throw 'Entrenamiento fallido' }
& $pythonExe kafka\producer.py --delay 0.05 --demo-invalid
if ($LASTEXITCODE -ne 0) { throw 'Productor fallido' }
& $pythonExe kafka\consumer.py --idle-timeout 20
if ($LASTEXITCODE -ne 0) { throw 'Consumidor fallido' }
& $pythonExe scripts\verify_pipeline.py
if ($LASTEXITCODE -ne 0) { throw 'Verificación fallida' }
Write-Host 'Demo terminada. Abre dashboards\Happiness.pbip y actualiza los datos.'
