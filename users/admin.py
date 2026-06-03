from django.contrib import admin
from django.contrib.auth import get_user_model


@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')

    class Meta:
        model = get_user_model()