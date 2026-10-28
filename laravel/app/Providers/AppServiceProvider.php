<?php

namespace App\Providers;

use App\Models\Unit;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\View;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        try {
            if (Schema::hasTable('units')) {
                View::composer('*', function ($view) {
                    $view->with('globalUnits', Unit::orderBy('kode_unit')->get());
                });
            }
        } catch (\Throwable $e) {
            // Fallback for migrations or environments where table is not ready
        }
    }
}
