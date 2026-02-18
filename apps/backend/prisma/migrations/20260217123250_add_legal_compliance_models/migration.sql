-- CreateEnum
CREATE TYPE "DocumentType" AS ENUM ('TOS', 'PRIVACY', 'CONTENT_POLICY', 'DMCA');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "previous_password_hashes" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LegalDocument" (
    "id" TEXT NOT NULL,
    "document_type" "DocumentType" NOT NULL,
    "version" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "effective_date" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "LegalDocument_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserConsent" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "document_id" TEXT NOT NULL,
    "consented_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ip_address" TEXT NOT NULL,
    "user_agent" TEXT NOT NULL,

    CONSTRAINT "UserConsent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CookieConsent" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "session_id" TEXT NOT NULL,
    "essential" BOOLEAN NOT NULL DEFAULT true,
    "analytics" BOOLEAN NOT NULL DEFAULT false,
    "marketing" BOOLEAN NOT NULL DEFAULT false,
    "consented_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "CookieConsent_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE INDEX "User_email_idx" ON "User"("email");

-- CreateIndex
CREATE INDEX "LegalDocument_document_type_is_active_idx" ON "LegalDocument"("document_type", "is_active");

-- CreateIndex
CREATE INDEX "LegalDocument_effective_date_idx" ON "LegalDocument"("effective_date");

-- CreateIndex
CREATE INDEX "UserConsent_user_id_idx" ON "UserConsent"("user_id");

-- CreateIndex
CREATE INDEX "UserConsent_document_id_idx" ON "UserConsent"("document_id");

-- CreateIndex
CREATE INDEX "UserConsent_consented_at_idx" ON "UserConsent"("consented_at");

-- CreateIndex
CREATE INDEX "CookieConsent_user_id_idx" ON "CookieConsent"("user_id");

-- CreateIndex
CREATE INDEX "CookieConsent_session_id_idx" ON "CookieConsent"("session_id");

-- CreateIndex
CREATE INDEX "CookieConsent_consented_at_idx" ON "CookieConsent"("consented_at");

-- AddForeignKey
ALTER TABLE "UserConsent" ADD CONSTRAINT "UserConsent_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "UserProfile"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserConsent" ADD CONSTRAINT "UserConsent_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "LegalDocument"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CookieConsent" ADD CONSTRAINT "CookieConsent_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "UserProfile"("id") ON DELETE SET NULL ON UPDATE CASCADE;
