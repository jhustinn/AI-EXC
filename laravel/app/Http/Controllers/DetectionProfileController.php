<?php

namespace App\Http\Controllers;

use App\Models\DetectionProfile;
use App\Models\Unit;
use Illuminate\Http\Request;

class DetectionProfileController extends Controller
{
    /**
     * Tampilkan daftar master Pola Deteksi, Trigger, & Geometri Zona.
     */
    public function index()
    {
        $profiles = DetectionProfile::withCount('units')->orderBy('is_default', 'desc')->orderBy('nama')->get();
        $units = Unit::with('detectionProfile')->orderBy('kode_unit')->get();

        $stats = [
            'total_profiles' => $profiles->count(),
            'default_profile' => $profiles->where('is_default', true)->first()?->nama ?? 'Standard Pit',
            'units_configured' => $units->whereNotNull('detection_profile_id')->count(),
            'total_units' => $units->count(),
        ];

        return view('master.pattern', compact('profiles', 'units', 'stats'));
    }

    /**
     * Simpan profil pola deteksi baru.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'kode_profil' => 'required|string|max:50|unique:detection_profiles,kode_profil',
            'nama' => 'required|string|max:100',
            'tipe_alat' => 'required|string|max:50',
            'deskripsi' => 'nullable|string',
            // Komponen
            'bucket_confidence' => 'required|numeric|between:0.05,0.95',
            'bucket_low_ratio' => 'required|numeric|between:0.10,0.99',
            'truck_confidence' => 'required|numeric|between:0.05,0.95',
            'truck_hold_seconds' => 'required|numeric|between:0.5,10.0',
            'truck_min_width_ratio' => 'required|numeric|between:0.05,0.50',
            'arm_confidence' => 'required|numeric|between:0.05,0.95',
            'arm_swing_threshold' => 'required|numeric|between:0.02,0.50',
            'plate_confidence' => 'required|numeric|between:0.10,0.95',
            'plate_ocr_enabled' => 'nullable|boolean',
            // Trigger
            'motion_threshold' => 'required|numeric|between:0.01,0.50',
            'dig_min_seconds' => 'required|numeric|between:0.5,10.0',
            'dump_min_seconds' => 'required|numeric|between:0.5,10.0',
            'phase_min_seconds' => 'required|numeric|between:0.2,5.0',
            'idle_seconds' => 'required|numeric|between:1.0,30.0',
            // Zona ROI
            'zona_gali_x1' => 'required|numeric|between:0,1',
            'zona_gali_y1' => 'required|numeric|between:0,1',
            'zona_gali_x2' => 'required|numeric|between:0,1',
            'zona_gali_y2' => 'required|numeric|between:0,1',
            'dump_top_ratio' => 'required|numeric|between:0.01,0.50',
            'dump_height_ratio' => 'required|numeric|between:0.10,0.95',
        ]);

        $validated['plate_ocr_enabled'] = $request->has('plate_ocr_enabled');
        $validated['is_default'] = false;

        $profile = DetectionProfile::create($validated);

        return redirect()->route('master.pattern')->with('success', "Profil deteksi '{$profile->nama}' berhasil dibuat!");
    }

    /**
     * Perbarui profil pola deteksi, trigger, atau zona.
     */
    public function update(Request $request, $id)
    {
        $profile = DetectionProfile::findOrFail($id);

        $validated = $request->validate([
            'nama' => 'required|string|max:100',
            'tipe_alat' => 'required|string|max:50',
            'deskripsi' => 'nullable|string',
            // Komponen
            'bucket_confidence' => 'required|numeric|between:0.05,0.95',
            'bucket_low_ratio' => 'required|numeric|between:0.10,0.99',
            'truck_confidence' => 'required|numeric|between:0.05,0.95',
            'truck_hold_seconds' => 'required|numeric|between:0.5,10.0',
            'truck_min_width_ratio' => 'required|numeric|between:0.05,0.50',
            'arm_confidence' => 'required|numeric|between:0.05,0.95',
            'arm_swing_threshold' => 'required|numeric|between:0.02,0.50',
            'plate_confidence' => 'required|numeric|between:0.10,0.95',
            'plate_ocr_enabled' => 'nullable|boolean',
            // Trigger
            'motion_threshold' => 'required|numeric|between:0.01,0.50',
            'dig_min_seconds' => 'required|numeric|between:0.5,10.0',
            'dump_min_seconds' => 'required|numeric|between:0.5,10.0',
            'phase_min_seconds' => 'required|numeric|between:0.2,5.0',
            'idle_seconds' => 'required|numeric|between:1.0,30.0',
            // Zona ROI
            'zona_gali_x1' => 'required|numeric|between:0,1',
            'zona_gali_y1' => 'required|numeric|between:0,1',
            'zona_gali_x2' => 'required|numeric|between:0,1',
            'zona_gali_y2' => 'required|numeric|between:0,1',
            'dump_top_ratio' => 'required|numeric|between:0.01,0.50',
            'dump_height_ratio' => 'required|numeric|between:0.10,0.95',
        ]);

        $validated['plate_ocr_enabled'] = $request->has('plate_ocr_enabled');

        $profile->update($validated);

        $this->notifyEngineSync();

        return redirect()->route('master.pattern')->with('success', "Konfigurasi pola '{$profile->nama}' berhasil diperbarui!");
    }

    /**
     * Hapus profil pola deteksi.
     */
    public function destroy($id)
    {
        $profile = DetectionProfile::findOrFail($id);

        if ($profile->is_default) {
            return redirect()->route('master.pattern')->with('error', "Profil default sistem '{$profile->nama}' tidak dapat dihapus!");
        }

        // Reassign unit yang memakai profil ini ke profil default
        $defaultProfile = DetectionProfile::where('is_default', true)->first();
        if ($defaultProfile) {
            Unit::where('detection_profile_id', $profile->id)->update([
                'detection_profile_id' => $defaultProfile->id,
            ]);
        }

        $profile->delete();

        return redirect()->route('master.pattern')->with('success', "Profil deteksi berhasil dihapus.");
    }

    /**
     * Terapkan profil deteksi ke unit ekskavator tertentu.
     */
    public function assignUnit(Request $request)
    {
        $request->validate([
            'unit_id' => 'required|exists:units,id',
            'profile_id' => 'required|exists:detection_profiles,id',
        ]);

        $unit = Unit::findOrFail($request->unit_id);
        $profile = DetectionProfile::findOrFail($request->profile_id);

        $unit->update(['detection_profile_id' => $profile->id]);

        $this->notifyEngineSync($unit->kode_unit);

        return redirect()->route('master.pattern')->with('success', "Profil '{$profile->nama}' berhasil diaplikasikan ke Unit {$unit->kode_unit} ({$unit->nama})!");
    }

    /**
     * Beritahu Engine AI Python untuk sinkronisasi konfigurasi baru (jika engine sedang berjalan).
     */
    private function notifyEngineSync(?string $unitCode = null): void
    {
        try {
            \Illuminate\Support\Facades\Http::timeout(1)->post('http://127.0.0.1:8010/api/profile/sync', [
                'unit' => $unitCode,
            ]);
        } catch (\Throwable $e) {
            // Engine offline atau belum aktif, fallback aman tanpa memblokir web request
        }
    }

    /**
     * API Endpoint untuk Engine Python AI membaca konfigurasi profil per unit.
     */
    public function apiGetConfig(Request $request, $kodeUnit)
    {
        $unit = Unit::where('kode_unit', $kodeUnit)->first();
        if (!$unit) {
            return response()->json(['error' => 'Unit not found'], 404);
        }

        $profile = $unit->detectionProfile ?? DetectionProfile::where('is_default', true)->first();
        if (!$profile) {
            return response()->json(['error' => 'No active profile found'], 404);
        }

        return response()->json([
            'unit' => $unit->kode_unit,
            'unit_nama' => $unit->nama,
            'profile' => $profile->toEngineConfig(),
        ]);
    }
}
