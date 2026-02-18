-- CreateEnum
CREATE TYPE "NSFWContentType" AS ENUM ('STORY', 'CHAPTER', 'WHISPER', 'IMAGE');

-- CreateEnum
CREATE TYPE "NSFWDetectionMethod" AS ENUM ('AUTOMATIC', 'MANUAL', 'USER_MARKED');

-- CreateEnum
CREATE TYPE "NSFWPreference" AS ENUM ('SHOW_ALL', 'BLUR_NSFW', 'HIDE_NSFW');

-- CreateTable
CREATE TABLE "TOTPDevice" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "secret" TEXT NOT NULL,
    "name" TEXT NOT NULL DEFAULT 'Authenticator',
    "confirmed" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_used_at" TIMESTAMP(3),

    CONSTRAINT "TOTPDevice_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BackupCode" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "code_hash" TEXT NOT NULL,
    "used_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BackupCode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "NSFWFlag" (
    "id" TEXT NOT NULL,
    "content_type" "NSFWContentType" NOT NULL,
    "content_id" TEXT NOT NULL,
    "is_nsfw" BOOLEAN NOT NULL DEFAULT false,
    "confidence" DOUBLE PRECISION,
    "labels" JSONB,
    "detection_method" "NSFWDetectionMethod" NOT NULL,
    "flagged_by" TEXT,
    "flagged_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "reviewed" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "NSFWFlag_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ContentPreference" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "nsfw_preference" "NSFWPreference" NOT NULL DEFAULT 'BLUR_NSFW',
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ContentPreference_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "TOTPDevice_user_id_idx" ON "TOTPDevice"("user_id");

-- CreateIndex
CREATE INDEX "TOTPDevice_confirmed_idx" ON "TOTPDevice"("confirmed");

-- CreateIndex
CREATE UNIQUE INDEX "BackupCode_code_hash_key" ON "BackupCode"("code_hash");

-- CreateIndex
CREATE INDEX "BackupCode_user_id_idx" ON "BackupCode"("user_id");

-- CreateIndex
CREATE INDEX "BackupCode_code_hash_idx" ON "BackupCode"("code_hash");

-- CreateIndex
CREATE INDEX "NSFWFlag_content_type_content_id_idx" ON "NSFWFlag"("content_type", "content_id");

-- CreateIndex
CREATE INDEX "NSFWFlag_is_nsfw_idx" ON "NSFWFlag"("is_nsfw");

-- CreateIndex
CREATE INDEX "NSFWFlag_reviewed_idx" ON "NSFWFlag"("reviewed");

-- CreateIndex
CREATE INDEX "NSFWFlag_flagged_at_idx" ON "NSFWFlag"("flagged_at");

-- CreateIndex
CREATE UNIQUE INDEX "ContentPreference_user_id_key" ON "ContentPreference"("user_id");

-- CreateIndex
CREATE INDEX "ContentPreference_user_id_idx" ON "ContentPreference"("user_id");
