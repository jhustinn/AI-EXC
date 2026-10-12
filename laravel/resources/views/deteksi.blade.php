@extends('layouts.app')

@section('title', 'Deteksi Aktivitas AI')
@section('breadcrumb', 'Monitoring / Deteksi Aktivitas AI')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h1 class="h4 mb-0 fw-bold">Deteksi Aktivitas AI</h1>
        <div class="d-flex gap-2">
            <select class="form-select form-select-sm" style="width:auto">
                <option>EXC-07</option>
                <option>EXC-03</option>
                <option>EXC-11</option>
            </select>
            <input type="date" class="form-control form-control-sm" style="width:auto"
                   value="{{ now()->format('Y-m-d') }}">
        </div>
    </div>

    <div class="row g-3">
        <div class="col-12 col-xl-8">
            <div class="panel">
                <div class="panel-head">
                    <h2 class="panel-title">Live Camera &mdash; Cabin View ({{ $unit }})</h2>
                    <span class="badge text-bg-success-subtle text-success-emphasis">
                        <i class="bi bi-circle-fill" style="font-size:.55rem"></i> Live
                    </span>
                </div>
                <div class="p-3">
                    <div class="live-wrap">
                        <img src="{{ config('hera.stream_url') }}/stream"
                             alt="Live camera {{ $unit }}"
                             onerror="document.getElementById('dHint').style.display='block'">
                        <span class="rec-dot"><i class="bi bi-record-fill"></i> REC</span>
                        <div id="dHint" class="position-absolute bottom-0 start-0 end-0 p-2 text-center"
                             style="display:none">
                            <span class="badge text-bg-dark">
                                Stream belum tersedia &mdash; engine Python belum jalan
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-12 col-xl-4">
            <div class="panel mb-3">
                <div class="panel-head"><h2 class="panel-title">Status Aktivitas</h2></div>
                <div class="p-3">
                    <div id="statusIdle" class="text-center py-4 text-secondary">
                        <i class="bi bi-hourglass-split fs-2 d-block mb-2"></i>
                        Menunggu engine deteksi
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head"><h2 class="panel-title">Ringkasan Hari Ini</h2></div>
                <table class="table table-sm mb-0">
                    <tbody>
                        <tr><td class="text-secondary">Mulai</td><td class="text-end fw-semibold">--:--</td></tr>
                        <tr><td class="text-secondary">Selesai</td><td class="text-end fw-semibold">--:--</td></tr>
                        <tr><td class="text-secondary">Durasi</td><td class="text-end fw-semibold">--:--</td></tr>
                        <tr><td class="text-secondary">Jenis</td><td class="text-end fw-semibold">-</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

@endsection