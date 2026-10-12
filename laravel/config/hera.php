<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Alamat service Python (engine deteksi)
    |--------------------------------------------------------------------------
    | Laravel HANYA membaca dari service ini. Video tidak pernah di-proxy
    | lewat PHP karena koneksi MJPEG bersifat long-lived dan menahan worker.
    */

    'stream_url' => env('PYTHON_STREAM_URL', 'http://127.0.0.1:8001'),

    'api_url' => env('PYTHON_API_URL', 'http://127.0.0.1:8000'),

    'api_timeout' => (float) env('PYTHON_API_TIMEOUT', 5),

    'unit' => env('HERA_DEFAULT_UNIT', 'EXC-07'),

];