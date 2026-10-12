$ErrorActionPreference = "Continue"
$log = "E:\App\employee-presence\data\run_start.log"
function Say($m) { "[$(Get-Date -Format 'HH:mm:ss')] $m" | Out-File $log -Append -Encoding utf8 }

"=== RUN $(Get-Date) ===" | Out-File $log -Encoding utf8

Say "1/4 atur metrik Ethernet..."
Set-NetIPInterface -InterfaceAlias "Ethernet" -InterfaceMetric 5
Set-NetIPInterface -InterfaceAlias "Wi-Fi" -InterfaceMetric 300
Get-NetIPInterface -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -in @("Ethernet", "Wi-Fi") } |
    ForEach-Object { Say "    $($_.InterfaceAlias) metric=$($_.InterfaceMetric) $($_.ConnectionState)" }

Say "2/4 hentikan proses python lama..."
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='python3.12.exe'" |
    Where-Object { $_.CommandLine -like "*employee-presence*" } |
    ForEach-Object { Say "    stop PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 5

foreach ($port in 8000, 8001, 8002, 8003, 8004) {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($c) { Say "    paksa stop port $port (PID $($c.OwningProcess))"; Stop-Process -Id ($c.OwningProcess | Select-Object -Unique) -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 3
$left = (Get-NetTCPConnection -LocalPort 8000, 8001, 8002, 8003, 8004 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count
Say "    port tersisa berlisten: $left"

Say "3/4 cek link & kamera..."
$ad = Get-NetAdapter -Name "Ethernet" -ErrorAction SilentlyContinue
Say "    Ethernet: $($ad.Status) $($ad.LinkSpeed)"
foreach ($ip in @("192.168.1.108", "192.168.1.109", "192.168.1.110", "192.168.1.111")) {
    $c = New-Object System.Net.Sockets.TcpClient
    $s = "tutup"
    try { if ($c.ConnectAsync($ip, 554).Wait(5000) -and $c.Connected) { $s = "554 BUKA" } } catch { }
    $c.Close()
    Say "    $ip RTSP $s"
}

Say "4/4 jalankan run.py all..."
$root = "E:\App\employee-presence"
Remove-Item "$root\data\record_cctv-*.log" -Force -ErrorAction SilentlyContinue
$p = Start-Process -FilePath "$root\.venv\Scripts\python.exe" `
     -ArgumentList "run.py", "--config", "config.cctv.yaml", "all" `
     -WorkingDirectory $root -WindowStyle Hidden -PassThru
Say "parent PID $($p.Id)"
Say "dashboard http://127.0.0.1:8000"
Say "selesai"