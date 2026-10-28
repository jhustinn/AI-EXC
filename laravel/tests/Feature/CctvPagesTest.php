<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Tests\TestCase;

class CctvPagesTest extends TestCase
{
    use DatabaseTransactions;

    protected User $user;

    protected function setUp(): void
    {
        parent::setUp();
        $this->user = User::where('role', 'admin')->first() ?? User::first();
    }

    public function test_dashboard_page_loads_for_authenticated_user(): void
    {
        $response = $this->actingAs($this->user)->get('/dashboard');
        $response->assertStatus(200);
        $response->assertSee('Fleet Loading');
    }

    public function test_monitoring_live_grid_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/monitoring/live');
        $response->assertStatus(200);
        $response->assertSee('AI LIVE');
        $response->assertSee('/stream/1');
        $response->assertSee('/stream/2');
    }

    public function test_telemetry_cameras_endpoint_returns_json(): void
    {
        $response = $this->get('/api/telemetry/cameras');
        $response->assertStatus(200);
        $response->assertJsonStructure([
            'cameras' => [
                '*' => ['id', 'nama', 'source_type', 'source_path']
            ]
        ]);
    }

    public function test_monitoring_deteksi_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/monitoring/deteksi');
        $response->assertStatus(200);
    }

    public function test_monitoring_produktivitas_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/monitoring/produktivitas');
        $response->assertStatus(200);
    }

    public function test_master_unit_page_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/master/unit');
        $response->assertStatus(200);
        $response->assertSee('Armada Unit Alat Berat');
    }

    public function test_master_truck_page_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/master/truck');
        $response->assertStatus(200);
    }

    public function test_master_kamera_page_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/master/kamera');
        $response->assertStatus(200);
    }

    public function test_laporan_harian_page_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/laporan/harian');
        $response->assertStatus(200);
    }

    public function test_pengaturan_page_loads(): void
    {
        $response = $this->actingAs($this->user)->get('/pengaturan');
        $response->assertStatus(200);
    }

    public function test_export_csv_returns_streamed_attachment(): void
    {
        $response = $this->actingAs($this->user)->get('/monitoring/export-csv');
        $response->assertStatus(200);
        $response->assertHeader('content-type', 'text/csv; charset=UTF-8');
    }
}
