@extends('layouts.app')

@section('title', 'Riwayat Deteksi & Siklus')
@section('breadcrumb', 'Monitoring / Riwayat Event Log')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Log Riwayat Aktivitas & Event Telemetri</h1>
            <p class="text-secondary small mb-0">
                Data historis seluruh transisi fase deteksi AI yang tersimpan di PostgreSQL &mdash; Unit <strong>{{ $unit }}</strong>.
            </p>
        </div>
        <div class="d-flex gap-2">
            <a href="{{ route('monitoring.export-csv', ['unit' => $unit]) }}" class="btn btn-outline-success btn-sm d-flex align-items-center gap-2 shadow-sm">
                <i class="bi bi-file-earmark-spreadsheet-fill"></i> Download CSV
            </a>
        </div>
    </div>

    <!-- FILTER BAR -->
    <div class="panel p-3 mb-4">
        <form method="GET" action="{{ route('monitoring.riwayat') }}" class="row g-2 align-items-end">
            <div class="col-12 col-sm-3">
                <label class="form-label">Pilih Unit Ekskavator</label>
                <select name="unit" class="form-select form-select-sm">
                    @foreach($allUnits as $u)
                        <option value="{{ $u->kode_unit }}" {{ $u->kode_unit === $unit ? 'selected' : '' }}>
                            {{ $u->kode_unit }} &mdash; {{ $u->nama }}
                        </option>
                    @endforeach
                </select>
            </div>

            <div class="col-12 col-sm-3">
                <label class="form-label">Filter Fase</label>
                <select name="fase" class="form-select form-select-sm">
                    <option value="all">Semua Fase</option>
                    <option value="mengeruk" {{ $faseFilter === 'mengeruk' ? 'selected' : '' }}>Mengeruk</option>
                    <option value="menuangkan" {{ $faseFilter === 'menuangkan' ? 'selected' : '' }}>Menuangkan</option>
                    <option value="memutar" {{ $faseFilter === 'memutar' ? 'selected' : '' }}>Memutar</option>
                    <option value="idle" {{ $faseFilter === 'idle' ? 'selected' : '' }}>Idle</option>
                </select>
            </div>

            <div class="col-12 col-sm-3">
                <label class="form-label">Tanggal Operasi</label>
                <input type="date" name="tanggal" class="form-control form-control-sm" value="{{ $dateFilter }}">
            </div>

            <div class="col-12 col-sm-3 d-flex gap-2">
                <button type="submit" class="btn btn-primary btn-sm flex-grow-1">
                    <i class="bi bi-funnel-fill"></i> Terapkan Filter
                </button>
                <a href="{{ route('monitoring.riwayat') }}" class="btn btn-outline-secondary btn-sm">Reset</a>
            </div>
        </form>
    </div>

    <!-- LOG TABLE -->
    <div class="panel">
        <div class="panel-head">
            <h2 class="panel-title"><i class="bi bi-journal-text text-primary"></i> Catatan Event Aktivitas</h2>
            <span class="small text-secondary">Menampilkan {{ $logs->total() }} entri event</span>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead>
                    <tr>
                        <th>No</th>
                        <th>Waktu Mulai</th>
                        <th>Waktu Selesai</th>
                        <th>Durasi</th>
                        <th>Fase Deteksi</th>
                        <th>Siklus</th>
                        <th>Dump Truck</th>
                        <th>Bucket</th>
                        <th>Motion</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($logs as $index => $log)
                        <tr>
                            <td>{{ $logs->firstItem() + $index }}</td>
                            <td>{{ $log->mulai?->format('H:i:s') }}</td>
                            <td>{{ $log->selesai?->format('H:i:s') ?? '-' }}</td>
                            <td class="fw-bold">{{ number_format($log->durasi_detik, 1) }}s</td>
                            <td>
                                @if($log->fase === 'mengeruk')
                                    <span class="badge text-bg-success-subtle text-success border border-success-subtle">Mengeruk</span>
                                @elseif($log->fase === 'menuangkan')
                                    <span class="badge text-bg-warning-subtle text-warning-emphasis border border-warning-subtle">Menuangkan</span>
                                @elseif($log->fase === 'memutar')
                                    <span class="badge text-bg-primary-subtle text-primary border border-primary-subtle">Memutar</span>
                                @else
                                    <span class="badge text-bg-secondary-subtle text-secondary border">Idle</span>
                                @endif
                            </td>
                            <td><strong>#{{ $log->siklus_ke }}</strong></td>
                            <td>{{ round($log->truck_confidence * 100) }}%</td>
                            <td>{{ round($log->bucket_confidence * 100) }}%</td>
                            <td class="text-secondary small">{{ $log->motion_score }}</td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="9" class="text-center py-5 text-secondary">
                                <i class="bi bi-inbox fs-2 d-block mb-2"></i>
                                Tidak ada log aktivitas yang sesuai dengan filter.
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
        @if($logs->hasPages())
            <div class="p-3 border-top d-flex justify-content-end">
                {{ $logs->links() }}
            </div>
        @endif
    </div>

@endsection
