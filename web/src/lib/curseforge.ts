interface ModAsset {
  id: number;
  modId: number;
  title: string;
  description: string;
  thumbnailUrl: string;
  url: string;
}

interface ModAuthor {
  id: number;
  name: string;
  url: string;
}

interface Category {
  id: number;
  gameId: number;
  name: string;
  slug: string;
  url: string;
  iconUrl: string;
  dateModified: string;
  isClass?: boolean;
  classId?: number;
  parentCategoryId?: number;
}

interface ModLinks {
  websiteUrl?: string;
  wikiUrl?: string;
  issuesUrl?: string;
  sourceUrl?: string;
}

interface FileHash {
  value: string;
  algo: number;
}

interface FileDependency {
  modId: number;
  relationType: number;
}

interface ModFile {
  id: number;
  gameId: number;
  modId: number;
  isAvailable: boolean;
  displayName: string;
  fileName: string;
  releaseType: number;
  fileStatus: number;
  hashes: FileHash[];
  fileDate: string;
  fileLength: number;
  downloadCount: number;
  downloadUrl?: string;
  gameVersions: string[];
  dependencies: FileDependency[];
  fileFingerprint?: number;
}

export interface CurseForgeMod {
  id: number;
  gameId: number;
  name: string;
  slug: string;
  links: ModLinks;
  summary: string;
  status: number;
  downloadCount: number;
  isFeatured: boolean;
  primaryCategoryId: number;
  categories: Category[];
  mainFileId: number;
  dateCreated: string;
  dateModified: string;
  dateReleased: string;
  authors: ModAuthor[];
  logo?: ModAsset;
  screenshots: ModAsset[];
  latestFiles: ModFile[];
  allowModDistribution?: boolean;
  rating?: number;
}

interface ApiResponse<T> {
  data: T;
  pagination?: {
    index: number;
    pageSize: number;
    resultCount: number;
    totalCount: number;
  };
}

// Minecraft game ID (fixed value in CurseForge)
export const MINECRAFT_GAME_ID = 432;

// Modpack class ID (fixed value in CurseForge)
export const MODPACK_CLASS_ID = 4471;

class CurseForgeClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.baseUrl = "https://api.curseforge.com/v1";
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          "x-api-key": this.apiKey,
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(
          `CurseForge API error: ${response.status} ${response.statusText}`
        );
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("CurseForge API request timeout (30s)");
      }
      throw error;
    }
  }

  async getMod(modId: number): Promise<CurseForgeMod> {
    const response = await this.request<CurseForgeMod>(`/mods/${modId}`);
    return response.data;
  }

  async getModFiles(
    modId: number,
    gameVersion?: string,
    pageSize?: number
  ): Promise<ModFile[]> {
    const params = new URLSearchParams();
    if (gameVersion) params.append("gameVersion", gameVersion);
    if (pageSize) params.append("pageSize", pageSize.toString());

    const queryString = params.toString();
    const response = await this.request<ModFile[]>(
      `/mods/${modId}/files${queryString ? `?${queryString}` : ""}`
    );
    return response.data;
  }

  async searchMods(
    searchFilter: string,
    categoryId?: number,
    pageSize: number = 20,
    index: number = 0
  ): Promise<{ data: CurseForgeMod[]; pagination: any }> {
    const params = new URLSearchParams({
      gameId: MINECRAFT_GAME_ID.toString(),
      classId: MODPACK_CLASS_ID.toString(),
      searchFilter,
      pageSize: pageSize.toString(),
      index: index.toString(),
    });

    if (categoryId) {
      params.append("categoryId", categoryId.toString());
    }

    const response = await this.request<CurseForgeMod[]>(
      `/mods/search?${params.toString()}`
    );
    return {
      data: response.data,
      pagination: response.pagination,
    };
  }

  async getCategories(): Promise<Category[]> {
    const response = await this.request<Category[]>(
      `/categories?gameId=${MINECRAFT_GAME_ID}&classId=${MODPACK_CLASS_ID}`
    );
    return response.data;
  }
}

// Singleton instance
let curseForgeClient: CurseForgeClient | null = null;

export function getCurseForgeClient(): CurseForgeClient {
  const apiKey = process.env.CURSEFORGE_API_KEY;

  if (!apiKey) {
    throw new Error("CURSEFORGE_API_KEY environment variable is required");
  }

  if (!curseForgeClient) {
    curseForgeClient = new CurseForgeClient(apiKey);
  }

  return curseForgeClient;
}

// Extract CurseForge ID from URL or return as-is if it's a number
export function extractCurseForgeId(input: string): number | null {
  // If it's a number, return it
  const numericId = parseInt(input, 10);
  if (!isNaN(numericId)) {
    return numericId;
  }

  // Try to extract from CurseForge URL
  // e.g., https://www.curseforge.com/minecraft/modpacks/all-the-mods-9
  // or https://www.curseforge.com/minecraft/modpacks/all-the-mods-9/files/123456
  const urlMatch = input.match(
    /curseforge\.com\/minecraft\/modpacks\/([^\/]+)/
  );
  if (urlMatch) {
    // The URL contains the slug, not the ID, so we can't extract the ID directly
    // We would need to search for it, but for now we return null
    return null;
  }

  return null;
}
