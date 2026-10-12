$ErrorActionPreference = "Continue"
$root = "E:\App\AI-CCTV\laravel"
$php = "C:\Program Files\php-8.5.6\php.exe"
$log = "E:\App\AI-CCTV\data\laravel_serve.log"

New-Item -ItemType Directory -Path "E:\App\AI-CCTV\data" -Force | Out-Null
Remove-Item $log -Force -ErrorAction SilentlyContinue

# pastikan port 8002 bebas
$busy = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    foreach ($p in ($busy.OwningProcess | Select-Object -Unique)) {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
}

# Laravel 13 butuh PHP >= 8.3, jadi PATH diarahkan ke php-8.5.6
$cmd = "`$env:PATH = 'C:\Program Files\php-8.5.6;' + `$env:PATH; " +
       "cd '$root'; php artisan serve --host=127.0.0.1 --port=8002 *> '$log'"

Start-Process powershell -ArgumentList '-NoProfile', '-Command', $cmd -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 12

try {
    $r = Invoke-WebRequest "http://127.0.0.1:8002" -TimeoutSec 15 -UseBasicParsing
    Write-Host "Laravel 13 jalan  ->  HTTP $($r.StatusCode)"
    Write-Host "Buka di browser :  http://localhost:8002"
} catch {
    Write-Host "GAGAL: $($_.Exception.Message)"
    if (Test-Path $log) { Get-Content $log -Tail 10 }
}