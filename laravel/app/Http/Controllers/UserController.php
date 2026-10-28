<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;
use Illuminate\View\View;

class UserController extends Controller
{
    /**
     * Tampilkan daftar seluruh pengguna sistem HERA.
     */
    public function index(Request $request): View
    {
        $query = User::query();

        // Filter role
        if ($request->filled('role')) {
            $query->where('role', $request->role);
        }

        // Pencarian nama atau email
        if ($request->filled('search')) {
            $s = $request->search;
            $query->where(function ($q) use ($s) {
                $q->where('name', 'ilike', "%{$s}%")
                  ->orWhere('email', 'ilike', "%{$s}%")
                  ->orWhere('jabatan', 'ilike', "%{$s}%");
            });
        }

        $users = $query->orderBy('role')->orderBy('name')->get();

        $stats = [
            'total' => User::count(),
            'admin' => User::where('role', 'admin')->count(),
            'supervisor' => User::where('role', 'supervisor')->count(),
            'operator' => User::where('role', 'operator')->count(),
            'active' => User::where('is_active', true)->count(),
        ];

        return view('master.user', [
            'breadcrumb' => 'Master Data / Manajemen Pengguna',
            'users' => $users,
            'stats' => $stats,
            'currentRole' => $request->role,
            'searchQuery' => $request->search,
        ]);
    }

    /**
     * Tambahkan pengguna baru.
     */
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'email', 'max:255', 'unique:users,email'],
            'password' => ['required', 'string', 'min:6'],
            'role' => ['required', 'in:admin,supervisor,operator'],
            'jabatan' => ['nullable', 'string', 'max:150'],
            'is_active' => ['nullable', 'boolean'],
        ], [
            'name.required' => 'Nama lengkap wajib diisi.',
            'email.required' => 'Email wajib diisi.',
            'email.unique' => 'Email ini sudah terdaftar di sistem.',
            'password.required' => 'Kata sandi wajib diisi.',
            'password.min' => 'Kata sandi minimal 6 karakter.',
            'role.required' => 'Hak akses (role) wajib dipilih.',
        ]);

        User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => Hash::make($validated['password']),
            'role' => $validated['role'],
            'jabatan' => $validated['jabatan'] ?? 'Staff Operasional',
            'is_active' => $request->has('is_active'),
        ]);

        return redirect()->route('master.user')
            ->with('success', "Pengguna {$validated['name']} ({$validated['email']}) berhasil ditambahkan.");
    }

    /**
     * Perbarui data pengguna yang ada.
     */
    public function update(Request $request, $id): RedirectResponse
    {
        $user = User::findOrFail($id);

        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'email', 'max:255', Rule::unique('users', 'email')->ignore($user->id)],
            'password' => ['nullable', 'string', 'min:6'],
            'role' => ['required', 'in:admin,supervisor,operator'],
            'jabatan' => ['nullable', 'string', 'max:150'],
            'is_active' => ['nullable', 'boolean'],
        ], [
            'name.required' => 'Nama lengkap wajib diisi.',
            'email.required' => 'Email wajib diisi.',
            'email.unique' => 'Email ini sudah digunakan oleh akun lain.',
            'password.min' => 'Kata sandi baru minimal 6 karakter.',
            'role.required' => 'Hak akses (role) wajib dipilih.',
        ]);

        // Pencegahan: User tidak bisa menonaktifkan akunnya sendiri jika sedang login
        if ($user->id === Auth::id() && !$request->has('is_active')) {
            return back()->with('error', 'Anda tidak dapat menonaktifkan akun Anda sendiri saat sedang login.');
        }

        $user->name = $validated['name'];
        $user->email = $validated['email'];
        $user->role = $validated['role'];
        $user->jabatan = $validated['jabatan'] ?? $user->jabatan;
        $user->is_active = $request->has('is_active');

        if (!empty($validated['password'])) {
            $user->password = Hash::make($validated['password']);
        }

        $user->save();

        return redirect()->route('master.user')
            ->with('success', "Data pengguna {$user->name} berhasil diperbarui.");
    }

    /**
     * Hapus akun pengguna.
     */
    public function destroy($id): RedirectResponse
    {
        $user = User::findOrFail($id);

        // Jangan izinkan user menghapus dirinya sendiri
        if ($user->id === Auth::id()) {
            return back()->with('error', 'Anda tidak dapat menghapus akun Anda sendiri.');
        }

        // Cek jika ini admin terakhir
        if ($user->role === 'admin' && User::where('role', 'admin')->count() <= 1) {
            return back()->with('error', 'Tidak dapat menghapus Administrator utama terakhir dalam sistem.');
        }

        $userName = $user->name;
        $user->delete();

        return redirect()->route('master.user')
            ->with('success', "Pengguna {$userName} telah berhasil dihapus dari sistem.");
    }
}
