<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>@yield('title', 'Dashboard') &mdash; {{ config('app.name', 'HERA AI-CCTV') }}</title>

    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Bootstrap 5.3 & Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

    <!-- Chart.js 4.4 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ asset('css/app.css') }}?v=2.1">

    @stack('styles')
</head>
<body>

<div class="d-flex" id="appShell">

    <!-- SIDEBAR NAVIGATION -->
    <aside class="sidebar flex-shrink-0" id="sidebar">
        <div class="sidebar-brand d-flex align-items-center gap-3">
            <div class="brand-logo">
                <i class="bi bi-camera-video-fill fs-5"></i>
            </div>
            <div class="min-w-0">
                <div class="fw-bold fs-6 lh-1 text-white">HERA CCTV</div>
                <small class="text-secondary opacity-75" style="font-size:11px;">Heavy Equipment AI Telemetry</small>
            </div>
        </div>

        <nav class="sidebar-nav">
            <div class="nav-group">Overview</div>
            <a href="{{ route('dashboard') }}"
               class="nav-item {{ request()->routeIs('dashboard') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-grid-1x2-fill"></i>
                    <span>Dashboard Utama</span>
                </span>
            </a>

            <div class="nav-group">Monitoring & AI</div>
            <a href="{{ route('monitoring.live') }}"
               class="nav-item {{ request()->routeIs('monitoring.live') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-camera-video"></i>
                    <span>Live Monitoring</span>
                </span>
                <span class="badge text-bg-danger rounded-pill" style="font-size:10px;">LIVE</span>
            </a>

            <a href="{{ route('deteksi') }}"
               class="nav-item {{ request()->routeIs('deteksi') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-cpu"></i>
                    <span>Deteksi Aktivitas AI</span>
                </span>
            </a>

            <a href="{{ route('monitoring.produktivitas') }}"
               class="nav-item {{ request()->routeIs('monitoring.produktivitas') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-bar-chart-line-fill"></i>
                    <span>Rekap Produktivitas</span>
                </span>
            </a>

            <a href="{{ route('monitoring.riwayat') }}"
               class="nav-item {{ request()->routeIs('monitoring.riwayat') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-clock-history"></i>
                    <span>Riwayat & Event Log</span>
                </span>
            </a>

            <div class="nav-group">Master Data</div>
            <a href="{{ route('master.unit') }}"
               class="nav-item {{ request()->routeIs('master.unit*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-truck-front-fill"></i>
                    <span>Unit Alat Berat</span>
                </span>
            </a>

            <a href="{{ route('master.truck') }}"
               class="nav-item {{ request()->routeIs('master.truck*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-truck"></i>
                    <span>Dump Truck Hauling</span>
                </span>
            </a>

            <a href="{{ route('master.kamera') }}"
               class="nav-item {{ request()->routeIs('master.kamera*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-webcam-fill"></i>
                    <span>Kamera & Video</span>
                </span>
            </a>

            <a href="{{ route('master.pattern') }}"
               class="nav-item {{ request()->routeIs('master.pattern*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-diagram-3-fill"></i>
                    <span>Pola Deteksi &amp; Triggers</span>
                </span>
                <span class="badge text-bg-primary-subtle text-primary border border-primary-subtle" style="font-size:9.5px;">PRESET</span>
            </a>

            <a href="{{ route('master.user') }}"
               class="nav-item {{ request()->routeIs('master.user*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-people-fill"></i>
                    <span>Manajemen User</span>
                </span>
            </a>

            <div class="nav-group">Laporan & Audit</div>
            <a href="{{ route('laporan.harian') }}"
               class="nav-item {{ request()->routeIs('laporan.*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-file-earmark-spreadsheet-fill"></i>
                    <span>Laporan Shift Kerja</span>
                </span>
            </a>

            <div class="nav-group">Sistem</div>
            <a href="{{ route('pengaturan') }}"
               class="nav-item {{ request()->routeIs('pengaturan*') ? 'active' : '' }}">
                <span class="nav-link-content">
                    <i class="bi bi-sliders"></i>
                    <span>Pengaturan AI & Sistem</span>
                </span>
            </a>
        </nav>
    </aside>

    <!-- MAIN VIEWPORT -->
    <div class="main-wrap flex-grow-1 d-flex flex-column">

        <!-- TOPBAR -->
        <header class="topbar d-flex align-items-center justify-content-between px-4 py-2">
            <div class="d-flex align-items-center gap-3">
                <span class="text-secondary small d-flex align-items-center gap-2">
                    <i class="bi bi-geo-alt-fill text-danger"></i>
                    <strong>PT CEI &mdash; Pit Sarolangun</strong> &rsaquo; {{ $breadcrumb ?? 'Dashboard' }}
                </span>
            </div>

            <div class="d-flex align-items-center gap-3">
                <!-- Clock -->
                <div class="d-none d-md-flex align-items-center gap-2 px-2 py-1 rounded bg-light border small text-secondary">
                    <i class="bi bi-clock"></i>
                    <span id="topbarClock">--:--:-- WIB</span>
                </div>

                <!-- AI Status Heartbeat -->
                <span class="badge d-flex align-items-center gap-1 text-bg-success-subtle text-success-emphasis border border-success-subtle px-2 py-1" id="globalEngineBadge">
                    <span class="spinner-grow spinner-grow-sm text-success" role="status" style="width:7px;height:7px;"></span>
                    <span id="globalEngineText">AI Online</span>
                </span>

                <!-- Quick Unit Selector -->
                <div class="dropdown">
                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle d-flex align-items-center gap-2" type="button" data-bs-toggle="dropdown">
                        <i class="bi bi-crosshair2 text-primary"></i>
                        <span>Unit: <strong>{{ $unit ?? 'EXC-07' }}</strong></span>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="min-width: 250px;">
                        <li><h6 class="dropdown-header">Pilih Unit Ekskavator</h6></li>
                        @if(isset($globalUnits) && $globalUnits->count() > 0)
                            @foreach($globalUnits as $gu)
                                <li>
                                    <a class="dropdown-item d-flex align-items-center justify-content-between py-2" href="{{ request()->fullUrlWithQuery(['unit' => $gu->kode_unit]) }}">
                                        <div class="d-flex align-items-center gap-2">
                                            @if(($unit ?? 'EXC-07') === $gu->kode_unit)
                                                <i class="bi bi-check-circle-fill text-success"></i>
                                            @else
                                                <i class="bi bi-circle text-muted"></i>
                                            @endif
                                            <span><strong>{{ $gu->kode_unit }}</strong> <small class="text-secondary">({{ $gu->nama }})</small></span>
                                        </div>
                                        <span class="badge {{ $gu->status === 'operasi' ? 'text-bg-success' : 'text-bg-secondary' }}" style="font-size:9px;">
                                            {{ strtoupper($gu->status) }}
                                        </span>
                                    </a>
                                </li>
                            @endforeach
                        @else
                            <li><a class="dropdown-item" href="?unit=EXC-07"><i class="bi bi-check-circle-fill text-success me-1"></i> EXC-07 (Cat 395)</a></li>
                            <li><a class="dropdown-item" href="?unit=EXC-03">EXC-03 (Komatsu PC2000)</a></li>
                            <li><a class="dropdown-item" href="?unit=EXC-11">EXC-11 (Hitachi EX1200)</a></li>
                        @endif
                    </ul>
                </div>

                <!-- User Profile Dropdown -->
                <div class="dropdown">
                    <a class="nav-link dropdown-toggle text-secondary p-0 d-flex align-items-center gap-2" href="#" data-bs-toggle="dropdown">
                        <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center fw-bold border border-primary-subtle" style="width:34px;height:34px;font-size:12px;">
                            {{ Auth::user()?->initials() ?? 'US' }}
                        </div>
                        <div class="d-none d-sm-flex flex-column text-start" style="line-height: 1.2;">
                            <span class="small fw-bold text-dark">{{ Auth::user()?->name ?? 'Guest User' }}</span>
                            <span class="text-secondary" style="font-size: 10px;">{{ Auth::user()?->jabatan ?? 'Personel Operasional' }}</span>
                        </div>
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end shadow-sm" style="min-width: 240px;">
                        <li class="px-3 py-2">
                            <div class="fw-bold text-dark small">{{ Auth::user()?->name }}</div>
                            <div class="text-secondary small mb-1" style="font-size: 11px;">{{ Auth::user()?->email }}</div>
                            <div>{!! Auth::user()?->roleBadge() !!}</div>
                        </li>
                        <li><hr class="dropdown-divider my-1"></li>
                        <li>
                            <a class="dropdown-item py-2 small" href="{{ route('master.user') }}">
                                <i class="bi bi-people text-secondary me-2"></i> Manajemen Personel
                            </a>
                        </li>
                        <li>
                            <a class="dropdown-item py-2 small" href="{{ route('pengaturan') }}">
                                <i class="bi bi-gear text-secondary me-2"></i> Pengaturan Sistem
                            </a>
                        </li>
                        <li><hr class="dropdown-divider my-1"></li>
                        <li>
                            <form action="{{ route('logout') }}" method="POST" class="d-inline">
                                @csrf
                                <button type="submit" class="dropdown-item py-2 small text-danger d-flex align-items-center w-100 border-0 bg-transparent">
                                    <i class="bi bi-box-arrow-right me-2"></i> Keluar (Logout)
                                </button>
                            </form>
                        </li>
                    </ul>
                </div>
            </div>
        </header>

        <!-- FLASH NOTIFICATIONS -->
        @if(session('success'))
            <div class="alert alert-success alert-dismissible fade show m-3 mb-0 py-2 small d-flex align-items-center gap-2" role="alert">
                <i class="bi bi-check-circle-fill fs-6"></i>
                <div>{{ session('success') }}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        @if(session('error'))
            <div class="alert alert-danger alert-dismissible fade show m-3 mb-0 py-2 small d-flex align-items-center gap-2" role="alert">
                <i class="bi bi-exclamation-triangle-fill fs-6"></i>
                <div>{{ session('error') }}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        @endif

        <!-- MAIN BODY -->
        <main class="content flex-grow-1">
            @yield('content')
        </main>

        <!-- FOOTER -->
        <footer class="px-4 py-3 text-secondary small border-top bg-white d-flex flex-wrap justify-content-between align-items-center">
            <div>
                <strong>HERA CCTV & Telemetry</strong> &middot; Heavy Equipment Realtime Activity &copy; {{ date('Y') }} PT Caritas Energi Indonesia.
            </div>
            <div class="d-flex gap-3">
                <span>Versi Engine: <strong>YOLO11-Custom v4.2</strong></span>
                <span>Database: <strong>PostgreSQL 17</strong></span>
            </div>
        </footer>
    </div>
</div>

<!-- Bootstrap Bundle -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

<script>
    // Live Topbar Clock (WIB)
    function updateClock() {
        const now = new Date();
        const str = now.toLocaleTimeString('id-ID', { hour12: false }) + ' WIB';
        const el = document.getElementById('topbarClock');
        if (el) el.textContent = str;
    }
    setInterval(updateClock, 1000);
    updateClock();
</script>

@stack('scripts')
</body>
</html>
