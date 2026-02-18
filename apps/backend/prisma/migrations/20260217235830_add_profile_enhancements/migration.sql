-- CreateEnum
CREATE TYPE "BadgeType" AS ENUM ('VERIFIED_AUTHOR', 'TOP_CONTRIBUTOR', 'EARLY_ADOPTER', 'PROLIFIC_WRITER', 'POPULAR_AUTHOR', 'COMMUNITY_CHAMPION');

-- AlterTable
ALTER TABLE "UserProfile" ADD COLUMN     "banner_key" TEXT,
ADD COLUMN     "instagram_url" TEXT,
ADD COLUMN     "pinned_story_1" TEXT,
ADD COLUMN     "pinned_story_2" TEXT,
ADD COLUMN     "pinned_story_3" TEXT,
ADD COLUMN     "theme_color" TEXT DEFAULT '#6366f1',
ADD COLUMN     "twitter_url" TEXT,
ADD COLUMN     "website_url" TEXT;

-- CreateTable
CREATE TABLE "UserBadge" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "badge_type" "BadgeType" NOT NULL,
    "earned_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB,

    CONSTRAINT "UserBadge_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "UserBadge_user_id_idx" ON "UserBadge"("user_id");

-- CreateIndex
CREATE INDEX "UserBadge_badge_type_idx" ON "UserBadge"("badge_type");

-- CreateIndex
CREATE UNIQUE INDEX "UserBadge_user_id_badge_type_key" ON "UserBadge"("user_id", "badge_type");

-- AddForeignKey
ALTER TABLE "UserBadge" ADD CONSTRAINT "UserBadge_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "UserProfile"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
