-- CreateTable
CREATE TABLE "MobileConfig" (
    "id" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "min_version" TEXT NOT NULL,
    "config" JSONB NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "MobileConfig_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "MobileConfig_platform_key" ON "MobileConfig"("platform");
