-- CreateTable
CREATE TABLE "MobileSession" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "device_token_id" TEXT,
    "refresh_token" TEXT NOT NULL,
    "client_type" TEXT NOT NULL,
    "device_info" JSONB,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_refreshed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "revoked_at" TIMESTAMP(3),

    CONSTRAINT "MobileSession_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "MobileSession_refresh_token_key" ON "MobileSession"("refresh_token");

-- CreateIndex
CREATE INDEX "MobileSession_user_id_idx" ON "MobileSession"("user_id");

-- CreateIndex
CREATE INDEX "MobileSession_refresh_token_idx" ON "MobileSession"("refresh_token");

-- CreateIndex
CREATE INDEX "MobileSession_is_active_idx" ON "MobileSession"("is_active");

-- CreateIndex
CREATE INDEX "MobileSession_expires_at_idx" ON "MobileSession"("expires_at");
