<?php

namespace Tests\Feature;

use App\Models\DetectionProfile;
use App\Models\Unit;
use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Tests\TestCase;

class DetectionProfileTest extends TestCase
{
    use DatabaseTransactions;

    protected User $user;

    protected function setUp(): void
    {
        parent::setUp();
        $this->user = User::where('role', 'admin')->first() ?? User::first();
    }

    public function test_pattern_master_page_loads_for_authenticated_user(): void
    {
        $response = $this->actingAs($this->user)->get('/master/pattern');
        $response->assertStatus(200);
        $response->assertSee('Master Pola Detektor, Triggers');
        $response->assertSee('PROF-CAT395-BOOM');
    }

    public function test_can_create_new_detection_profile(): void
    {
        $payload = [
            'kode_profil' => 'PROF-TEST-UNIT-01',
            'nama' => 'Test Profile Unit',
            'tipe_alat' => 'Excavator Medium',
            'deskripsi' => 'Automated test profile',
            'bucket_confidence' => 0.40,
            'bucket_low_ratio' => 0.65,
            'truck_confidence' => 0.50,
            'truck_hold_seconds' => 2.5,
            'truck_min_width_ratio' => 0.15,
            'arm_confidence' => 0.35,
            'arm_swing_threshold' => 0.08,
            'plate_confidence' => 0.45,
            'plate_ocr_enabled' => 1,
            'motion_threshold' => 0.06,
            'dig_min_seconds' => 2.0,
            'dump_min_seconds' => 1.8,
            'phase_min_seconds' => 0.6,
            'idle_seconds' => 12.0,
            'zona_gali_x1' => 0.05,
            'zona_gali_y1' => 0.45,
            'zona_gali_x2' => 0.95,
            'zona_gali_y2' => 0.98,
            'dump_top_ratio' => 0.08,
            'dump_height_ratio' => 0.40,
        ];

        $response = $this->actingAs($this->user)->post('/master/pattern', $payload);
        $response->assertRedirect('/master/pattern');
        $response->assertSessionHas('success');

        $this->assertDatabaseHas('detection_profiles', [
            'kode_profil' => 'PROF-TEST-UNIT-01',
            'nama' => 'Test Profile Unit',
            'bucket_confidence' => 0.40,
        ]);
    }

    public function test_can_update_existing_detection_profile(): void
    {
        $profile = DetectionProfile::first();
        $this->assertNotNull($profile);

        $payload = [
            'nama' => 'Updated Profile Name',
            'tipe_alat' => 'Excavator Heavy Update',
            'deskripsi' => 'Updated description',
            'bucket_confidence' => 0.42,
            'bucket_low_ratio' => 0.60,
            'truck_confidence' => 0.55,
            'truck_hold_seconds' => 3.0,
            'truck_min_width_ratio' => 0.12,
            'arm_confidence' => 0.38,
            'arm_swing_threshold' => 0.07,
            'plate_confidence' => 0.48,
            'plate_ocr_enabled' => 1,
            'motion_threshold' => 0.05,
            'dig_min_seconds' => 2.2,
            'dump_min_seconds' => 2.0,
            'phase_min_seconds' => 0.8,
            'idle_seconds' => 10.0,
            'zona_gali_x1' => 0.10,
            'zona_gali_y1' => 0.50,
            'zona_gali_x2' => 0.90,
            'zona_gali_y2' => 0.95,
            'dump_top_ratio' => 0.06,
            'dump_height_ratio' => 0.35,
        ];

        $response = $this->actingAs($this->user)->put("/master/pattern/{$profile->id}", $payload);
        $response->assertRedirect('/master/pattern');
        $response->assertSessionHas('success');

        $this->assertDatabaseHas('detection_profiles', [
            'id' => $profile->id,
            'nama' => 'Updated Profile Name',
            'bucket_confidence' => 0.42,
        ]);
    }

    public function test_cannot_delete_default_profile(): void
    {
        $defaultProfile = DetectionProfile::where('is_default', true)->first();
        $this->assertNotNull($defaultProfile);

        $response = $this->actingAs($this->user)->delete("/master/pattern/{$defaultProfile->id}");
        $response->assertRedirect('/master/pattern');
        $response->assertSessionHas('error');

        $this->assertDatabaseHas('detection_profiles', [
            'id' => $defaultProfile->id,
        ]);
    }

    public function test_can_assign_profile_to_unit(): void
    {
        $unit = Unit::first();
        $profile = DetectionProfile::first();
        $this->assertNotNull($unit);
        $this->assertNotNull($profile);

        $response = $this->actingAs($this->user)->post('/master/pattern/assign-unit', [
            'unit_id' => $unit->id,
            'profile_id' => $profile->id,
        ]);

        $response->assertRedirect('/master/pattern');
        $response->assertSessionHas('success');

        $this->assertDatabaseHas('units', [
            'id' => $unit->id,
            'detection_profile_id' => $profile->id,
        ]);
    }

    public function test_public_telemetry_profile_api_returns_correct_config(): void
    {
        $unit = Unit::first();
        $this->assertNotNull($unit);

        $response = $this->get("/api/telemetry/profile/{$unit->kode_unit}");
        $response->assertStatus(200);
        $response->assertJsonStructure([
            'unit',
            'unit_nama',
            'profile' => [
                'id',
                'kode_profil',
                'nama',
                'detector' => [
                    'confidence',
                    'release_confidence',
                    'truck_confidence',
                    'hold_seconds',
                    'min_width_ratio',
                    'arm_confidence',
                    'arm_swing_threshold',
                    'plate_confidence',
                    'plate_ocr_enabled',
                ],
                'zones' => [
                    'dig',
                    'dump_top_ratio',
                    'dump_height_ratio',
                    'motion_threshold',
                ],
                'activity' => [
                    'dig_min_seconds',
                    'dump_min_seconds',
                    'phase_min_seconds',
                    'idle_seconds',
                    'bucket_low_ratio',
                ],
            ],
        ]);
    }
}
