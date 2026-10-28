<?php

namespace App\Http\Controllers;

use App\Models\ActivityLog;
use App\Models\Camera;
use App\Models\Cycle;
use App\Models\Unit;
use App\Services\PythonApi;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\StreamedResponse;

class MonitoringController extends Controller
{
    public function __construct(protected PythonApi $api) {}

    public function live(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $unit = Unit::with('cameras')->where('kode_unit', $selectedUnit)->first()
            ?? Unit::with('cameras')->first();

        $cameras = Camera::with('unit')->where('is_active', true)->orderBy('id')->get();
        $allUnits = Unit::orderBy('kode_unit')->get();

        return view('monitoring.live', [
            'breadcrumb' => 'Monitoring / Live Multi-Camera Matrix',
            'unit' => $unit?->kode_unit ?? 'EXC-07',
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'cameras' => $cameras,
            'streamUrl' => rtrim(config('hera.stream_url'), '/'),
            'apiUrl' => rtrim(config('hera.api_url'), '/'),
        ]);
    }

    public function deteksi(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $unit = Unit::where('kode_unit', $selectedUnit)->first();

        $allUnits = Unit::orderBy('kode_unit')->get();
        $status = $this->api->status()['data'] ?? [];

        return view('monitoring.deteksi', [
            'breadcrumb' => 'Monitoring / Deteksi Aktivitas AI',
            'unit' => $selectedUnit,
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'status' => $status,
            'streamUrl' => rtrim(config('hera.stream_url'), '/'),
            'apiUrl' => rtrim(config('hera.api_url'), '/'),
        ]);
    }

    public function produktivitas(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $unit = Unit::where('kode_unit', $selectedUnit)->first();
        $allUnits = Unit::orderBy('kode_unit')->get();

        $cycles = Cycle::where('unit_id', $unit?->id)
            ->orderBy('siklus_ke')
            ->get();

        $avgDig = $cycles->avg('durasi_mengeruk') ?? 11.5;
        $avgDump = $cycles->avg('durasi_menuangkan') ?? 9.8;
        $avgTotal = $cycles->avg('durasi_total') ?? 24.3;
        $totalTon = $cycles->sum('payload_est_ton');

        return view('monitoring.produktivitas', [
            'breadcrumb' => 'Monitoring / Rekap Produktivitas',
            'unit' => $selectedUnit,
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'cycles' => $cycles,
            'avgDig' => round($avgDig, 1),
            'avgDump' => round($avgDump, 1),
            'avgTotal' => round($avgTotal, 1),
            'totalTon' => round($totalTon, 1),
        ]);
    }

    public function riwayat(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $faseFilter = $request->query('fase');
        $dateFilter = $request->query('tanggal', Carbon::today('Asia/Jakarta')->toDateString());

        $unit = Unit::where('kode_unit', $selectedUnit)->first();
        $allUnits = Unit::orderBy('kode_unit')->get();

        $query = ActivityLog::with('unit')
            ->where('unit_id', $unit?->id);

        if ($faseFilter && $faseFilter !== 'all') {
            $query->where('fase', $faseFilter);
        }

        if ($dateFilter) {
            $query->whereDate('mulai', $dateFilter);
        }

        $logs = $query->latest('mulai')->paginate(25)->withQueryString();

        return view('monitoring.riwayat', [
            'breadcrumb' => 'Monitoring / Riwayat Deteksi & Siklus',
            'unit' => $selectedUnit,
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'logs' => $logs,
            'faseFilter' => $faseFilter,
            'dateFilter' => $dateFilter,
        ]);
    }

    public function exportCsv(Request $request): StreamedResponse
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $unit = Unit::where('kode_unit', $selectedUnit)->first();

        $headers = [
            'Content-Type' => 'text/csv',
            'Content-Disposition' => 'attachment; filename="riwayat_aktivitas_' . $selectedUnit . '_' . date('Ymd_His') . '.csv"',
        ];

        $callback = function () use ($unit) {
            $handle = fopen('php://output', 'w');
            fputcsv($handle, ['ID', 'Unit', 'Siklus Ke', 'Fase', 'Waktu Mulai', 'Waktu Selesai', 'Durasi (detik)', 'Truck Conf', 'Bucket Conf', 'Motion Score']);

            $logs = ActivityLog::where('unit_id', $unit?->id)
                ->orderBy('mulai', 'asc')
                ->cursor();

            foreach ($logs as $log) {
                fputcsv($handle, [
                    $log->id,
                    $unit?->kode_unit,
                    $log->siklus_ke,
                    $log->fase_label,
                    $log->mulai?->format('Y-m-d H:i:s'),
                    $log->selesai?->format('Y-m-d H:i:s') ?? '-',
                    $log->durasi_detik,
                    $log->truck_confidence,
                    $log->bucket_confidence,
                    $log->motion_score,
                ]);
            }
            fclose($handle);
        };

        return response()->stream($callback, 200, $headers);
    }

    public function apiCameras()
    {
        $cameras = Camera::with('unit')->where('is_active', true)->orderBy('id')->get();
        return response()->json([
            'cameras' => $cameras->map(function ($cam) {
                return [
                    'id' => $cam->id,
                    'nama' => $cam->nama,
                    'posisi' => $cam->posisi,
                    'unit' => $cam->unit?->kode_unit ?? 'EXC-07',
                    'source_type' => $cam->source_type,
                    'source_path' => $cam->source_path,
                    'fps' => $cam->fps,
                    'resolusi' => $cam->resolusi,
                    'is_primary' => (bool)$cam->is_primary,
                ];
            }),
        ]);
    }
}
