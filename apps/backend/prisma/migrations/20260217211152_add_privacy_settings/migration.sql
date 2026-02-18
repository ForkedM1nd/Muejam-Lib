-- CreateEnum
CREATE TYPE "VisibilityLevel" AS ENUM ('PUBLIC', 'FOLLOWERS_ONLY', 'PRIVATE');

-- CreateEnum
CREATE TYPE "CommentPermission" AS ENUM ('ANYONE', 'FOLLOWERS', 'DISABLED');

-- CreateEnum
CREATE TYPE "FollowerApproval" AS ENUM ('ANYONE', 'APPROVAL_REQUIRED');

-- CreateTable
CREATE TABLE "PrivacySettings" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "profile_visibility" "VisibilityLevel" NOT NULL DEFAULT 'PUBLIC',
    "reading_history_visibility" "VisibilityLevel" NOT NULL DEFAULT 'PRIVATE',
    "analytics_opt_out" BOOLEAN NOT NULL DEFAULT false,
    "marketing_emails" BOOLEAN NOT NULL DEFAULT true,
    "comment_permissions" "CommentPermission" NOT NULL DEFAULT 'ANYONE',
    "follower_approval_required" "FollowerApproval" NOT NULL DEFAULT 'ANYONE',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PrivacySettings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "PrivacySettings_user_id_key" ON "PrivacySettings"("user_id");

-- CreateIndex
CREATE INDEX "PrivacySettings_user_id_idx" ON "PrivacySettings"("user_id");
