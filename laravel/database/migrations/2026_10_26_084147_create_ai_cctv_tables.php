<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // 1. Master Unit Alat Berat
        Schema::create('units', function (Blueprint $table) {
            $table->id();
            $table->string('kode_unit', 50)->unique();
            $table->string('nama', 100);
            $table->string('jenis', 50)->default('Excavator');
            $table->string('merk', 50)->default('Caterpillar');
            $table->string('model', 50)->default('395 Ultra-Class');
            $table->decimal('kapasitas_bucket_m3', 5, 2)->default(6.50);
            $table->string('status', 30)->default('OPERATIONAL'); // OPERATIONAL, IDLE, MAINTENANCE, OFFLINE
            $table->string('lokasi_pit', 100)->default('Pit Sarolangun Block B');
            $table->string('operator', 100)->nullable()->default('Ahmad Fauzi');
            $table->text('keterangan')->nullable();
            $table->timestamps();
        });

        // 2. Master Kamera & Stream Video
        Schema::create('cameras', function (Blueprint $table) {
            $table->id();
            $table->foreignId('unit_id')->constrained('units')->onDelete('cascade');
            $table->string('nama', 100);
            $table->string('posisi', 50)->default('Cabin Dashcam');
            $table->string('source_type', 30)->default('video'); // video, rtsp, usb
            $table->text('source_path')->default('video/night_dashcam.mp4');
            $table->integer('fps')->default(18);
            $table->string('resolusi', 20)->default('476x848');
            $table->boolean('is_primary')->default(true);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        // 3. Master Dump Truck
        Schema::create('trucks', function (Blueprint $table) {
            $table->id();
            $table->string('kode_truk', 50)->unique();
            $table->string('no_polisi', 30)->nullable();
            $table->string('merk_tipe', 100)->default('Loxa Mining Dump Truck 6x4');
            $table->string('vendor', 100)->default('PT Caritas Energi Indonesia');
            $table->decimal('kapasitas_ton', 6, 2)->default(35.00);
            $table->string('status', 30)->default('ACTIVE'); // ACTIVE, HAULING, STANDBY, MAINTENANCE
            $table->timestamps();
        });

        // 4. Log Aktivitas AI Deteksi (Event riwayat resolusi tinggi)
        Schema::create('activity_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('unit_id')->constrained('units')->onDelete('cascade');
            $table->foreignId('truck_id')->nullable()->constrained('trucks')->nullOnDelete();
            $table->integer('siklus_ke')->default(0);
            $table->string('fase', 30); // mengeruk, menuangkan, memutar, idle, kembali, mengangkat
            $table->string('fase_label', 50);
            $table->timestampTz('mulai');
            $table->timestampTz('selesai')->nullable();
            $table->decimal('durasi_detik', 8, 2)->default(0);
            $table->decimal('truck_confidence', 5, 3)->default(0);
            $table->decimal('bucket_confidence', 5, 3)->default(0);
            $table->decimal('excavator_confidence', 5, 3)->default(0);
            $table->decimal('motion_score', 7, 4)->default(0);
            $table->timestamps();

            $table->index(['unit_id', 'mulai']);
            $table->index(['fase']);
            $table->index(['siklus_ke']);
        });

        // 5. Agregat Siklus Kerja (1 Siklus = Pengerukan + Menuangkan selesai)
        Schema::create('cycles', function (Blueprint $table) {
            $table->id();
            $table->foreignId('unit_id')->constrained('units')->onDelete('cascade');
            $table->foreignId('truck_id')->nullable()->constrained('trucks')->nullOnDelete();
            $table->integer('siklus_ke');
            $table->decimal('durasi_mengeruk', 8, 2)->default(0);
            $table->decimal('durasi_menuangkan', 8, 2)->default(0);
            $table->decimal('durasi_total', 8, 2)->default(0);
            $table->timestampTz('waktu_mulai');
            $table->timestampTz('waktu_selesai')->nullable();
            $table->decimal('payload_est_ton', 6, 2)->default(7.50);
            $table->string('status', 30)->default('COMPLETED'); // COMPLETED, IN_PROGRESS, ABORTED
            $table->timestamps();

            $table->index(['unit_id', 'waktu_mulai']);
        });

        // 6. Rekapitulasi Shift Kerja & Produktivitas
        Schema::create('shift_reports', function (Blueprint $table) {
            $table->id();
            $table->foreignId('unit_id')->constrained('units')->onDelete('cascade');
            $table->date('tanggal');
            $table->string('shift', 30)->default('Shift 1 (Pagi)');
            $table->string('operator', 100)->default('Ahmad Fauzi');
            $table->integer('total_siklus')->default(0);
            $table->decimal('total_mengeruk_detik', 10, 2)->default(0);
            $table->decimal('total_menuangkan_detik', 10, 2)->default(0);
            $table->decimal('total_idle_detik', 10, 2)->default(0);
            $table->decimal('total_tonase_est', 10, 2)->default(0);
            $table->decimal('efisiensi_operasional', 5, 2)->default(0); // persen
            $table->text('catatan')->nullable();
            $table->timestamps();

            $table->unique(['unit_id', 'tanggal', 'shift']);
        });

        // 7. Pengaturan Sistem & Ambang AI
        Schema::create('system_settings', function (Blueprint $table) {
            $table->id();
            $table->string('kategori', 50)->default('ai_engine');
            $table->string('key', 100)->unique();
            $table->text('value')->nullable();
            $table->string('tipe', 20)->default('string'); // string, number, boolean, json
            $table->text('keterangan')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('system_settings');
        Schema::dropIfExists('shift_reports');
        Schema::dropIfExists('cycles');
        Schema::dropIfExists('activity_logs');
        Schema::dropIfExists('trucks');
        Schema::dropIfExists('cameras');
        Schema::dropIfExists('units');
    }
};
