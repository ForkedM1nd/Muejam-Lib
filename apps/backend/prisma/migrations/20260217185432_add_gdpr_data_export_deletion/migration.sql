-- CreateEnum
CREATE TYPE "DataExportStatus" AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

-- CreateEnum
CREATE TYPE "DeletionStatus" AS ENUM ('PENDING', 'CANCELLED', 'COMPLETED');

-- CreateTable
CREATE TABLE "DataExportRequest" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "status" "DataExportStatus" NOT NULL DEFAULT 'PENDING',
    "requested_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "completed_at" TIMESTAMP(3),
    "download_url" TEXT,
    "expires_at" TIMESTAMP(3),
    "error_message" TEXT,

    CONSTRAINT "DataExportRequest_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeletionRequest" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "requested_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "scheduled_deletion_at" TIMESTAMP(3) NOT NULL,
    "cancelled_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "status" "DeletionStatus" NOT NULL DEFAULT 'PENDING',

    CONSTRAINT "DeletionRequest_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "DataExportRequest_user_id_idx" ON "DataExportRequest"("user_id");

-- CreateIndex
CREATE INDEX "DataExportRequest_status_idx" ON "DataExportRequest"("status");

-- CreateIndex
CREATE INDEX "DataExportRequest_requested_at_idx" ON "DataExportRequest"("requested_at");

-- CreateIndex
CREATE INDEX "DeletionRequest_user_id_idx" ON "DeletionRequest"("user_id");

-- CreateIndex
CREATE INDEX "DeletionRequest_status_idx" ON "DeletionRequest"("status");

-- CreateIndex
CREATE INDEX "DeletionRequest_scheduled_deletion_at_idx" ON "DeletionRequest"("scheduled_deletion_at");
