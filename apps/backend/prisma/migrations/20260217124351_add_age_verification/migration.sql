-- AlterTable
ALTER TABLE "UserProfile" ADD COLUMN     "age_verified" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "age_verified_at" TIMESTAMP(3);
