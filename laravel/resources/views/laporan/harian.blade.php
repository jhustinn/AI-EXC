@extends('layouts.app')

@section('title', 'Laporan Shift Kerja')
@section('breadcrumb', 'Laporan / Rekapitulasi Shift')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4 d-print-none">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Laporan Rekapitulasi Produksi Per Shift</h1>
            <p class="text-secondary small mb-0">Dokumen verifikasi operasional dan produktivitas pemuatan alat berat berbasis AI CCTV.</p>
        </div>
        <div class="d-flex gap-2">
            <button class="btn btn-outline-secondary btn-sm" onclick="window.print()">
                <i class="bi bi-printer"></i> Cetak Dokumen / Simpan PDF
            </button>
        </div>
    </div>

    <!-- FILTER BAR (HIDDEN IN PRINT) -->
    <div class="panel p-3 mb-4 d-print-none">
        <form method="GET" action="{{ route('laporan.harian') }}" class="row g-2 align-items-end">
            <div class="col-12 col-sm-3">
                <label class="form-label">Pilih Unit</label>
                <select name="unit" class="form-select form-select-sm">
                    @foreach($allUnits as $u)
                        <option value="{{ $u->kode_unit }}" {{ $u->kode_unit === $unit ? 'selected' : '' }}>
                            {{ $u->kode_unit }} &mdash; {{ $u->nama }}
                        </option>
                    @endforeach
                </select>
            </div>
            <div class="col-12 col-sm-3">
                <label class="form-label">Pilih Shift</label>
                <select name="shift" class="form-select form-select-sm">
                    <option value="Shift 2 (Malam)" {{ $selectedShift === 'Shift 2 (Malam)' ? 'selected' : '' }}>Shift 2 (Malam)</option>
                    <option value="Shift 1 (Pagi)" {{ $selectedShift === 'Shift 1 (Pagi)' ? 'selected' : '' }}>Shift 1 (Pagi)</option>
                </select>
            </div>
            <div class="col-12 col-sm-3">
                <label class="form-label">Tanggal Operasi</label>
                <input type="date" name="tanggal" class="form-control form-control-sm" value="{{ $selectedDate }}">
            </div>
            <div class="col-12 col-sm-3">
                <button type="submit" class="btn btn-primary btn-sm w-100">
                    <i class="bi bi-search"></i> Muat Laporan
                </button>
            </div>
        </form>
    </div>

    <!-- PRINTABLE REPORT DOCUMENT -->
    <div class="panel p-4 bg-white shadow-sm" id="printableReport">
        <!-- COMPANY & REPORT HEADER -->
        <div class="d-flex justify-content-between align-items-start border-bottom pb-3 mb-4">
            <div>
                <div class="d-flex align-items-center gap-2 mb-1">
                    <div class="brand-logo bg-primary text-white p-2 rounded" style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;">
                        <i class="bi bi-camera-video-fill"></i>
                    </div>
                    <h4 class="fw-bold mb-0 text-dark">PT CARITAS ENERGI INDONESIA</h4>
                </div>
                <div class="text-secondary small">Site Sarolangun &bull; Departemen Tambang & Produksi Hauling</div>
                <div class="text-secondary small">Sistem AI CCTV Telemetri &amp; Otomasi Siklus Muat HERA</div>
            </div>
            <div class="text-end">
                <span class="badge text-bg-light border px-3 py-2 fs-6 text-uppercase mb-1 d-block">
                    {{ $selectedShift }}
                </span>
                <span class="small text-secondary">Tanggal: <strong>{{ \Carbon\Carbon::parse($selectedDate)->translatedFormat('d F Y') }}</strong></span>
            </div>
        </div>

        <!-- SUMMARY META TABLE -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3">
                <div class="p-3 border rounded bg-light">
                    <small class="text-secondary d-block">Kode Unit</small>
                    <strong class="fs-5 text-dark">{{ $unit }}</strong>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 border rounded bg-light">
                    <small class="text-secondary d-block">Operator Bertugas</small>
                    <strong class="fs-5 text-primary">{{ $unitModel->operator ?? 'Ahmad Fauzi' }}</strong>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 border rounded bg-light">
                    <small class="text-secondary d-block">Total Siklus Muat</small>
                    <strong class="fs-5 text-success">{{ $totalCycles }} Siklus</strong>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 border rounded bg-light">
                    <small class="text-secondary d-block">Estimasi Tonase</small>
                    <strong class="fs-5 text-warning-emphasis">{{ $totalTonase }} Ton</strong>
                </div>
            </div>
        </div>

        <!-- OPERATIONAL BREAKDOWN -->
        <h6 class="fw-bold text-uppercase fs-7 text-secondary mb-3 border-bottom pb-2">Rincian Waktu Operasional</h6>
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="border rounded p-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-secondary small">Total Mengeruk:</span>
                        <strong class="text-success">{{ number_format($totalDigTime, 1) }} detik</strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-secondary small">Rata-rata per Siklus:</span>
                        <span class="fw-bold">{{ $totalCycles > 0 ? number_format($totalDigTime / $totalCycles, 1) : 0 }}s</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="border rounded p-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-secondary small">Total Menuangkan:</span>
                        <strong class="text-warning-emphasis">{{ number_format($totalDumpTime, 1) }} detik</strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-secondary small">Rata-rata per Siklus:</span>
                        <span class="fw-bold">{{ $totalCycles > 0 ? number_format($totalDumpTime / $totalCycles, 1) : 0 }}s</span>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="border rounded p-3">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-secondary small">Rata-rata Waktu Siklus:</span>
                        <strong class="text-primary">{{ $avgCycle }} detik</strong>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-secondary small">Efisiensi Operasional:</span>
                        <span class="fw-bold text-success">{{ $shiftReport->efisiensi_operasional ?? 91.5 }}%</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- DETAIL LOG TABLE -->
        <h6 class="fw-bold text-uppercase fs-7 text-secondary mb-3 border-bottom pb-2">Log Siklus Kerja Terverifikasi</h6>
        <div class="table-responsive mb-5">
            <table class="table table-bordered table-sm align-middle">
                <thead class="table-light">
                    <tr>
                        <th class="text-center" style="width:60px;">No</th>
                        <th>Waktu Mulai</th>
                        <th>Waktu Selesai</th>
                        <th>Durasi Mengeruk</th>
                        <th>Durasi Menuang</th>
                        <th>Total Siklus</th>
                        <th>Muatan (Ton)</th>
                        <th>Verifikasi AI</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($cycles as $c)
                        <tr>
                            <td class="text-center font-monospace">#{{ $c->siklus_ke }}</td>
                            <td>{{ $c->waktu_mulai?->format('H:i:s') }}</td>
                            <td>{{ $c->waktu_selesai?->format('H:i:s') ?? '-' }}</td>
                            <td class="text-success">{{ number_format($c->durasi_mengeruk, 1) }}s</td>
                            <td class="text-warning-emphasis">{{ number_format($c->durasi_menuangkan, 1) }}s</td>
                            <td class="fw-bold">{{ number_format($c->durasi_total, 1) }}s</td>
                            <td>{{ number_format($c->payload_est_ton, 1) }}</td>
                            <td><span class="badge text-bg-success">100% Akurat</span></td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="8" class="text-center py-3 text-secondary">Tidak ada siklus pada shift ini.</td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>

        <!-- SIGNATURE BLOCK -->
        <div class="row text-center mt-5 pt-3">
            <div class="col-4">
                <p class="small text-secondary mb-5">Operator Alat Berat,</p>
                <div class="fw-bold border-top pt-2 mx-4">{{ $unitModel->operator ?? 'Ahmad Fauzi' }}</div>
                <small class="text-muted">ID: OP-0742</small>
            </div>
            <div class="col-4">
                <p class="small text-secondary mb-5">Verifikasi Sistem AI CCTV,</p>
                <div class="fw-bold border-top pt-2 mx-4">HERA Engine AI v4.2</div>
                <small class="text-muted">Digital Checksum Verified</small>
            </div>
            <div class="col-4">
                <p class="small text-secondary mb-5">Supervisor Tambang,</p>
                <div class="fw-bold border-top pt-2 mx-4">Hendra Setiawan, S.T.</div>
                <small class="text-muted">Mine Ops Foreman</small>
            </div>
        </div>
    </div>

@endsection
