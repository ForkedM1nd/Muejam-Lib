-- CreateTable
CREATE TABLE "OnboardingProgress" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "profile_completed" BOOLEAN NOT NULL DEFAULT false,
    "interests_selected" BOOLEAN NOT NULL DEFAULT false,
    "tutorial_completed" BOOLEAN NOT NULL DEFAULT false,
    "first_story_read" BOOLEAN NOT NULL DEFAULT false,
    "first_whisper_posted" BOOLEAN NOT NULL DEFAULT false,
    "first_follow" BOOLEAN NOT NULL DEFAULT false,
    "authors_followed_count" INTEGER NOT NULL DEFAULT 0,
    "onboarding_completed" BOOLEAN NOT NULL DEFAULT false,
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "OnboardingProgress_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "OnboardingProgress_user_id_key" ON "OnboardingProgress"("user_id");

-- CreateIndex
CREATE INDEX "OnboardingProgress_user_id_idx" ON "OnboardingProgress"("user_id");

-- CreateIndex
CREATE INDEX "OnboardingProgress_onboarding_completed_idx" ON "OnboardingProgress"("onboarding_completed");
