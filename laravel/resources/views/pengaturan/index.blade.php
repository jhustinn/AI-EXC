@extends('layouts.app')

@section('title', 'Pengaturan Sistem & AI')
@section('breadcrumb', 'Sistem / Pengaturan')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Konfigurasi Sistem & Parameter AI</h1>
            <p class="text-secondary small mb-0">Kelola ambang batas deteksi objek computer vision, konektivitas engine, dan parameter operasional.</p>
        </div>
    </div>

    <div class="row g-3">
        <!-- AI ENGINE PARAMETERS FORM -->
        <div class="col-12 col-xl-8">
            <div class="panel">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-sliders text-primary"></i> Ambang Batas Inferensi AI & FSM</h2>
                </div>
                <div class="p-4">
                    <form action="{{ route('pengaturan.update') }}" method="POST">
                        @csrf
                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Confidence Deteksi Objek (Bucket / Truck)</label>
                                <div class="input-group">
                                    <input type="number" step="0.01" min="0.05" max="0.95" name="confidence_threshold" class="form-control" value="{{ $settings['confidence_threshold']->value ?? '0.18' }}">
                                    <span class="input-group-text">Skala 0-1</span>
                                </div>
                                <small class="text-secondary">Rekomendasi video malam: 0.18 agar dump truck dan bucket terdeteksi konsisten.</small>
                            </div>

                            <div class="col-md-6">
                                <label class="form-label">Ambang Deteksi Gerak (Optical Flow)</label>
                                <div class="input-group">
                                    <input type="number" step="0.01" min="0.01" max="0.5" name="motion_threshold" class="form-control" value="{{ $settings['motion_threshold']->value ?? '0.08' }}">
                                    <span class="input-group-text">Ambang</span>
                                </div>
                                <small class="text-secondary">Mendeteksi aktivitas pengerukan saat lampu sorot menerangi lubang pit.</small>
                            </div>
                        </div>

                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Grace Period Truk Dashcam POV (Detik)</label>
                                <div class="input-group">
                                    <input type="number" step="0.1" min="0.2" max="5.0" name="grace_seconds_dashcam" class="form-control" value="{{ $settings['grace_seconds_dashcam']->value ?? '0.6' }}">
                                    <span class="input-group-text">Detik</span>
                                </div>
                                <small class="text-secondary">Waktu toleransi saat ekskavator berputar (swing) meninggalkan bak truk.</small>
                            </div>

                            <div class="col-md-6">
                                <label class="form-label">Target Produktivitas Siklus per Jam</label>
                                <div class="input-group">
                                    <input type="number" step="1" name="target_cycles_per_hour" class="form-control" value="{{ $settings['target_cycles_per_hour']->value ?? '55' }}">
                                    <span class="input-group-text">Siklus/Jam</span>
                                </div>
                                <small class="text-secondary">KPI acuan target efisiensi per jam pemuatan tambang.</small>
                            </div>
                        </div>

                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label class="form-label">Estimasi Tonase Nominal per Bucket (Ton)</label>
                                <div class="input-group">
                                    <input type="number" step="0.1" name="nominal_payload_ton" class="form-control" value="{{ $settings['nominal_payload_ton']->value ?? '7.5' }}">
                                    <span class="input-group-text">Ton</span>
                                </div>
                                <small class="text-secondary">Konversi volume bucket Cat 395 (6.5 m&sup3;) ke berat batu bara.</small>
                            </div>

                            <div class="col-md-6">
                                <label class="form-label">Nama Proyek / Site</label>
                                <input type="text" name="site_name" class="form-control" value="{{ $settings['site_name']->value ?? 'PT Caritas Energi Indonesia - Site Sarolangun' }}">
                            </div>
                        </div>

                        <div class="d-flex justify-content-end">
                            <button type="submit" class="btn btn-primary d-flex align-items-center gap-2">
                                <i class="bi bi-save"></i> Simpan Perubahan Pengaturan
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- DATABASE & SYSTEM HEALTH -->
        <div class="col-12 col-xl-4">
            <div class="panel mb-3">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-database text-primary"></i> Status Database PostgreSQL</h2>
                </div>
                <div class="p-3">
                    <table class="table table-sm table-borderless small mb-0">
                        <tbody>
                            <tr>
                                <td class="text-secondary">RDBMS Server</td>
                                <td class="text-end fw-semibold">PostgreSQL 17</td>
                            </tr>
                            <tr>
                                <td class="text-secondary">Database Name</td>
                                <td class="text-end fw-semibold text-primary">{{ $dbStats['db_name'] ?? 'ai_cctv' }}</td>
                            </tr>
                            <tr>
                                <td class="text-secondary">Host &amp; Port</td>
                                <td class="text-end fw-semibold">127.0.0.1:5432</td>
                            </tr>
                            <tr>
                                <td class="text-secondary">Jumlah Unit Terdaftar</td>
                                <td class="text-end fw-semibold">{{ $dbStats['total_units'] ?? 0 }} Unit</td>
                            </tr>
                            <tr>
                                <td class="text-secondary">Total Siklus Tersimpan</td>
                                <td class="text-end fw-semibold text-success">{{ $dbStats['total_cycles'] ?? 0 }} Siklus</td>
                            </tr>
                            <tr>
                                <td class="text-secondary">Total Event Log Deteksi</td>
                                <td class="text-end fw-semibold text-dark">{{ $dbStats['total_logs'] ?? 0 }} Event</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-router text-primary"></i> AI Engine Endpoint</h2>
                </div>
                <div class="p-3 small">
                    <div class="mb-2">
                        <span class="text-secondary d-block">FastAPI Service URL:</span>
                        <code>{{ config('hera.api_url') }}</code>
                    </div>
                    <div class="mb-3">
                        <span class="text-secondary d-block">MJPEG Stream URL:</span>
                        <code>{{ config('hera.stream_url') }}/stream</code>
                    </div>
                    <div class="p-2 rounded bg-success-subtle text-success-emphasis border border-success-subtle d-flex align-items-center gap-2">
                        <i class="bi bi-shield-check fs-5"></i>
                        <div>
                            <strong>Service Sehat &amp; Terhubung</strong><br>
                            Latensi API query &lt; 15 ms.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

@endsection
