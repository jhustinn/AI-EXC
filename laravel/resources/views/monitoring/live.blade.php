@extends('layouts.app')

@section('title', 'Live Multi-Camera Matrix & Patrol')
@section('breadcrumb', 'Monitoring / Live Multi-Camera Matrix')

@section('content')

    <!-- TOP CONTROL BAR -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-3">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Live Multi-Camera Matrix &amp; Patroli Otomatis</h1>
            <p class="text-secondary small mb-0">
                Monitoring visual CCTV armada tambang multi-titik &bull; Tampilan grid dinamis &amp; patroli rotasi kamera otomatis.
            </p>
        </div>

        <div class="d-flex flex-wrap align-items-center gap-2">
            <!-- PATROLI / AUTO-TOUR CONTROLS -->
            <div class="d-flex align-items-center bg-white p-1 rounded border shadow-sm gap-1">
                <button type="button" class="btn btn-outline-secondary btn-sm px-2" title="Kamera Sebelumnya (Panah Kiri)" onclick="prevCamera()">
                    <i class="bi bi-chevron-left"></i>
                </button>

                <button type="button" class="btn btn-sm btn-primary d-flex align-items-center gap-2 px-3" id="btnTourToggle" onclick="toggleAutoTour()">
                    <i class="bi bi-play-circle-fill" id="tourIcon"></i>
                    <span id="tourBtnText">Patroli Otomatis: OFF</span>
                </button>

                <button type="button" class="btn btn-outline-secondary btn-sm px-2" title="Kamera Berikutnya (Panah Kanan)" onclick="nextCamera()">
                    <i class="bi bi-chevron-right"></i>
                </button>

                <select id="tourIntervalSelect" class="form-select form-select-sm border-0 bg-light" style="width:auto;font-size:12px;" onchange="updateTourInterval()">
                    <option value="5">Tiap 5 Detik</option>
                    <option value="8" selected>Tiap 8 Detik</option>
                    <option value="12">Tiap 12 Detik</option>
                    <option value="20">Tiap 20 Detik</option>
                </select>
            </div>

            <!-- GRID VIEW SELECTOR -->
            <div class="btn-group shadow-sm" role="group">
                <button type="button" class="btn btn-outline-secondary btn-sm" id="btnGrid1" title="1x1 Fokus Tunggal (Shortcut: 1)" onclick="setGridMode('1x1')">
                    <i class="bi bi-square"></i> 1x1
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm" id="btnGrid2" title="1x2 Dual View (Shortcut: 2)" onclick="setGridMode('1x2')">
                    <i class="bi bi-layout-split"></i> 1x2
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm active" id="btnGrid4" title="2x2 Quad Matrix (Shortcut: 4)" onclick="setGridMode('2x2')">
                    <i class="bi bi-grid-fill"></i> 2x2
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm" id="btnGrid6" title="3x2 Grid Penuh (Shortcut: 6)" onclick="setGridMode('3x2')">
                    <i class="bi bi-grid-3x2-gap-fill"></i> Semua ({{ $cameras->count() }})
                </button>
            </div>

            <button class="btn btn-outline-dark btn-sm shadow-sm" title="Layar Penuh (Shortcut: F)" onclick="toggleFullScreenMatrix()">
                <i class="bi bi-fullscreen"></i>
            </button>
        </div>
    </div>

    <!-- PATROLI STATUS & PROGRESS BAR -->
    <div class="bg-white border rounded px-3 py-2 mb-3 shadow-sm d-flex flex-wrap align-items-center justify-content-between gap-3">
        <div class="d-flex align-items-center gap-3">
            <span class="badge text-bg-dark font-monospace" id="tourActiveBadge">
                <i class="bi bi-camera-video"></i> <span id="activeCamLabel">CAM-01: Cabin Dashcam</span>
            </span>
            <span class="small text-secondary" id="tourStatusText">
                Status: <strong class="text-dark">Manual View</strong> &bull; Klik kamera manapun untuk memperbesar
            </span>
        </div>

        <div class="d-flex align-items-center gap-2" style="min-width: 200px;">
            <small class="text-secondary" style="font-size:11px;">Timer Rotasi:</small>
            <div class="tour-progress-wrap flex-grow-1 rounded">
                <div class="tour-progress-bar" id="tourBar"></div>
            </div>
            <span class="small font-monospace text-secondary" id="tourCountdown" style="font-size:11px;">--s</span>
        </div>
    </div>

    <!-- MAIN MULTI-CAMERA MATRIX CONTAINER -->
    <div id="cctvMatrixContainer" class="grid-mode-2x2">
        <div class="row g-3" id="cameraGridRow">
            @foreach($cameras as $index => $cam)
                <div class="col-cam col-12" id="camCol-{{ $index }}" data-index="{{ $index }}" data-cam-id="{{ $cam->id }}">
                    <div class="camera-tile h-100 {{ $index === 0 ? 'tour-active' : '' }}" id="camTile-{{ $index }}">
                        <!-- TILE HEADER -->
                        <div class="camera-tile-header">
                            <div class="d-flex align-items-center gap-2 min-w-0">
                                <span class="badge text-bg-danger rounded-pill px-2" style="font-size:10px;">
                                    <i class="bi bi-record-fill"></i> AI LIVE
                                </span>
                                <h3 class="camera-tile-title text-truncate" title="{{ $cam->nama }}">{{ $cam->nama }}</h3>
                            </div>

                            <div class="d-flex align-items-center gap-1">
                                <span class="badge text-bg-secondary-subtle text-light border border-secondary" style="font-size:10.5px;">
                                    {{ $cam->unit->kode_unit ?? 'MINE' }}
                                </span>
                                <button class="btn btn-sm btn-link text-white p-0 px-1" title="Fokuskan Kamera Ini (1x1)" onclick="focusCamera({{ $index }})">
                                    <i class="bi bi-arrows-angle-expand"></i>
                                </button>
                                <button class="btn btn-sm btn-link text-white p-0 px-1" title="Ambil Foto Snapshot" onclick="snapshotCamera({{ $index }})">
                                    <i class="bi bi-camera"></i>
                                </button>
                            </div>
                        </div>

                        <!-- TILE VIDEO BODY -->
                        <div class="camera-tile-video-wrap" onclick="focusCamera({{ $index }})" style="cursor: pointer;">
                            <!-- LIVE AI MULTI-CAMERA STREAM -->
                            <img id="feed-{{ $index }}"
                                 src="{{ $streamUrl }}/stream/{{ $cam->id }}"
                                 alt="{{ $cam->nama }}"
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="onFeedSuccess({{ $index }})"
                                 onerror="onFeedError({{ $index }})">

                            <!-- OVERLAY CONTROLS -->
                            <div class="live-badge-rec">
                                <i class="bi bi-record-fill"></i>
                                <span>CAM {{ sprintf('%02d', $index + 1) }}</span>
                            </div>

                            <div class="position-absolute bottom-0 start-0 m-2 badge bg-dark bg-opacity-75 text-white font-monospace" style="font-size:10px;">
                                {{ $cam->resolusi }} &bull; {{ $cam->fps }} FPS
                            </div>
                        </div>

                        <!-- TILE FOOTER -->
                        <div class="camera-tile-footer">
                            <span class="text-truncate" style="max-width: 65%;">
                                <i class="bi bi-geo-alt text-primary me-1"></i> {{ $cam->posisi }}
                            </span>
                            <span class="text-success fw-semibold font-monospace" style="font-size:10.5px;">
                                <i class="bi bi-activity"></i> &lt; 75ms
                            </span>
                        </div>
                    </div>
                </div>
            @endforeach
        </div>
    </div>

    <!-- BOTTOM CAMERA PRESET TABS / CAROUSEL -->
    <div class="panel mt-3 p-3">
        <div class="d-flex align-items-center justify-content-between mb-2">
            <span class="small fw-bold text-uppercase text-secondary">Preset Kamera &amp; Switch Cepat:</span>
            <small class="text-muted">Gunakan tombol <strong>1, 2, 4, 6</strong> untuk tata letak &bull; <strong>&larr; / &rarr;</strong> untuk rotasi</small>
        </div>
        <div class="d-flex flex-wrap gap-2" id="cameraPresetTabs">
            @foreach($cameras as $index => $cam)
                <button type="button"
                        class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-2 cam-preset-btn {{ $index === 0 ? 'active btn-primary text-white' : '' }}"
                        id="presetBtn-{{ $index }}"
                        onclick="jumpToCamera({{ $index }})">
                    <span class="badge text-bg-light rounded-pill" style="font-size:10px;">#{{ $index + 1 }}</span>
                    <span>{{ $cam->nama }}</span>
                    <span class="badge bg-secondary text-white" style="font-size:10px;">{{ $cam->unit->kode_unit ?? '' }}</span>
                </button>
            @endforeach
        </div>
    </div>

@endsection

@push('scripts')
<script>
    const TOTAL_CAMS = {{ $cameras->count() }};
    const CAMERA_NAMES = {!! json_encode($cameras->pluck('nama')) !!};
    let currentGridMode = '2x2';
    let currentActiveIndex = 0;
    let isAutoTour = false;
    let tourIntervalSec = 8;
    let tourRemainingSec = 8;
    let tourTimer = null;
    let progressTimer = null;

    // 1. Grid Mode Switcher
    function setGridMode(mode) {
        currentGridMode = mode;
        const container = document.getElementById('cctvMatrixContainer');
        container.className = 'grid-mode-' + mode;

        document.querySelectorAll('.btn-group button').forEach(b => b.classList.remove('active'));
        if (mode === '1x1') document.getElementById('btnGrid1').classList.add('active');
        if (mode === '1x2') document.getElementById('btnGrid2').classList.add('active');
        if (mode === '2x2') document.getElementById('btnGrid4').classList.add('active');
        if (mode === '3x2') document.getElementById('btnGrid6').classList.add('active');

        applySlotClasses();
    }

    // Mengatur camera slot untuk tiap mode grid
    function applySlotClasses() {
        document.querySelectorAll('.col-cam').forEach((col, idx) => {
            col.classList.remove('active-primary', 'active-slot-1', 'active-slot-2', 'active-slot-3', 'active-slot-4');
        });

        // Slot 1 selalu kamera aktif saat ini
        const idx1 = currentActiveIndex;
        const idx2 = (currentActiveIndex + 1) % TOTAL_CAMS;
        const idx3 = (currentActiveIndex + 2) % TOTAL_CAMS;
        const idx4 = (currentActiveIndex + 3) % TOTAL_CAMS;

        const col1 = document.getElementById('camCol-' + idx1);
        if (col1) {
            col1.classList.add('active-primary', 'active-slot-1');
        }

        const col2 = document.getElementById('camCol-' + idx2);
        if (col2) col2.classList.add('active-slot-2');

        const col3 = document.getElementById('camCol-' + idx3);
        if (col3) col3.classList.add('active-slot-3');

        const col4 = document.getElementById('camCol-' + idx4);
        if (col4) col4.classList.add('active-slot-4');

        // Update highlight outline
        document.querySelectorAll('.camera-tile').forEach((t, i) => {
            if (i === currentActiveIndex) {
                t.classList.add('tour-active');
            } else {
                t.classList.remove('tour-active');
            }
        });

        // Update active preset tab
        document.querySelectorAll('.cam-preset-btn').forEach((b, i) => {
            if (i === currentActiveIndex) {
                b.className = 'btn btn-sm btn-primary text-white d-flex align-items-center gap-2 cam-preset-btn active';
            } else {
                b.className = 'btn btn-sm btn-outline-secondary d-flex align-items-center gap-2 cam-preset-btn';
            }
        });

        // Update status text
        const name = CAMERA_NAMES[currentActiveIndex] || 'CAM-' + (currentActiveIndex + 1);
        document.getElementById('activeCamLabel').textContent = name;
    }

    // 2. Perpindahan Kamera (Navigation)
    function jumpToCamera(index) {
        currentActiveIndex = (index + TOTAL_CAMS) % TOTAL_CAMS;
        resetTourCountdown();
        applySlotClasses();
    }

    function nextCamera() {
        jumpToCamera(currentActiveIndex + 1);
    }

    function prevCamera() {
        jumpToCamera(currentActiveIndex - 1);
    }

    function focusCamera(index) {
        currentActiveIndex = index;
        if (currentGridMode !== '1x1') {
            setGridMode('1x1');
        } else {
            applySlotClasses();
        }
    }

    // 3. Auto-Patrol / Auto-Tour
    function toggleAutoTour() {
        isAutoTour = !isAutoTour;
        const btn = document.getElementById('btnTourToggle');
        const icon = document.getElementById('tourIcon');
        const txt = document.getElementById('tourBtnText');
        const statusTxt = document.getElementById('tourStatusText');

        if (isAutoTour) {
            btn.className = 'btn btn-sm btn-success d-flex align-items-center gap-2 px-3 shadow-sm';
            icon.className = 'bi bi-pause-circle-fill';
            txt.textContent = 'Patroli Otomatis: ON';
            statusTxt.innerHTML = 'Status: <strong class="text-success"><i class="bi bi-broadcast"></i> Patroli Berputar Aktif</strong>';
            startTourTimers();
        } else {
            btn.className = 'btn btn-sm btn-primary d-flex align-items-center gap-2 px-3';
            icon.className = 'bi bi-play-circle-fill';
            txt.textContent = 'Patroli Otomatis: OFF';
            statusTxt.innerHTML = 'Status: <strong class="text-dark">Manual View</strong>';
            stopTourTimers();
        }
    }

    function updateTourInterval() {
        tourIntervalSec = parseInt(document.getElementById('tourIntervalSelect').value, 10) || 8;
        if (isAutoTour) {
            startTourTimers();
        }
    }

    function startTourTimers() {
        stopTourTimers();
        resetTourCountdown();

        tourTimer = setInterval(() => {
            nextCamera();
            resetTourCountdown();
        }, tourIntervalSec * 1000);

        const updateFreqMs = 100;
        progressTimer = setInterval(() => {
            tourRemainingSec -= (updateFreqMs / 1000);
            if (tourRemainingSec < 0) tourRemainingSec = tourIntervalSec;

            const pct = Math.max(0, Math.min(100, ((tourIntervalSec - tourRemainingSec) / tourIntervalSec) * 100));
            document.getElementById('tourBar').style.width = pct + '%';
            document.getElementById('tourCountdown').textContent = Math.ceil(tourRemainingSec) + 's';
        }, updateFreqMs);
    }

    function stopTourTimers() {
        if (tourTimer) clearInterval(tourTimer);
        if (progressTimer) clearInterval(progressTimer);
        tourTimer = null;
        progressTimer = null;
        document.getElementById('tourBar').style.width = '0%';
        document.getElementById('tourCountdown').textContent = '--s';
    }

    function resetTourCountdown() {
        tourRemainingSec = tourIntervalSec;
        document.getElementById('tourBar').style.width = '0%';
        document.getElementById('tourCountdown').textContent = tourIntervalSec + 's';
    }

    // 4. Snapshot & Fullscreen
    function snapshotCamera(index) {
        const feed = document.getElementById('feed-' + index);
        if (!feed) return;

        const canvas = document.createElement('canvas');
        canvas.width = feed.videoWidth || feed.naturalWidth || 640;
        canvas.height = feed.videoHeight || feed.naturalHeight || 480;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(feed, 0, 0, canvas.width, canvas.height);

        const a = document.createElement('a');
        a.download = 'snapshot_cam' + (index + 1) + '_' + new Date().getTime() + '.jpg';
        a.href = canvas.toDataURL('image/jpeg');
        a.click();
    }

    function toggleFullScreenMatrix() {
        const el = document.getElementById('cctvMatrixContainer');
        if (!document.fullscreenElement) {
            el.requestFullscreen().catch(() => {});
        } else {
            document.exitFullscreen();
        }
    }

    function onFeedSuccess(index) {
        const tile = document.getElementById('camTile-' + index);
        if (tile) {
            const notice = tile.querySelector('.feed-error-notice');
            if (notice) notice.remove();
        }
    }

    function onFeedError(index) {
        const tile = document.getElementById('camTile-' + index);
        const feed = document.getElementById('feed-' + index);
        if (tile) {
            const wrap = tile.querySelector('.camera-tile-video-wrap');
            if (wrap && !wrap.querySelector('.feed-error-notice')) {
                const notice = document.createElement('div');
                notice.className = 'feed-error-notice position-absolute text-white text-center p-3';
                notice.style.background = 'rgba(15,23,42,0.92)';
                notice.innerHTML = '<i class="bi bi-arrow-repeat text-warning fs-3 d-block mb-1 animate-spin"></i><small>Menghubungkan AI Engine...</small>';
                wrap.appendChild(notice);
            }
        }
        if (feed && !feed._retryTimer) {
            feed._retryTimer = setTimeout(() => {
                feed._retryTimer = null;
                const baseSrc = feed.src.split('?')[0];
                feed.src = baseSrc + '?t=' + new Date().getTime();
            }, 3000);
        }
    }

    // 5. Keyboard Navigation
    document.addEventListener('keydown', (e) => {
        // Jangan tangkap jika user mengetik di input/select
        if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return;

        if (e.key === 'ArrowRight') {
            nextCamera();
        } else if (e.key === 'ArrowLeft') {
            prevCamera();
        } else if (e.key === ' ') {
            e.preventDefault();
            toggleAutoTour();
        } else if (e.key === '1') {
            setGridMode('1x1');
        } else if (e.key === '2') {
            setGridMode('1x2');
        } else if (e.key === '4') {
            setGridMode('2x2');
        } else if (e.key === '6') {
            setGridMode('3x2');
        } else if (e.key.toLowerCase() === 'f') {
            toggleFullScreenMatrix();
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        setGridMode('2x2');
    });
</script>
@endpush
