<?php

namespace App\Http\Controllers;

use App\Models\Camera;
use App\Models\Truck;
use App\Models\Unit;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MasterController extends Controller
{
    // ================= UNIT =================
    public function unitIndex(): View
    {
        $units = Unit::with('detectionProfile')->withCount('cameras', 'cycles')->orderBy('kode_unit')->get();
        $profiles = \App\Models\DetectionProfile::orderBy('nama')->get();
        return view('master.unit', [
            'breadcrumb' => 'Master Data / Unit Alat Berat',
            'units' => $units,
            'profiles' => $profiles,
        ]);
    }

    public function unitStore(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'kode_unit' => 'required|string|max:50|unique:units,kode_unit',
            'nama' => 'required|string|max:100',
            'jenis' => 'required|string|max:50',
            'merk' => 'required|string|max:50',
            'model' => 'required|string|max:50',
            'kapasitas_bucket_m3' => 'required|numeric|min:0.5',
            'status' => 'required|string',
            'lokasi_pit' => 'required|string|max:100',
            'operator' => 'nullable|string|max:100',
        ]);

        Unit::create($validated);
        return redirect()->route('master.unit')->with('success', "Unit {$validated['kode_unit']} berhasil ditambahkan.");
    }

    public function unitUpdate(Request $request, $id): RedirectResponse
    {
        $unit = Unit::findOrFail($id);
        $validated = $request->validate([
            'nama' => 'required|string|max:100',
            'merk' => 'required|string|max:50',
            'model' => 'required|string|max:50',
            'kapasitas_bucket_m3' => 'required|numeric|min:0.5',
            'status' => 'required|string',
            'lokasi_pit' => 'required|string|max:100',
            'operator' => 'nullable|string|max:100',
        ]);

        $unit->update($validated);
        return redirect()->route('master.unit')->with('success', "Unit {$unit->kode_unit} berhasil diperbarui.");
    }

    public function unitDestroy($id): RedirectResponse
    {
        $unit = Unit::withCount('cameras', 'cycles')->findOrFail($id);
        
        if ($unit->cameras_count > 0 || $unit->cycles_count > 0) {
            return back()->with('error', "Unit {$unit->kode_unit} tidak dapat dihapus karena masih memiliki {$unit->cameras_count} kamera terhubung dan {$unit->cycles_count} log siklus kerja.");
        }

        $kode = $unit->kode_unit;
        $unit->delete();
        return redirect()->route('master.unit')->with('success', "Unit {$kode} berhasil dihapus dari armada.");
    }

    // ================= DUMP TRUCK =================
    public function truckIndex(): View
    {
        $trucks = Truck::orderBy('kode_truk')->get();
        $stats = [
            'total' => $trucks->count(),
            'operasional' => $trucks->where('status', 'OPERASIONAL')->count(),
            'total_kapasitas' => $trucks->sum('kapasitas_ton'),
        ];

        return view('master.truck', [
            'breadcrumb' => 'Master Data / Dump Truck Hauling',
            'trucks' => $trucks,
            'stats' => $stats,
        ]);
    }

    public function truckStore(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'kode_truk' => 'required|string|max:50|unique:trucks,kode_truk',
            'no_polisi' => 'nullable|string|max:30',
            'merk_tipe' => 'required|string|max:100',
            'vendor' => 'required|string|max:100',
            'kapasitas_ton' => 'required|numeric|min:5',
            'status' => 'required|string',
        ]);

        Truck::create($validated);
        return redirect()->route('master.truck')->with('success', "Dump Truck {$validated['kode_truk']} berhasil didaftarkan.");
    }

    public function truckUpdate(Request $request, $id): RedirectResponse
    {
        $truck = Truck::findOrFail($id);
        $validated = $request->validate([
            'no_polisi' => 'nullable|string|max:30',
            'merk_tipe' => 'required|string|max:100',
            'vendor' => 'required|string|max:100',
            'kapasitas_ton' => 'required|numeric|min:5',
            'status' => 'required|string',
        ]);

        $truck->update($validated);
        return redirect()->route('master.truck')->with('success', "Data Dump Truck {$truck->kode_truk} berhasil diperbarui.");
    }

    public function truckDestroy($id): RedirectResponse
    {
        $truck = Truck::findOrFail($id);
        $kode = $truck->kode_truk;
        $truck->delete();
        return redirect()->route('master.truck')->with('success', "Dump Truck {$kode} berhasil dihapus.");
    }

    // ================= KAMERA =================
    public function kameraIndex(): View
    {
        $cameras = Camera::with('unit')->orderBy('nama')->get();
        $units = Unit::orderBy('kode_unit')->get();
        return view('master.kamera', [
            'breadcrumb' => 'Master Data / Kamera & Stream Video',
            'cameras' => $cameras,
            'units' => $units,
        ]);
    }

    public function kameraStore(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'unit_id' => 'required|exists:units,id',
            'nama' => 'required|string|max:100',
            'posisi' => 'required|string|max:50',
            'source_type' => 'required|string|in:video,rtsp,usb,http,stream',
            'source_path' => 'required|string',
            'resolusi' => 'required|string|max:20',
            'fps' => 'required|integer|min:5|max:60',
            'is_primary' => 'nullable|boolean',
        ]);

        $validated['is_primary'] = $request->boolean('is_primary', false);
        $validated['is_active'] = true;

        if ($validated['is_primary']) {
            Camera::where('unit_id', $validated['unit_id'])->update(['is_primary' => false]);
        }

        Camera::create($validated);
        return redirect()->route('master.kamera')->with('success', "Kamera {$validated['nama']} berhasil disimpan.");
    }

    public function kameraUpdate(Request $request, $id): RedirectResponse
    {
        $camera = Camera::findOrFail($id);
        $validated = $request->validate([
            'unit_id' => 'required|exists:units,id',
            'nama' => 'required|string|max:100',
            'posisi' => 'required|string|max:50',
            'source_type' => 'required|string|in:video,rtsp,usb,http,stream',
            'source_path' => 'required|string',
            'resolusi' => 'required|string|max:20',
            'fps' => 'required|integer|min:5|max:60',
            'is_primary' => 'nullable|boolean',
            'is_active' => 'nullable|boolean',
        ]);

        $validated['is_primary'] = $request->boolean('is_primary', false);
        $validated['is_active'] = $request->has('is_active');

        if ($validated['is_primary']) {
            Camera::where('unit_id', $validated['unit_id'])
                ->where('id', '!=', $camera->id)
                ->update(['is_primary' => false]);
        }

        $camera->update($validated);
        return redirect()->route('master.kamera')->with('success', "Kamera {$camera->nama} berhasil diperbarui.");
    }

    public function kameraDestroy($id): RedirectResponse
    {
        $camera = Camera::findOrFail($id);
        $nama = $camera->nama;
        $camera->delete();
        return redirect()->route('master.kamera')->with('success', "Kamera {$nama} telah berhasil dihapus.");
    }

    /**
     * Endpoint AJAX untuk menguji konektivitas stream kamera secara real-time.
     */
    public function kameraTest(Request $request): JsonResponse
    {
        $sourcePath = trim($request->input('source_path', ''));
        $sourceType = trim($request->input('source_type', 'rtsp'));

        if (empty($sourcePath)) {
            return response()->json([
                'success' => false,
                'status' => 'offline',
                'latency_ms' => null,
                'message' => 'Path atau URL stream kamera belum diisi.',
            ]);
        }

        $t0 = microtime(true);

        // Kasus 1: HTTP / HTTPS stream (misal ustreamer atau IP cam MJPEG)
        if (str_starts_with($sourcePath, 'http://') || str_starts_with($sourcePath, 'https://')) {
            try {
                $ctx = stream_context_create([
                    'http' => [
                        'method' => 'GET',
                        'timeout' => 2.5,
                        'follow_location' => 1,
                        'header' => "User-Agent: HERA-CCTV-HealthChecker/1.0\r\n",
                    ],
                ]);

                $fp = @fopen($sourcePath, 'r', false, $ctx);
                if ($fp) {
                    // Baca 1 byte untuk memastikan stream hidup
                    @fread($fp, 1024);
                    @fclose($fp);
                    $latencyMs = round((microtime(true) - $t0) * 1000, 1);
                    return response()->json([
                        'success' => true,
                        'status' => 'online',
                        'latency_ms' => $latencyMs,
                        'message' => "Stream HTTP terhubung responsif ({$latencyMs} ms).",
                    ]);
                }
            } catch (\Throwable $e) {
                // Lanjut ke respon gagal
            }

            return response()->json([
                'success' => false,
                'status' => 'offline',
                'latency_ms' => null,
                'message' => 'Gagal membuka koneksi HTTP ke kamera. Pastikan Raspberry Pi menyala dan terhubung ke jaringan.',
            ]);
        }

        // Kasus 2: RTSP Stream
        if (str_starts_with($sourcePath, 'rtsp://')) {
            $parsed = parse_url($sourcePath);
            $host = $parsed['host'] ?? '';
            $port = $parsed['port'] ?? 554;

            if (empty($host)) {
                return response()->json([
                    'success' => false,
                    'status' => 'offline',
                    'latency_ms' => null,
                    'message' => 'Format URL RTSP tidak valid.',
                ]);
            }

            $errno = 0;
            $errstr = '';
            $fp = @fsockopen($host, $port, $errno, $errstr, 2.0);
            if ($fp) {
                fclose($fp);
                $latencyMs = round((microtime(true) - $t0) * 1000, 1);
                return response()->json([
                    'success' => true,
                    'status' => 'online',
                    'latency_ms' => $latencyMs,
                    'message' => "Port RTSP {$host}:{$port} terbuka dan dapat dijangkau ({$latencyMs} ms).",
                ]);
            }

            return response()->json([
                'success' => false,
                'status' => 'offline',
                'latency_ms' => null,
                'message' => "Koneksi RTSP ke {$host}:{$port} gagal dijangkau ({$errstr}).",
            ]);
        }

        // Kasus 3: File Video Lokal
        $projectRoot = dirname(base_path());
        $fullPath = file_exists($sourcePath) ? $sourcePath : $projectRoot . DIRECTORY_SEPARATOR . $sourcePath;
        if (file_exists($fullPath) && is_file($fullPath)) {
            $sizeMb = round(filesize($fullPath) / (1024 * 1024), 2);
            return response()->json([
                'success' => true,
                'status' => 'online',
                'latency_ms' => 0.5,
                'message' => "Berkas video lokal valid ({$sizeMb} MB).",
            ]);
        }

        return response()->json([
            'success' => false,
            'status' => 'offline',
            'latency_ms' => null,
            'message' => "Berkas video lokal tidak ditemukan di: {$sourcePath}",
        ]);
    }
}
