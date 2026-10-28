<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('detection_profiles', function (Blueprint $table) {
            $table->id();
            $table->string('kode_profil', 50)->unique();
            $table->string('nama', 100);
            $table->string('tipe_alat', 50)->default('Excavator');
            $table->text('deskripsi')->nullable();
            $table->boolean('is_default')->default(false);

            // 1. Pola Detektor Komponen (Thresholds)
            $table->decimal('bucket_confidence', 4, 2)->default(0.18);
            $table->decimal('bucket_low_ratio', 4, 2)->default(0.55);
            $table->decimal('truck_confidence', 4, 2)->default(0.18);
            $table->decimal('truck_hold_seconds', 4, 1)->default(4.0);
            $table->decimal('truck_min_width_ratio', 4, 2)->default(0.12);
            $table->decimal('arm_confidence', 4, 2)->default(0.20);
            $table->decimal('arm_swing_threshold', 4, 2)->default(0.15);
            $table->decimal('plate_confidence', 4, 2)->default(0.40);
            $table->boolean('plate_ocr_enabled')->default(true);

            // 2. Trigger Parameter Siklus FSM
            $table->decimal('motion_threshold', 6, 4)->default(0.08);
            $table->decimal('dig_min_seconds', 4, 1)->default(2.0);
            $table->decimal('dump_min_seconds', 4, 1)->default(1.2);
            $table->decimal('phase_min_seconds', 4, 1)->default(0.8);
            $table->decimal('idle_seconds', 4, 1)->default(5.0);

            // 3. Konfigurasi Geometri & ROI Zona Gali / Tuang
            $table->decimal('zona_gali_x1', 5, 4)->default(0.05);
            $table->decimal('zona_gali_y1', 5, 4)->default(0.40);
            $table->decimal('zona_gali_x2', 5, 4)->default(0.95);
            $table->decimal('zona_gali_y2', 5, 4)->default(0.99);
            $table->decimal('dump_top_ratio', 5, 4)->default(0.12);
            $table->decimal('dump_height_ratio', 5, 4)->default(0.60);

            $table->timestamps();
        });

        // Tambah foreign key ke tabel units
        Schema::table('units', function (Blueprint $table) {
            $table->foreignId('detection_profile_id')->nullable()->after('keterangan')->constrained('detection_profiles')->nullOnDelete();
        });

        // Seed 4 Template Awal Standar Pertambangan
        DB::table('detection_profiles')->insert([
            [
                'kode_profil' => 'PROF-CAT395-BOOM',
                'nama' => 'Cat 395 Cabin Boom POV (Standard Pit)',
                'tipe_alat' => 'Excavator Cat 395',
                'deskripsi' => 'Profil standar kamera dashcam kabin mengarah ke lengan boom. Dikalibrasi untuk sudut pandang vertikal (476x848) siang dan malam.',
                'is_default' => true,
                'bucket_confidence' => 0.18,
                'bucket_low_ratio' => 0.55,
                'truck_confidence' => 0.18,
                'truck_hold_seconds' => 4.0,
                'truck_min_width_ratio' => 0.12,
                'arm_confidence' => 0.20,
                'arm_swing_threshold' => 0.15,
                'plate_confidence' => 0.40,
                'plate_ocr_enabled' => true,
                'motion_threshold' => 0.08,
                'dig_min_seconds' => 2.0,
                'dump_min_seconds' => 1.2,
                'phase_min_seconds' => 0.8,
                'idle_seconds' => 5.0,
                'zona_gali_x1' => 0.05,
                'zona_gali_y1' => 0.40,
                'zona_gali_x2' => 0.95,
                'zona_gali_y2' => 0.99,
                'dump_top_ratio' => 0.12,
                'dump_height_ratio' => 0.60,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'kode_profil' => 'PROF-PC2000-SIDE',
                'nama' => 'Komatsu PC2000 Highwall (Overburden Side View)',
                'tipe_alat' => 'Excavator PC2000',
                'deskripsi' => 'Profil kamera eksternal samping (bench side / highwall) untuk ekskavator pengupasan tanah penutup (OB). Bidang pandang horizontal (1280x720).',
                'is_default' => false,
                'bucket_confidence' => 0.25,
                'bucket_low_ratio' => 0.50,
                'truck_confidence' => 0.28,
                'truck_hold_seconds' => 3.5,
                'truck_min_width_ratio' => 0.15,
                'arm_confidence' => 0.25,
                'arm_swing_threshold' => 0.18,
                'plate_confidence' => 0.45,
                'plate_ocr_enabled' => true,
                'motion_threshold' => 0.06,
                'dig_min_seconds' => 2.5,
                'dump_min_seconds' => 1.5,
                'phase_min_seconds' => 1.0,
                'idle_seconds' => 6.0,
                'zona_gali_x1' => 0.10,
                'zona_gali_y1' => 0.50,
                'zona_gali_x2' => 0.65,
                'zona_gali_y2' => 0.95,
                'dump_top_ratio' => 0.15,
                'dump_height_ratio' => 0.55,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'kode_profil' => 'PROF-EX1200-STOCKPILE',
                'nama' => 'Hitachi EX1200 Seam Face (Stockpile Rehandling)',
                'tipe_alat' => 'Excavator EX1200',
                'deskripsi' => 'Profil cepat untuk pemuatan batu bara di stockpile seam 3 ke dump truck hauling dengan ritme pengerukan tinggi.',
                'is_default' => false,
                'bucket_confidence' => 0.20,
                'bucket_low_ratio' => 0.48,
                'truck_confidence' => 0.22,
                'truck_hold_seconds' => 3.0,
                'truck_min_width_ratio' => 0.14,
                'arm_confidence' => 0.22,
                'arm_swing_threshold' => 0.12,
                'plate_confidence' => 0.35,
                'plate_ocr_enabled' => true,
                'motion_threshold' => 0.07,
                'dig_min_seconds' => 1.8,
                'dump_min_seconds' => 1.0,
                'phase_min_seconds' => 0.6,
                'idle_seconds' => 4.0,
                'zona_gali_x1' => 0.20,
                'zona_gali_y1' => 0.35,
                'zona_gali_x2' => 0.80,
                'zona_gali_y2' => 0.95,
                'dump_top_ratio' => 0.10,
                'dump_height_ratio' => 0.50,
                'created_at' => now(),
                'updated_at' => now(),
            ],
            [
                'kode_profil' => 'PROF-NIGHT-SENSITIVE',
                'nama' => 'Low-Light Night Dashcam (High Sensitivity Optical Flow)',
                'tipe_alat' => 'Semua Unit (Malam/Kabut)',
                'deskripsi' => 'Sensitivitas tinggi untuk kondisi malam berkabut, debu tebal, atau penerangan minim. Buffer penahanan truk diperpanjang hingga 5 detik.',
                'is_default' => false,
                'bucket_confidence' => 0.14,
                'bucket_low_ratio' => 0.52,
                'truck_confidence' => 0.15,
                'truck_hold_seconds' => 5.0,
                'truck_min_width_ratio' => 0.10,
                'arm_confidence' => 0.18,
                'arm_swing_threshold' => 0.10,
                'plate_confidence' => 0.30,
                'plate_ocr_enabled' => false,
                'motion_threshold' => 0.05,
                'dig_min_seconds' => 1.5,
                'dump_min_seconds' => 1.2,
                'phase_min_seconds' => 0.8,
                'idle_seconds' => 5.0,
                'zona_gali_x1' => 0.05,
                'zona_gali_y1' => 0.38,
                'zona_gali_x2' => 0.95,
                'zona_gali_y2' => 0.99,
                'dump_top_ratio' => 0.12,
                'dump_height_ratio' => 0.65,
                'created_at' => now(),
                'updated_at' => now(),
            ],
        ]);

        // Hubungkan unit EXC-07 ke profil default
        $defaultProfile = DB::table('detection_profiles')->where('kode_profil', 'PROF-CAT395-BOOM')->first();
        if ($defaultProfile) {
            DB::table('units')->where('kode_unit', 'EXC-07')->update([
                'detection_profile_id' => $defaultProfile->id,
            ]);
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('units', function (Blueprint $table) {
            $table->dropForeign(['detection_profile_id']);
            $table->dropColumn('detection_profile_id');
        });

        Schema::dropIfExists('detection_profiles');
    }
};
