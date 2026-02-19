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
from .sync_views import (
    sync_stories,
    sync_whispers,
    sync_batch,
    sync_status,
    resolve_conflict
)
from .mobile_config_views import (
    get_mobile_config,
    update_mobile_config
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

# Sync endpoints for mobile data synchronization
sync_urlpatterns = [
    path('stories/', sync_stories, name='sync-stories'),
    path('whispers/', sync_whispers, name='sync-whispers'),
    path('batch/', sync_batch, name='sync-batch'),
    path('status/', sync_status, name='sync-status'),
    path('resolve-conflict/', resolve_conflict, name='resolve-conflict'),
]

# Mobile configuration endpoints
config_urlpatterns = [
    path('mobile/', get_mobile_config, name='get-mobile-config'),
    path('mobile/', update_mobile_config, name='update-mobile-config'),
]
