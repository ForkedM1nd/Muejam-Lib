from django.urls import path
from .views import health_check
from .api_key_views import (
    create_api_key,
    list_api_keys,
    rotate_api_key,
    revoke_api_key
)
from .pii_config_views import (
    get_pii_configs,
    get_pii_config,
    update_pii_config,
    add_to_whitelist,
    remove_from_whitelist,
    initialize_pii_configs
)

urlpatterns = [
    path('', health_check, name='health-check'),
    
    # API Key Management
    path('api-keys/', create_api_key, name='create-api-key'),
    path('api-keys/list/', list_api_keys, name='list-api-keys'),
    path('api-keys/<str:key_id>/rotate/', rotate_api_key, name='rotate-api-key'),
    path('api-keys/<str:key_id>/revoke/', revoke_api_key, name='revoke-api-key'),
    
    # PII Detection Configuration (Admin only)
    path('admin/pii-config/', get_pii_configs, name='get-pii-configs'),
    path('admin/pii-config/initialize/', initialize_pii_configs, name='initialize-pii-configs'),
    path('admin/pii-config/<str:pii_type>/', get_pii_config, name='get-pii-config'),
    path('admin/pii-config/<str:pii_type>/update/', update_pii_config, name='update-pii-config'),
    path('admin/pii-config/<str:pii_type>/whitelist/', add_to_whitelist, name='add-to-whitelist'),
    path('admin/pii-config/<str:pii_type>/whitelist/remove/', remove_from_whitelist, name='remove-from-whitelist'),
]
