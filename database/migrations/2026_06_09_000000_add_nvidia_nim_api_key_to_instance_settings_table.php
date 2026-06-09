<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('instance_settings', function (Blueprint $table) {
            if (! Schema::hasColumn('instance_settings', 'nvidia_nim_api_key')) {
                $table->text('nvidia_nim_api_key')->nullable();
            }
        });
    }

    public function down(): void
    {
        Schema::table('instance_settings', function (Blueprint $table) {
            if (Schema::hasColumn('instance_settings', 'nvidia_nim_api_key')) {
                $table->dropColumn('nvidia_nim_api_key');
            }
        });
    }
};
