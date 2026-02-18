#!/bin/bash

# PostgreSQL Restore Script for MueJam
# This script restores a PostgreSQL database from backup

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration from environment variables
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-muejam}"
DB_USER="${DB_USER:-muejam_user}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgres}"
BACKUP_STORAGE_TYPE="${BACKUP_STORAGE_TYPE:-local}"
S3_BUCKET="${S3_BUCKET:-}"
AZURE_CONTAINER="${AZURE_CONTAINER:-}"
GCS_BUCKET="${GCS_BUCKET:-}"
ENCRYPTION_ENABLED="${ENCRYPTION_ENABLED:-true}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/backup/encryption.key}"

# Logging
LOG_FILE="${BACKUP_DIR}/restore.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --file BACKUP_FILE    Backup file to restore (required)"
    echo "  -l, --list                List available backups"
    echo "  -d, --download            Download backup from cloud storage"
    echo "  -y, --yes                 Skip confirmation prompt"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --list"
    echo "  $0 --file muejam_backup_20240101_120000.sql.gz"
    echo "  $0 --file muejam_backup_20240101_120000.sql.gz --download --yes"
    exit 1
}

# Parse arguments
BACKUP_FILE=""
LIST_BACKUPS=false
DOWNLOAD_BACKUP=false
SKIP_CONFIRMATION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -d|--download)
            DOWNLOAD_BACKUP=true
            shift
            ;;
        -y|--yes)
            SKIP_CONFIRMATION=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# List backups
if [ "$LIST_BACKUPS" = true ]; then
    echo "Available local backups:"
    ls -lh "$BACKUP_DIR"/muejam_backup_*.sql.gz 2>/dev/null || echo "No local backups found"
    
    echo ""
    echo "Available cloud backups:"
    case "$BACKUP_STORAGE_TYPE" in
        s3)
            if [ -n "$S3_BUCKET" ]; then
                aws s3 ls "s3://${S3_BUCKET}/backups/" | grep "muejam_backup_"
            fi
            ;;
        azure)
            if [ -n "$AZURE_CONTAINER" ]; then
                az storage blob list --container-name "$AZURE_CONTAINER" --prefix "backups/muejam_backup_" --output table
            fi
            ;;
        gcs)
            if [ -n "$GCS_BUCKET" ]; then
                gsutil ls "gs://${GCS_BUCKET}/backups/muejam_backup_*"
            fi
            ;;
    esac
    exit 0
fi

# Validate backup file
if [ -z "$BACKUP_FILE" ]; then
    log_error "Backup file not specified"
    usage
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Download backup from cloud if needed
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

if [ "$DOWNLOAD_BACKUP" = true ] || [ ! -f "$BACKUP_PATH" ]; then
    log "Downloading backup from cloud storage..."
    
    case "$BACKUP_STORAGE_TYPE" in
        s3)
            if [ -n "$S3_BUCKET" ]; then
                aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_FILE}" "$BACKUP_PATH"
            else
                log_error "S3_BUCKET not configured"
                exit 1
            fi
            ;;
        azure)
            if [ -n "$AZURE_CONTAINER" ]; then
                az storage blob download \
                    --container-name "$AZURE_CONTAINER" \
                    --name "backups/${BACKUP_FILE}" \
                    --file "$BACKUP_PATH"
            else
                log_error "AZURE_CONTAINER not configured"
                exit 1
            fi
            ;;
        gcs)
            if [ -n "$GCS_BUCKET" ]; then
                gsutil cp "gs://${GCS_BUCKET}/backups/${BACKUP_FILE}" "$BACKUP_PATH"
            else
                log_error "GCS_BUCKET not configured"
                exit 1
            fi
            ;;
        local)
            if [ ! -f "$BACKUP_PATH" ]; then
                log_error "Backup file not found: ${BACKUP_PATH}"
                exit 1
            fi
            ;;
    esac
    
    log_success "Backup downloaded successfully"
fi

# Verify backup file exists
if [ ! -f "$BACKUP_PATH" ]; then
    log_error "Backup file not found: ${BACKUP_PATH}"
    exit 1
fi

# Get backup info
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
log "Backup file: ${BACKUP_FILE}"
log "Backup size: ${BACKUP_SIZE}"

# Confirmation prompt
if [ "$SKIP_CONFIRMATION" = false ]; then
    echo ""
    log_warning "WARNING: This will restore the database from backup!"
    log_warning "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
    log_warning "Backup: ${BACKUP_FILE}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

# Start restore
log "Starting database restore..."

# Check if PostgreSQL is accessible
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    log_error "PostgreSQL is not accessible at ${DB_HOST}:${DB_PORT}"
    exit 1
fi

# Decrypt backup if encrypted
RESTORE_FILE="$BACKUP_PATH"
if [ "$ENCRYPTION_ENABLED" = "true" ]; then
    if [ -f "$ENCRYPTION_KEY_FILE" ]; then
        log "Decrypting backup..."
        RESTORE_FILE="${BACKUP_PATH}.decrypted"
        openssl enc -aes-256-cbc -d -pbkdf2 \
            -in "$BACKUP_PATH" \
            -out "$RESTORE_FILE" \
            -pass file:"$ENCRYPTION_KEY_FILE"
        
        if [ $? -eq 0 ]; then
            log_success "Backup decrypted successfully"
        else
            log_error "Failed to decrypt backup"
            exit 1
        fi
    else
        log_warning "Encryption key file not found, assuming unencrypted backup"
    fi
fi

# Verify backup integrity
log "Verifying backup integrity..."
if gzip -t "$RESTORE_FILE" 2>/dev/null; then
    log_success "Backup integrity verified"
else
    log_error "Backup integrity check failed"
    rm -f "$RESTORE_FILE"
    exit 1
fi

# Terminate existing connections
log "Terminating existing database connections..."
PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    2>> "$LOG_FILE" || true

# Drop and recreate database
log "Dropping existing database..."
PGPASSWORD="$PGPASSWORD" dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$DB_NAME" 2>> "$LOG_FILE"

log "Creating new database..."
PGPASSWORD="$PGPASSWORD" createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>> "$LOG_FILE"

# Restore database
log "Restoring database from backup..."
if gunzip -c "$RESTORE_FILE" | PGPASSWORD="$PGPASSWORD" pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-acl \
    2>> "$LOG_FILE"; then
    
    log_success "Database restored successfully"
else
    log_error "Failed to restore database"
    rm -f "$RESTORE_FILE"
    exit 1
fi

# Clean up decrypted file
if [ "$RESTORE_FILE" != "$BACKUP_PATH" ]; then
    rm -f "$RESTORE_FILE"
fi

# Verify restore
log "Verifying restore..."
TABLE_COUNT=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>> "$LOG_FILE")

log "Tables restored: ${TABLE_COUNT}"

if [ "$TABLE_COUNT" -gt 0 ]; then
    log_success "Restore verification passed"
else
    log_warning "No tables found in restored database"
fi

# Send notification
if [ -n "${BACKUP_NOTIFICATION_WEBHOOK:-}" ]; then
    log "Sending restore notification..."
    curl -X POST "$BACKUP_NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"Database restore completed\",
            \"backup_file\": \"${BACKUP_FILE}\",
            \"database\": \"${DB_NAME}\",
            \"tables_restored\": ${TABLE_COUNT},
            \"timestamp\": \"${TIMESTAMP}\"
        }" > /dev/null 2>&1
fi

# Summary
log "========================================="
log "Restore Summary:"
log "  Backup: ${BACKUP_FILE}"
log "  Database: ${DB_NAME}"
log "  Tables: ${TABLE_COUNT}"
log "  Status: SUCCESS"
log "========================================="

log_success "Restore completed successfully!"
exit 0
