import { NextResponse } from "next/server";
import { getCurseForgeClient } from "@/lib/curseforge";

export async function GET() {
    try {
        const client = getCurseForgeClient();
        const categories = await client.getCategories();

        return NextResponse.json(categories);
    } catch (error) {
        console.error("Error fetching categories:", error);
        return NextResponse.json(
            { error: "Failed to fetch categories" },
            { status: 500 }
        );
    }
}
