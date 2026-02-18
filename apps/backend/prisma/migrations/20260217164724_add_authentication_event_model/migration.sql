-- CreateEnum
CREATE TYPE "AuthEventType" AS ENUM ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'TOKEN_REFRESH', 'PASSWORD_CHANGE', 'SUSPICIOUS_ACTIVITY');

-- CreateTable
CREATE TABLE "AuthenticationEvent" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "event_type" "AuthEventType" NOT NULL,
    "ip_address" TEXT NOT NULL,
    "user_agent" TEXT NOT NULL,
    "location" TEXT,
    "success" BOOLEAN NOT NULL DEFAULT true,
    "metadata" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuthenticationEvent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "AuthenticationEvent_user_id_created_at_idx" ON "AuthenticationEvent"("user_id", "created_at");

-- CreateIndex
CREATE INDEX "AuthenticationEvent_event_type_idx" ON "AuthenticationEvent"("event_type");

-- CreateIndex
CREATE INDEX "AuthenticationEvent_ip_address_idx" ON "AuthenticationEvent"("ip_address");

-- CreateIndex
CREATE INDEX "AuthenticationEvent_created_at_idx" ON "AuthenticationEvent"("created_at");
