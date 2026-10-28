@extends('layouts.app')

@section('title', 'Master Data Kamera & Video')
@section('breadcrumb', 'Master Data / Kamera & Video')

@section('content')

    <!-- HEADER & ACTION -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark d-flex align-items-center gap-2">
                <i class="bi bi-webcam-fill text-primary"></i>
                <span>Data Konfigurasi Kamera &amp; Stream AI</span>
            </h1>
            <p class="text-secondary small mb-0">
                Kelola feed CCTV armada tambang, integrasi Raspberry Pi Zero, kamera IP RTSP, dan uji konektivitas stream secara real-time.
            </p>
        </div>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" data-bs-toggle="modal" data-bs-target="#addCameraModal">
            <i class="bi bi-plus-lg"></i> Tambah Kamera Baru
        </button>
    </div>

    <!-- SUMMARY METRIC CHIPS -->
    <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-camera-video fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Kamera</div>
                    <div class="fs-4 fw-bold text-dark">{{ $cameras->count() }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-broadcast-pin fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Primary AI Feeds</div>
                    <div class="fs-4 fw-bold text-dark">{{ $cameras->where('is_primary', true)->count() }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-info-subtle text-info">
                    <i class="bi bi-cpu fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Unit Terhubung</div>
                    <div class="fs-4 fw-bold text-dark">{{ $cameras->pluck('unit_id')->unique()->count() }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-warning-subtle text-warning">
                    <i class="bi bi-router fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Protokol Stream</div>
                    <div class="fs-6 fw-bold text-dark">RTSP &bull; HTTP &bull; File</div>
                </div>
            </div>
        </div>
    </div>

    <!-- CAMERAS TABLE PANEL -->
    <div class="panel">
        <div class="panel-head d-flex justify-content-between align-items-center">
            <h2 class="panel-title"><i class="bi bi-camera-video text-primary"></i> Daftar Sumber Kamera Terpasang</h2>
            <span class="badge text-bg-light border text-secondary">{{ $cameras->count() }} Kamera Terdaftar</span>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light small text-secondary">
                    <tr>
                        <th style="width: 45px;">#</th>
                        <th>Nama Kamera &amp; Posisi</th>
                        <th>Unit Terkait</th>
                        <th>Tipe Sumber</th>
                        <th>Path / URL Stream</th>
                        <th>Format &amp; FPS</th>
                        <th>Feed AI</th>
                        <th class="text-end" style="width: 190px;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($cameras as $index => $c)
                        <tr>
                            <td class="text-secondary small">{{ $index + 1 }}</td>
                            <td>
                                <div class="fw-bold text-dark">{{ $c->nama }}</div>
                                <div class="text-secondary small d-flex align-items-center gap-1">
                                    <i class="bi bi-geo-alt"></i> {{ $c->posisi }}
                                </div>
                            </td>
                            <td>
                                <span class="badge text-bg-primary-subtle text-primary border border-primary-subtle">
                                    {{ $c->unit->kode_unit ?? '-' }}
                                </span>
                            </td>
                            <td>
                                @if(str_contains(strtolower($c->source_path), '8080') || str_starts_with(strtolower($c->source_path), 'http'))
                                    <span class="badge text-bg-info text-dark text-uppercase"><i class="bi bi-motherboard me-1"></i> HTTP / RPi</span>
                                @elseif($c->source_type === 'rtsp')
                                    <span class="badge text-bg-dark text-uppercase"><i class="bi bi-broadcast me-1"></i> RTSP</span>
                                @else
                                    <span class="badge text-bg-secondary text-uppercase"><i class="bi bi-film me-1"></i> File</span>
                                @endif
                            </td>
                            <td>
                                <code class="small text-muted font-monospace d-inline-block text-truncate" style="max-width: 240px;" title="{{ $c->source_path }}">
                                    {{ $c->source_path }}
                                </code>
                            </td>
                            <td class="small text-secondary">
                                <span class="fw-semibold text-dark">{{ $c->resolusi }}</span> &bull; {{ $c->fps }} FPS
                            </td>
                            <td>
                                @if($c->is_primary)
                                    <span class="badge text-bg-success"><i class="bi bi-check-circle-fill"></i> Primary Feed</span>
                                @else
                                    <span class="badge text-bg-light text-secondary border">Secondary</span>
                                @endif
                            </td>
                            <td class="text-end">
                                <!-- UJI KONEKSI BUTTON -->
                                <button type="button" 
                                        class="btn btn-sm btn-outline-info me-1" 
                                        onclick="testStreamConnection('{{ $c->source_path }}', '{{ $c->source_type }}', '{{ $c->nama }}')"
                                        title="Uji Koneksi Kamera">
                                    <i class="bi bi-reception-4"></i>
                                </button>

                                <!-- EDIT BUTTON -->
                                <button type="button" 
                                        class="btn btn-sm btn-outline-secondary me-1" 
                                        data-bs-toggle="modal" 
                                        data-bs-target="#editCameraModal{{ $c->id }}"
                                        title="Ubah Kamera">
                                    <i class="bi bi-pencil-fill"></i>
                                </button>

                                <!-- DELETE BUTTON -->
                                <button type="button" 
                                        class="btn btn-sm btn-outline-danger" 
                                        data-bs-toggle="modal" 
                                        data-bs-target="#deleteCameraModal{{ $c->id }}"
                                        title="Hapus Kamera">
                                    <i class="bi bi-trash-fill"></i>
                                </button>
                            </td>
                        </tr>

                        <!-- MODAL EDIT KAMERA -->
                        <div class="modal fade" id="editCameraModal{{ $c->id }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered">
                                <form action="{{ route('master.kamera.update', $c->id) }}" method="POST" class="modal-content">
                                    @csrf
                                    @method('PUT')
                                    <div class="modal-header">
                                        <h5 class="modal-title fw-bold">Ubah Konfigurasi Kamera</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Unit Alat Berat</label>
                                            <select name="unit_id" class="form-select" required>
                                                @foreach($units as $u)
                                                    <option value="{{ $u->id }}" {{ $u->id === $c->unit_id ? 'selected' : '' }}>
                                                        {{ $u->kode_unit }} &mdash; {{ $u->nama }}
                                                    </option>
                                                @endforeach
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Nama Kamera</label>
                                            <input type="text" name="nama" class="form-control" value="{{ $c->nama }}" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Posisi Pemasangan</label>
                                            <input type="text" name="posisi" class="form-control" value="{{ $c->posisi }}" required>
                                        </div>
                                        <div class="row g-2 mb-3">
                                            <div class="col-6">
                                                <label class="form-label small fw-semibold">Tipe Sumber</label>
                                                <select name="source_type" class="form-select">
                                                    <option value="http" {{ ($c->source_type === 'http' || str_starts_with($c->source_path, 'http')) ? 'selected' : '' }}>HTTP MJPEG (Raspberry Pi Dashcam)</option>
                                                    <option value="rtsp" {{ $c->source_type === 'rtsp' ? 'selected' : '' }}>RTSP IP Camera</option>
                                                    <option value="video" {{ $c->source_type === 'video' ? 'selected' : '' }}>File Video Lokal</option>
                                                    <option value="usb" {{ $c->source_type === 'usb' ? 'selected' : '' }}>USB Webcam</option>
                                                </select>
                                            </div>
                                            <div class="col-6">
                                                <label class="form-label small fw-semibold">FPS Target</label>
                                                <input type="number" name="fps" class="form-control" value="{{ $c->fps }}" required min="5" max="60">
                                            </div>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Path / URL Stream</label>
                                            <input type="text" name="source_path" class="form-control" value="{{ $c->source_path }}" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Resolusi</label>
                                            <input type="text" name="resolusi" class="form-control" value="{{ $c->resolusi }}" required>
                                        </div>
                                        <div class="form-check form-switch mb-2">
                                            <input class="form-check-input" type="checkbox" name="is_primary" value="1" id="isPrimEdit{{ $c->id }}" {{ $c->is_primary ? 'checked' : '' }}>
                                            <label class="form-check-label small fw-semibold" for="isPrimEdit{{ $c->id }}">Jadikan Feed Utama (Primary AI Feed)</label>
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                                        <button type="submit" class="btn btn-primary btn-sm">Simpan Perubahan</button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        <!-- MODAL HAPUS KAMERA -->
                        <div class="modal fade" id="deleteCameraModal{{ $c->id }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered modal-sm">
                                <form action="{{ route('master.kamera.destroy', $c->id) }}" method="POST" class="modal-content">
                                    @csrf
                                    @method('DELETE')
                                    <div class="modal-body text-center p-4">
                                        <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2 d-block"></i>
                                        <h6 class="fw-bold mb-1">Hapus Kamera?</h6>
                                        <p class="text-secondary small mb-3">Kamera <strong>{{ $c->nama }}</strong> akan dihapus dari daftar monitoring.</p>
                                        <div class="d-flex justify-content-center gap-2">
                                            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
                                            <button type="submit" class="btn btn-sm btn-danger">Ya, Hapus</button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>

                    @empty
                        <tr>
                            <td colspan="8" class="text-center py-5 text-secondary">
                                <i class="bi bi-camera-video-off fs-1 opacity-50 mb-2 d-block"></i>
                                Belum ada kamera terdaftar di sistem.
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    <!-- MODAL TAMBAH KAMERA -->
    <div class="modal fade" id="addCameraModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <form action="{{ route('master.kamera.store') }}" method="POST" class="modal-content">
                @csrf
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">Tambah Kamera Baru</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <!-- PRESET CEPAT -->
                    <div class="mb-3 p-2 rounded bg-light border">
                        <small class="text-secondary fw-bold d-block mb-1" style="font-size:11px;">
                            <i class="bi bi-lightning-charge-fill text-warning"></i> PRESET CEPAT:
                        </small>
                        <div class="d-flex flex-wrap gap-1">
                            <button type="button" class="btn btn-xs btn-outline-secondary py-1 px-2 small" onclick="applyPreset('rpi')">
                                <i class="bi bi-motherboard text-danger"></i> Raspberry Pi Zero
                            </button>
                            <button type="button" class="btn btn-xs btn-outline-secondary py-1 px-2 small" onclick="applyPreset('rtsp')">
                                <i class="bi bi-broadcast text-primary"></i> RTSP IP Cam
                            </button>
                            <button type="button" class="btn btn-xs btn-outline-secondary py-1 px-2 small" onclick="applyPreset('night')">
                                <i class="bi bi-moon-stars text-warning"></i> File Night Dashcam
                            </button>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Unit Alat Berat <span class="text-danger">*</span></label>
                        <select name="unit_id" class="form-select" required>
                            @foreach($units as $u)
                                <option value="{{ $u->id }}">{{ $u->kode_unit }} &mdash; {{ $u->nama }}</option>
                            @endforeach
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Nama Kamera <span class="text-danger">*</span></label>
                        <input type="text" name="nama" id="newCamNama" class="form-control" required placeholder="Dashcam Kabin EXC-07">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Posisi Pemasangan <span class="text-danger">*</span></label>
                        <input type="text" name="posisi" id="newCamPosisi" class="form-control" required value="Cabin Dashcam (Boom POV)">
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Tipe Sumber</label>
                            <select name="source_type" id="newCamType" class="form-select">
                                <option value="http" selected>HTTP MJPEG (Raspberry Pi Dashcam)</option>
                                <option value="rtsp">RTSP IP Camera</option>
                                <option value="video">File Video Lokal</option>
                                <option value="usb">USB Webcam</option>
                            </select>
                        </div>
                        <div class="col-6">
                            <label class="form-label small fw-semibold">FPS Target</label>
                            <input type="number" name="fps" id="newCamFps" class="form-control" required value="20" min="5" max="60">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Path / URL Stream <span class="text-danger">*</span></label>
                        <div class="input-group">
                            <input type="text" name="source_path" id="newCamPath" class="form-control" required value="http://heracam.local:8080/stream">
                            <button class="btn btn-outline-info" type="button" onclick="testModalField()">
                                <i class="bi bi-play-circle"></i> Tes
                            </button>
                        </div>
                        <div id="modalTestResult" class="mt-1 small" style="display:none;"></div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Resolusi</label>
                        <input type="text" name="resolusi" id="newCamRes" class="form-control" required value="1280x720">
                    </div>
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="is_primary" value="1" id="isPrim" checked>
                        <label class="form-check-label small fw-semibold" for="isPrim">Jadikan Feed Utama (Primary Feed)</label>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                    <button type="submit" class="btn btn-primary btn-sm">Simpan Kamera</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL TEST STREAM CONNECTION DIALOG -->
    <div class="modal fade" id="testStreamModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title fw-bold d-flex align-items-center gap-2">
                        <i class="bi bi-activity text-primary"></i>
                        <span>Diagnostik Stream Kamera</span>
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center py-4">
                    <div id="testStreamLoading">
                        <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                            <span class="visually-hidden">Memeriksa koneksi...</span>
                        </div>
                        <h6 class="fw-bold mb-1">Menghubungi Sumber Kamera...</h6>
                        <p class="text-secondary small font-monospace" id="testStreamTargetUrl">-</p>
                    </div>

                    <div id="testStreamSuccess" style="display:none;">
                        <div class="rounded-circle bg-success-subtle text-success d-inline-flex p-3 mb-3">
                            <i class="bi bi-check-circle-fill fs-2"></i>
                        </div>
                        <h5 class="fw-bold text-success mb-1">Koneksi Stream Online!</h5>
                        <p class="text-secondary small mb-3" id="testStreamSuccessMsg">-</p>
                        <div class="d-flex justify-content-center gap-3 p-3 bg-light rounded border text-start small mb-3">
                            <div>
                                <span class="text-secondary d-block">Status Jaringan:</span>
                                <strong class="text-success"><i class="bi bi-wifi"></i> Terhubung</strong>
                            </div>
                            <div class="border-start ps-3">
                                <span class="text-secondary d-block">Latensi Ping:</span>
                                <strong class="text-primary font-monospace" id="testStreamLatency">- ms</strong>
                            </div>
                        </div>
                    </div>

                    <div id="testStreamFail" style="display:none;">
                        <div class="rounded-circle bg-danger-subtle text-danger d-inline-flex p-3 mb-3">
                            <i class="bi bi-x-circle-fill fs-2"></i>
                        </div>
                        <h5 class="fw-bold text-danger mb-1">Koneksi Stream Terputus</h5>
                        <p class="text-secondary small mb-3" id="testStreamFailMsg">-</p>
                        <div class="alert alert-warning text-start small mb-0">
                            <strong>Petunjuk Lapangan:</strong>
                            <ul class="mb-0 ps-3 mt-1">
                                <li>Pastikan Raspberry Pi / IP Camera menyala dan tersambung ke Wi-Fi.</li>
                                <li>Cek apakah service <code>ustreamer</code> atau <code>mediamtx</code> aktif di Pi.</li>
                                <li>Pastikan laptop dan kamera berada dalam subnet jaringan yang sama.</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Tutup</button>
                </div>
            </div>
        </div>
    </div>

@endsection

@push('scripts')
<script>
    const TEST_URL = @json(route('master.kamera.test'));
    const CSRF_TOKEN = '{{ csrf_token() }}';

    function applyPreset(type) {
        if (type === 'rpi') {
            document.getElementById('newCamNama').value = 'Dashcam Pi Zero W (Cabin Front)';
            document.getElementById('newCamPosisi').value = 'Cabin Front Windshield';
            document.getElementById('newCamType').value = 'http';
            document.getElementById('newCamPath').value = 'http://192.168.1.40:8080/stream.mjpg';
            document.getElementById('newCamRes').value = '854x480';
            document.getElementById('newCamFps').value = 18;
        } else if (type === 'rtsp') {
            document.getElementById('newCamNama').value = 'CCTV Pit Bench Loading';
            document.getElementById('newCamPosisi').value = 'External Pit Mast';
            document.getElementById('newCamType').value = 'rtsp';
            document.getElementById('newCamPath').value = 'rtsp://192.168.1.50:8554/live';
            document.getElementById('newCamRes').value = '1920x1080';
            document.getElementById('newCamFps').value = 25;
        } else if (type === 'night') {
            document.getElementById('newCamNama').value = 'Dashcam Malam Ref';
            document.getElementById('newCamPosisi').value = 'Cabin Dashcam (Boom POV)';
            document.getElementById('newCamType').value = 'video';
            document.getElementById('newCamPath').value = 'video/night_dashcam.mp4';
            document.getElementById('newCamRes').value = '476x848';
            document.getElementById('newCamFps').value = 18;
        }
    }

    function testStreamConnection(path, type, name) {
        const modalEl = document.getElementById('testStreamModal');
        const modal = new bootstrap.Modal(modalEl);
        
        document.getElementById('testStreamLoading').style.display = 'block';
        document.getElementById('testStreamSuccess').style.display = 'none';
        document.getElementById('testStreamFail').style.display = 'none';
        document.getElementById('testStreamTargetUrl').textContent = path;
        modal.show();

        fetch(TEST_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': CSRF_TOKEN
            },
            body: JSON.stringify({ source_path: path, source_type: type })
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById('testStreamLoading').style.display = 'none';
            if (data.success) {
                document.getElementById('testStreamSuccess').style.display = 'block';
                document.getElementById('testStreamSuccessMsg').textContent = data.message;
                document.getElementById('testStreamLatency').textContent = data.latency_ms + ' ms';
            } else {
                document.getElementById('testStreamFail').style.display = 'block';
                document.getElementById('testStreamFailMsg').textContent = data.message;
            }
        })
        .catch(err => {
            document.getElementById('testStreamLoading').style.display = 'none';
            document.getElementById('testStreamFail').style.display = 'block';
            document.getElementById('testStreamFailMsg').textContent = 'Koneksi gagal atau request timeout.';
        });
    }

    function testModalField() {
        const path = document.getElementById('newCamPath').value;
        const type = document.getElementById('newCamType').value;
        const resBox = document.getElementById('modalTestResult');
        resBox.style.display = 'block';
        resBox.innerHTML = '<span class="spinner-border spinner-border-sm text-info"></span> Menguji...';

        fetch(TEST_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': CSRF_TOKEN
            },
            body: JSON.stringify({ source_path: path, source_type: type })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                resBox.innerHTML = `<span class="badge text-bg-success"><i class="bi bi-check-circle"></i> Online (${data.latency_ms} ms)</span>`;
            } else {
                resBox.innerHTML = `<span class="badge text-bg-danger"><i class="bi bi-x-circle"></i> ${data.message}</span>`;
            }
        })
        .catch(() => {
            resBox.innerHTML = `<span class="badge text-bg-danger"><i class="bi bi-x-circle"></i> Gagal menghubungi host</span>`;
        });
    }
</script>
@endpush
