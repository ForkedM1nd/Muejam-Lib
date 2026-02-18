-- CreateEnum
CREATE TYPE "ModerationActionType" AS ENUM ('DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND');

-- CreateEnum
CREATE TYPE "ModeratorRoleType" AS ENUM ('MODERATOR', 'SENIOR_MODERATOR', 'ADMINISTRATOR');

-- CreateTable
CREATE TABLE "ModerationAction" (
    "id" TEXT NOT NULL,
    "report_id" TEXT NOT NULL,
    "moderator_id" TEXT NOT NULL,
    "action_type" "ModerationActionType" NOT NULL,
    "reason" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB,

    CONSTRAINT "ModerationAction_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ModeratorRole" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "role" "ModeratorRoleType" NOT NULL,
    "assigned_by" TEXT NOT NULL,
    "assigned_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_active" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "ModeratorRole_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "ModerationAction_report_id_idx" ON "ModerationAction"("report_id");

-- CreateIndex
CREATE INDEX "ModerationAction_moderator_id_idx" ON "ModerationAction"("moderator_id");

-- CreateIndex
CREATE INDEX "ModerationAction_created_at_idx" ON "ModerationAction"("created_at");

-- CreateIndex
CREATE UNIQUE INDEX "ModeratorRole_user_id_key" ON "ModeratorRole"("user_id");

-- CreateIndex
CREATE INDEX "ModeratorRole_user_id_idx" ON "ModeratorRole"("user_id");

-- CreateIndex
CREATE INDEX "ModeratorRole_role_idx" ON "ModeratorRole"("role");

-- CreateIndex
CREATE INDEX "ModeratorRole_is_active_idx" ON "ModeratorRole"("is_active");

-- AddForeignKey
ALTER TABLE "ModerationAction" ADD CONSTRAINT "ModerationAction_report_id_fkey" FOREIGN KEY ("report_id") REFERENCES "Report"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
