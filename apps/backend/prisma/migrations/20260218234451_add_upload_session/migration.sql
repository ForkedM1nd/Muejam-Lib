-- CreateTable
CREATE TABLE "UploadSession" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "filename" TEXT NOT NULL,
    "total_size" INTEGER NOT NULL,
    "chunk_size" INTEGER NOT NULL,
    "chunks_total" INTEGER NOT NULL,
    "chunks_uploaded" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL,
    "s3_upload_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "UploadSession_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "UploadSession_user_id_idx" ON "UploadSession"("user_id");

-- CreateIndex
CREATE INDEX "UploadSession_status_idx" ON "UploadSession"("status");
