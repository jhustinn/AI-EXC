@extends('layouts.app')

@section('title', 'Rekap Produktivitas')
@section('breadcrumb', 'Monitoring / Rekap Produktivitas')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Analitik Produktivitas Siklus Pemuatan (Loading)</h1>
            <p class="text-secondary small mb-0">
                Laporan efisiensi waktu gali, waktu tuang, dan tonase batu bara &mdash; Unit <strong>{{ $unit }}</strong>.
            </p>
        </div>
        <div class="d-flex align-items-center gap-2">
            <a href="{{ route('monitoring.export-csv', ['unit' => $unit]) }}" class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-2">
                <i class="bi bi-file-earmark-excel"></i> Export CSV
            </a>
            <button class="btn btn-primary btn-sm" onclick="window.print()">
                <i class="bi bi-printer"></i> Cetak Ringkasan
            </button>
        </div>
    </div>

    <!-- 4 KPI SUMMARY CARDS -->
    <div class="row g-3 mb-4">
        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <span class="kpi-label">Rata-rata Durasi Mengeruk</span>
                <div class="kpi-value text-success">{{ $avgDig }} <small class="fs-6 text-secondary">detik</small></div>
                <div class="kpi-sub"><i class="bi bi-check-circle-fill text-success"></i> Standar industri: 10-14 detik</div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <span class="kpi-label">Rata-rata Durasi Menuangkan</span>
                <div class="kpi-value text-warning">{{ $avgDump }} <small class="fs-6 text-secondary">detik</small></div>
                <div class="kpi-sub"><i class="bi bi-check-circle-fill text-warning"></i> Standar industri: 7-11 detik</div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <span class="kpi-label">Rata-rata Waktu Siklus (Cycle Time)</span>
                <div class="kpi-value text-primary">{{ $avgTotal }} <small class="fs-6 text-secondary">detik</small></div>
                <div class="kpi-sub"><i class="bi bi-speedometer2 text-primary"></i> Termasuk swing kabin</div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <span class="kpi-label">Estimasi Total Tonase Dimuat</span>
                <div class="kpi-value text-dark">{{ $totalTon }} <small class="fs-6 text-secondary">Ton</small></div>
                <div class="kpi-sub"><i class="bi bi-database-fill text-dark"></i> {{ $cycles->count() }} bucket siklus</div>
            </div>
        </div>
    </div>

    <!-- CHARTS ROW -->
    <div class="row g-3 mb-4">
        <!-- LINE CHART -->
        <div class="col-12 col-xl-8">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-graph-up text-primary"></i> Tren Durasi Siklus (Mengeruk vs Menuang)</h2>
                </div>
                <div class="p-3">
                    <div style="height: 280px;">
                        <canvas id="prodChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- DOUGHNUT CHART -->
        <div class="col-12 col-xl-4">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-pie-chart text-primary"></i> Proporsi Waktu Operasional</h2>
                </div>
                <div class="p-3">
                    <div style="height: 280px;">
                        <canvas id="ratioChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- DETAIL CYCLES TABLE -->
    <div class="panel">
        <div class="panel-head">
            <h2 class="panel-title"><i class="bi bi-list-check text-primary"></i> Data Rinci Seluruh Siklus Operasi</h2>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead>
                    <tr>
                        <th>Siklus</th>
                        <th>Waktu Mulai</th>
                        <th>Waktu Selesai</th>
                        <th>Durasi Mengeruk</th>
                        <th>Durasi Menuangkan</th>
                        <th>Durasi Siklus Total</th>
                        <th>Estimasi Muatan</th>
                        <th>Dump Truck</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($cycles as $c)
                        <tr>
                            <td class="fw-bold">#{{ $c->siklus_ke }}</td>
                            <td>{{ $c->waktu_mulai?->format('H:i:s') }}</td>
                            <td>{{ $c->waktu_selesai?->format('H:i:s') ?? '-' }}</td>
                            <td class="text-success fw-semibold">{{ number_format($c->durasi_mengeruk, 1) }}s</td>
                            <td class="text-warning fw-semibold">{{ number_format($c->durasi_menuangkan, 1) }}s</td>
                            <td class="fw-bold text-dark">{{ number_format($c->durasi_total, 1) }}s</td>
                            <td>{{ number_format($c->payload_est_ton, 1) }} Ton</td>
                            <td><span class="badge text-bg-warning-subtle text-warning-emphasis">DT-01 (PT CEI)</span></td>
                            <td><span class="badge text-bg-success-subtle text-success border border-success-subtle">Completed</span></td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="9" class="text-center py-4 text-secondary">Belum ada siklus tercatat.</td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

@endsection

@push('scripts')
<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Line chart
        const ctxP = document.getElementById('prodChart').getContext('2d');
        new Chart(ctxP, {
            type: 'line',
            data: {
                labels: {!! json_encode($cycles->pluck('siklus_ke')->map(fn($n)=>'#'.$n)) !!},
                datasets: [
                    {
                        label: 'Durasi Mengeruk (s)',
                        data: {!! json_encode($cycles->pluck('durasi_mengeruk')) !!},
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Durasi Menuang (s)',
                        data: {!! json_encode($cycles->pluck('durasi_menuangkan')) !!},
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, title: { display: true, text: 'Detik' } } }
            }
        });

        // Ratio Doughnut
        const ctxR = document.getElementById('ratioChart').getContext('2d');
        new Chart(ctxR, {
            type: 'doughnut',
            data: {
                labels: ['Mengeruk', 'Menuangkan', 'Swing / Putar'],
                datasets: [{
                    data: [{{ $avgDig }}, {{ $avgDump }}, 4.0],
                    backgroundColor: ['#10b981', '#f59e0b', '#3b82f6'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    });
</script>
@endpush
