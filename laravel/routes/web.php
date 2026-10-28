<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\DetectionProfileController;
use App\Http\Controllers\LaporanController;
use App\Http\Controllers\MasterController;
use App\Http\Controllers\MonitoringController;
use App\Http\Controllers\PengaturanController;
use App\Http\Controllers\UserController;
use Illuminate\Support\Facades\Route;

// Redirect root to dashboard (will redirect to /login if unauthenticated)
Route::get('/', fn () => redirect()->route('dashboard'));

// ================= PUBLIC API TELEMETRY (AI ENGINE & INTEGRATION) =================
Route::prefix('api')->group(function () {
    Route::get('/telemetry/live', [DashboardController::class, 'telemetryLive'])->name('api.telemetry.live');
    Route::get('/telemetry/profile/{kodeUnit}', [DetectionProfileController::class, 'apiGetConfig'])->name('api.telemetry.profile');
    Route::get('/telemetry/cameras', [MonitoringController::class, 'apiCameras'])->name('api.telemetry.cameras');
});

// ================= AUTENTIKASI (GUEST) =================
Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login']);
});

// ================= OPERASIONAL HERA (PROTECTED / AUTH) =================
Route::middleware('auth')->group(function () {

    // Logout
    Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

    // 1. Dashboard Utama
    Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');

    // 2. Monitoring & AI Deteksi
    Route::prefix('monitoring')->group(function () {
        Route::get('/live', [MonitoringController::class, 'live'])->name('monitoring.live');
        Route::get('/deteksi', [MonitoringController::class, 'deteksi'])->name('deteksi');
        Route::get('/produktivitas', [MonitoringController::class, 'produktivitas'])->name('monitoring.produktivitas');
        Route::get('/riwayat', [MonitoringController::class, 'riwayat'])->name('monitoring.riwayat');
        Route::get('/export-csv', [MonitoringController::class, 'exportCsv'])->name('monitoring.export-csv');
    });

    // 3. Master Data
    Route::prefix('master')->group(function () {
        // Master Unit Alat Berat
        Route::get('/unit', [MasterController::class, 'unitIndex'])->name('master.unit');
        Route::post('/unit', [MasterController::class, 'unitStore'])->name('master.unit.store');
        Route::put('/unit/{id}', [MasterController::class, 'unitUpdate'])->name('master.unit.update');
        Route::delete('/unit/{id}', [MasterController::class, 'unitDestroy'])->name('master.unit.destroy');

        // Master Dump Truck
        Route::get('/truck', [MasterController::class, 'truckIndex'])->name('master.truck');
        Route::post('/truck', [MasterController::class, 'truckStore'])->name('master.truck.store');
        Route::put('/truck/{id}', [MasterController::class, 'truckUpdate'])->name('master.truck.update');
        Route::delete('/truck/{id}', [MasterController::class, 'truckDestroy'])->name('master.truck.destroy');

        // Master Kamera & Video
        Route::get('/kamera', [MasterController::class, 'kameraIndex'])->name('master.kamera');
        Route::post('/kamera', [MasterController::class, 'kameraStore'])->name('master.kamera.store');
        Route::put('/kamera/{id}', [MasterController::class, 'kameraUpdate'])->name('master.kamera.update');
        Route::delete('/kamera/{id}', [MasterController::class, 'kameraDestroy'])->name('master.kamera.destroy');
        Route::post('/kamera/test-connection', [MasterController::class, 'kameraTest'])->name('master.kamera.test');

        // Master Pola Detektor, Trigger & Zona Gali (Preset AI)
        Route::get('/pattern', [DetectionProfileController::class, 'index'])->name('master.pattern');
        Route::post('/pattern', [DetectionProfileController::class, 'store'])->name('master.pattern.store');
        Route::put('/pattern/{id}', [DetectionProfileController::class, 'update'])->name('master.pattern.update');
        Route::delete('/pattern/{id}', [DetectionProfileController::class, 'destroy'])->name('master.pattern.destroy');
        Route::post('/pattern/assign-unit', [DetectionProfileController::class, 'assignUnit'])->name('master.pattern.assign');

        // Master User & Hak Akses
        Route::get('/user', [UserController::class, 'index'])->name('master.user');
        Route::post('/user', [UserController::class, 'store'])->name('master.user.store');
        Route::put('/user/{id}', [UserController::class, 'update'])->name('master.user.update');
        Route::delete('/user/{id}', [UserController::class, 'destroy'])->name('master.user.destroy');
    });

    // 4. Laporan Produksi
    Route::prefix('laporan')->group(function () {
        Route::get('/harian', [LaporanController::class, 'harian'])->name('laporan.harian');
    });

    // 5. Pengaturan Sistem & AI
    Route::get('/pengaturan', [PengaturanController::class, 'index'])->name('pengaturan');
    Route::post('/pengaturan', [PengaturanController::class, 'update'])->name('pengaturan.update');
});
