<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\DatabaseTransactions;
use Tests\TestCase;

class AuthTest extends TestCase
{
    use DatabaseTransactions;

    public function test_guest_is_redirected_to_login_when_accessing_dashboard(): void
    {
        $response = $this->get('/dashboard');
        $response->assertRedirect('/login');
    }

    public function test_guest_is_redirected_to_login_when_accessing_monitoring(): void
    {
        $response = $this->get('/monitoring/live');
        $response->assertRedirect('/login');
    }

    public function test_guest_is_redirected_to_login_when_accessing_master_user(): void
    {
        $response = $this->get('/master/user');
        $response->assertRedirect('/login');
    }

    public function test_login_screen_can_be_rendered(): void
    {
        $response = $this->get('/login');
        $response->assertStatus(200);
        $response->assertSee('HERA');
        $response->assertSee('AI-CCTV');
    }

    public function test_user_can_authenticate_using_the_login_screen(): void
    {
        $user = User::where('email', 'admin@herasystem.com')->first();
        if (!$user) {
            $user = User::create([
                'name' => 'Test Admin',
                'email' => 'test.admin@herasystem.com',
                'password' => 'password123',
                'role' => 'admin',
                'jabatan' => 'Superintendent',
                'is_active' => true,
            ]);
        }

        $response = $this->post('/login', [
            'email' => $user->email,
            'password' => 'password123',
        ]);

        $this->assertAuthenticated();
        $response->assertRedirect(route('dashboard'));
    }

    public function test_user_cannot_authenticate_with_invalid_password(): void
    {
        $response = $this->post('/login', [
            'email' => 'admin@herasystem.com',
            'password' => 'wrong-password-123',
        ]);

        $this->assertGuest();
        $response->assertSessionHasErrors('email');
    }

    public function test_authenticated_user_cannot_view_login_screen(): void
    {
        $user = User::first() ?? User::create([
            'name' => 'Test User',
            'email' => 'tester@herasystem.com',
            'password' => 'password123',
            'role' => 'operator',
            'is_active' => true,
        ]);

        $response = $this->actingAs($user)->get('/login');
        $response->assertRedirect('/dashboard');
    }

    public function test_user_can_logout(): void
    {
        $user = User::first();
        $response = $this->actingAs($user)->post('/logout');

        $this->assertGuest();
        $response->assertRedirect('/login');
    }
}
