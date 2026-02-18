-- CreateTable
CREATE TABLE "APIKey" (
    "id" TEXT NOT NULL,
    "key_hash" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_used_at" TIMESTAMP(3),
    "expires_at" TIMESTAMP(3) NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "permissions" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "APIKey_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "APIKey_key_hash_key" ON "APIKey"("key_hash");

-- CreateIndex
CREATE INDEX "APIKey_user_id_idx" ON "APIKey"("user_id");

-- CreateIndex
CREATE INDEX "APIKey_key_hash_idx" ON "APIKey"("key_hash");

-- CreateIndex
CREATE INDEX "APIKey_is_active_expires_at_idx" ON "APIKey"("is_active", "expires_at");
