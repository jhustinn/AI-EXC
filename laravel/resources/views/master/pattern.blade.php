@extends('layouts.app')

@section('title', 'Master Pola Deteksi & Triggers')
@section('breadcrumb', 'Master Data / Pola Deteksi & Triggers')

@section('content')

    <!-- HEADER & ACTION BAR -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark d-flex align-items-center gap-2">
                <i class="bi bi-diagram-3-fill text-primary"></i>
                <span>Master Pola Detektor, Triggers &amp; Zona Gali AI</span>
            </h1>
            <p class="text-secondary small mb-0">
                Konfigurasi profil presisi deteksi komputer vision: ambang keyakinan bucket, kinematika arm, bak dump truck, OCR plat nomor, dan ambang pemicu siklus kerja tambang.
            </p>
        </div>
        <div class="d-flex align-items-center gap-2">
            <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" data-bs-toggle="modal" data-bs-target="#addProfileModal">
                <i class="bi bi-plus-circle-fill"></i> Buat Profil Pola Baru
            </button>
        </div>
    </div>

    <!-- STATS SUMMARY CARDS -->
    <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-sliders2 fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Profil / Preset</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['total_profiles'] }} Preset</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-check-circle-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Unit Terkonfigurasi</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['units_configured'] }} / {{ $stats['total_units'] }} Unit</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-warning-subtle text-warning-emphasis">
                    <i class="bi bi-camera-reels-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Profil Default Sistem</div>
                    <div class="fs-6 fw-bold text-truncate text-dark" style="max-width: 170px;" title="{{ $stats['default_profile'] }}">
                        {{ $stats['default_profile'] }}
                    </div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-info-subtle text-info">
                    <i class="bi bi-layers-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Pola Komponen AI</div>
                    <div class="fs-6 fw-bold text-dark">Bucket &bull; Arm &bull; Truck &bull; Plat</div>
                </div>
            </div>
        </div>
    </div>

    <!-- TABEL PENUGASAN PROFIL KE UNIT AKTIF -->
    <div class="panel mb-4">
        <div class="panel-head d-flex justify-content-between align-items-center">
            <h2 class="panel-title mb-0">
                <i class="bi bi-truck-front text-primary"></i>
                <span>Penugasan Profil Pola Deteksi ke Armada Ekskavator</span>
            </h2>
            <span class="small text-secondary">Setiap unit dapat memiliki kalibrasi pola &amp; zona yang independen</span>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light small text-secondary">
                    <tr>
                        <th>Kode Unit</th>
                        <th>Model Ekskavator &amp; Pit</th>
                        <th>Profil Deteksi Aktif</th>
                        <th>Zona Gali &amp; Tuang</th>
                        <th>Trigger Mengeruk / Menuang</th>
                        <th>Kamera Utama</th>
                        <th class="text-end" style="width: 160px;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach($units as $u)
                        @php
                            $prof = $u->detectionProfile ?? $profiles->firstWhere('is_default', true);
                        @endphp
                        <tr>
                            <td>
                                <strong class="fs-6 text-dark">{{ $u->kode_unit }}</strong>
                            </td>
                            <td>
                                <div class="fw-semibold text-dark">{{ $u->nama }}</div>
                                <div class="small text-secondary"><i class="bi bi-geo-alt"></i> {{ $u->lokasi_pit }}</div>
                            </td>
                            <td>
                                @if($u->detectionProfile)
                                    <span class="badge text-bg-primary-subtle text-primary border border-primary-subtle px-2 py-1">
                                        <i class="bi bi-cpu-fill me-1"></i> {{ $u->detectionProfile->nama }}
                                    </span>
                                @else
                                    <span class="badge text-bg-secondary-subtle text-secondary border px-2 py-1">
                                        Default: {{ $prof->nama ?? 'Standard Pit' }}
                                    </span>
                                @endif
                            </td>
                            <td class="small font-monospace">
                                <div><span class="text-success fw-semibold">Gali:</span> [{{ $prof->zona_gali_x1 }}, {{ $prof->zona_gali_y1 }}, {{ $prof->zona_gali_x2 }}, {{ $prof->zona_gali_y2 }}]</div>
                                <div><span class="text-warning-emphasis fw-semibold">Tuang:</span> Top {{ round($prof->dump_top_ratio * 100) }}% / T {{ round($prof->dump_height_ratio * 100) }}%</div>
                            </td>
                            <td class="small">
                                <div><i class="bi bi-shovel text-success"></i> Motion: &gt;{{ $prof->motion_threshold }} ({{ $prof->dig_min_seconds }}s)</div>
                                <div><i class="bi bi-box-arrow-in-down text-warning"></i> Truck Hold: {{ $prof->truck_hold_seconds }}s ({{ $prof->dump_min_seconds }}s)</div>
                            </td>
                            <td class="small">
                                @if($u->primaryCamera)
                                    <span class="badge text-bg-dark font-monospace">{{ $u->primaryCamera->nama }}</span>
                                    <span class="text-secondary d-block" style="font-size:11px;">{{ $u->primaryCamera->resolusi }} &bull; {{ $u->primaryCamera->fps }} FPS</span>
                                @else
                                    <span class="text-secondary">Belum ada kamera</span>
                                @endif
                            </td>
                            <td class="text-end">
                                <button type="button" class="btn btn-sm btn-outline-primary" 
                                        onclick="openAssignModal({{ $u->id }}, '{{ $u->kode_unit }}', '{{ $u->nama }}', {{ $u->detection_profile_id ?? ($prof->id ?? 'null') }})">
                                    <i class="bi bi-arrow-repeat"></i> Ganti Profil
                                </button>
                            </td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    </div>

    <!-- DAFTAR PRESET PROFIL POLA & TRIGGER -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h3 class="h5 fw-bold text-dark mb-0">
            <i class="bi bi-collection-fill text-primary"></i> Preset Profil Pola &amp; Triggers Tersimpan
        </h3>
        <span class="text-secondary small">{{ $profiles->count() }} Template Tersedia</span>
    </div>

    <div class="row g-3 mb-4">
        @foreach($profiles as $p)
            <div class="col-12 col-xl-6">
                <div class="panel h-100 border {{ $p->is_default ? 'border-primary shadow-sm' : '' }}">
                    <div class="panel-head d-flex justify-content-between align-items-center bg-light">
                        <div class="d-flex align-items-center gap-2 min-w-0">
                            @if($p->is_default)
                                <span class="badge text-bg-primary"><i class="bi bi-star-fill"></i> DEFAULT SISTEM</span>
                            @else
                                <span class="badge text-bg-secondary"><i class="bi bi-bookmark-fill"></i> PRESET</span>
                            @endif
                            <h4 class="panel-title text-truncate mb-0 fw-bold" title="{{ $p->nama }}">{{ $p->nama }}</h4>
                        </div>
                        <span class="badge text-bg-light border text-secondary font-monospace" style="font-size: 11px;">
                            {{ $p->kode_profil }}
                        </span>
                    </div>

                    <div class="p-3">
                        <p class="small text-secondary mb-3">{{ $p->deskripsi }}</p>

                        <!-- COMPONENT PATTERNS RADAR / CHIPS -->
                        <div class="border rounded p-2 mb-3 bg-white">
                            <h6 class="fs-7 text-uppercase fw-bold text-secondary mb-2">
                                <i class="bi bi-bounding-box-circles text-primary"></i> 1. Pola Deteksi Objek Komponen
                            </h6>
                            <div class="row g-2 text-center small">
                                <div class="col-6 col-sm-3">
                                    <div class="p-2 border rounded bg-light">
                                        <div class="text-secondary" style="font-size:11px;">Bucket Pengeruk</div>
                                        <strong class="text-success fs-6">{{ round($p->bucket_confidence * 100) }}%</strong>
                                        <div class="text-muted" style="font-size:10px;">Low: {{ round($p->bucket_low_ratio * 100) }}%</div>
                                    </div>
                                </div>
                                <div class="col-6 col-sm-3">
                                    <div class="p-2 border rounded bg-light">
                                        <div class="text-secondary" style="font-size:11px;">Dump Truck</div>
                                        <strong class="text-warning-emphasis fs-6">{{ round($p->truck_confidence * 100) }}%</strong>
                                        <div class="text-muted" style="font-size:10px;">Hold: {{ $p->truck_hold_seconds }}s</div>
                                    </div>
                                </div>
                                <div class="col-6 col-sm-3">
                                    <div class="p-2 border rounded bg-light">
                                        <div class="text-secondary" style="font-size:11px;">Arm &amp; Boom</div>
                                        <strong class="text-primary fs-6">{{ round($p->arm_confidence * 100) }}%</strong>
                                        <div class="text-muted" style="font-size:10px;">Swing: &gt;{{ $p->arm_swing_threshold }}</div>
                                    </div>
                                </div>
                                <div class="col-6 col-sm-3">
                                    <div class="p-2 border rounded bg-light">
                                        <div class="text-secondary" style="font-size:11px;">Plat Nomor OCR</div>
                                        @if($p->plate_ocr_enabled)
                                            <strong class="text-info fs-6">{{ round($p->plate_confidence * 100) }}%</strong>
                                            <div class="text-success fw-bold" style="font-size:10px;">Aktif OCR</div>
                                        @else
                                            <strong class="text-muted fs-6">Disabled</strong>
                                            <div class="text-muted" style="font-size:10px;">Non-aktif</div>
                                        @endif
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- TRIGGER CONDITIONS -->
                        <div class="border rounded p-2 mb-3 bg-white">
                            <h6 class="fs-7 text-uppercase fw-bold text-secondary mb-2">
                                <i class="bi bi-lightning-charge-fill text-warning"></i> 2. Parameter Trigger Siklus Kerja
                            </h6>
                            <div class="row g-2 small">
                                <div class="col-6">
                                    <div class="d-flex justify-content-between p-2 rounded bg-light">
                                        <span class="text-secondary"><i class="bi bi-shovel text-success"></i> Trigger Mengeruk:</span>
                                        <strong>Motion &gt; {{ $p->motion_threshold }} &bull; {{ $p->dig_min_seconds }}s</strong>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="d-flex justify-content-between p-2 rounded bg-light">
                                        <span class="text-secondary"><i class="bi bi-box-arrow-in-down text-warning"></i> Trigger Menuang:</span>
                                        <strong>Truck Diam &gt; {{ $p->dump_min_seconds }}s</strong>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="d-flex justify-content-between p-2 rounded bg-light">
                                        <span class="text-secondary"><i class="bi bi-stopwatch text-secondary"></i> Jeda Idle Standby:</span>
                                        <strong>{{ $p->idle_seconds }} detik</strong>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="d-flex justify-content-between p-2 rounded bg-light">
                                        <span class="text-secondary"><i class="bi bi-arrow-repeat text-primary"></i> Debounce Transisi:</span>
                                        <strong>{{ $p->phase_min_seconds }} detik</strong>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- GEOMETRI ROI ZONA GALI & TUANG -->
                        <div class="border rounded p-2 mb-3 bg-white">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <h6 class="fs-7 text-uppercase fw-bold text-secondary mb-0">
                                    <i class="bi bi-bounding-box text-primary"></i> 3. ROI Zona Gali &amp; Zona Tuang
                                </h6>
                                <span class="badge text-bg-light border text-dark font-monospace" style="font-size:10px;">
                                    Gali: [{{ $p->zona_gali_x1 }}, {{ $p->zona_gali_y1 }}, {{ $p->zona_gali_x2 }}, {{ $p->zona_gali_y2 }}]
                                </span>
                            </div>

                            <!-- MINI ROI CANVAS PREVIEW -->
                            <div class="position-relative rounded bg-dark border overflow-hidden mt-2" style="height: 110px;">
                                <div class="position-absolute text-white-50 p-1" style="font-size: 9px; top: 2px; left: 4px;">
                                    Video Feed Frame Simulator
                                </div>

                                <!-- Zona Gali Box -->
                                <div class="position-absolute border border-2 border-primary bg-primary bg-opacity-25 d-flex align-items-center justify-content-center text-white fw-bold font-monospace"
                                     style="left: {{ $p->zona_gali_x1 * 100 }}%; top: {{ $p->zona_gali_y1 * 100 }}%; width: {{ ($p->zona_gali_x2 - $p->zona_gali_x1) * 100 }}%; height: {{ ($p->zona_gali_y2 - $p->zona_gali_y1) * 100 }}%; font-size: 10px; border-radius: 4px;">
                                    <span>ZONA GALI PIT</span>
                                </div>

                                <!-- Zona Tuang Simulator Box -->
                                <div class="position-absolute border border-2 border-warning bg-warning bg-opacity-25 d-flex align-items-center justify-content-center text-warning fw-bold font-monospace"
                                     style="left: 10%; top: {{ $p->dump_top_ratio * 100 }}%; width: 45%; height: {{ $p->dump_height_ratio * 100 }}%; font-size: 9.5px; border-radius: 4px;">
                                    <span>ZONA TUANG TRUK</span>
                                </div>
                            </div>
                        </div>

                        <!-- CARD FOOTER ACTIONS -->
                        <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                            <span class="small text-secondary">
                                Digunakan oleh: <strong>{{ $p->units_count }} Unit Armada</strong>
                            </span>
                            <div class="d-flex gap-2">
                                <button type="button" class="btn btn-sm btn-outline-primary" onclick="openEditProfileModal({{ json_encode($p) }})">
                                    <i class="bi bi-pencil-square"></i> Edit Pola &amp; Trigger
                                </button>
                                @if(!$p->is_default)
                                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="confirmDeleteProfile({{ $p->id }}, '{{ $p->nama }}')">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                @endif
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        @endforeach
    </div>

    <!-- MODAL PENUGASAN PROFIL KE UNIT -->
    <div class="modal fade" id="assignUnitModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <form action="{{ route('master.pattern.assign') }}" method="POST">
                    @csrf
                    <input type="hidden" name="unit_id" id="assignUnitId">
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">Terapkan Profil Pola ke Unit</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="p-3 bg-light rounded border mb-3">
                            <div class="text-secondary small">Unit Ekskavator Sasaran:</div>
                            <strong class="fs-5 text-dark" id="assignUnitName">-</strong>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-semibold">Pilih Preset Pola Deteksi &amp; Triggers</label>
                            <select name="profile_id" id="assignProfileSelect" class="form-select" required>
                                @foreach($profiles as $pr)
                                    <option value="{{ $pr->id }}">
                                        {{ $pr->nama }} ({{ $pr->tipe_alat }})
                                    </option>
                                @endforeach
                            </select>
                            <small class="text-secondary d-block mt-1">
                                Ambang batas deteksi objek, koordinat zona gali, dan parameter trigger akan otomatis aktif untuk unit ini.
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                        <button type="submit" class="btn btn-primary btn-sm">Terapkan Sekarang</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- MODAL TAMBAH PROFIL BARU -->
    <div class="modal fade" id="addProfileModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form action="{{ route('master.pattern.store') }}" method="POST">
                    @csrf
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">Buat Profil Pola Deteksi &amp; Triggers Baru</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- IDENTITAS PROFIL -->
                        <div class="row g-3 mb-3">
                            <div class="col-md-4">
                                <label class="form-label">Kode Profil (Unik)</label>
                                <input type="text" name="kode_profil" class="form-control font-monospace" placeholder="PROF-CUSTOM-01" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Nama Profil</label>
                                <input type="text" name="nama" class="form-control" placeholder="Contoh: Loading Bench Barat Seam 2" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Tipe Alat Berat</label>
                                <input type="text" name="tipe_alat" class="form-control" placeholder="Excavator Cat 395" required>
                            </div>
                            <div class="col-12">
                                <label class="form-label">Deskripsi / Catatan Lapangan</label>
                                <textarea name="deskripsi" class="form-control" rows="2" placeholder="Catatan sudut pandang kamera, kondisi pencahayaan, atau material pit..."></textarea>
                            </div>
                        </div>

                        <!-- 1. POLA DETEKTOR KOMPONEN -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            1. Ambang Keyakinan Objek (Confidence Floor)
                        </h6>
                        <div class="row g-3 mb-3">
                            <div class="col-md-3">
                                <label class="form-label small">Bucket Confidence</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="bucket_confidence" class="form-control form-control-sm" value="0.18" required>
                                <small class="text-secondary" style="font-size:10.5px;">Standar: 0.18</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Bucket Low Ratio</label>
                                <input type="number" step="0.01" min="0.10" max="0.99" name="bucket_low_ratio" class="form-control form-control-sm" value="0.55" required>
                                <small class="text-secondary" style="font-size:10.5px;">Tinggi frame gali (0-1)</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Truck Confidence</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="truck_confidence" class="form-control form-control-sm" value="0.18" required>
                                <small class="text-secondary" style="font-size:10.5px;">Standar: 0.18</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Truck Hold (Detik)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="truck_hold_seconds" class="form-control form-control-sm" value="4.0" required>
                                <small class="text-secondary" style="font-size:10.5px;">Buffer debu (detik)</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Arm / Boom Conf</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="arm_confidence" class="form-control form-control-sm" value="0.20" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Swing Ambang Gerak</label>
                                <input type="number" step="0.01" min="0.02" max="0.50" name="arm_swing_threshold" class="form-control form-control-sm" value="0.15" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Plat Nomor Conf</label>
                                <input type="number" step="0.01" min="0.10" max="0.95" name="plate_confidence" class="form-control form-control-sm" value="0.40" required>
                            </div>
                            <div class="col-md-3 d-flex align-items-center">
                                <div class="form-check mt-3">
                                    <input class="form-check-input" type="checkbox" name="plate_ocr_enabled" value="1" id="addOcrCheck" checked>
                                    <label class="form-check-label small fw-semibold" for="addOcrCheck">
                                        Aktifkan OCR Plat
                                    </label>
                                </div>
                            </div>
                            <input type="hidden" name="truck_min_width_ratio" value="0.12">
                        </div>

                        <!-- 2. PARAMETER TRIGGER SIKLUS -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            2. Parameter Trigger Siklus Operasi (FSM)
                        </h6>
                        <div class="row g-3 mb-3">
                            <div class="col-md-3">
                                <label class="form-label small">Motion Threshold (Gali)</label>
                                <input type="number" step="0.005" min="0.01" max="0.50" name="motion_threshold" class="form-control form-control-sm" value="0.08" required>
                                <small class="text-secondary" style="font-size:10.5px;">Optical flow di pit</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Trigger Mengeruk (s)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="dig_min_seconds" class="form-control form-control-sm" value="2.0" required>
                                <small class="text-secondary" style="font-size:10.5px;">Durasi pemicu</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Trigger Menuang (s)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="dump_min_seconds" class="form-control form-control-sm" value="1.2" required>
                                <small class="text-secondary" style="font-size:10.5px;">Durasi di atas bak</small>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Idle Timeout (s)</label>
                                <input type="number" step="0.5" min="1.0" max="30.0" name="idle_seconds" class="form-control form-control-sm" value="5.0" required>
                            </div>
                            <input type="hidden" name="phase_min_seconds" value="0.8">
                        </div>

                        <!-- 3. GEOMETRI & ROI ZONA GALI & TUANG -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            3. Koordinat ROI Zona Gali &amp; Zona Tuang (Normalized 0.0 - 1.0)
                        </h6>
                        <div class="row g-3">
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali X1 (Kiri)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_x1" class="form-control form-control-sm" value="0.05" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali Y1 (Atas)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_y1" class="form-control form-control-sm" value="0.40" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali X2 (Kanan)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_x2" class="form-control form-control-sm" value="0.95" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali Y2 (Bawah)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_y2" class="form-control form-control-sm" value="0.99" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small">Pintu Bak Truk (Dump Top Ratio)</label>
                                <input type="number" step="0.01" min="0.01" max="0.50" name="dump_top_ratio" class="form-control form-control-sm" value="0.12" required>
                                <small class="text-secondary" style="font-size:10.5px;">Batas atas pintu bak truk</small>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small">Tinggi Bak Truk (Dump Height Ratio)</label>
                                <input type="number" step="0.01" min="0.10" max="0.95" name="dump_height_ratio" class="form-control form-control-sm" value="0.60" required>
                                <small class="text-secondary" style="font-size:10.5px;">Proporsi kedalaman bak</small>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                        <button type="submit" class="btn btn-primary btn-sm">Simpan Preset Pola</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- MODAL EDIT PROFIL -->
    <div class="modal fade" id="editProfileModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form id="editProfileForm" method="POST">
                    @csrf
                    @method('PUT')
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">Edit Pola Detektor &amp; Triggers</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- IDENTITAS -->
                        <div class="row g-3 mb-3">
                            <div class="col-md-4">
                                <label class="form-label">Kode Profil</label>
                                <input type="text" id="editKode" class="form-control font-monospace bg-light" readonly>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Nama Profil</label>
                                <input type="text" name="nama" id="editNama" class="form-control" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Tipe Alat Berat</label>
                                <input type="text" name="tipe_alat" id="editTipe" class="form-control" required>
                            </div>
                            <div class="col-12">
                                <label class="form-label">Deskripsi</label>
                                <textarea name="deskripsi" id="editDeskripsi" class="form-control" rows="2"></textarea>
                            </div>
                        </div>

                        <!-- 1. POLA DETEKTOR KOMPONEN -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            1. Ambang Keyakinan Objek (Confidence Floor)
                        </h6>
                        <div class="row g-3 mb-3">
                            <div class="col-md-3">
                                <label class="form-label small">Bucket Confidence</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="bucket_confidence" id="editBucketConf" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Bucket Low Ratio</label>
                                <input type="number" step="0.01" min="0.10" max="0.99" name="bucket_low_ratio" id="editBucketLow" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Truck Confidence</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="truck_confidence" id="editTruckConf" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Truck Hold (Detik)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="truck_hold_seconds" id="editTruckHold" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Arm / Boom Conf</label>
                                <input type="number" step="0.01" min="0.05" max="0.95" name="arm_confidence" id="editArmConf" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Swing Ambang Gerak</label>
                                <input type="number" step="0.01" min="0.02" max="0.50" name="arm_swing_threshold" id="editSwingThresh" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Plat Nomor Conf</label>
                                <input type="number" step="0.01" min="0.10" max="0.95" name="plate_confidence" id="editPlateConf" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3 d-flex align-items-center">
                                <div class="form-check mt-3">
                                    <input class="form-check-input" type="checkbox" name="plate_ocr_enabled" value="1" id="editOcrCheck">
                                    <label class="form-check-label small fw-semibold" for="editOcrCheck">
                                        Aktifkan OCR Plat
                                    </label>
                                </div>
                            </div>
                            <input type="hidden" name="truck_min_width_ratio" id="editMinWidth" value="0.12">
                        </div>

                        <!-- 2. PARAMETER TRIGGER SIKLUS -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            2. Parameter Trigger Siklus Operasi (FSM)
                        </h6>
                        <div class="row g-3 mb-3">
                            <div class="col-md-3">
                                <label class="form-label small">Motion Threshold (Gali)</label>
                                <input type="number" step="0.005" min="0.01" max="0.50" name="motion_threshold" id="editMotionThresh" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Trigger Mengeruk (s)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="dig_min_seconds" id="editDigMin" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Trigger Menuang (s)</label>
                                <input type="number" step="0.1" min="0.5" max="10.0" name="dump_min_seconds" id="editDumpMin" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Idle Timeout (s)</label>
                                <input type="number" step="0.5" min="1.0" max="30.0" name="idle_seconds" id="editIdleSec" class="form-control form-control-sm" required>
                            </div>
                            <input type="hidden" name="phase_min_seconds" id="editPhaseMin" value="0.8">
                        </div>

                        <!-- 3. GEOMETRI & ROI ZONA GALI & TUANG -->
                        <h6 class="fw-bold fs-7 text-uppercase text-secondary border-bottom pb-1 mb-3">
                            3. Koordinat ROI Zona Gali &amp; Zona Tuang
                        </h6>
                        <div class="row g-3">
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali X1 (Kiri)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_x1" id="editGaliX1" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali Y1 (Atas)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_y1" id="editGaliY1" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali X2 (Kanan)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_x2" id="editGaliX2" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label small">Zona Gali Y2 (Bawah)</label>
                                <input type="number" step="0.01" min="0" max="1" name="zona_gali_y2" id="editGaliY2" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small">Pintu Bak Truk (Dump Top Ratio)</label>
                                <input type="number" step="0.01" min="0.01" max="0.50" name="dump_top_ratio" id="editDumpTop" class="form-control form-control-sm" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small">Tinggi Bak Truk (Dump Height Ratio)</label>
                                <input type="number" step="0.01" min="0.10" max="0.95" name="dump_height_ratio" id="editDumpHeight" class="form-control form-control-sm" required>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                        <button type="submit" class="btn btn-primary btn-sm">Simpan Perubahan</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- MODAL HAPUS PROFIL -->
    <div class="modal fade" id="deleteProfileModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <form id="deleteProfileForm" method="POST">
                    @csrf
                    @method('DELETE')
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold text-danger"><i class="bi bi-exclamation-triangle-fill"></i> Hapus Profil Pola Deteksi</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Apakah Anda yakin ingin menghapus profil preset <strong id="deleteProfileName"></strong>?</p>
                        <div class="alert alert-warning small py-2 mb-0">
                            Unit armada yang sedang menggunakan profil ini akan otomatis dialihkan ke <strong>Profil Default Sistem</strong>.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                        <button type="submit" class="btn btn-danger btn-sm">Ya, Hapus Profil</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

@endsection

@push('scripts')
<script>
    function openAssignModal(unitId, unitKode, unitNama, currentProfileId) {
        document.getElementById('assignUnitId').value = unitId;
        document.getElementById('assignUnitName').textContent = unitKode + ' (' + unitNama + ')';
        if (currentProfileId) {
            document.getElementById('assignProfileSelect').value = currentProfileId;
        }
        new bootstrap.Modal(document.getElementById('assignUnitModal')).show();
    }

    function openEditProfileModal(p) {
        document.getElementById('editProfileForm').action = '/master/pattern/' + p.id;
        document.getElementById('editKode').value = p.kode_profil;
        document.getElementById('editNama').value = p.nama;
        document.getElementById('editTipe').value = p.tipe_alat;
        document.getElementById('editDeskripsi').value = p.deskripsi || '';

        document.getElementById('editBucketConf').value = p.bucket_confidence;
        document.getElementById('editBucketLow').value = p.bucket_low_ratio;
        document.getElementById('editTruckConf').value = p.truck_confidence;
        document.getElementById('editTruckHold').value = p.truck_hold_seconds;
        document.getElementById('editArmConf').value = p.arm_confidence;
        document.getElementById('editSwingThresh').value = p.arm_swing_threshold;
        document.getElementById('editPlateConf').value = p.plate_confidence;
        document.getElementById('editOcrCheck').checked = !!p.plate_ocr_enabled;
        document.getElementById('editMinWidth').value = p.truck_min_width_ratio;

        document.getElementById('editMotionThresh').value = p.motion_threshold;
        document.getElementById('editDigMin').value = p.dig_min_seconds;
        document.getElementById('editDumpMin').value = p.dump_min_seconds;
        document.getElementById('editIdleSec').value = p.idle_seconds;
        document.getElementById('editPhaseMin').value = p.phase_min_seconds;

        document.getElementById('editGaliX1').value = p.zona_gali_x1;
        document.getElementById('editGaliY1').value = p.zona_gali_y1;
        document.getElementById('editGaliX2').value = p.zona_gali_x2;
        document.getElementById('editGaliY2').value = p.zona_gali_y2;
        document.getElementById('editDumpTop').value = p.dump_top_ratio;
        document.getElementById('editDumpHeight').value = p.dump_height_ratio;

        new bootstrap.Modal(document.getElementById('editProfileModal')).show();
    }

    function confirmDeleteProfile(id, name) {
        document.getElementById('deleteProfileForm').action = '/master/pattern/' + id;
        document.getElementById('deleteProfileName').textContent = name;
        new bootstrap.Modal(document.getElementById('deleteProfileModal')).show();
    }
</script>
@endpush
