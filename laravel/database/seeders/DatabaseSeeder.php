<?php

namespace Database\Seeders;

use App\Models\Camera;
use App\Models\Cycle;
use App\Models\ShiftReport;
use App\Models\SystemSetting;
use App\Models\Truck;
use App\Models\Unit;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // 1. Admin User
        User::updateOrCreate(
            ['email' => 'admin@herasystem.com'],
            [
                'name' => 'Mine Operations Admin',
                'password' => Hash::make('password123'),
                'email_verified_at' => now(),
            ]
        );

        // 2. Heavy Equipment Units
        $exc07 = Unit::updateOrCreate(
            ['kode_unit' => 'EXC-07'],
            [
                'nama' => 'Excavator Cat 395 - Pit Sarolangun',
                'jenis' => 'Excavator',
                'merk' => 'Caterpillar',
                'model' => '395 Ultra-Class',
                'kapasitas_bucket_m3' => 6.50,
                'status' => 'OPERATIONAL',
                'lokasi_pit' => 'Pit Sarolangun Block B',
                'operator' => 'Ahmad Fauzi',
                'keterangan' => 'Unit produksi utama loading batu bara malam/siang.',
            ]
        );

        $exc03 = Unit::updateOrCreate(
            ['kode_unit' => 'EXC-03'],
            [
                'nama' => 'Komatsu PC2000-8 - Loading Bench Barat',
                'jenis' => 'Excavator',
                'merk' => 'Komatsu',
                'model' => 'PC2000-8',
                'kapasitas_bucket_m3' => 12.00,
                'status' => 'OPERATIONAL',
                'lokasi_pit' => 'Pit Barat Overburden',
                'operator' => 'Bambang Sugiono',
                'keterangan' => 'Loading OB ke dump truck kelas 100T.',
            ]
        );

        $exc11 = Unit::updateOrCreate(
            ['kode_unit' => 'EXC-11'],
            [
                'nama' => 'Hitachi EX1200 - Pit Timur',
                'jenis' => 'Excavator',
                'merk' => 'Hitachi',
                'model' => 'EX1200-7',
                'kapasitas_bucket_m3' => 7.00,
                'status' => 'STANDBY',
                'lokasi_pit' => 'Pit Timur Seam 3',
                'operator' => 'Dedi Iskandar',
                'keterangan' => 'Standby penggantian teeth bucket.',
            ]
        );

        // 3. Cameras
        Camera::updateOrCreate(
            ['nama' => 'Cabin Dashcam EXC-07'],
            [
                'unit_id' => $exc07->id,
                'posisi' => 'Cabin Dashcam (Boom POV)',
                'source_type' => 'video',
                'source_path' => 'video/night_dashcam.mp4',
                'fps' => 18,
                'resolusi' => '476x848',
                'is_primary' => true,
                'is_active' => true,
            ]
        );

        Camera::updateOrCreate(
            ['nama' => 'Bench View Side EXC-07'],
            [
                'unit_id' => $exc07->id,
                'posisi' => 'External Bench Angle',
                'source_type' => 'video',
                'source_path' => 'video/sample.mp4',
                'fps' => 20,
                'resolusi' => '1280x720',
                'is_primary' => false,
                'is_active' => true,
            ]
        );

        // 4. Mining Dump Trucks
        $truckData = [
            ['kode' => 'DT-01', 'plat' => 'BH 8492 BM', 'merk' => 'Loxa 6x4 Mining Dump', 'vendor' => 'PT Caritas Energi Indonesia', 'kap' => 35.0],
            ['kode' => 'DT-02', 'plat' => 'BH 8102 CEI', 'merk' => 'Shacman F3000 Tipper', 'vendor' => 'PT Caritas Energi Indonesia', 'kap' => 38.0],
            ['kode' => 'DT-03', 'plat' => 'BH 8763 AM', 'merk' => 'Sinotruk Howo 371', 'vendor' => 'PT Caritas Energi Indonesia', 'kap' => 35.0],
            ['kode' => 'DT-04', 'plat' => 'BH 8819 KL', 'merk' => 'Loxa 6x4 Mining Dump', 'vendor' => 'PT Surya Global Trans', 'kap' => 35.0],
            ['kode' => 'DT-05', 'plat' => 'BH 8234 XY', 'merk' => 'Hino 700 Heavy Tipper', 'vendor' => 'PT Surya Global Trans', 'kap' => 32.0],
            ['kode' => 'DT-06', 'plat' => 'BH 8901 ZZ', 'merk' => 'Loxa 6x4 Mining Dump', 'vendor' => 'PT Caritas Energi Indonesia', 'kap' => 35.0],
        ];

        $firstTruck = null;
        foreach ($truckData as $t) {
            $truck = Truck::updateOrCreate(
                ['kode_truk' => $t['kode']],
                [
                    'no_polisi' => $t['plat'],
                    'merk_tipe' => $t['merk'],
                    'vendor' => $t['vendor'],
                    'kapasitas_ton' => $t['kap'],
                    'status' => 'ACTIVE',
                ]
            );
            if (!$firstTruck) $firstTruck = $truck;
        }

        // 5. Seed Historical Cycles for EXC-07
        $now = Carbon::now('Asia/Jakarta');
        $durations = [
            [9.6, 6.3], [5.9, 9.0], [12.6, 11.0], [14.4, 10.2],
            [11.9, 12.4], [13.5, 10.0], [14.0, 4.2], [13.1, 6.0], [12.5, 9.5]
        ];

        $curTime = $now->copy()->subMinutes(18);
        foreach ($durations as $i => $d) {
            $dig = $d[0];
            $dump = $d[1];
            $total = $dig + $dump + 3.5; // with swing time
            $startTime = $curTime->copy();
            $endTime = $startTime->copy()->addSeconds($total);

            Cycle::updateOrCreate(
                ['unit_id' => $exc07->id, 'siklus_ke' => $i + 1],
                [
                    'truck_id' => $firstTruck?->id,
                    'durasi_mengeruk' => $dig,
                    'durasi_menuangkan' => $dump,
                    'durasi_total' => $total,
                    'waktu_mulai' => $startTime,
                    'waktu_selesai' => $endTime,
                    'payload_est_ton' => 7.80,
                    'status' => 'COMPLETED',
                ]
            );
            $curTime = $endTime->copy()->addSeconds(2);
        }

        // 6. Shift Report Seed
        ShiftReport::updateOrCreate(
            ['unit_id' => $exc07->id, 'tanggal' => $now->toDateString(), 'shift' => 'Shift 2 (Malam)'],
            [
                'operator' => 'Ahmad Fauzi',
                'total_siklus' => count($durations),
                'total_mengeruk_detik' => array_sum(array_column($durations, 0)),
                'total_menuangkan_detik' => array_sum(array_column($durations, 1)),
                'total_idle_detik' => 120.0,
                'total_tonase_est' => count($durations) * 7.80,
                'efisiensi_operasional' => 91.50,
                'catatan' => 'Operasi loading lancar, cuaca cerah di pit Sarolangun.',
            ]
        );

        // 7. System Settings
        $settings = [
            ['ai_engine', 'engine_url', 'http://127.0.0.1:8010', 'string', 'URL Endpoint AI Detection Engine Python'],
            ['ai_engine', 'confidence_threshold', '0.18', 'number', 'Ambang confidence deteksi objek'],
            ['ai_engine', 'motion_threshold', '0.08', 'number', 'Ambang optical motion detection di zona gali'],
            ['ai_engine', 'grace_seconds_dashcam', '0.6', 'number', 'Grace period dump truck saat swing kabin dashcam'],
            ['operational', 'target_cycles_per_hour', '55', 'number', 'Target produktivitas siklus per jam'],
            ['operational', 'nominal_payload_ton', '7.5', 'number', 'Kapasitas rata-rata muatan per bucket (ton)'],
            ['site', 'site_name', 'PT Caritas Energi Indonesia - Site Sarolangun', 'string', 'Nama lokasi tambang / proyek'],
        ];

        foreach ($settings as $s) {
            SystemSetting::updateOrCreate(
                ['key' => $s[1]],
                [
                    'kategori' => $s[0],
                    'value' => $s[2],
                    'tipe' => $s[3],
                    'keterangan' => $s[4],
                ]
            );
        }
    }
}
