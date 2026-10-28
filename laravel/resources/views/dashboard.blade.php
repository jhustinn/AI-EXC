@extends('layouts.app')

@section('title', 'Dashboard Operasional')
@section('breadcrumb', 'Dashboard')

@section('content')

    <!-- TOP HEADER & STATUS BAR -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Fleet Loading & Digging Telemetry</h1>
            <p class="text-secondary small mb-0">
                Monitoring real-time deteksi aktivitas alat berat berbasis Computer Vision AI &mdash; Unit <strong>{{ $unit }}</strong> ({{ $unitModel->nama ?? 'Cat 395' }}).
            </p>
        </div>
        <div class="d-flex align-items-center gap-2">
            <!-- Audio Chime Toggle -->
            <button type="button" class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-2 shadow-sm" id="btnAudioToggle" onclick="toggleAudioAlert()">
                <i class="bi bi-volume-up-fill text-primary" id="audioIcon"></i>
                <span id="audioLabel" class="d-none d-sm-inline">Audio: ON</span>
            </button>

            <span class="badge bg-white text-secondary border px-3 py-2 d-flex align-items-center gap-2 shadow-sm">
                <i class="bi bi-person-badge text-primary"></i>
                <span>Operator: <strong>{{ $unitModel->operator ?? 'Ahmad Fauzi' }}</strong></span>
            </span>
            <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" onclick="fetchLiveTelemetry()">
                <i class="bi bi-arrow-repeat" id="refreshIcon"></i> Sync Data
            </button>
        </div>
    </div>

    <!-- 4 UTAMA KPI CARDS -->
    <div class="row g-3 mb-4">
        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="kpi-label">Durasi Mengeruk</span>
                    <div class="kpi-icon bg-dig-soft">
                        <i class="bi bi-arrow-down-circle"></i>
                    </div>
                </div>
                <div class="kpi-value" id="kpiMengeruk">00:00:00</div>
                <div class="kpi-sub">
                    <span class="text-success fw-semibold"><i class="bi bi-activity"></i> Aktif</span>
                    <span>&bull; Pengisian bucket pit</span>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="kpi-label">Durasi Menuangkan</span>
                    <div class="kpi-icon bg-dump-soft">
                        <i class="bi bi-truck"></i>
                    </div>
                </div>
                <div class="kpi-value" id="kpiMenuangkan">00:00:00</div>
                <div class="kpi-sub">
                    <span class="text-warning fw-semibold"><i class="bi bi-box-arrow-in-down"></i> Hauler</span>
                    <span>&bull; Dumping ke bak truck</span>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="kpi-label">Total Siklus Selesai</span>
                    <div class="kpi-icon bg-cycle-soft">
                        <i class="bi bi-arrow-repeat"></i>
                    </div>
                </div>
                <div class="kpi-value" id="kpiSiklus">0 Siklus</div>
                <div class="kpi-sub">
                    <span class="text-primary fw-semibold" id="estTonnage"><i class="bi bi-database"></i> {{ $totalTonnage }} Ton</span>
                    <span>&bull; Rata-rata 24.3s/siklus</span>
                </div>
            </div>
        </div>

        <div class="col-12 col-sm-6 col-xl-3">
            <div class="kpi-card">
                <div class="d-flex align-items-center justify-content-between mb-2">
                    <span class="kpi-label">Waktu Standby / Idle</span>
                    <div class="kpi-icon bg-idle-soft">
                        <i class="bi bi-stopwatch"></i>
                    </div>
                </div>
                <div class="kpi-value" id="kpiIdle">00:00:00</div>
                <div class="kpi-sub">
                    <span class="text-secondary fw-semibold">Efisiensi: <strong class="text-success">92.4%</strong></span>
                </div>
            </div>
        </div>
    </div>

    <!-- MAIN INTERACTIVE MONITORING ROW: LIVE STREAM + ACTIVE RADAR -->
    <div class="row g-3 mb-4">
        <!-- LIVE STREAM THEATER -->
        <div class="col-12 col-xl-7">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        <i class="bi bi-camera-reels text-primary"></i>
                        <span>Live AI Visual Telemetry &mdash; {{ $unit }}</span>
                    </h2>
                    <div class="d-flex align-items-center gap-2">
                        <!-- Quick Camera Switcher -->
                        <div class="dropdown">
                            <button class="btn btn-xs btn-outline-secondary dropdown-toggle d-flex align-items-center gap-1 py-1" type="button" data-bs-toggle="dropdown" style="font-size: 11px;">
                                <i class="bi bi-camera-video text-primary"></i>
                                <span id="activeCamLabel">Kamera: Dashcam Boom</span>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="font-size: 12px;">
                                <li><h6 class="dropdown-header">Pilih Sumber Kamera</h6></li>
                                @foreach($cameras as $c)
                                    <li>
                                        <a class="dropdown-item d-flex align-items-center justify-content-between gap-2" href="#" onclick="switchDashboardCam('{{ $c->id }}', '{{ $c->nama }}', '{{ $c->is_primary }}', '{{ $c->source_path }}')">
                                            <span>{{ $c->nama }}</span>
                                            @if($c->is_primary)
                                                <span class="badge text-bg-danger" style="font-size:9px;">AI LIVE</span>
                                            @else
                                                <span class="badge text-bg-secondary" style="font-size:9px;">FEED</span>
                                            @endif
                                        </a>
                                    </li>
                                @endforeach
                            </ul>
                        </div>

                        <span class="badge text-bg-success-subtle text-success-emphasis border border-success-subtle px-2 py-1" id="streamFpsBadge">
                            <i class="bi bi-broadcast"></i> 18 FPS
                        </span>
                    </div>
                </div>
                <div class="p-3">
                    <div class="live-stream-box" id="streamContainer">
                        <img id="liveVideoFeed"
                             src="{{ $streamUrl }}/stream"
                             alt="Live Feed {{ $unit }}">

                        <div class="live-badge-rec">
                            <i class="bi bi-record-fill"></i>
                            <span>LIVE STREAM &bull; AI CCTV</span>
                        </div>

                        <div class="live-controls-overlay">
                            <button class="live-btn-icon" title="Ambil Foto Snapshot" onclick="captureSnapshot()">
                                <i class="bi bi-camera-fill"></i>
                            </button>
                            <button class="live-btn-icon" title="Layar Penuh" onclick="toggleFullScreen()">
                                <i class="bi bi-fullscreen"></i>
                            </button>
                        </div>

                        <!-- Offline Overlay Fallback -->
                        <div id="streamOfflineHint" class="position-absolute p-4 text-center text-white" style="display:none;background:rgba(5,8,17,0.92);border-radius:10px;">
                            <i class="bi bi-exclamation-triangle-fill text-warning fs-1 d-block mb-2"></i>
                            <h5 class="fw-bold mb-1">Stream Sedang Menghubungkan</h5>
                            <p class="small text-secondary mb-3">
                                Engine deteksi Python (Port 8010) sedang menyalakan feed kamera.
                            </p>
                            <button class="btn btn-outline-light btn-sm" onclick="reconnectStream()">
                                <i class="bi bi-arrow-clockwise"></i> Coba Sambung Ulang
                            </button>
                        </div>
                    </div>

                    <div class="d-flex flex-wrap align-items-center justify-content-between mt-3 text-secondary small">
                        <div class="d-flex gap-3">
                            <span><i class="bi bi-camera text-primary"></i> Kamera: <strong>Dashcam Cabin (Boom POV)</strong></span>
                            <span><i class="bi bi-aspect-ratio"></i> Rasio: <strong>476x848 (Vertikal)</strong></span>
                        </div>
                        <div>
                            <span class="text-success"><i class="bi bi-shield-check"></i> Model Aktif: <strong>YOLO11 Mining Engine</strong></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ACTIVE ACTIVITY RADAR & DIAGNOSTICS -->
        <div class="col-12 col-xl-5">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        <i class="bi bi-speedometer2 text-primary"></i>
                        <span>Status Operasi Real-Time</span>
                    </h2>
                    <span id="activePhasePill" class="phase-pulse-badge text-bg-success">
                        <span class="phase-pulse-dot bg-white"></span>
                        <span id="activePhaseText">Mengeruk</span>
                    </span>
                </div>
                <div class="p-3">
                    <!-- Large Phase Display -->
                    <div class="text-center p-3 rounded bg-light border mb-3">
                        <span class="text-secondary small text-uppercase fw-bold letter-spacing-1">Fase Kerja Berjalan</span>
                        <h2 class="display-6 fw-bold mb-0 text-dark" id="displayPhaseLabel">Mengeruk</h2>
                        <div class="text-secondary small mt-1">
                            Durasi berjalan: <strong class="text-primary fs-6" id="displayPhaseDuration">00:00</strong> &bull; Sinyal: <span id="displaySignalSource">bucket</span>
                        </div>
                    </div>

                    <!-- AI Confidence Radar Bars -->
                    <h6 class="fw-bold fs-7 text-uppercase text-secondary mb-3">Tingkat Keyakinan Deteksi AI</h6>

                    <div class="mb-3">
                        <div class="d-flex justify-content-between small fw-semibold mb-1">
                            <span><i class="bi bi-truck text-warning"></i> Dump Truck (Bak Oranye)</span>
                            <span id="truckConfVal" class="text-warning">95%</span>
                        </div>
                        <div class="progress" style="height: 7px;">
                            <div class="progress-bar bg-warning" id="truckConfBar" role="progressbar" style="width: 95%;"></div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <div class="d-flex justify-content-between small fw-semibold mb-1">
                            <span><i class="bi bi-box text-success"></i> Bucket & Gigi Pengeruk</span>
                            <span id="bucketConfVal" class="text-success">70%</span>
                        </div>
                        <div class="progress" style="height: 7px;">
                            <div class="progress-bar bg-success" id="bucketConfBar" role="progressbar" style="width: 70%;"></div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <div class="d-flex justify-content-between small fw-semibold mb-1">
                            <span><i class="bi bi-truck-front text-primary"></i> Anatomi Lengan & Badan Excavator</span>
                            <span id="excConfVal" class="text-primary">85%</span>
                        </div>
                        <div class="progress" style="height: 7px;">
                            <div class="progress-bar bg-primary" id="excConfBar" role="progressbar" style="width: 85%;"></div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <div class="d-flex justify-content-between small fw-semibold mb-1">
                            <span><i class="bi bi-activity text-info"></i> Energi Gerak Zona Gali (Optical Flow)</span>
                            <span id="motionConfVal" class="text-info">0.124</span>
                        </div>
                        <div class="progress" style="height: 7px;">
                            <div class="progress-bar bg-info" id="motionConfBar" role="progressbar" style="width: 45%;"></div>
                        </div>
                    </div>

                    <!-- Active Zone Indicator -->
                    <div class="border rounded p-2 bg-body-tertiary small d-flex justify-content-between align-items-center mt-3">
                        <div>
                            <span class="text-secondary">Zona Tuang:</span>
                            <strong id="zoneTuangStatus" class="text-success ms-1">Aktif di Bak Truk</strong>
                        </div>
                        <div>
                            <span class="text-secondary">Zona Gali:</span>
                            <strong id="zoneGaliStatus" class="text-primary ms-1">Pit Dasar</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- CYCLE STEP TRACE VISUALIZER -->
    <div class="panel mb-4">
        <div class="panel-head">
            <h2 class="panel-title">
                <i class="bi bi-bezier2 text-primary"></i>
                <span>Visualisasi Urutan Siklus (Working Cycle Steps)</span>
            </h2>
            <span class="small text-secondary">Transisi otomatis berbasis Finite State Machine AI</span>
        </div>
        <div class="p-3">
            <div class="cycle-trace">
                <div class="cycle-step" id="step-mengangkat" data-fase="mengangkat">
                    <div class="step-icon"><i class="bi bi-arrow-up-circle-fill"></i></div>
                    <div class="step-title">1. Mengangkat</div>
                    <div class="step-sub" id="time-mengangkat">-</div>
                </div>
                <i class="bi bi-chevron-right text-secondary opacity-50"></i>

                <div class="cycle-step" id="step-mengeruk" data-fase="mengeruk">
                    <div class="step-icon"><i class="bi bi-shovel-fill text-success"></i></div>
                    <div class="step-title">2. Mengeruk</div>
                    <div class="step-sub" id="time-mengeruk">Aktif</div>
                </div>
                <i class="bi bi-chevron-right text-secondary opacity-50"></i>

                <div class="cycle-step" id="step-memutar" data-fase="memutar">
                    <div class="step-icon"><i class="bi bi-arrow-repeat text-indigo"></i></div>
                    <div class="step-title">3. Memutar (Swing)</div>
                    <div class="step-sub" id="time-memutar">-</div>
                </div>
                <i class="bi bi-chevron-right text-secondary opacity-50"></i>

                <div class="cycle-step" id="step-menuangkan" data-fase="menuangkan">
                    <div class="step-icon"><i class="bi bi-box-arrow-in-down text-warning"></i></div>
                    <div class="step-title">4. Menuangkan</div>
                    <div class="step-sub" id="time-menuangkan">-</div>
                </div>
                <i class="bi bi-chevron-right text-secondary opacity-50"></i>

                <div class="cycle-step" id="step-kembali" data-fase="kembali">
                    <div class="step-icon"><i class="bi bi-arrow-counterclockwise text-primary"></i></div>
                    <div class="step-title">5. Kembali ke Pit</div>
                    <div class="step-sub" id="time-kembali">-</div>
                </div>
            </div>
        </div>
    </div>

    <!-- RECENT CYCLES TABLE & HOURLY CHART -->
    <div class="row g-3">
        <!-- CHART -->
        <div class="col-12 col-xl-6">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        <i class="bi bi-graph-up-arrow text-primary"></i>
                        <span>Grafik Durasi Siklus (Detik)</span>
                    </h2>
                    <span class="badge bg-light text-dark border">10 Siklus Terakhir</span>
                </div>
                <div class="p-3">
                    <div style="height: 260px;">
                        <canvas id="cycleChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- TABLE -->
        <div class="col-12 col-xl-6">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        <i class="bi bi-table text-primary"></i>
                        <span>Daftar Siklus Terakhir (Tercatat Database)</span>
                    </h2>
                    <a href="{{ route('monitoring.riwayat') }}" class="btn btn-outline-secondary btn-sm">
                        Lihat Semua <i class="bi bi-arrow-right"></i>
                    </a>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead>
                            <tr>
                                <th>Siklus</th>
                                <th>Mulai</th>
                                <th>Mengeruk</th>
                                <th>Menuang</th>
                                <th>Total</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="recentCyclesTableBody">
                            @forelse($recentCycles as $c)
                                <tr>
                                    <td class="fw-bold">#{{ $c->siklus_ke }}</td>
                                    <td>{{ $c->waktu_mulai?->format('H:i:s') }}</td>
                                    <td class="text-success fw-semibold">{{ number_format($c->durasi_mengeruk, 1) }}s</td>
                                    <td class="text-warning fw-semibold">{{ number_format($c->durasi_menuangkan, 1) }}s</td>
                                    <td class="fw-bold">{{ number_format($c->durasi_total, 1) }}s</td>
                                    <td><span class="badge text-bg-success-subtle text-success border border-success-subtle">Selesai</span></td>
                                </tr>
                            @empty
                                <tr>
                                    <td colspan="6" class="text-center py-4 text-secondary">
                                        Belum ada siklus tercatat.
                                    </td>
                                </tr>
                            @endforelse
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

@endsection

@push('scripts')
<script>
    const API_LIVE_URL = @json(route('api.telemetry.live', ['unit' => $unit]));
    let cycleChartInstance = null;

    // Inisialisasi Chart.js
    function initCycleChart() {
        const ctx = document.getElementById('cycleChart').getContext('2d');
        const labels = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10'];
        const digData = [9.6, 5.9, 12.6, 14.4, 11.9, 13.5, 14.0, 13.1, 10.5, 11.2];
        const dumpData = [6.3, 9.0, 11.0, 10.2, 12.4, 10.0, 4.2, 6.0, 9.5, 8.8];

        cycleChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Durasi Mengeruk (s)',
                        data: digData,
                        backgroundColor: '#10b981',
                        borderRadius: 4,
                    },
                    {
                        label: 'Durasi Menuang (s)',
                        data: dumpData,
                        backgroundColor: '#f59e0b',
                        borderRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, title: { display: true, text: 'Detik', font: { size: 11 } } }
                }
            }
        });
    }

    // Helper formatting durasi
    function formatDurasi(sec) {
        sec = Math.max(0, Math.floor(sec || 0));
        const j = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        const s = sec % 60;
        return [j, m, s].map(n => String(n).padStart(2, '0')).join(':');
    }

    // Polling Realtime Engine Telemetry (< 15ms)
    function fetchLiveTelemetry() {
        const icon = document.getElementById('refreshIcon');
        if (icon) icon.classList.add('spin-animation');

        fetch(API_LIVE_URL)
            .then(res => res.json())
            .then(data => {
                if (icon) icon.classList.remove('spin-animation');

                // Update Status Engine
                const badge = document.getElementById('globalEngineBadge');
                const badgeText = document.getElementById('globalEngineText');
                if (data.online) {
                    badge.className = 'badge d-flex align-items-center gap-1 text-bg-success-subtle text-success-emphasis border border-success-subtle px-2 py-1';
                    badgeText.textContent = 'AI Online';
                } else {
                    badge.className = 'badge d-flex align-items-center gap-1 text-bg-secondary px-2 py-1';
                    badgeText.textContent = 'Engine Offline';
                }

                if (!data.status || !data.status.kpi) return;
                const st = data.status;

                // KPI values
                document.getElementById('kpiMengeruk').textContent = formatDurasi(st.kpi.durasi_mengeruk);
                document.getElementById('kpiMenuangkan').textContent = formatDurasi(st.kpi.durasi_menuangkan);
                document.getElementById('kpiIdle').textContent = formatDurasi(st.kpi.waktu_idle);
                document.getElementById('kpiSiklus').textContent = (st.kpi.jumlah_siklus || 0) + ' Siklus';

                // Display Active Phase
                const phaseLabel = st.fase_label || 'Standby';
                document.getElementById('displayPhaseLabel').textContent = phaseLabel;
                document.getElementById('displayPhaseDuration').textContent = formatDurasi(st.durasi_fase_detik);
                document.getElementById('displaySignalSource').textContent = st.sumber_sinyal || 'camera';

                // Radar confidence values
                const tc = Math.round((st.truck_confidence || 0) * 100);
                document.getElementById('truckConfVal').textContent = tc > 0 ? tc + '%' : 'Tidak terdeteksi';
                document.getElementById('truckConfBar').style.width = tc + '%';

                const bc = Math.round((st.bucket_confidence || 0) * 100);
                document.getElementById('bucketConfVal').textContent = bc > 0 ? bc + '%' : 'Menghitung geometri';
                document.getElementById('bucketConfBar').style.width = bc + '%';

                const ec = Math.round((st.excavator_confidence || 0) * 100);
                document.getElementById('excConfVal').textContent = ec > 0 ? ec + '%' : 'Kabine POV';
                document.getElementById('excConfBar').style.width = ec + '%';

                const motion = Math.min(1.0, (st.zona_gali_motion || 0));
                document.getElementById('motionConfVal').textContent = (st.zona_gali_motion || 0).toFixed(4);
                document.getElementById('motionConfBar').style.width = Math.round(motion * 100) + '%';

                // Phase Badge Color
                const phasePill = document.getElementById('activePhasePill');
                const phaseText = document.getElementById('activePhaseText');
                phaseText.textContent = phaseLabel;

                const f = (st.fase || '').toLowerCase();
                if (f === 'mengeruk') {
                    phasePill.className = 'phase-pulse-badge text-bg-success';
                } else if (f === 'menuangkan') {
                    phasePill.className = 'phase-pulse-badge text-bg-warning';
                } else if (f === 'memutar' || f === 'kembali') {
                    phasePill.className = 'phase-pulse-badge text-bg-primary';
                } else {
                    phasePill.className = 'phase-pulse-badge text-bg-secondary';
                }

                // Audio Chime on Phase Change or Cycle Complete
                if (prevFase && prevFase !== f && f === 'menuangkan') {
                    playChime('dump');
                }
                const curCycles = (st.kpi && st.kpi.jumlah_siklus) ? st.kpi.jumlah_siklus : 0;
                if (prevCycleCount > 0 && curCycles > prevCycleCount) {
                    playChime('cycle');
                }
                prevFase = f;
                prevCycleCount = curCycles;

                // Update Cycle Trace Steps
                updateCycleTrace(f);
            })
            .catch(err => {
                if (icon) icon.classList.remove('spin-animation');
            });
    }

    function updateCycleTrace(fase) {
        document.querySelectorAll('.cycle-step').forEach(step => {
            const stepFase = step.dataset.fase;
            const sub = step.querySelector('.step-sub');
            if (stepFase === fase) {
                step.classList.add('active');
                if (sub) sub.textContent = 'Aktif';
            } else {
                step.classList.remove('active');
                if (sub) sub.textContent = '-';
            }
        });
    }

    // Stream state handlers
    function onStreamSuccess() {
        document.getElementById('streamOfflineHint').style.display = 'none';
    }

    function onStreamFail() {
        document.getElementById('streamOfflineHint').style.display = 'block';
    }

    function reconnectStream() {
        const img = document.getElementById('liveVideoFeed');
        img.src = @json($streamUrl) + '/stream?t=' + new Date().getTime();
    }

    function toggleFullScreen() {
        const box = document.getElementById('streamContainer');
        if (!document.fullscreenElement) {
            box.requestFullscreen().catch(err => {});
        } else {
            document.exitFullscreen();
        }
    }

    function captureSnapshot() {
        const img = document.getElementById('liveVideoFeed');
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || 476;
        canvas.height = img.naturalHeight || 848;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const a = document.createElement('a');
        a.download = 'snapshot_{{ $unit }}_' + new Date().getTime() + '.jpg';
        a.href = canvas.toDataURL('image/jpeg');
        a.click();
    }

    let prevFase = null;
    let prevCycleCount = 0;
    let audioCtx = null;
    let audioEnabled = localStorage.getItem('hera_audio') !== 'false';

    function initAudioUI() {
        const icon = document.getElementById('audioIcon');
        const label = document.getElementById('audioLabel');
        if (audioEnabled) {
            icon.className = 'bi bi-volume-up-fill text-primary';
            label.textContent = 'Audio: ON';
        } else {
            icon.className = 'bi bi-volume-mute-fill text-secondary';
            label.textContent = 'Audio: OFF';
        }
    }

    function toggleAudioAlert() {
        audioEnabled = !audioEnabled;
        localStorage.setItem('hera_audio', audioEnabled ? 'true' : 'false');
        initAudioUI();
        if (audioEnabled) {
            playChime('test');
        }
    }

    function getAudioContext() {
        if (!audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AudioContext();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        return audioCtx;
    }

    function playTone(ctx, freq, startTime, duration, vol = 0.12) {
        try {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(vol, startTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(startTime);
            osc.stop(startTime + duration);
        } catch (e) {}
    }

    function playChime(type) {
        if (!audioEnabled) return;
        try {
            const ctx = getAudioContext();
            const now = ctx.currentTime;
            if (type === 'dump') {
                // Harmonic dual-tone saat mulai loading dump truck
                playTone(ctx, 523.25, now, 0.12, 0.15);
                playTone(ctx, 659.25, now + 0.13, 0.16, 0.15);
            } else if (type === 'cycle') {
                // Triumphant 3-tone chime saat 1 siklus selesai (+1 cycle)
                playTone(ctx, 523.25, now, 0.10, 0.12);
                playTone(ctx, 659.25, now + 0.11, 0.10, 0.12);
                playTone(ctx, 783.99, now + 0.22, 0.22, 0.15);
            } else if (type === 'test') {
                playTone(ctx, 660, now, 0.15, 0.10);
            }
        } catch (e) {}
    }

    function switchDashboardCam(id, name, isPrimary, sourcePath) {
        document.getElementById('activeCamLabel').textContent = 'Kamera: ' + name;
        const img = document.getElementById('liveVideoFeed');
        if (isPrimary === '1' || isPrimary === 'true' || isPrimary === true) {
            img.src = @json($streamUrl) + '/stream?t=' + new Date().getTime();
        } else if (sourcePath.startsWith('http://') || sourcePath.startsWith('https://')) {
            img.src = sourcePath + '?t=' + new Date().getTime();
        } else {
            img.src = @json($streamUrl) + '/stream?t=' + new Date().getTime();
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const feedImg = document.getElementById('liveVideoFeed');
        if (feedImg) {
            feedImg.addEventListener('load', onStreamSuccess);
            feedImg.addEventListener('error', onStreamFail);
            if (feedImg.complete && feedImg.naturalWidth > 0) {
                onStreamSuccess();
            }
        }
        initAudioUI();
        initCycleChart();
        fetchLiveTelemetry();
        setInterval(fetchLiveTelemetry, 1500);
    });
</script>
<style>
    .spin-animation {
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
@endpush
