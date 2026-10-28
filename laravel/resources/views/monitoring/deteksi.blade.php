@extends('layouts.app')

@section('title', 'Deteksi Aktivitas AI')
@section('breadcrumb', 'Monitoring / Deteksi Aktivitas AI')

@section('content')

    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-3">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark">Diagnostik Deteksi Komputer Vision AI</h1>
            <p class="text-secondary small mb-0">
                Inspeksi teknis inferensi model deep learning YOLO & Kinematika Fisik Alat Berat &mdash; Unit <strong>{{ $unit }}</strong>.
            </p>
        </div>
        <div class="d-flex align-items-center gap-2">
            <span class="badge bg-white text-secondary border px-3 py-2">
                <i class="bi bi-motherboard text-primary"></i> Device: <strong>NVIDIA GPU / CUDA</strong>
            </span>
        </div>
    </div>

    <div class="row g-3 mb-3">
        <!-- LIVE CAMERA WITH BOUNDING BOXES -->
        <div class="col-12 col-xl-7">
            <div class="panel h-100">
                <div class="panel-head">
                    <h2 class="panel-title">
                        <i class="bi bi-bounding-box text-primary"></i>
                        <span>Visual Detection Feed ({{ $unit }})</span>
                    </h2>
                    <span class="badge text-bg-success-subtle text-success border border-success-subtle">
                        <i class="bi bi-circle-fill" style="font-size:7px;"></i> AI Live
                    </span>
                </div>
                <div class="p-3">
                    <div class="live-stream-box" style="min-height: 440px;">
                        <img src="{{ $streamUrl }}/stream"
                             alt="AI Detection {{ $unit }}"
                             onerror="document.getElementById('detHint').style.display='block'">
                        <div id="detHint" class="position-absolute p-3 text-center text-white" style="display:none;background:rgba(5,8,17,0.9);">
                            <span class="badge text-bg-warning">Engine belum terhubung</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- INFERENCE TELEMETRY & CONFIDENCE -->
        <div class="col-12 col-xl-5">
            <div class="panel mb-3">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-speedometer text-primary"></i> Performa & Latensi Inferensi</h2>
                </div>
                <div class="p-3">
                    <div class="row text-center g-2 mb-3">
                        <div class="col-4">
                            <div class="p-2 border rounded bg-light">
                                <small class="text-secondary d-block">Inference</small>
                                <strong class="fs-5 text-primary" id="infTime">~22 ms</strong>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 border rounded bg-light">
                                <small class="text-secondary d-block">Throughput</small>
                                <strong class="fs-5 text-success">45 FPS</strong>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 border rounded bg-light">
                                <small class="text-secondary d-block">Device</small>
                                <strong class="fs-5 text-dark">GPU 0</strong>
                            </div>
                        </div>
                    </div>

                    <h6 class="fw-bold fs-7 text-uppercase text-secondary mb-2">Confidence Matrix (Ambang &gt; 0.18)</h6>
                    <table class="table table-sm align-middle mb-0">
                        <tbody>
                            <tr>
                                <td><i class="bi bi-truck text-warning me-2"></i><strong>Dump Truck Hauler</strong></td>
                                <td class="text-end fw-semibold text-warning" id="detTruckConf">--%</td>
                            </tr>
                            <tr>
                                <td><i class="bi bi-box text-success me-2"></i><strong>Bucket & Teeth</strong></td>
                                <td class="text-end fw-semibold text-success" id="detBucketConf">--%</td>
                            </tr>
                            <tr>
                                <td><i class="bi bi-truck-front text-primary me-2"></i><strong>Badan Excavator</strong></td>
                                <td class="text-end fw-semibold text-primary" id="detExcConf">--%</td>
                            </tr>
                            <tr>
                                <td><i class="bi bi-activity text-info me-2"></i><strong>Optical Flow Gali</strong></td>
                                <td class="text-end fw-semibold text-info" id="detMotionConf">--</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="panel">
                <div class="panel-head">
                    <h2 class="panel-title"><i class="bi bi-cpu-fill text-primary"></i> Konfigurasi Model AI</h2>
                </div>
                <div class="p-3">
                    <ul class="list-group list-group-flush small">
                        <li class="list-group-item d-flex justify-content-between px-0">
                            <span class="text-secondary">Model Arsitektur</span>
                            <span class="fw-semibold">YOLO11 Nano Finetuned (Mining V4)</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between px-0">
                            <span class="text-secondary">Orientasi Mode</span>
                            <span class="badge text-bg-primary">Cabin Boom POV (Auto-detect)</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between px-0">
                            <span class="text-secondary">Tailgate HSV Filter</span>
                            <span class="text-success fw-semibold"><i class="bi bi-check-circle"></i> Aktif (Mining Orange)</span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between px-0">
                            <span class="text-secondary">Kinematika Lengan</span>
                            <span class="text-success fw-semibold"><i class="bi bi-check-circle"></i> Elbow, Wrist, Tip Tracked</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

@endsection

@push('scripts')
<script>
    const DET_API = @json(route('api.telemetry.live', ['unit' => $unit]));

    function updateDetDiagnostics() {
        fetch(DET_API)
            .then(res => res.json())
            .then(d => {
                if (!d.status) return;
                const s = d.status;
                document.getElementById('detTruckConf').textContent = Math.round((s.truck_confidence || 0) * 100) + '%';
                document.getElementById('detBucketConf').textContent = Math.round((s.bucket_confidence || 0) * 100) + '%';
                document.getElementById('detExcConf').textContent = Math.round((s.excavator_confidence || 0) * 100) + '%';
                document.getElementById('detMotionConf').textContent = (s.zona_gali_motion || 0).toFixed(4);
            })
            .catch(() => {});
    }

    document.addEventListener('DOMContentLoaded', () => {
        updateDetDiagnostics();
        setInterval(updateDetDiagnostics, 1500);
    });
</script>
@endpush
