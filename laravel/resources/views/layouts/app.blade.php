<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>@yield('title', 'Dashboard') — {{ config('app.name') }}</title>

    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="stylesheet" href="{{ asset('css/app.css') }}">

    @stack('styles')
</head>
<body class="bg-body-tertiary">

<div class="d-flex" id="appShell">

    <aside class="sidebar flex-shrink-0" id="sidebar">
        <div class="sidebar-brand d-flex align-items-center gap-2">
            <i class="bi bi-camera-video-fill fs-4"></i>
            <div>
                <div class="fw-bold lh-1">HERA</div>
                <small class="d-block opacity-75">Heavy Equipment<br>Management System</small>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ route('dashboard') }}"
               class="nav-item {{ request()->routeIs('dashboard') ? 'active' : '' }}">
                <i class="bi bi-speedometer2"></i> Dashboard
            </a>

            <div class="nav-group">Unit</div>

            <div class="nav-group">Monitoring</div>
            <a href="#" class="nav-item"><i class="bi bi-camera-video"></i> Live Monitoring</a>
            <a href="{{ route('deteksi') }}"
               class="nav-item {{ request()->routeIs('deteksi*') ? 'active' : '' }}">
                <i class="bi bi-activity"></i> Deteksi Aktivitas AI
            </a>
            <a href="#" class="nav-item"><i class="bi bi-bar-chart-line"></i> Rekap Produktivitas</a>
            <a href="#" class="nav-item"><i class="bi bi-film"></i> Riwayat Video</a>

            <div class="nav-group">Operational</div>
            <div class="nav-group">Maintenance</div>
            <div class="nav-group">Laporan</div>
            <div class="nav-group">Master</div>
            <div class="nav-group">Pengaturan</div>
        </nav>
    </aside>

    <div class="main-wrap flex-grow-1 d-flex flex-column">

        <header class="topbar d-flex align-items-center justify-content-between px-4 py-2">
            <div class="d-flex align-items-center gap-3">
                <i class="bi bi-bounding-box-circles text-secondary"></i>
                <span class="text-secondary small">Monitoring &rsaquo; {{ $breadcrumb ?? 'Dashboard' }}</span>
            </div>
            <div class="d-flex align-items-center gap-3">
                <span class="badge text-bg-success-subtle text-success-emphasis" id="engineBadge">
                    <i class="bi bi-circle-fill" style="font-size:.55rem"></i> AI Online
                </span>
                <a class="nav-link p-0" href="#"><i class="bi bi-bell text-secondary fs-5"></i></a>
                <div class="dropdown">
                    <a class="nav-link dropdown-toggle text-secondary p-0" href="#" data-bs-toggle="dropdown">
                        <i class="bi bi-person-circle fs-5"></i> Admin
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end shadow">
                        <li><a class="dropdown-item" href="#">Profil</a></li>
                        <li><a class="dropdown-item" href="#">Pengaturan</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#">Keluar</a></li>
                    </ul>
                </div>
            </div>
        </header>

        <main class="content flex-grow-1">
            @yield('content')
        </main>

        <footer class="px-4 py-3 text-secondary small border-top bg-white">
            {{ config('app.name') }} &middot; Pastikan data mesin dan operasional dikelola
            sesuai kebijakan data perusahaan.
        </footer>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
@stack('scripts')
</body>
</html>