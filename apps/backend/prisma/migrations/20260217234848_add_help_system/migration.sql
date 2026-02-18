-- CreateEnum
CREATE TYPE "HelpArticleCategory" AS ENUM ('GETTING_STARTED', 'READING_STORIES', 'WRITING_CONTENT', 'ACCOUNT_SETTINGS', 'PRIVACY_SAFETY', 'TROUBLESHOOTING');

-- CreateEnum
CREATE TYPE "HelpArticleStatus" AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED');

-- CreateTable
CREATE TABLE "HelpArticle" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "category" "HelpArticleCategory" NOT NULL,
    "content" TEXT NOT NULL,
    "excerpt" TEXT,
    "status" "HelpArticleStatus" NOT NULL DEFAULT 'DRAFT',
    "view_count" INTEGER NOT NULL DEFAULT 0,
    "helpful_yes" INTEGER NOT NULL DEFAULT 0,
    "helpful_no" INTEGER NOT NULL DEFAULT 0,
    "author_id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "published_at" TIMESTAMP(3),

    CONSTRAINT "HelpArticle_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "HelpSearchQuery" (
    "id" TEXT NOT NULL,
    "query" TEXT NOT NULL,
    "article_id" TEXT,
    "user_id" TEXT,
    "clicked" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "HelpSearchQuery_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "HelpArticleFeedback" (
    "id" TEXT NOT NULL,
    "article_id" TEXT NOT NULL,
    "user_id" TEXT,
    "helpful" BOOLEAN NOT NULL,
    "comment" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "HelpArticleFeedback_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SupportRequest" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "subject" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'open',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SupportRequest_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "HelpArticle_slug_key" ON "HelpArticle"("slug");

-- CreateIndex
CREATE INDEX "HelpArticle_category_status_idx" ON "HelpArticle"("category", "status");

-- CreateIndex
CREATE INDEX "HelpArticle_slug_idx" ON "HelpArticle"("slug");

-- CreateIndex
CREATE INDEX "HelpArticle_view_count_idx" ON "HelpArticle"("view_count");

-- CreateIndex
CREATE INDEX "HelpArticle_published_at_idx" ON "HelpArticle"("published_at");

-- CreateIndex
CREATE INDEX "HelpSearchQuery_query_idx" ON "HelpSearchQuery"("query");

-- CreateIndex
CREATE INDEX "HelpSearchQuery_created_at_idx" ON "HelpSearchQuery"("created_at");

-- CreateIndex
CREATE INDEX "HelpSearchQuery_clicked_idx" ON "HelpSearchQuery"("clicked");

-- CreateIndex
CREATE INDEX "HelpArticleFeedback_article_id_idx" ON "HelpArticleFeedback"("article_id");

-- CreateIndex
CREATE INDEX "HelpArticleFeedback_created_at_idx" ON "HelpArticleFeedback"("created_at");

-- CreateIndex
CREATE INDEX "SupportRequest_user_id_idx" ON "SupportRequest"("user_id");

-- CreateIndex
CREATE INDEX "SupportRequest_status_idx" ON "SupportRequest"("status");

-- CreateIndex
CREATE INDEX "SupportRequest_created_at_idx" ON "SupportRequest"("created_at");

-- AddForeignKey
ALTER TABLE "HelpSearchQuery" ADD CONSTRAINT "HelpSearchQuery_article_id_fkey" FOREIGN KEY ("article_id") REFERENCES "HelpArticle"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "HelpArticleFeedback" ADD CONSTRAINT "HelpArticleFeedback_article_id_fkey" FOREIGN KEY ("article_id") REFERENCES "HelpArticle"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
