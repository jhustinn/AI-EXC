# Men supervisory dua layanan: engine Python (8010) dan Laravel (8002).
# Dipakai karena keduanya pernah mati sendiri tanpa alasan jelas -
# dashboard menolak koneksi padahal engine masih hidup.
#
# Jalankan:  powershell -File scripts\watchdog.ps1
# Berhenti:  Ctrl+C di jendela ini.

$ErrorActionPreference = 'Continue'
$root = 'E:\App\AI-CCTV'
$log  = "$root\data\watchdog.log"

function catat($m) {
    "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $m | Add-Content $log -Encoding UTF8
}

function hidup($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -EA SilentlyContinue)
}

function pyserial($port) {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -EA SilentlyContinue
    if ($c) { return $c[0].OwningProcess }
    return $null
}

catat "=== watchdog START ==="

while ($true) {
    # --- engine Python 8010 ---
    if (-not (hidup 8010)) {
        catat "engine 8010 MATI - menjalankan ulang"
        $env:PYTHONPATH = "$root\src"
        Start-Process -FilePath "$root\.venv\Scripts\python.exe" `
            -ArgumentList '-m','uvicorn','excavator.web.main:app','--host','127.0.0.1','--port','8010' `
            -WorkingDirectory $root `
            -RedirectStandardOutput "$root\data\engine.log" `
            -RedirectStandardError  "$root\data\engine.err" `
            -NoNewWindow
        Start-Sleep 25
        catat ("engine 8010 -> " + (hidup 8010))
    }

    # --- Laravel 8002 ---
    if (-not (hidup 8002)) {
        catat "laravel 8002 MATI - menjalankan ulang"
        Start-Process powershell `
            -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"$root\laravel\start-server.ps1" `
            -WindowStyle Hidden
        Start-Sleep 25
        catat ("laravel 8002 -> " + (hidup 8002))
    }

    Start-Sleep 15
}