<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Cycle;
use App\Models\ShiftReport;
use App\Models\Unit;
use App\Services\PythonApi;
use App\Services\TelemetryRecorder;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function __construct(
        protected PythonApi $api,
        protected TelemetryRecorder $recorder
    ) {}

    public function index(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $unit = Unit::with('primaryCamera')->where('kode_unit', $selectedUnit)->first()
            ?? Unit::with('primaryCamera')->first();

        $allUnits = Unit::orderBy('kode_unit')->get();

        $today = Carbon::today('Asia/Jakarta');
        $shiftReport = ShiftReport::where('unit_id', $unit?->id)
            ->whereDate('tanggal', $today)
            ->first();

        $recentCycles = Cycle::where('unit_id', $unit?->id)
            ->latest('waktu_mulai')
            ->take(10)
            ->get();

        $totalCycles = Cycle::where('unit_id', $unit?->id)->count();
        $avgCycleTime = Cycle::where('unit_id', $unit?->id)->avg('durasi_total') ?? 24.5;
        $totalTonnage = Cycle::where('unit_id', $unit?->id)->sum('payload_est_ton') ?? 0;
        $cameras = Camera::with('unit')->orderByDesc('is_primary')->orderBy('nama')->get();

        return view('dashboard', [
            'breadcrumb' => 'Dashboard Operasional',
            'unit' => $unit?->kode_unit ?? 'EXC-07',
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'cameras' => $cameras,
            'shiftReport' => $shiftReport,
            'recentCycles' => $recentCycles,
            'totalCycles' => $totalCycles,
            'avgCycleTime' => round($avgCycleTime, 1),
            'totalTonnage' => round($totalTonnage, 1),
            'streamUrl' => rtrim(config('hera.stream_url'), '/'),
            'apiUrl' => rtrim(config('hera.api_url'), '/'),
        ]);
    }

    /**
     * Endpoint API super enteng untuk polling real-time (< 15 ms).
     */
    public function telemetryLive(Request $request): JsonResponse
    {
        $unitKode = $request->query('unit', config('hera.unit', 'EXC-07'));

        // Coba sinkronisasi event baru dari Python jika tersedia
        try {
            $this->recorder->sync($unitKode);
        } catch (\Throwable $e) {
            // Fail gracefully jika engine python offline
        }

        $status = $this->api->status();
        $riwayat = $this->api->riwayat(20);

        $unit = Unit::where('kode_unit', $unitKode)->first();
        $dbCycles = $unit ? Cycle::where('unit_id', $unit->id)->latest('waktu_mulai')->take(10)->get() : [];

        return response()->json([
            'ok' => $status['ok'],
            'online' => $this->api->isOnline(),
            'status' => $status['data'] ?? [],
            'riwayat' => $riwayat['data']['events'] ?? [],
            'db_cycles' => $dbCycles,
            'server_time' => Carbon::now('Asia/Jakarta')->format('H:i:s'),
        ]);
    }
}
