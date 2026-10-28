<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

/**
 * Klien untuk service Python (engine deteksi).
 *
 * Laravel HANYA membaca. Semua penulisan database dilakukan Python.
 * Video tidak pernah di-proxy lewat PHP - browser terhubung langsung ke
 * server MJPEG milik Python lewat config('hera.stream_url').
 */
class PythonApi
{
    /**
     * Ambil status realtime + KPI.
     *
     * @return array{ok: bool, data: array, error: string|null}
     */
    public function status(): array
    {
        return $this->get('/api/status');
    }

    /** @return array{ok: bool, data: array, error: string|null} */
    public function kpi(): array
    {
        return $this->get('/api/kpi');
    }

    /** @return array{ok: bool, data: array, error: string|null} */
    public function riwayat(int $limit = 50): array
    {
        return $this->get('/api/riwayat?limit=' . $limit);
    }

    /** @return array{ok: bool, data: array, error: string|null} */
    public function health(): array
    {
        return $this->get('/api/health');
    }

    /**
     * True bila engine Python hidup dan tidak melaporkan error.
     */
    public function isOnline(): bool
    {
        $res = $this->health();

        return $res['ok'] && ($res['data']['status'] ?? '') === 'ok';
    }

    /**
     * Konversi detik ke format HH:MM:SS.
     */
    public static function durasi(?float $detik): string
    {
        $d = (int) round($detik ?? 0);
        $jam = intdiv($d, 3600);
        $menit = intdiv($d % 3600, 60);
        $detik = $d % 60;

        return sprintf('%02d:%02d:%02d', $jam, $menit, $detik);
    }

    /**
     * @return array{ok: bool, data: array, error: string|null}
     */
    private function get(string $path): array
    {
        try {
            $resp = Http::connectTimeout(0.8)
                ->timeout((float) config('hera.api_timeout', 1.5))
                ->acceptJson()
                ->get(rtrim(config('hera.api_url'), '/') . $path);

            if (! $resp->successful()) {
                return [
                    'ok' => false,
                    'data' => [],
                    'error' => "HTTP {$resp->status()} dari engine Python",
                ];
            }

            return ['ok' => true, 'data' => $resp->json() ?? [], 'error' => null];
        } catch (Throwable $e) {
            // Engine mati adalah kondisi normal, bukan exception fatal.
            Log::debug('python api gagal: ' . $e->getMessage());

            return ['ok' => false, 'data' => [], 'error' => $e->getMessage()];
        }
    }
}