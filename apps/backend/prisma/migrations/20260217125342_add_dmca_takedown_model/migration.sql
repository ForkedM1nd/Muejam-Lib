-- CreateEnum
CREATE TYPE "DMCAStatus" AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

-- CreateTable
CREATE TABLE "DMCATakedown" (
    "id" TEXT NOT NULL,
    "copyright_holder" TEXT NOT NULL,
    "contact_info" TEXT NOT NULL,
    "copyrighted_work_description" TEXT NOT NULL,
    "infringing_url" TEXT NOT NULL,
    "good_faith_statement" BOOLEAN NOT NULL DEFAULT false,
    "signature" TEXT NOT NULL,
    "status" "DMCAStatus" NOT NULL DEFAULT 'PENDING',
    "submitted_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "reviewed_at" TIMESTAMP(3),
    "reviewed_by" TEXT,

    CONSTRAINT "DMCATakedown_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "DMCATakedown_status_idx" ON "DMCATakedown"("status");

-- CreateIndex
CREATE INDEX "DMCATakedown_submitted_at_idx" ON "DMCATakedown"("submitted_at");
