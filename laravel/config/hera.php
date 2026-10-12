<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Alamat service Python (engine deteksi)
    |--------------------------------------------------------------------------
    |
    | API data dan stream MJPEG dilayani satu proses FastAPI di port 8010.
    | Port 8000 dipakai aplikasi lain di mesin ini, jadi digeser ke 8010.
    |
    | Video TIDAK pernah di-proxy lewat PHP. Browserconnects langsung ke
    | server MJPEG milik Python. Koneksi MJPEG bersifat panjang-menempel
    | (long-lived) dan akan menahan worker PHP kalau diproxy.
    |
    */

    'api_url' => env('PYTHON_API_URL', 'http://127.0.0.1:8010'),

    'stream_url' => env('PYTHON_STREAM_URL', 'http://127.0.0.1:8010'),

    'api_timeout' => (int) env('PYTHON_API_TIMEOUT', 5),

    'unit' => env('HERA_DEFAULT_UNIT', 'EXC-07'),

];