<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Tests\TestCase;

class UserManagementTest extends TestCase
{
    use DatabaseTransactions;

    public function test_admin_can_view_user_management_page(): void
    {
        $admin = User::where('role', 'admin')->first();
        $response = $this->actingAs($admin)->get('/master/user');

        $response->assertStatus(200);
        $response->assertSee('Manajemen Pengguna');
        $response->assertSee('Hendra Setiawan');
    }

    public function test_admin_can_create_new_user(): void
    {
        $admin = User::where('role', 'admin')->first();

        $userData = [
            'name' => 'Budi Santoso',
            'email' => 'budi.santoso@herasystem.com',
            'password' => 'secret123',
            'role' => 'operator',
            'jabatan' => 'Operator Excavator Cat 349',
            'is_active' => '1',
        ];

        $response = $this->actingAs($admin)->post('/master/user', $userData);

        $response->assertRedirect('/master/user');
        $this->assertDatabaseHas('users', [
            'email' => 'budi.santoso@herasystem.com',
            'role' => 'operator',
        ]);
    }

    public function test_admin_can_update_user(): void
    {
        $admin = User::where('role', 'admin')->first();
        $targetUser = User::where('role', 'operator')->first();

        $response = $this->actingAs($admin)->put("/master/user/{$targetUser->id}", [
            'name' => 'Ahmad Fauzi Updated',
            'email' => $targetUser->email,
            'role' => 'operator',
            'jabatan' => 'Lead Operator',
            'is_active' => '1',
        ]);

        $response->assertRedirect('/master/user');
        $this->assertDatabaseHas('users', [
            'id' => $targetUser->id,
            'name' => 'Ahmad Fauzi Updated',
            'jabatan' => 'Lead Operator',
        ]);
    }

    public function test_admin_cannot_delete_own_account(): void
    {
        $admin = User::where('role', 'admin')->first();

        $response = $this->actingAs($admin)->delete("/master/user/{$admin->id}");

        $response->assertSessionHas('error');
        $this->assertDatabaseHas('users', ['id' => $admin->id]);
    }
}
