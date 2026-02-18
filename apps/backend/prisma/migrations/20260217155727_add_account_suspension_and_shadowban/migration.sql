-- CreateTable
CREATE TABLE "AccountSuspension" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "suspended_by" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "suspended_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(3),
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "AccountSuspension_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Shadowban" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "applied_by" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "applied_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "Shadowban_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "AccountSuspension_user_id_idx" ON "AccountSuspension"("user_id");

-- CreateIndex
CREATE INDEX "AccountSuspension_is_active_idx" ON "AccountSuspension"("is_active");

-- CreateIndex
CREATE INDEX "AccountSuspension_expires_at_idx" ON "AccountSuspension"("expires_at");

-- CreateIndex
CREATE INDEX "Shadowban_user_id_idx" ON "Shadowban"("user_id");

-- CreateIndex
CREATE INDEX "Shadowban_is_active_idx" ON "Shadowban"("is_active");
