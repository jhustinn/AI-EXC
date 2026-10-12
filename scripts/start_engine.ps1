$ErrorActionPreference = "Continue"
$root = "E:\App\AI-CCTV"
$log = "$root\data\engine.log"
$port = 8010

New-Item -ItemType Directory -Path "$root\data" -Force | Out-Null

# pastikan port bebas
$busy = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    foreach ($procId in ($busy.OwningProcess | Select-Object -Unique)) {
        Write-Host "stop PID $procId di port $port"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
}

Remove-Item $log -Force -ErrorAction SilentlyContinue

$cmd = "`$env:PYTHONPATH='$root\src'; " +
       "`$env:EXCAVATOR_CONFIG='$root\config.excavator.yaml'; " +
       "cd '$root'; " +
       ".venv\Scripts\python.exe -m uvicorn excavator.web.main:app " +
       "--host 127.0.0.1 --port $port *> '$log'"

Start-Process powershell -ArgumentList '-NoProfile', '-Command', $cmd -WindowStyle Hidden | Out-Null

# tunggu sampai health endpoint menjawab
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 5
        if ($r.engine) {
            Write-Host "engine jalan  ->  http://127.0.0.1:$port"
            Write-Host "stream        ->  http://127.0.0.1:$port/stream"
            Write-Host "dashboard     ->  http://localhost:8002/dashboard"
            exit 0
        }
    } catch {
        # lanjut menunggu
    }
}

Write-Host "GAGAL start. Isi log:"
Get-Content $log -Tail 20 -ErrorAction SilentlyContinue
exit 1