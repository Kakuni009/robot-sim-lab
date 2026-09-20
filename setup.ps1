$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.runtime/python'
    $env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.cache/uv'
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
        & uv venv --managed-python --python 3.12 --seed .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
    }
    & ./.venv/Scripts/python.exe -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128 --cache-dir .cache/pip --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed.' }
    & ./.venv/Scripts/python.exe scripts/install_isaac.py
    if ($LASTEXITCODE -ne 0) { throw 'Isaac Sim installation failed.' }
    & ./.venv/Scripts/python.exe -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed.' }
} finally {
    Pop-Location
}
