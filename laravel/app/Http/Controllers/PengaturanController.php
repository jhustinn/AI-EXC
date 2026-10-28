<?php

namespace App\Http\Controllers;

use App\Models\ActivityLog;
use App\Models\Cycle;
use App\Models\SystemSetting;
use App\Models\Unit;
use App\Services\PythonApi;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class PengaturanController extends Controller
{
    public function __construct(protected PythonApi $api) {}

    public function index()
    {
        $settings = SystemSetting::all()->keyBy('key');
        $health = $this->api->health();

        // Database stats
        $dbStats = [
            'total_units' => Unit::count(),
            'total_logs' => ActivityLog::count(),
            'total_cycles' => Cycle::count(),
            'db_connection' => config('database.default'),
            'db_name' => config('database.connections.pgsql.database'),
        ];

        return view('pengaturan.index', [
            'breadcrumb' => 'Pengaturan / Konfigurasi Sistem & AI',
            'settings' => $settings,
            'health' => $health,
            'dbStats' => $dbStats,
        ]);
    }

    public function update(Request $request)
    {
        $inputs = $request->except('_token');

        foreach ($inputs as $key => $val) {
            SystemSetting::updateOrCreate(
                ['key' => $key],
                ['value' => (string) $val]
            );
        }

        return redirect()->route('pengaturan')->with('success', 'Pengaturan sistem berhasil diperbarui.');
    }
}
