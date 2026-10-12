@extends('layouts.app')

@section('title', 'Dashboard')
@section('breadcrumb', 'Dashboard')

@section('content')

    {{-- ============ KEUJURAN SISTEM ============ --}}
    <div class="alert alert-warning d-flex align-items-start gap-2 mb-3 py-2 small">
        <i class="bi bi-exclamation-triangle-fill mt-1"></i>
        <div>
            <strong>Fase adalah inferensi, bukan pengamatan langsung.</strong>
            Ukuran bucket belum dideteksi. Fase <em>Mengeruk</em> dibaca dari
            energi gerak di zona gali, dan <em>Menuangkan</em> dari dump truck
            yang diam - itu korelasi, bukan bukti bucket meng emptying.
            Siklus dihitung saat satu fase Menuangkan selesai. Angka confidence
            adalah confidence deteksi truck.
        </div>
    </div>

    {{-- ============ KPI (dari engine Python) ============ --}}
    <div class="row g-3 mb-3">
        @php
            $kpi = [
                ['label' => 'Durasi Mengeruk', 'icon' => 'bi bi-arrow-down-circle',
                 'bg' => 'bg-dig',   'id' => 'kpiMengeruk'],
                ['label' => 'Durasi Menuangkan', 'icon' => 'bi bi-truck',
                 'bg' => 'bg-dump',  'id' => 'kpiMenuangkan'],
                ['label' => 'Jumlah Siklus', 'icon' => 'bi bi-arrow-repeat',
                 'bg' => 'bg-cycle', 'id' => 'kpiSiklus'],
                ['label' => 'Waktu Idle', 'icon' => 'bi bi-clock',
                 'bg' => 'bg-idle',  'id' => 'kpiIdle'],
            ];
        @endphp

        @foreach ($kpi as $k)
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="kpi d-flex gap-3">
                    <div class="kpi-icon {{ $k['bg'] }}">
                        <i class="{{ $k['icon'] }}"></i>
                    </div>
                    <div class="min-w-0">
                        <div class="kpi-label">{{ $k['label'] }}</div>
                        <div class="kpi-value" id="{{ $k['id'] }}">00:00:00</div>
                        <div class="kpi-sub">terukur engine</div>
                    </div>
                </div>
            </div>
        @endforeach
    </div>

    {{-- ============ LIVE + STATUS FASE ============ --}}
    <div class="row g-3 mb-3">
        <div class="col-12 col-xl-7">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        Live Camera <span class="text-secondary fw-normal">({{ $unit }})</span>
                    </h2>
                    <span class="badge text-bg-success-subtle text-success-emphasis" id="engineBadge">
                        <i class="bi bi-circle-fill" style="font-size:.55rem"></i>
                        <span id="engineBadgeText">connecting...</span>
                    </span>
                </div>
                <div class="p-3">
                    <div class="live-wrap">
                        {{-- Stream dilayani Python langsung; tidak lewat PHP. --}}
                        <img id="liveImage"
                             src="{{ rtrim(config('hera.stream_url'), '/') }}/stream"
                             alt="Live camera {{ $unit }}"
                             onload="herraStreamOK()"
                             onerror="herraStreamError()">
                        <span class="rec-dot"><i class="bi bi-record-fill"></i> LIVE</span>
                        <div id="liveHint" class="position-absolute bottom-0 start-0 end-0 p-2 text-center"
                             style="display:none">
                            <span class="badge text-bg-dark">
                                Stream belum tersedia - engine Python belum jalan
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-12 col-xl-5">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">Status Aktivitas</h2>
                </div>
                <div class="p-3" id="panelStatus">
                    <div class="text-center py-4 text-secondary" id="statusLoading">
                        <i class="bi bi-hourglass-split fs-2 d-block mb-2"></i>
                        Menunggu engine deteksi
                    </div>
                </div>
            </div>
        </div>
    </div>

    {{-- ============ TRACE FASE ============ --}}
    <div class="panel mb-3">
        <div class="panel-head">
            <h2 class="panel-title">Urutan Aktivitas Siklus</h2>
            <span class="small text-secondary" id="traceNote">5 fase</span>
        </div>
        <div class="p-3">
            <div class="trace">
                @foreach (['Mengangkat', 'Mengeruk', 'Memutar', 'Menuangkan', 'Kembali'] as $s)
                    <div class="trace-step" data-fase="{{ \Illuminate\Support\Str::slug($s) }}">
                        <div class="thumb d-flex align-items-center justify-content-center"
                             style="height:58px;border-radius:8px;border:2px solid #cbd5e1;background:#0b1220">
                            <i class="bi bi-circle text-secondary"></i>
                        </div>
                        <div class="label">{{ $s }}</div>
                        <div class="time">-</div>
                    </div>
                    @if (! $loop->last)<i class="bi bi-arrow-right trace-arrow"></i>@endif
                @endforeach
            </div>
        </div>
    </div>

    {{-- ============ RIWAYAT ============ --}}
    <div class="panel mb-4">
        <div class="panel-head">
            <h2 class="panel-title">Riwayat Deteksi Aktivitas</h2>
            <button class="btn btn-outline-secondary btn-sm" onclick="herraMuatRiwayat()">
                <i class="bi bi-arrow-clockwise"></i> Muat
            </button>
        </div>
        <div class="table-responsive">
            <table class="table table-sm mb-0 align-middle">
                <thead class="table-light">
                    <tr>
                        <th>No.</th><th>Waktu Mulai</th><th>Waktu Selesai</th>
                        <th>Durasi</th><th>Fase</th><th>Truck Conf.</th><th>Gerak Zona Gali</th>
                    </tr>
                </thead>
                <tbody id="riwayatBody">
                    <tr>
                        <td colspan="7" class="text-center text-secondary py-4">
                            Belum ada riwayat.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

@endsection

@push('scripts')
<script>
const HERRA_API = @json(rtrim(config('hera.api_url'), '/'));

function herraDurasi(detik) {
    detik = Math.max(0, Math.floor(detik || 0));
    const j = Math.floor(detik / 3600);
    const m = Math.floor((detik % 3600) / 60);
    const d = detik % 60;
    return [j, m, d].map(n => String(n).padStart(2, '0')).join(':');
}

function herraWaktu(iso) {
    if (!iso) return '-';
    const t = new Date(iso);
    return isNaN(t) ? '-' : t.toLocaleTimeString('id-ID', {hour12: false});
}

function herraStreamError() {
    document.getElementById('liveHint').style.display = 'block';
    document.getElementById('engineBadgeText').textContent = 'engine offline';
    document.getElementById('engineBadge').className = 'badge text-bg-secondary';
}

// Stream MJPEG bisa sempat putus sebentar lalu nyambung lagi,
// jadi hint disembunyikan lagi begitu frame masuk lagi.
function herraStreamOK() {
    document.getElementById('liveHint').style.display = 'none';
}

function herraMuatStatus() {
    fetch(HERRA_API + '/api/status')
        .then(r => r.json())
        .then(d => {
            document.getElementById('engineBadge').className =
                'badge text-bg-success-subtle text-success-emphasis';
            document.getElementById('engineBadgeText').textContent = 'AI Online';

            document.getElementById('kpiMengeruk').textContent =
                herraDurasi(d.kpi.durasi_mengeruk);
            document.getElementById('kpiMenuangkan').textContent =
                herraDurasi(d.kpi.durasi_menuangkan);
            document.getElementById('kpiIdle').textContent =
                herraDurasi(d.kpi.waktu_idle);
            document.getElementById('kpiSiklus').textContent =
                d.kpi.jumlah_siklus + ' siklus';

            document.getElementById('panelStatus').innerHTML = herraKartuFase(d);
            herraTandaiTrace(d.fase);
        })
        .catch(herraStreamError);
}

function herraKartuFase(d) {
    const pct = Math.round((d.truck_confidence || 0) * 100);
    const adaTruck = pct > 0;
    const badge = adaTruck
        ? '<span class="badge text-bg-warning">' + pct + '%</span>'
        : '<span class="badge text-bg-secondary">tidak ada</span>';

    let zona = '<div class="text-secondary small mt-2">Zona tuang: tidak aktif (tidak ada truck)</div>';
    if (d.zona_tuang) {
        zona = '<div class="text-secondary small mt-2">Zona tuang aktif di atas bak truck</div>';
    }

    return `
        <div class="text-center py-2">
            <div class="display-6 fw-bold" id="faseNama">${d.fase_label}</div>
            <div class="text-secondary small mb-3">
                berlangsung ${herraDurasi(d.durasi_fase_detik)}
            </div>
        </div>
        <div class="d-flex justify-content-between align-items-center border-top pt-2">
            <div>
                <div class="fw-semibold"><i class="bi bi-truck"></i> Dump Truck</div>
                <div class="small text-secondary">sumber sinyal: ${d.sumber_sinyal}</div>
            </div>
            ${badge}
        </div>
        <div class="d-flex justify-content-between align-items-center border-top pt-2 mt-2">
            <div>
                <div class="fw-semibold"><i class="bi bi-activity"></i> Energi Gerek Zona Gali</div>
                <div class="small text-secondary">proxy aktivitas mengguk</div>
            </div>
            <span class="badge text-bg-info">${d.zona_gali_motion}</span>
        </div>
        ${zona}`;
}

function herraTandaiTrace(faseAktif) {
    document.querySelectorAll('.trace-step').forEach(el => {
        const on = el.dataset.fase === faseAktif;
        const thumb = el.querySelector('.thumb');
        const icon = el.querySelector('.thumb i');
        thumb.style.borderColor = on ? '#16a34a' : '#cbd5e1';
        icon.className = on ? 'bi bi-check-circle-fill text-success' : 'bi bi-circle text-secondary';
        el.querySelector('.time').textContent = on ? 'sekarang' : '-';
    });
}

function herraMuatRiwayat() {
    fetch(HERRA_API + '/api/riwayat?limit=40')
        .then(r => r.json())
        .then(d => {
            const tbody = document.getElementById('riwayatBody');
            if (!d.events.length) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-secondary py-4">'
                    + 'Belum ada riwayat.</td></tr>';
                return;
            }
            tbody.innerHTML = d.events.map((e, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td>${herraWaktu(e.mulai)}</td>
                    <td>${herraWaktu(e.selesai)}</td>
                    <td class="fw-semibold">${herraDurasi(e.durasi)}</td>
                    <td><span class="status-pill text-bg-light border">${e.fase_label}</span></td>
                    <td>${Math.round(e.truck_confidence * 100)}%</td>
                    <td class="text-secondary">${e.zona_gali_motion}</td>
                </tr>`).join('');
        })
        .catch(() => {});
}

herraMuatStatus();
herraMuatRiwayat();
setInterval(herraMuatStatus, 2000);
setInterval(herraMuatRiwayat, 15000);
</script>
@endpush