-- CreateEnum
CREATE TYPE "FilterType" AS ENUM ('PROFANITY', 'SPAM', 'HATE_SPEECH');

-- CreateEnum
CREATE TYPE "FilterSensitivity" AS ENUM ('STRICT', 'MODERATE', 'PERMISSIVE');

-- CreateTable
CREATE TABLE "ContentFilterConfig" (
    "id" TEXT NOT NULL,
    "filter_type" "FilterType" NOT NULL,
    "sensitivity" "FilterSensitivity" NOT NULL DEFAULT 'MODERATE',
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "whitelist" JSONB NOT NULL DEFAULT '[]',
    "blacklist" JSONB NOT NULL DEFAULT '[]',
    "updated_at" TIMESTAMP(3) NOT NULL,
    "updated_by" TEXT NOT NULL,

    CONSTRAINT "ContentFilterConfig_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AutomatedFlag" (
    "id" TEXT NOT NULL,
    "content_type" TEXT NOT NULL,
    "content_id" TEXT NOT NULL,
    "flag_type" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "reviewed" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "AutomatedFlag_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "ContentFilterConfig_filter_type_enabled_idx" ON "ContentFilterConfig"("filter_type", "enabled");

-- CreateIndex
CREATE UNIQUE INDEX "ContentFilterConfig_filter_type_key" ON "ContentFilterConfig"("filter_type");

-- CreateIndex
CREATE INDEX "AutomatedFlag_content_type_content_id_idx" ON "AutomatedFlag"("content_type", "content_id");

-- CreateIndex
CREATE INDEX "AutomatedFlag_reviewed_idx" ON "AutomatedFlag"("reviewed");

-- CreateIndex
CREATE INDEX "AutomatedFlag_created_at_idx" ON "AutomatedFlag"("created_at");
