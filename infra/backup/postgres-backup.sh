#!/bin/bash

# PostgreSQL Backup Script for MueJam
# This script creates automated backups of the PostgreSQL database
# and uploads them to cloud storage (S3/Azure/GCS)

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration from environment variables
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-muejam}"
DB_USER="${DB_USER:-muejam_user}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgres}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_STORAGE_TYPE="${BACKUP_STORAGE_TYPE:-local}"  # local, s3, azure, gcs
S3_BUCKET="${S3_BUCKET:-}"
AZURE_CONTAINER="${AZURE_CONTAINER:-}"
GCS_BUCKET="${GCS_BUCKET:-}"
ENCRYPTION_ENABLED="${ENCRYPTION_ENABLED:-true}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/backup/encryption.key}"

# Logging
LOG_FILE="${BACKUP_DIR}/backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="muejam_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Start backup
log "Starting PostgreSQL backup..."
log "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log "Backup file: ${BACKUP_FILE}"

# Check if PostgreSQL is accessible
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    log_error "PostgreSQL is not accessible at ${DB_HOST}:${DB_PORT}"
    exit 1
fi

# Create backup using pg_dump
log "Creating database dump..."
if PGPASSWORD="$PGPASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="${BACKUP_PATH}.tmp" 2>> "$LOG_FILE"; then
    
    # Compress the backup
    log "Compressing backup..."
    gzip -9 "${BACKUP_PATH}.tmp"
    mv "${BACKUP_PATH}.tmp.gz" "$BACKUP_PATH"
    
    log_success "Database dump created successfully"
else
    log_error "Failed to create database dump"
    rm -f "${BACKUP_PATH}.tmp"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
log "Backup size: ${BACKUP_SIZE}"

# Encrypt backup if enabled
if [ "$ENCRYPTION_ENABLED" = "true" ]; then
    if [ -f "$ENCRYPTION_KEY_FILE" ]; then
        log "Encrypting backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$BACKUP_PATH" \
            -out "${BACKUP_PATH}.enc" \
            -pass file:"$ENCRYPTION_KEY_FILE"
        
        if [ $? -eq 0 ]; then
            rm "$BACKUP_PATH"
            mv "${BACKUP_PATH}.enc" "$BACKUP_PATH"
            log_success "Backup encrypted successfully"
        else
            log_error "Failed to encrypt backup"
            exit 1
        fi
    else
        log_warning "Encryption key file not found, skipping encryption"
    fi
fi

# Upload to cloud storage
case "$BACKUP_STORAGE_TYPE" in
    s3)
        if [ -n "$S3_BUCKET" ]; then
            log "Uploading to S3 bucket: ${S3_BUCKET}"
            if aws s3 cp "$BACKUP_PATH" "s3://${S3_BUCKET}/backups/${BACKUP_FILE}" \
                --storage-class STANDARD_IA \
                --metadata "timestamp=${TIMESTAMP},database=${DB_NAME}"; then
                log_success "Backup uploaded to S3"
            else
                log_error "Failed to upload backup to S3"
                exit 1
            fi
        else
            log_error "S3_BUCKET not configured"
            exit 1
        fi
        ;;
    
    azure)
        if [ -n "$AZURE_CONTAINER" ]; then
            log "Uploading to Azure Blob Storage: ${AZURE_CONTAINER}"
            if az storage blob upload \
                --container-name "$AZURE_CONTAINER" \
                --file "$BACKUP_PATH" \
                --name "backups/${BACKUP_FILE}" \
                --tier Cool; then
                log_success "Backup uploaded to Azure"
            else
                log_error "Failed to upload backup to Azure"
                exit 1
            fi
        else
            log_error "AZURE_CONTAINER not configured"
            exit 1
        fi
        ;;
    
    gcs)
        if [ -n "$GCS_BUCKET" ]; then
            log "Uploading to Google Cloud Storage: ${GCS_BUCKET}"
            if gsutil -m cp "$BACKUP_PATH" "gs://${GCS_BUCKET}/backups/${BACKUP_FILE}"; then
                log_success "Backup uploaded to GCS"
            else
                log_error "Failed to upload backup to GCS"
                exit 1
            fi
        else
            log_error "GCS_BUCKET not configured"
            exit 1
        fi
        ;;
    
    local)
        log "Backup stored locally at: ${BACKUP_PATH}"
        ;;
    
    *)
        log_error "Unknown backup storage type: ${BACKUP_STORAGE_TYPE}"
        exit 1
        ;;
esac

# Clean up old backups
log "Cleaning up old backups (retention: ${BACKUP_RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "muejam_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
DELETED_COUNT=$(find "$BACKUP_DIR" -name "muejam_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} | wc -l)
log "Deleted ${DELETED_COUNT} old backup(s)"

# Clean up old backups from cloud storage
case "$BACKUP_STORAGE_TYPE" in
    s3)
        if [ -n "$S3_BUCKET" ]; then
            log "Cleaning up old S3 backups..."
            CUTOFF_DATE=$(date -d "${BACKUP_RETENTION_DAYS} days ago" +%Y-%m-%d)
            aws s3 ls "s3://${S3_BUCKET}/backups/" | while read -r line; do
                BACKUP_DATE=$(echo "$line" | awk '{print $1}')
                BACKUP_NAME=$(echo "$line" | awk '{print $4}')
                if [[ "$BACKUP_DATE" < "$CUTOFF_DATE" ]]; then
                    aws s3 rm "s3://${S3_BUCKET}/backups/${BACKUP_NAME}"
                    log "Deleted old S3 backup: ${BACKUP_NAME}"
                fi
            done
        fi
        ;;
esac

# Verify backup integrity
log "Verifying backup integrity..."
if [ "$ENCRYPTION_ENABLED" = "true" ]; then
    # Decrypt and verify
    openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "$BACKUP_PATH" \
        -pass file:"$ENCRYPTION_KEY_FILE" | gzip -t
else
    gzip -t "$BACKUP_PATH"
fi

if [ $? -eq 0 ]; then
    log_success "Backup integrity verified"
else
    log_error "Backup integrity check failed"
    exit 1
fi

# Send notification (optional)
if [ -n "${BACKUP_NOTIFICATION_WEBHOOK:-}" ]; then
    log "Sending backup notification..."
    curl -X POST "$BACKUP_NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"Database backup completed successfully\",
            \"backup_file\": \"${BACKUP_FILE}\",
            \"backup_size\": \"${BACKUP_SIZE}\",
            \"timestamp\": \"${TIMESTAMP}\",
            \"database\": \"${DB_NAME}\"
        }" > /dev/null 2>&1
fi

# Summary
log "========================================="
log "Backup Summary:"
log "  File: ${BACKUP_FILE}"
log "  Size: ${BACKUP_SIZE}"
log "  Location: ${BACKUP_STORAGE_TYPE}"
log "  Encrypted: ${ENCRYPTION_ENABLED}"
log "  Status: SUCCESS"
log "========================================="

log_success "Backup completed successfully!"
exit 0
