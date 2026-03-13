-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "discordId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "avatar" TEXT,
    "isAdmin" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Modpack" (
    "id" SERIAL NOT NULL,
    "curseforgeId" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "logoUrl" TEXT,
    "author" TEXT,
    "gameVersions" TEXT,
    "categories" TEXT,
    "totalDownloads" INTEGER NOT NULL DEFAULT 0,
    "cachedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Modpack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TranslationPack" (
    "id" TEXT NOT NULL,
    "modpackId" INTEGER NOT NULL,
    "modpackVersion" TEXT NOT NULL,
    "userId" TEXT,
    "sourceLang" TEXT NOT NULL DEFAULT 'en_us',
    "targetLang" TEXT NOT NULL DEFAULT 'ko_kr',
    "status" TEXT NOT NULL DEFAULT 'pending',
    "resourcePackPath" TEXT,
    "overrideFilePath" TEXT,
    "isManualTranslation" BOOLEAN NOT NULL DEFAULT false,
    "llmModel" TEXT,
    "temperature" DOUBLE PRECISION,
    "batchSize" INTEGER,
    "usedGlossary" BOOLEAN NOT NULL DEFAULT false,
    "reviewed" BOOLEAN NOT NULL DEFAULT false,
    "downloadCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "durationSeconds" DOUBLE PRECISION,
    "fileCount" INTEGER,
    "handlerStats" TEXT,
    "inputTokens" INTEGER,
    "outputTokens" INTEGER,
    "totalEntries" INTEGER,
    "totalTokens" INTEGER,
    "translatedEntries" INTEGER,

    CONSTRAINT "TranslationPack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Review" (
    "id" TEXT NOT NULL,
    "packId" TEXT NOT NULL,
    "userId" TEXT,
    "works" BOOLEAN NOT NULL,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "ipAddress" TEXT,
    "isAnonymous" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Review_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Map" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "thumbnailUrl" TEXT,
    "originalLink" TEXT,
    "author" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Map_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MapTranslation" (
    "id" TEXT NOT NULL,
    "mapId" INTEGER NOT NULL,
    "version" TEXT NOT NULL,
    "userId" TEXT,
    "sourceLang" TEXT NOT NULL DEFAULT 'en_us',
    "targetLang" TEXT NOT NULL DEFAULT 'ko_kr',
    "status" TEXT NOT NULL DEFAULT 'pending',
    "resourcePackUrl" TEXT,
    "overrideFileUrl" TEXT,
    "originalLink" TEXT,
    "minecraftVersion" TEXT,
    "downloadCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "MapTranslation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MapReview" (
    "id" TEXT NOT NULL,
    "mapTranslationId" TEXT NOT NULL,
    "userId" TEXT,
    "works" BOOLEAN NOT NULL,
    "rating" INTEGER NOT NULL,
    "comment" TEXT,
    "ipAddress" TEXT,
    "isAnonymous" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MapReview_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_discordId_key" ON "User"("discordId");

-- CreateIndex
CREATE UNIQUE INDEX "Modpack_curseforgeId_key" ON "Modpack"("curseforgeId");

-- CreateIndex
CREATE INDEX "TranslationPack_modpackId_idx" ON "TranslationPack"("modpackId");

-- CreateIndex
CREATE INDEX "TranslationPack_modpackVersion_idx" ON "TranslationPack"("modpackVersion");

-- CreateIndex
CREATE INDEX "TranslationPack_status_idx" ON "TranslationPack"("status");

-- CreateIndex
CREATE INDEX "TranslationPack_modpackId_modpackVersion_idx" ON "TranslationPack"("modpackId", "modpackVersion");

-- CreateIndex
CREATE INDEX "Review_packId_idx" ON "Review"("packId");

-- CreateIndex
CREATE INDEX "Review_ipAddress_idx" ON "Review"("ipAddress");

-- CreateIndex
CREATE UNIQUE INDEX "Map_slug_key" ON "Map"("slug");

-- CreateIndex
CREATE INDEX "MapTranslation_mapId_idx" ON "MapTranslation"("mapId");

-- CreateIndex
CREATE INDEX "MapTranslation_status_idx" ON "MapTranslation"("status");

-- CreateIndex
CREATE INDEX "MapReview_mapTranslationId_idx" ON "MapReview"("mapTranslationId");

-- CreateIndex
CREATE INDEX "MapReview_ipAddress_idx" ON "MapReview"("ipAddress");

-- AddForeignKey
ALTER TABLE "TranslationPack" ADD CONSTRAINT "TranslationPack_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TranslationPack" ADD CONSTRAINT "TranslationPack_modpackId_fkey" FOREIGN KEY ("modpackId") REFERENCES "Modpack"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Review" ADD CONSTRAINT "Review_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Review" ADD CONSTRAINT "Review_packId_fkey" FOREIGN KEY ("packId") REFERENCES "TranslationPack"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MapTranslation" ADD CONSTRAINT "MapTranslation_mapId_fkey" FOREIGN KEY ("mapId") REFERENCES "Map"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MapTranslation" ADD CONSTRAINT "MapTranslation_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MapReview" ADD CONSTRAINT "MapReview_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MapReview" ADD CONSTRAINT "MapReview_mapTranslationId_fkey" FOREIGN KEY ("mapTranslationId") REFERENCES "MapTranslation"("id") ON DELETE CASCADE ON UPDATE CASCADE;
