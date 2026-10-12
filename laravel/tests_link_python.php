<?php

/*
 * Uji sambungan Laravel -> engine Python.
 * Jalankan:  C:\Program Files\php-8.5.6\php.exe tests_link_python.php
 */

require __DIR__ . '/vendor/autoload.php';

$app = require_once __DIR__ . '/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Services\PythonApi;

$api = app(PythonApi::class);

echo str_repeat('=', 60), PHP_EOL;
echo 'KONEKSI LARAVEL -> ENGINE PYTHON', PHP_EOL;
echo str_repeat('=', 60), PHP_EOL;

echo 'engine online  : ' . ($api->isOnline() ? 'YA' : 'TIDAK') . PHP_EOL;

$status = $api->status();
if (! $status['ok']) {
    echo 'GAGAL        : ' . $status['error'] . PHP_EOL;
    echo 'cek engine    : powershell -File scripts\start_engine.ps1' . PHP_EOL;
    exit(1);
}

$d = $status['data'];
echo 'unit          : ' . ($d['engine']['unit'] ?? '-') . PHP_EOL;
echo 'sumber        : ' . ($d['engine']['sumber'] ?? '-') . PHP_EOL;
echo 'kelas COCO    : ' . implode(', ', $d['engine']['kelas'] ?? []) . PHP_EOL;
echo 'frame diproses: ' . ($d['engine']['frame_total'] ?? '-') . PHP_EOL;
echo 'error engine  : ' . (($d['engine']['error'] ?? null) ?: 'tidak ada') . PHP_EOL;
echo str_repeat('-', 60), PHP_EOL;
echo 'fase sekarang : ' . $d['fase_label'] . PHP_EOL;
echo 'truck conf    : ' . $d['truck_confidence'] . PHP_EOL;
echo 'sumber sinyal : ' . $d['sumber_sinyal'] . PHP_EOL;
echo 'zona tuang    : ' . ($d['zona_tuang'] ? implode(', ', array_map(fn ($v) => round($v), $d['zona_tuang'])) : 'tidak aktif') . PHP_EOL;
echo str_repeat('-', 60), PHP_EOL;
echo 'durasi mengeruk  : ' . PythonApi::durasi($d['kpi']['durasi_mengeruk']) . PHP_EOL;
echo 'durasi menuang   : ' . PythonApi::durasi($d['kpi']['durasi_menuangkan']) . PHP_EOL;
echo 'waktu idle       : ' . PythonApi::durasi($d['kpi']['waktu_idle']) . PHP_EOL;
echo 'jumlah siklus    : ' . $d['kpi']['jumlah_siklus'] . PHP_EOL;

$riwayat = $api->riwayat(10);
$events = $riwayat['data']['events'] ?? [];
echo str_repeat('-', 60), PHP_EOL;
echo 'riwayat event   : ' . count($events) . PHP_EOL;
foreach (array_slice($events, 0, 5) as $e) {
    echo sprintf(
        "  %-10s %6.1fs  truck=%.2f  gerak=%.4f  siklus #%d\n",
        $e['fase_label'], $e['durasi'], $e['truck_confidence'],
        $e['zona_gali_motion'], $e['siklus']
    );
}
echo str_repeat('=', 60), PHP_EOL;
echo 'SEMUA KONEKSI OK', PHP_EOL;