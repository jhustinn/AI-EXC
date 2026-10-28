<?php

namespace App\Http\Controllers;

use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class AuthController extends Controller
{
    /**
     * Tampilkan formulir login.
     */
    public function showLogin(): View|RedirectResponse
    {
        if (Auth::check()) {
            return redirect()->route('dashboard');
        }

        return view('auth.login');
    }

    /**
     * Proses autentikasi login.
     */
    public function login(Request $request): RedirectResponse
    {
        $credentials = $request->validate([
            'email' => ['required', 'string', 'email'],
            'password' => ['required', 'string'],
        ], [
            'email.required' => 'Alamat email wajib diisi.',
            'email.email' => 'Format email tidak valid.',
            'password.required' => 'Kata sandi wajib diisi.',
        ]);

        $remember = $request->boolean('remember');

        // Coba autentikasi dengan akun yang aktif
        if (Auth::attempt(array_merge($credentials, ['is_active' => true]), $remember)) {
            $request->session()->regenerate();

            $user = Auth::user();
            $intended = redirect()->intended(route('dashboard'))->getTargetUrl();
            if (str_contains($intended, '/api/')) {
                return redirect()->route('dashboard')
                    ->with('success', "Selamat datang kembali, {$user->name} ({$user->jabatan})");
            }

            return redirect()->to($intended)
                ->with('success', "Selamat datang kembali, {$user->name} ({$user->jabatan})");
        }

        return back()->withErrors([
            'email' => 'Email atau kata sandi tidak cocok, atau akun Anda dinonaktifkan.',
        ])->onlyInput('email');
    }

    /**
     * Proses keluar (logout).
     */
    public function logout(Request $request): RedirectResponse
    {
        Auth::logout();

        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('login')
            ->with('success', 'Anda telah berhasil keluar dari sistem HERA.');
    }
}
