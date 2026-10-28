@extends('layouts.app')

@section('title', 'Manajemen Pengguna & Hak Akses')
@section('breadcrumb', 'Master Data / Manajemen Pengguna')

@section('content')

    <!-- Header & Action -->
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
            <h1 class="h4 mb-1 fw-bold text-dark d-flex align-items-center gap-2">
                <i class="bi bi-people-fill text-primary"></i>
                <span>Manajemen Pengguna & Personel</span>
            </h1>
            <p class="text-secondary small mb-0">Kelola akun personel operasional, hak akses role (Admin, Supervisor, Operator), dan kredensial login HERA.</p>
        </div>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-2 shadow-sm" data-bs-toggle="modal" data-bs-target="#addUserModal">
            <i class="bi bi-person-plus-fill"></i> Tambah Pengguna Baru
        </button>
    </div>

    <!-- Stats Summary Cards -->
    <div class="row g-3 mb-4">
        <div class="col-6 col-md-3 col-xl">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-people fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Total Akun</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['total'] }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3 col-xl">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-danger-subtle text-danger">
                    <i class="bi bi-shield-lock-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Administrator</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['admin'] }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3 col-xl">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-primary-subtle text-primary">
                    <i class="bi bi-person-badge-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Supervisor</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['supervisor'] }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3 col-xl">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-person-workspace fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Operator</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['operator'] }}</div>
                </div>
            </div>
        </div>

        <div class="col-6 col-md-3 col-xl">
            <div class="panel p-3 d-flex align-items-center gap-3">
                <div class="rounded-3 p-3 bg-success-subtle text-success">
                    <i class="bi bi-check-circle-fill fs-4"></i>
                </div>
                <div>
                    <div class="text-secondary small fw-medium">Akun Aktif</div>
                    <div class="fs-4 fw-bold text-dark">{{ $stats['active'] }}</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Filter & Search Toolbar -->
    <div class="panel p-3 mb-4">
        <form method="GET" action="{{ route('master.user') }}" class="row g-2 align-items-center">
            <div class="col-12 col-md-4">
                <div class="input-group input-group-sm">
                    <span class="input-group-text bg-white border-end-0 text-secondary"><i class="bi bi-search"></i></span>
                    <input type="text" name="search" class="form-control border-start-0" placeholder="Cari nama, email, jabatan..." value="{{ $searchQuery }}">
                </div>
            </div>
            <div class="col-6 col-md-3">
                <select name="role" class="form-select form-select-sm" onchange="this.form.submit()">
                    <option value="">Semua Peran (Role)</option>
                    <option value="admin" {{ $currentRole === 'admin' ? 'selected' : '' }}>Administrator</option>
                    <option value="supervisor" {{ $currentRole === 'supervisor' ? 'selected' : '' }}>Supervisor</option>
                    <option value="operator" {{ $currentRole === 'operator' ? 'selected' : '' }}>Operator</option>
                </select>
            </div>
            <div class="col-6 col-md-auto d-flex gap-2">
                <button type="submit" class="btn btn-sm btn-outline-secondary">Terapkan</button>
                @if($searchQuery || $currentRole)
                    <a href="{{ route('master.user') }}" class="btn btn-sm btn-link text-secondary">Reset</a>
                @endif
            </div>
        </form>
    </div>

    <!-- Users Table Panel -->
    <div class="panel">
        <div class="panel-head d-flex justify-content-between align-items-center">
            <h2 class="panel-title mb-0">Daftar Akun Personel</h2>
            <span class="badge text-bg-light border text-secondary">{{ count($users) }} Akun Terdaftar</span>
        </div>
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="table-light small text-secondary">
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>Personel</th>
                        <th>Peran (Role)</th>
                        <th>Jabatan & Penugasan</th>
                        <th>Status</th>
                        <th>Terdaftar Sejak</th>
                        <th class="text-end" style="width: 140px;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($users as $index => $u)
                        <tr>
                            <td class="text-secondary small">{{ $index + 1 }}</td>
                            <td>
                                <div class="d-flex align-items-center gap-3">
                                    <div class="rounded-circle d-flex align-items-center justify-content-center fw-bold shadow-sm {{ $u->role === 'admin' ? 'bg-danger-subtle text-danger' : ($u->role === 'supervisor' ? 'bg-primary-subtle text-primary' : 'bg-success-subtle text-success') }}" 
                                         style="width: 38px; height: 38px; font-size: 13px;">
                                        {{ $u->initials() }}
                                    </div>
                                    <div>
                                        <div class="fw-bold text-dark d-flex align-items-center gap-2">
                                            <span>{{ $u->name }}</span>
                                            @if($u->id === Auth::id())
                                                <span class="badge text-bg-secondary" style="font-size: 10px;">Anda</span>
                                            @endif
                                        </div>
                                        <div class="text-secondary small mono" style="font-size: 12px;">{{ $u->email }}</div>
                                    </div>
                                </div>
                            </td>
                            <td>
                                {!! $u->roleBadge() !!}
                            </td>
                            <td>
                                <div class="small fw-semibold text-dark">{{ $u->jabatan ?? '-' }}</div>
                                <div class="text-secondary small" style="font-size: 11px;">PT Caritas Energi Indonesia</div>
                            </td>
                            <td>
                                @if($u->is_active)
                                    <span class="badge text-bg-success-subtle text-success border border-success-subtle">
                                        <i class="bi bi-check-circle-fill me-1"></i> Aktif
                                    </span>
                                @else
                                    <span class="badge text-bg-secondary-subtle text-secondary border border-secondary-subtle">
                                        <i class="bi bi-slash-circle me-1"></i> Nonaktif
                                    </span>
                                @endif
                            </td>
                            <td class="small text-secondary">
                                {{ $u->created_at ? $u->created_at->format('d M Y') : 'Default' }}
                            </td>
                            <td class="text-end">
                                <button class="btn btn-sm btn-outline-secondary me-1" 
                                        data-bs-toggle="modal" 
                                        data-bs-target="#editUserModal{{ $u->id }}"
                                        title="Ubah Data">
                                    <i class="bi bi-pencil-fill"></i>
                                </button>

                                @if($u->id !== Auth::id())
                                    <button class="btn btn-sm btn-outline-danger" 
                                            data-bs-toggle="modal" 
                                            data-bs-target="#deleteUserModal{{ $u->id }}"
                                            title="Hapus Akun">
                                        <i class="bi bi-trash-fill"></i>
                                    </button>
                                @else
                                    <button class="btn btn-sm btn-outline-secondary disabled" title="Tidak dapat menghapus akun sendiri">
                                        <i class="bi bi-lock-fill"></i>
                                    </button>
                                @endif
                            </td>
                        </tr>

                        <!-- Modal Edit User -->
                        <div class="modal fade" id="editUserModal{{ $u->id }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered">
                                <div class="modal-content">
                                    <form action="{{ route('master.user.update', $u->id) }}" method="POST">
                                        @csrf
                                        @method('PUT')
                                        <div class="modal-header">
                                            <h5 class="modal-title fw-bold">Ubah Akun Personel</h5>
                                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                        </div>
                                        <div class="modal-body">
                                            <div class="mb-3">
                                                <label class="form-label small fw-semibold">Nama Lengkap</label>
                                                <input type="text" name="name" class="form-control" value="{{ $u->name }}" required>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label small fw-semibold">Alamat Email</label>
                                                <input type="email" name="email" class="form-control" value="{{ $u->email }}" required>
                                            </div>
                                            <div class="row g-2 mb-3">
                                                <div class="col-md-6">
                                                    <label class="form-label small fw-semibold">Hak Akses (Role)</label>
                                                    <select name="role" class="form-select" required>
                                                        <option value="admin" {{ $u->role === 'admin' ? 'selected' : '' }}>Administrator (Akses Penuh)</option>
                                                        <option value="supervisor" {{ $u->role === 'supervisor' ? 'selected' : '' }}>Supervisor (Monitoring & Laporan)</option>
                                                        <option value="operator" {{ $u->role === 'operator' ? 'selected' : '' }}>Operator (Dashboard & View)</option>
                                                    </select>
                                                </div>
                                                <div class="col-md-6">
                                                    <label class="form-label small fw-semibold">Jabatan / Posisi</label>
                                                    <input type="text" name="jabatan" class="form-control" value="{{ $u->jabatan }}" placeholder="Contoh: Foreman Pit B">
                                                </div>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label small fw-semibold">Kata Sandi Baru (Kosongkan jika tidak diubah)</label>
                                                <input type="password" name="password" class="form-control" placeholder="Minimal 6 karakter">
                                            </div>
                                            <div class="form-check form-switch mt-3">
                                                <input class="form-check-input" type="checkbox" name="is_active" value="1" id="isActiveEdit{{ $u->id }}" {{ $u->is_active ? 'checked' : '' }} {{ $u->id === Auth::id() ? 'disabled' : '' }}>
                                                <label class="form-check-label small fw-semibold" for="isActiveEdit{{ $u->id }}">
                                                    Akun Aktif (Dapat Login ke HERA)
                                                </label>
                                                @if($u->id === Auth::id())
                                                    <input type="hidden" name="is_active" value="1">
                                                    <div class="form-text text-secondary" style="font-size: 11px;">Anda sedang menggunakan akun ini, status aktif dikunci.</div>
                                                @endif
                                            </div>
                                        </div>
                                        <div class="modal-footer">
                                            <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
                                            <button type="submit" class="btn btn-sm btn-primary">Simpan Perubahan</button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>

                        <!-- Modal Hapus User -->
                        @if($u->id !== Auth::id())
                            <div class="modal fade" id="deleteUserModal{{ $u->id }}" tabindex="-1" aria-hidden="true">
                                <div class="modal-dialog modal-dialog-centered modal-sm">
                                    <div class="modal-content">
                                        <form action="{{ route('master.user.destroy', $u->id) }}" method="POST">
                                            @csrf
                                            @method('DELETE')
                                            <div class="modal-body text-center p-4">
                                                <i class="bi bi-exclamation-triangle-fill text-danger fs-1 mb-2 d-block"></i>
                                                <h6 class="fw-bold mb-1">Hapus Pengguna?</h6>
                                                <p class="text-secondary small mb-3">Akun <strong>{{ $u->name }}</strong> ({{ $u->email }}) akan dihapus secara permanen dari sistem.</p>
                                                <div class="d-flex justify-content-center gap-2">
                                                    <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
                                                    <button type="submit" class="btn btn-sm btn-danger">Ya, Hapus</button>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
                        @endif

                    @empty
                        <tr>
                            <td colspan="7" class="text-center py-5 text-secondary">
                                <i class="bi bi-people fs-1 text-secondary opacity-50 mb-2 d-block"></i>
                                Tidak ditemukan data pengguna sesuai kriteria pencarian.
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal Tambah User -->
    <div class="modal fade" id="addUserModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <form action="{{ route('master.user.store') }}" method="POST">
                    @csrf
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">Tambah Akun Personel Baru</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label small fw-semibold">Nama Lengkap <span class="text-danger">*</span></label>
                            <input type="text" name="name" class="form-control" placeholder="Contoh: Hendra Pratama, S.T." required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-semibold">Alamat Email <span class="text-danger">*</span></label>
                            <input type="email" name="email" class="form-control" placeholder="nama@herasystem.com" required>
                        </div>
                        <div class="row g-2 mb-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold">Hak Akses (Role) <span class="text-danger">*</span></label>
                                <select name="role" class="form-select" required>
                                    <option value="operator" selected>Operator (View & Telemetri)</option>
                                    <option value="supervisor">Supervisor (Monitoring & Laporan)</option>
                                    <option value="admin">Administrator (Akses Penuh)</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-semibold">Jabatan / Posisi</label>
                                <input type="text" name="jabatan" class="form-control" placeholder="Contoh: Dispatch Pit A">
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-semibold">Kata Sandi Awal <span class="text-danger">*</span></label>
                            <input type="password" name="password" class="form-control" placeholder="Minimal 6 karakter" required>
                        </div>
                        <div class="form-check form-switch mt-3">
                            <input class="form-check-input" type="checkbox" name="is_active" value="1" id="isActiveNew" checked>
                            <label class="form-check-label small fw-semibold" for="isActiveNew">
                                Aktifkan Akun Segera
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Batal</button>
                        <button type="submit" class="btn btn-sm btn-primary">Tambah Akun</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

@endsection
