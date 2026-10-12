<?php

use Illuminate\Support\Facades\Route;

Route::get('/', fn () => redirect()->route('dashboard'));

Route::get('/dashboard', function () {
    return view('dashboard', [
        'breadcrumb' => 'Dashboard',
        'unit' => env('HERA_DEFAULT_UNIT', 'EXC-07'),
    ]);
})->name('dashboard');

Route::get('/monitoring/deteksi', function () {
    return view('deteksi', [
        'breadcrumb' => 'Monitoring / Deteksi Aktivitas AI',
        'unit' => env('HERA_DEFAULT_UNIT', 'EXC-07'),
    ]);
})->name('deteksi');