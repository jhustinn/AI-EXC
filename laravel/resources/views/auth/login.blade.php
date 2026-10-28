<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login &middot; HERA AI-CCTV Pit Sarolangun</title>
    <!-- Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        :root {
            --bg-deep: #090d16;
            --bg-card: #111827;
            --border-card: #1f2937;
            --primary-accent: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --amber-accent: #f59e0b;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-deep);
            color: #f3f4f6;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-image: 
                radial-gradient(circle at 15% 20%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 80%, rgba(245, 158, 11, 0.07) 0%, transparent 45%),
                linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
            padding: 24px 16px;
        }

        .login-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05);
            width: 100%;
            max-width: 460px;
            overflow: hidden;
            position: relative;
        }

        .login-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #f59e0b, #3b82f6, #10b981);
        }

        .form-control, .form-check-input {
            background-color: #0b101b;
            border: 1px solid #283548;
            color: #f3f4f6;
            font-size: 0.925rem;
            border-radius: 8px;
            padding: 10px 14px;
        }

        .form-control:focus {
            background-color: #0d1424;
            border-color: var(--primary-accent);
            box-shadow: 0 0 0 3px var(--primary-glow);
            color: #ffffff;
        }

        .form-control::placeholder {
            color: #64748b;
            font-size: 0.875rem;
        }

        .input-group-text {
            background-color: #151e2e;
            border: 1px solid #283548;
            color: #94a3b8;
            border-radius: 8px;
        }

        .btn-submit {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border: 1px solid #3b82f6;
            color: #ffffff;
            font-weight: 600;
            padding: 11px 18px;
            border-radius: 8px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }

        .btn-submit:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e40af);
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.5);
            color: #ffffff;
            transform: translateY(-1px);
        }

        .demo-chip {
            background: #151e2e;
            border: 1px solid #283548;
            border-radius: 8px;
            padding: 8px 10px;
            cursor: pointer;
            transition: all 0.15s ease;
            text-align: left;
            font-size: 0.78rem;
            color: #cbd5e1;
        }

        .demo-chip:hover {
            background: #1e293b;
            border-color: #3b82f6;
            color: #ffffff;
            transform: translateY(-1px);
        }

        .mono {
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>

<div class="login-card">
    <div class="p-4 p-sm-5">
        <!-- Logo & Header -->
        <div class="text-center mb-4">
            <div class="d-inline-flex align-items-center justify-content-center bg-dark border border-secondary border-opacity-25 rounded-3 p-2 mb-3" style="width: 54px; height: 54px; box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);">
                <i class="bi bi-shield-check text-primary fs-2"></i>
            </div>
            <h4 class="fw-bold mb-1 tracking-tight text-white d-flex align-items-center justify-content-center gap-2">
                <span>HERA</span>
                <span class="badge text-bg-warning text-dark px-2 py-1 fs-6 fw-bold">AI-CCTV</span>
            </h4>
            <div class="text-secondary small">Heavy Equipment Realtime Activity</div>
            <div class="mt-2 text-secondary-emphasis" style="font-size: 0.78rem;">
                <i class="bi bi-geo-alt-fill text-danger me-1"></i> PT Caritas Energi Indonesia &bull; Pit Sarolangun
            </div>
        </div>

        <!-- Flash & Error Alert -->
        @if(session('success'))
            <div class="alert alert-success border-success border-opacity-25 py-2 px-3 small rounded-3 d-flex align-items-center gap-2 mb-3" style="background: rgba(16, 185, 129, 0.1); color: #34d399;">
                <i class="bi bi-check-circle-fill"></i>
                <div>{{ session('success') }}</div>
            </div>
        @endif

        @if($errors->any())
            <div class="alert alert-danger border-danger border-opacity-25 py-2 px-3 small rounded-3 d-flex align-items-center gap-2 mb-3" style="background: rgba(239, 68, 68, 0.1); color: #f87171;">
                <i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
                <div>
                    @foreach($errors->all() as $error)
                        <div>{{ $error }}</div>
                    @endforeach
                </div>
            </div>
        @endif

        <!-- Login Form -->
        <form action="{{ route('login') }}" method="POST" id="loginForm">
            @csrf

            <!-- Email -->
            <div class="mb-3">
                <label for="email" class="form-label small text-secondary fw-semibold">Email / Akun Personel</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                    <input type="email" 
                           class="form-control @error('email') is-invalid @enderror" 
                           id="email" 
                           name="email" 
                           value="{{ old('email', 'admin@herasystem.com') }}" 
                           placeholder="nama@herasystem.com" 
                           required 
                           autofocus>
                </div>
            </div>

            <!-- Password -->
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <label for="password" class="form-label small text-secondary fw-semibold mb-0">Kata Sandi</label>
                </div>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-key"></i></span>
                    <input type="password" 
                           class="form-control @error('password') is-invalid @enderror" 
                           id="password" 
                           name="password" 
                           value="password123" 
                           placeholder="Masukkan kata sandi..." 
                           required>
                    <button class="btn btn-outline-secondary border-start-0" type="button" id="togglePasswordBtn" style="background:#151e2e; border-color:#283548; color:#94a3b8;">
                        <i class="bi bi-eye" id="togglePasswordIcon"></i>
                    </button>
                </div>
            </div>

            <!-- Remember Me -->
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="remember" id="remember" checked>
                    <label class="form-check-label text-secondary small" for="remember">
                        Ingat sesi saya di perangkat ini
                    </label>
                </div>
            </div>

            <!-- Submit Button -->
            <button type="submit" class="btn btn-submit w-100 d-flex align-items-center justify-content-center gap-2 mb-4">
                <span>Masuk ke Dashboard Operasional</span>
                <i class="bi bi-arrow-right-short fs-5"></i>
            </button>
        </form>

        <!-- Demo Accounts Quick Switcher -->
        <div class="pt-3 border-top border-secondary border-opacity-25">
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="text-secondary" style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700;">
                    <i class="bi bi-lightning-charge-fill text-warning me-1"></i> Akun Demo Cepat
                </span>
                <span class="badge text-bg-dark border border-secondary border-opacity-50 mono" style="font-size: 0.65rem;">
                    PASS: password123
                </span>
            </div>

            <div class="d-flex flex-column gap-2">
                <!-- Admin -->
                <button type="button" class="demo-chip d-flex align-items-center justify-content-between" onclick="fillCredentials('admin@herasystem.com', 'password123')">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge text-bg-danger-subtle text-danger border border-danger-subtle px-2 py-1">Admin</span>
                        <div>
                            <div class="fw-semibold text-white">Hendra Setiawan, S.T.</div>
                            <div class="text-secondary" style="font-size: 0.7rem;">Mine Operations Superintendent</div>
                        </div>
                    </div>
                    <i class="bi bi-arrow-right text-secondary small"></i>
                </button>

                <!-- Supervisor -->
                <button type="button" class="demo-chip d-flex align-items-center justify-content-between" onclick="fillCredentials('supervisor@herasystem.com', 'password123')">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge text-bg-primary-subtle text-primary border border-primary-subtle px-2 py-1">Spv</span>
                        <div>
                            <div class="fw-semibold text-white">Bambang Pratama</div>
                            <div class="text-secondary" style="font-size: 0.7rem;">Foreman Shift Loading Pit B</div>
                        </div>
                    </div>
                    <i class="bi bi-arrow-right text-secondary small"></i>
                </button>

                <!-- Operator -->
                <button type="button" class="demo-chip d-flex align-items-center justify-content-between" onclick="fillCredentials('operator@herasystem.com', 'password123')">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge text-bg-success-subtle text-success border border-success-subtle px-2 py-1">Op</span>
                        <div>
                            <div class="fw-semibold text-white">Ahmad Fauzi</div>
                            <div class="text-secondary" style="font-size: 0.7rem;">Operator Senior Cat 395</div>
                        </div>
                    </div>
                    <i class="bi bi-arrow-right text-secondary small"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- Status Footer -->
    <div class="px-4 py-3 bg-black bg-opacity-40 border-top border-secondary border-opacity-25 d-flex justify-content-between align-items-center" style="font-size: 0.72rem;">
        <span class="d-flex align-items-center gap-1 text-secondary">
            <span class="spinner-grow spinner-grow-sm text-success" role="status" style="width: 6px; height: 6px;"></span>
            <span>AI YOLO11 v4.2 &bull; Active</span>
        </span>
        <span class="text-secondary">PostgreSQL 17 &bull; v2.4</span>
    </div>
</div>

<script>
    // Quick Demo autofill
    function fillCredentials(email, pass) {
        document.getElementById('email').value = email;
        document.getElementById('password').value = pass;
        // highlight briefly
        const emailEl = document.getElementById('email');
        emailEl.focus();
        emailEl.classList.add('border-primary');
        setTimeout(() => emailEl.classList.remove('border-primary'), 400);
    }

    // Toggle password visibility
    const toggleBtn = document.getElementById('togglePasswordBtn');
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePasswordIcon');

    toggleBtn.addEventListener('click', () => {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleIcon.classList.replace('bi-eye', 'bi-eye-slash');
        } else {
            passwordInput.type = 'password';
            toggleIcon.classList.replace('bi-eye-slash', 'bi-eye');
        }
    });
</script>

</body>
</html>
