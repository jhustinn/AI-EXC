@extends('layouts.app')

@section('title', 'Master Data Unit Alat Berat')
@section('breadcrumb', 'Master Data / Unit Alat Berat')

@section('content')

    <!-- HEADER & ACTION -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark d-flex align-items-center gap-2">
                <i class="bi bi-truck-front-fill text-primary"></i>
                <span>Data Armada Unit Alat Berat (Excavator Fleet)</span>
            </h1>
            <p class="text-secondary small mb-0">Kelola daftar unit ekskavator, kapasitas bucket, lokasi pit penugasan, dan operator penanggung jawab.</p>
        </div>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" data-bs-toggle="modal" data-bs-target="#addUnitModal">
            <i class="bi bi-plus-lg"></i> Tambah Unit Baru
        </button>
    </div>

    <!-- SUMMARY METRIC CHIPS -->
    <div class="row g-3 mb-4">
        <div class="col-6 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-truck-front fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Armada Ekskavator</div>
                    <div class="fs-4 fw-bold text-dark">{{ $units->count() }} Unit</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-check-circle-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Unit Beroperasi (Loading)</div>
                    <div class="fs-4 fw-bold text-dark">{{ $units->where('status', 'OPERATIONAL')->count() }} Unit</div>
                </div>
            </div>
        </div>

        <div class="col-12 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-info-subtle text-info">
                    <i class="bi bi-box-seam fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Kapasitas Bucket</div>
                    <div class="fs-4 fw-bold text-dark">{{ $units->sum('kapasitas_bucket_m3') }} m&sup3;</div>
                </div>
            </div>
        </div>
    </div>

    <!-- UNITS GRID -->
    <div class="row g-3">
        @foreach($units as $u)
            <div class="col-12 col-md-6 col-xl-4">
                <div class="panel h-100 d-flex flex-column">
                    <div class="panel-head">
                        <div class="d-flex align-items-center gap-2">
                            <i class="bi bi-truck-front-fill text-primary fs-5"></i>
                            <h2 class="panel-title">{{ $u->kode_unit }}</h2>
                        </div>
                        <span class="badge {{ $u->status === 'OPERATIONAL' ? 'text-bg-success-subtle text-success border border-success-subtle' : 'text-bg-warning-subtle text-warning-emphasis' }}">
                            {{ $u->status }}
                        </span>
                    </div>
                    <div class="p-3 flex-grow-1 d-flex flex-column justify-content-between">
                        <div>
                            <h5 class="fw-bold mb-1 text-dark">{{ $u->nama }}</h5>
                            <p class="text-secondary small mb-3">{{ $u->keterangan ?? 'Unit operasional tambang PT CEI.' }}</p>

                            <table class="table table-sm table-borderless small mb-3">
                                <tbody>
                                    <tr>
                                        <td class="text-secondary">Merk &amp; Model</td>
                                        <td class="text-end fw-semibold">{{ $u->merk }} {{ $u->model }}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Kapasitas Bucket</td>
                                        <td class="text-end fw-semibold text-primary">{{ $u->kapasitas_bucket_m3 }} m&sup3;</td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Lokasi Pit</td>
                                        <td class="text-end fw-semibold">{{ $u->lokasi_pit }}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Operator</td>
                                        <td class="text-end fw-semibold">{{ $u->operator ?? '-' }}</td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Pola Deteksi AI</td>
                                        <td class="text-end fw-semibold">
                                            @if($u->detectionProfile)
                                                <a href="{{ route('master.pattern') }}" class="badge text-bg-primary-subtle text-primary border border-primary-subtle text-decoration-none" title="{{ $u->detectionProfile->deskripsi }}">
                                                    <i class="bi bi-diagram-3-fill me-1"></i> {{ $u->detectionProfile->nama }}
                                                </a>
                                            @else
                                                <a href="{{ route('master.pattern') }}" class="badge text-bg-secondary-subtle text-secondary border text-decoration-none">
                                                    Default Pit
                                                </a>
                                            @endif
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Kamera Terhubung</td>
                                        <td class="text-end fw-semibold">
                                            <span class="badge text-bg-light border text-dark">{{ $u->cameras_count }} Kamera</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="text-secondary">Total Siklus Selesai</td>
                                        <td class="text-end fw-semibold">
                                            <span class="badge text-bg-light border text-dark">{{ $u->cycles_count }} Siklus</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div class="d-flex gap-2 border-top pt-3">
                            <a href="{{ route('dashboard', ['unit' => $u->kode_unit]) }}" class="btn btn-outline-primary btn-sm flex-grow-1">
                                <i class="bi bi-speedometer2"></i> Dashboard
                            </a>
                            <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#editUnitModal{{ $u->id }}" title="Ubah Unit">
                                <i class="bi bi-pencil-fill"></i>
                            </button>
                            <button type="button" class="btn btn-outline-danger btn-sm" data-bs-toggle="modal" data-bs-target="#deleteUnitModal{{ $u->id }}" title="Hapus Unit">
                                <i class="bi bi-trash-fill"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- MODAL EDIT UNIT -->
            <div class="modal fade" id="editUnitModal{{ $u->id }}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <form action="{{ route('master.unit.update', $u->id) }}" method="POST" class="modal-content">
                        @csrf
                        @method('PUT')
                        <div class="modal-header">
                            <h5 class="modal-title fw-bold">Ubah Data Unit: {{ $u->kode_unit }}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Kode Unit</label>
                                <input type="text" class="form-control bg-light" value="{{ $u->kode_unit }}" readonly disabled>
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Nama Unit</label>
                                <input type="text" name="nama" class="form-control" value="{{ $u->nama }}" required>
                            </div>
                            <div class="row g-2 mb-3">
                                <div class="col-6">
                                    <label class="form-label small fw-semibold">Merk</label>
                                    <input type="text" name="merk" class="form-control" value="{{ $u->merk }}" required>
                                </div>
                                <div class="col-6">
                                    <label class="form-label small fw-semibold">Model</label>
                                    <input type="text" name="model" class="form-control" value="{{ $u->model }}" required>
                                </div>
                            </div>
                            <div class="row g-2 mb-3">
                                <div class="col-6">
                                    <label class="form-label small fw-semibold">Kapasitas Bucket (m&sup3;)</label>
                                    <input type="number" step="0.1" name="kapasitas_bucket_m3" class="form-control" value="{{ $u->kapasitas_bucket_m3 }}" required min="0.5">
                                </div>
                                <div class="col-6">
                                    <label class="form-label small fw-semibold">Status Operasi</label>
                                    <select name="status" class="form-select">
                                        <option value="OPERATIONAL" {{ $u->status === 'OPERATIONAL' ? 'selected' : '' }}>OPERATIONAL</option>
                                        <option value="IDLE" {{ $u->status === 'IDLE' ? 'selected' : '' }}>IDLE</option>
                                        <option value="STANDBY" {{ $u->status === 'STANDBY' ? 'selected' : '' }}>STANDBY</option>
                                        <option value="MAINTENANCE" {{ $u->status === 'MAINTENANCE' ? 'selected' : '' }}>MAINTENANCE</option>
                                    </select>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Lokasi Pit</label>
                                <input type="text" name="lokasi_pit" class="form-control" value="{{ $u->lokasi_pit }}" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label small fw-semibold">Operator Penanggung Jawab</label>
                                <input type="text" name="operator" class="form-control" value="{{ $u->operator }}">
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                            <button type="submit" class="btn btn-primary btn-sm">Simpan Perubahan</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- MODAL HAPUS UNIT -->
            <div class="modal fade" id="deleteUnitModal{{ $u->id }}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-sm">
                    <form action="{{ route('master.unit.destroy', $u->id) }}" method="POST" class="modal-content">
                        @csrf
                        @method('DELETE')
                        <div class="modal-body text-center p-4">
                            <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2 d-block"></i>
                            <h6 class="fw-bold mb-1">Hapus Unit {{ $u->kode_unit }}?</h6>
                            <p class="text-secondary small mb-3">Unit armada <strong>{{ $u->nama }}</strong> akan dihapus permanen.</p>
                            @if($u->cameras_count > 0 || $u->cycles_count > 0)
                                <div class="alert alert-warning small text-start p-2 mb-3">
                                    <i class="bi bi-info-circle me-1"></i> Unit masih memiliki {{ $u->cameras_count }} kamera atau {{ $u->cycles_count }} log siklus kerja.
                                </div>
                            @endif
                            <div class="d-flex justify-content-center gap-2">
                                <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
                                <button type="submit" class="btn btn-sm btn-danger" {{ ($u->cameras_count > 0 || $u->cycles_count > 0) ? 'disabled' : '' }}>
                                    Ya, Hapus
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>

        @endforeach
    </div>

    <!-- MODAL TAMBAH UNIT -->
    <div class="modal fade" id="addUnitModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <form action="{{ route('master.unit.store') }}" method="POST" class="modal-content">
                @csrf
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">Tambah Unit Alat Berat Baru</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Kode Unit (Contoh: EXC-08) <span class="text-danger">*</span></label>
                        <input type="text" name="kode_unit" class="form-control" required placeholder="EXC-08">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Nama Unit <span class="text-danger">*</span></label>
                        <input type="text" name="nama" class="form-control" required placeholder="Excavator Cat 395 Pit C">
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Merk <span class="text-danger">*</span></label>
                            <input type="text" name="merk" class="form-control" required value="Caterpillar">
                        </div>
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Model <span class="text-danger">*</span></label>
                            <input type="text" name="model" class="form-control" required value="395">
                        </div>
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Kapasitas Bucket (m&sup3;) <span class="text-danger">*</span></label>
                            <input type="number" step="0.1" name="kapasitas_bucket_m3" class="form-control" required value="6.5" min="0.5">
                        </div>
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Status Operasi</label>
                            <select name="status" class="form-select">
                                <option value="OPERATIONAL" selected>OPERATIONAL</option>
                                <option value="IDLE">IDLE</option>
                                <option value="STANDBY">STANDBY</option>
                                <option value="MAINTENANCE">MAINTENANCE</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Lokasi Pit <span class="text-danger">*</span></label>
                        <input type="text" name="lokasi_pit" class="form-control" required value="Pit Sarolangun Block B">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Operator Penanggung Jawab</label>
                        <input type="text" name="operator" class="form-control" placeholder="Nama Operator">
                    </div>
                    <input type="hidden" name="jenis" value="Excavator">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                    <button type="submit" class="btn btn-primary btn-sm">Simpan Unit</button>
                </div>
            </form>
        </div>
    </div>

@endsection
