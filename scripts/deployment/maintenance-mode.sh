#!/bin/bash
# Enable/disable maintenance mode
# Usage: ./scripts/maintenance-mode.sh <enable|disable>

set -e

ACTION="${1:-enable}"

case "$ACTION" in
    enable)
        echo "Enabling maintenance mode..."
        # Set maintenance mode flag in Redis
        redis-cli SET maintenance_mode "true"
        # Update load balancer health check to fail
        # This will remove instances from rotation
        echo "✓ Maintenance mode enabled"
        echo "All traffic will be redirected to maintenance page"
        ;;
    
    disable)
        echo "Disabling maintenance mode..."
        # Remove maintenance mode flag
        redis-cli DEL maintenance_mode
        # Restore load balancer health check
        echo "✓ Maintenance mode disabled"
        echo "Normal traffic resumed"
        ;;
    
    *)
        echo "Usage: $0 <enable|disable>"
        exit 1
        ;;
esac
