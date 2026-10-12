@extends('layouts.app')

@section('title', 'Dashboard')
@section('breadcrumb', 'Dashboard')

@section('content')

    {{-- ================= KPI ================= --}}
    <div class="row g-3 mb-3">
        @php
            $kpis = [
                ['label' => 'Durasi Mengeruk', 'value' => '00:00:00', 'icon' => 'bi bi-arrow-down-circle',
                 'bg' => 'bg-dig', 'delta' => '+0%', 'sub' => 'dari periode sebelumnya'],
                ['label' => 'Durasi Menuangkan', 'value' => '00:00:00', 'icon' => 'bi bi-truck',
                 'bg' => 'bg-dump', 'delta' => '+0%', 'sub' => 'dari periode sebelumnya'],
                ['label' => 'Jumlah Siklus', 'value' => '0 siklus', 'icon' => 'bi bi-arrow-repeat',
                 'bg' => 'bg-cycle', 'delta' => '+0%', 'sub' => 'dari periode sebelumnya'],
                ['label' => 'Waktu Idle', 'value' => '00:00:00', 'icon' => 'bi bi-clock',
                 'bg' => 'bg-idle', 'delta' => '+0%', 'sub' => 'dari periode sebelumnya'],
            ];
        @endphp

        @foreach ($kpis as $k)
            <div class="col-12 col-sm-6 col-xl-3">
                <div class="kpi d-flex gap-3">
                    <div class="kpi-icon {{ $k['bg'] }}">
                        <i class="{{ $k['icon'] }}"></i>
                    </div>
                    <div class="min-w-0">
                        <div class="kpi-label">{{ $k['label'] }}</div>
                        <div class="kpi-value">{{ $k['value'] }}</div>
                        <div class="kpi-delta up"><i class="bi bi-arrow-up-short"></i>{{ $k['delta'] }}</div>
                        <div class="kpi-sub">{{ $k['sub'] }}</div>
                    </div>
                </div>
            </div>
        @endforeach
    </div>

    {{-- ================= LIVE + HASIL DETEKSI ================= --}}
    <div class="row g-3 mb-3">
        <div class="col-12 col-xl-7">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        Live Camera &mdash; Cabin View
                        <span class="text-secondary fw-normal">({{ $unit ?? 'EXC-07' }})</span>
                    </h2>
                    <span class="badge text-bg-success-subtle text-success-emphasis">
                        <i class="bi bi-circle-fill" style="font-size:.55rem"></i> Live
                    </span>
                </div>
                <div class="p-3">
                    <div class="live-wrap">
                        {{-- Sumber stream.engine Python, bukan di-proxy lewat PHP. --}}
                        <img id="liveImage"
                             src="{{ config('hera.stream_url') }}/stream"
                             alt="Live camera cabin view"
                             onerror="document.getElementById('liveHint').style.display='block'">
                        <span class="live-badge">{{ now()->format('d/m/Y H:i:s') }}</span>
                        <span class="rec-dot"><i class="bi bi-record-fill"></i> REC</span>
                        <div id="liveHint" class="position-absolute bottom-0 start-0 end-0 p-2 text-center"
                             style="display:none">
                            <span class="badge text-bg-dark">
                                Stream belum tersedia &mdash; engine Python belum jalan
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-12 col-xl-5">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">Hasil Deteksi AI (Realtime)</h2>
                </div>
                <div class="p-3">
                    <div class="row g-3">
                        <div class="col-12 col-sm-6">
                            <div class="detect-card">
                                <img src="{{ asset('img/placeholder-dig.svg') }}" alt="Deteksi mengguk">
                                <span class="detect-tag">MENGERUK</span>
                            </div>
                            <div class="detect-foot">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <div class="detect-name"><i class="bi bi-wrench-adjustable"></i> Mengeruk (Digging)</div>
                                        <div class="detect-desc">Sedang melakukan aktivitas mengguk material</div>
                                    </div>
                                    <span class="badge text-bg-success">0%</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-12 col-sm-6">
                            <div class="detect-card dump">
                                <img src="{{ asset('img/placeholder-dump.svg') }}" alt="Deteksi menuangkan">
                                <span class="detect-tag">MENUANGKAN</span>
                            </div>
                            <div class="detect-foot">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <div class="detect-name"><i class="bi bi-truck"></i> Menuangkan (Dumping)</div>
                                        <div class="detect-desc">Sedang menuangkan material ke truck</div>
                                    </div>
                                    <span class="badge text-bg-warning">0%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    {{-- ================= TRACE ================= --}}
    <div class="panel mb-3">
        <div class="panel-head">
            <h2 class="panel-title">Urutan Aktivitas Terakhir</h2>
        </div>
        <div class="p-3">
            @php
                $steps = [
                    ['label' => 'Mengangkat', 'time' => '--:--:--', 'on' => false],
                    ['label' => 'Mengeruk', 'time' => '--:--:--', 'on' => true],
                    ['label' => 'Memutar', 'time' => '--:--:--', 'on' => false],
                    ['label' => 'Menuangkan', 'time' => '--:--:--', 'on' => true, 'dump' => true],
                    ['label' => 'Kembali', 'time' => '--:--:--', 'on' => false],
                ];
            @endphp
            <div class="trace">
                @foreach ($steps as $i => $s)
                    @if ($i > 0)
                        <i class="bi bi-arrow-right trace-arrow"></i>
                    @endif
                    <div class="trace-step {{ $s['on'] ? 'on' : '' }} {{ !empty($s['dump']) ? 'dump' : '' }}">
                        <img class="thumb" src="{{ asset('img/placeholder-step.svg') }}" alt="{{ $s['label'] }}">
                        <div class="label">{{ $s['label'] }}</div>
                        <div class="time">{{ $s['time'] }}</div>
                    </div>
                @endforeach
            </div>
        </div>
    </div>

    {{-- ================= RIWAYAT ================= --}}
    <div class="panel mb-4">
        <div class="panel-head">
            <h2 class="panel-title">Riwayat Deteksi Aktivitas</h2>
            <div class="d-flex gap-2">
                <a href="#" class="btn btn-primary btn-sm"><i class="bi bi-play-circle"></i> Lihat Video</a>
                <button class="btn btn-outline-secondary btn-sm"><i class="bi bi-download"></i> Export</button>
            </div>
        </div>
        <div class="table-responsive">
            <table class="table table-sm mb-0 align-middle">
                <thead class="table-light">
                    <tr>
                        <th>No.</th>
                        <th>Waktu Mulai</th>
                        <th>Waktu Selesai</th>
                        <th>Durasi</th>
                        <th>Jenis Aktivitas</th>
                        <th>Confidence</th>
                        <th></th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="riwayatBody">
                    <tr>
                        <td colspan="8" class="text-center text-secondary py-4">
                            Belum ada riwayat. Riwayat akan terisi setelah engine deteksi berjalan.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

@endsection