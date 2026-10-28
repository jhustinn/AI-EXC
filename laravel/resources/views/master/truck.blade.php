@extends('layouts.app')

@section('title', 'Master Data Dump Truck')
@section('breadcrumb', 'Master Data / Dump Truck')

@section('content')

    <!-- HEADER & ACTION -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark d-flex align-items-center gap-2">
                <i class="bi bi-truck text-primary"></i>
                <span>Data Armada Dump Truck Hauling</span>
            </h1>
            <p class="text-secondary small mb-0">Kelola daftar kendaraan angkut tambang, plat nomor polisi, kapasitas muat (ton), dan status operasional.</p>
        </div>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" data-bs-toggle="modal" data-bs-target="#addTruckModal">
            <i class="bi bi-plus-lg"></i> Tambah Dump Truck Baru
        </button>
    </div>

    <!-- SUMMARY METRIC CHIPS -->
    <div class="row g-3 mb-4">
        <div class="col-6 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-truck fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Armada Truk</div>
                    <div class="fs-4 fw-bold text-dark">{{ $trucks->count() }} Unit</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-check-circle-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Armada Aktif / Hauling</div>
                    <div class="fs-4 fw-bold text-dark">{{ $trucks->whereIn('status', ['ACTIVE', 'OPERASIONAL', 'HAULING'])->count() }} Unit</div>
                </div>
            </div>
        </div>

        <div class="col-12 col-md-4">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-warning-subtle text-warning-emphasis">
                    <i class="bi bi-speedometer2 fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Kapasitas Angkut</div>
                    <div class="fs-4 fw-bold text-dark">{{ $trucks->sum('kapasitas_ton') }} Ton</div>
                </div>
            </div>
        </div>
    </div>

    <!-- TRUCKS TABLE -->
    <div class="panel">
        <div class="panel-head d-flex justify-content-between align-items-center">
            <h2 class="panel-title"><i class="bi bi-truck text-primary"></i> Daftar Truk Tambang Terdaftar</h2>
            <span class="badge text-bg-light border text-secondary">{{ $trucks->count() }} Truk Terdaftar</span>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light small text-secondary">
                    <tr>
                        <th style="width: 45px;">#</th>
                        <th>Kode Truk</th>
                        <th>Plat Nomor</th>
                        <th>Merk &amp; Tipe Bak</th>
                        <th>Vendor / Kontraktor</th>
                        <th>Kapasitas Muat</th>
                        <th>Status</th>
                        <th class="text-end" style="width: 140px;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($trucks as $index => $t)
                        <tr>
                            <td class="text-secondary small">{{ $index + 1 }}</td>
                            <td>
                                <div class="d-flex align-items-center gap-2">
                                    <div class="bg-warning-subtle text-warning-emphasis p-2 rounded">
                                        <i class="bi bi-truck"></i>
                                    </div>
                                    <div>
                                        <strong class="d-block text-dark">{{ $t->kode_truk }}</strong>
                                        <small class="text-secondary">Hauling Fleet</small>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="badge text-bg-dark font-monospace px-2 py-1">
                                    {{ $t->no_polisi ?? 'NO PLATE' }}
                                </span>
                            </td>
                            <td class="small">{{ $t->merk_tipe }}</td>
                            <td class="small text-secondary">{{ $t->vendor }}</td>
                            <td><strong class="text-primary">{{ $t->kapasitas_ton }} Ton</strong></td>
                            <td>
                                @if(in_array($t->status, ['ACTIVE', 'OPERASIONAL', 'HAULING']))
                                    <span class="badge text-bg-success-subtle text-success border border-success-subtle">
                                        <i class="bi bi-check-circle-fill me-1"></i> {{ $t->status }}
                                    </span>
                                @elseif($t->status === 'STANDBY')
                                    <span class="badge text-bg-warning-subtle text-warning border border-warning-subtle">
                                        {{ $t->status }}
                                    </span>
                                @else
                                    <span class="badge text-bg-secondary-subtle text-secondary border">
                                        {{ $t->status }}
                                    </span>
                                @endif
                            </td>
                            <td class="text-end">
                                <button type="button" 
                                        class="btn btn-sm btn-outline-secondary me-1" 
                                        data-bs-toggle="modal" 
                                        data-bs-target="#editTruckModal{{ $t->id }}"
                                        title="Ubah Data">
                                    <i class="bi bi-pencil-fill"></i>
                                </button>
                                <button type="button" 
                                        class="btn btn-sm btn-outline-danger" 
                                        data-bs-toggle="modal" 
                                        data-bs-target="#deleteTruckModal{{ $t->id }}"
                                        title="Hapus Truk">
                                    <i class="bi bi-trash-fill"></i>
                                </button>
                            </td>
                        </tr>

                        <!-- MODAL EDIT TRUCK -->
                        <div class="modal fade" id="editTruckModal{{ $t->id }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered">
                                <form action="{{ route('master.truck.update', $t->id) }}" method="POST" class="modal-content">
                                    @csrf
                                    @method('PUT')
                                    <div class="modal-header">
                                        <h5 class="modal-title fw-bold">Ubah Dump Truck: {{ $t->kode_truk }}</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Kode Truk</label>
                                            <input type="text" class="form-control bg-light" value="{{ $t->kode_truk }}" readonly disabled>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Nomor Polisi (Plat)</label>
                                            <input type="text" name="no_polisi" class="form-control" value="{{ $t->no_polisi }}">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Merk &amp; Tipe Kendaraan</label>
                                            <input type="text" name="merk_tipe" class="form-control" value="{{ $t->merk_tipe }}" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label small fw-semibold">Vendor / Kontraktor</label>
                                            <input type="text" name="vendor" class="form-control" value="{{ $t->vendor }}" required>
                                        </div>
                                        <div class="row g-2 mb-3">
                                            <div class="col-6">
                                                <label class="form-label small fw-semibold">Kapasitas (Ton)</label>
                                                <input type="number" step="1" name="kapasitas_ton" class="form-control" value="{{ $t->kapasitas_ton }}" required min="5">
                                            </div>
                                            <div class="col-6">
                                                <label class="form-label small fw-semibold">Status Operasi</label>
                                                <select name="status" class="form-select">
                                                    <option value="ACTIVE" {{ $t->status === 'ACTIVE' ? 'selected' : '' }}>ACTIVE</option>
                                                    <option value="HAULING" {{ $t->status === 'HAULING' ? 'selected' : '' }}>HAULING</option>
                                                    <option value="STANDBY" {{ $t->status === 'STANDBY' ? 'selected' : '' }}>STANDBY</option>
                                                    <option value="MAINTENANCE" {{ $t->status === 'MAINTENANCE' ? 'selected' : '' }}>MAINTENANCE</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                                        <button type="submit" class="btn btn-primary btn-sm">Simpan Perubahan</button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        <!-- MODAL HAPUS TRUCK -->
                        <div class="modal fade" id="deleteTruckModal{{ $t->id }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered modal-sm">
                                <form action="{{ route('master.truck.destroy', $t->id) }}" method="POST" class="modal-content">
                                    @csrf
                                    @method('DELETE')
                                    <div class="modal-body text-center p-4">
                                        <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2 d-block"></i>
                                        <h6 class="fw-bold mb-1">Hapus Dump Truck?</h6>
                                        <p class="text-secondary small mb-3">Unit armada <strong>{{ $t->kode_truk }}</strong> akan dihapus permanen dari sistem.</p>
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
                                <i class="bi bi-truck fs-1 opacity-50 mb-2 d-block"></i>
                                Belum ada data dump truck terdaftar.
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    <!-- MODAL TAMBAH TRUCK -->
    <div class="modal fade" id="addTruckModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <form action="{{ route('master.truck.store') }}" method="POST" class="modal-content">
                @csrf
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">Daftarkan Dump Truck Baru</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Kode Truk (Contoh: DT-09) <span class="text-danger">*</span></label>
                        <input type="text" name="kode_truk" class="form-control" required placeholder="DT-09">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Nomor Polisi (Plat)</label>
                        <input type="text" name="no_polisi" class="form-control" placeholder="BH 8492 BM">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Merk &amp; Tipe Kendaraan <span class="text-danger">*</span></label>
                        <input type="text" name="merk_tipe" class="form-control" required value="Loxa Mining Dump Truck 6x4">
                    </div>
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Vendor / Pemilik <span class="text-danger">*</span></label>
                        <input type="text" name="vendor" class="form-control" required value="PT Caritas Energi Indonesia">
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Kapasitas Muatan (Ton) <span class="text-danger">*</span></label>
                            <input type="number" step="1" name="kapasitas_ton" class="form-control" required value="35" min="5">
                        </div>
                        <div class="col-6">
                            <label class="form-label small fw-semibold">Status Operasi</label>
                            <select name="status" class="form-select">
                                <option value="ACTIVE" selected>ACTIVE</option>
                                <option value="HAULING">HAULING</option>
                                <option value="STANDBY">STANDBY</option>
                                <option value="MAINTENANCE">MAINTENANCE</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Batal</button>
                    <button type="submit" class="btn btn-primary btn-sm">Simpan Dump Truck</button>
                </div>
            </form>
        </div>
    </div>

@endsection
