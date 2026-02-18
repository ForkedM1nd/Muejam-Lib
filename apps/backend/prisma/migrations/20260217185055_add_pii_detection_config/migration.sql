-- CreateEnum
CREATE TYPE "PIIType" AS ENUM ('EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD');

-- CreateEnum
CREATE TYPE "PIISensitivity" AS ENUM ('STRICT', 'MODERATE', 'PERMISSIVE');

-- CreateTable
CREATE TABLE "PIIDetectionConfig" (
    "id" TEXT NOT NULL,
    "pii_type" "PIIType" NOT NULL,
    "sensitivity" "PIISensitivity" NOT NULL DEFAULT 'MODERATE',
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "whitelist" JSONB NOT NULL DEFAULT '[]',
    "pattern" TEXT,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "updated_by" TEXT NOT NULL,

    CONSTRAINT "PIIDetectionConfig_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "PIIDetectionConfig_pii_type_enabled_idx" ON "PIIDetectionConfig"("pii_type", "enabled");

-- CreateIndex
CREATE UNIQUE INDEX "PIIDetectionConfig_pii_type_key" ON "PIIDetectionConfig"("pii_type");
