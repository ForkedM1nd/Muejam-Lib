-- CreateEnum
CREATE TYPE "AuditActionType" AS ENUM ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_CHANGE', 'TWO_FA_ENABLED', 'TWO_FA_DISABLED', 'CONTENT_TAKEDOWN', 'USER_SUSPENSION', 'REPORT_RESOLUTION', 'ROLE_ASSIGNMENT', 'CONFIG_CHANGE', 'USER_ROLE_CHANGE', 'SYSTEM_SETTINGS_UPDATE', 'DATA_EXPORT_REQUEST', 'ACCOUNT_DELETION_REQUEST', 'PRIVACY_SETTINGS_CHANGE', 'API_KEY_CREATED', 'API_KEY_REVOKED', 'CONSENT_RECORDED', 'CONSENT_WITHDRAWN');

-- CreateEnum
CREATE TYPE "AuditResourceType" AS ENUM ('USER', 'STORY', 'CHAPTER', 'WHISPER', 'REPORT', 'MODERATION_ACTION', 'PRIVACY_SETTINGS', 'API_KEY', 'SYSTEM_CONFIG', 'DATA_EXPORT', 'DELETION_REQUEST');

-- CreateEnum
CREATE TYPE "AuditResult" AS ENUM ('SUCCESS', 'FAILURE', 'PARTIAL');

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "action_type" "AuditActionType" NOT NULL,
    "resource_type" "AuditResourceType",
    "resource_id" TEXT,
    "ip_address" TEXT NOT NULL,
    "user_agent" TEXT NOT NULL,
    "result" "AuditResult" NOT NULL DEFAULT 'SUCCESS',
    "metadata" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "AuditLog_user_id_created_at_idx" ON "AuditLog"("user_id", "created_at");

-- CreateIndex
CREATE INDEX "AuditLog_action_type_created_at_idx" ON "AuditLog"("action_type", "created_at");

-- CreateIndex
CREATE INDEX "AuditLog_resource_type_resource_id_idx" ON "AuditLog"("resource_type", "resource_id");

-- CreateIndex
CREATE INDEX "AuditLog_created_at_idx" ON "AuditLog"("created_at");

-- CreateIndex
CREATE INDEX "AuditLog_ip_address_created_at_idx" ON "AuditLog"("ip_address", "created_at");
