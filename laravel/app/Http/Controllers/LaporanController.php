<?php

namespace App\Http\Controllers;

use App\Models\Cycle;
use App\Models\ShiftReport;
use App\Models\Unit;
use Carbon\Carbon;
use Illuminate\Http\Request;

class LaporanController extends Controller
{
    public function harian(Request $request)
    {
        $selectedUnit = $request->query('unit', config('hera.unit', 'EXC-07'));
        $selectedDate = $request->query('tanggal', Carbon::today('Asia/Jakarta')->toDateString());
        $selectedShift = $request->query('shift', 'Shift 2 (Malam)');

        $unit = Unit::where('kode_unit', $selectedUnit)->first();
        $allUnits = Unit::orderBy('kode_unit')->get();

        $shiftReport = ShiftReport::where('unit_id', $unit?->id)
            ->whereDate('tanggal', $selectedDate)
            ->where('shift', $selectedShift)
            ->first();

        $cycles = Cycle::where('unit_id', $unit?->id)
            ->whereDate('waktu_mulai', $selectedDate)
            ->orderBy('siklus_ke')
            ->get();

        $totalCycles = $cycles->count();
        $totalTonase = $cycles->sum('payload_est_ton');
        $avgCycle = $cycles->avg('durasi_total') ?? 24.5;
        $totalDigTime = $cycles->sum('durasi_mengeruk');
        $totalDumpTime = $cycles->sum('durasi_menuangkan');

        return view('laporan.harian', [
            'breadcrumb' => 'Laporan / Rekapitulasi Produksi Shift',
            'unit' => $selectedUnit,
            'unitModel' => $unit,
            'allUnits' => $allUnits,
            'selectedDate' => $selectedDate,
            'selectedShift' => $selectedShift,
            'shiftReport' => $shiftReport,
            'cycles' => $cycles,
            'totalCycles' => $totalCycles,
            'totalTonase' => round($totalTonase, 1),
            'avgCycle' => round($avgCycle, 1),
            'totalDigTime' => round($totalDigTime, 1),
            'totalDumpTime' => round($totalDumpTime, 1),
        ]);
    }
}
