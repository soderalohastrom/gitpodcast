"use server";

import { db } from "~/server/db";
import { eq, and } from "drizzle-orm";
import { diagramCache, audioBlobStorage } from "~/server/db/schema";

export async function getCachedDiagram(username: string, repo: string) {
  try {
    const cached = await db
      .select()
      .from(diagramCache)
      .where(
        and(eq(diagramCache.username, username), eq(diagramCache.repo, repo)),
      )
      .limit(1);

    return cached[0]?.diagram ?? null;
  } catch (error) {
    console.error("Error fetching cached diagram:", error);
    return null;
  }
}

export async function getCachedAudioBase64(username: string, repo: string): Promise<string | null> {
    try {
      const cached = await db
        .select()
        .from(audioBlobStorage)
        .where(
          and(eq(audioBlobStorage.username, username), eq(audioBlobStorage.repo, repo)),
        )
        .limit(1);

      return cached[0]?.audioBase64 ?? null; // Assuming audioBase64 contains Base64 audio data
    } catch (error) {
      console.error("Error fetching cached audio data:", error);
      return null;
    }
  }

  export async function getCachedWebVtt(username: string, repo: string): Promise<string | null> {
    try {
        const cached = await db
            .select()
            .from(audioBlobStorage)
            .where(
                and(eq(audioBlobStorage.username, username), eq(audioBlobStorage.repo, repo)),
            )
            .limit(1);

        return cached[0]?.webVtt ?? null; // Assuming webVtt contains the VTT data
    } catch (error) {
        console.error("Error fetching cached WebVTT data:", error);
        return null;
    }
}

export async function getCachedExplanation(username: string, repo: string) {
  try {
    const cached = await db
      .select()
      .from(diagramCache)
      .where(
        and(eq(diagramCache.username, username), eq(diagramCache.repo, repo)),
      )
      .limit(1);

    return cached[0]?.explanation ?? null;
  } catch (error) {
    console.error("Error fetching cached explanation:", error);
    return null;
  }
}

export async function cacheDiagramAndExplanation(
  username: string,
  repo: string,
  diagram: string,
  explanation: string,
) {
  try {
    await db
      .insert(diagramCache)
      .values({
        username,
        repo,
        explanation,
        diagram,
      })
      .onConflictDoUpdate({
        target: [diagramCache.username, diagramCache.repo],
        set: {
          diagram,
          updatedAt: new Date(),
        },
      });
  } catch (error) {
    console.error("Error caching diagram:", error);
  }
}

export async function cacheAudioAndWebVtt(
    username: string,
    repo: string,
    audioBase64: string,
    webVtt?: string // Optional parameter for WebVTT caption data
) {
    try {
        await db
            .insert(audioBlobStorage)
            .values({
                username,
                repo,
                audioBase64,
                webVtt, // Include webVtt in the values to insert
            })
            .onConflictDoUpdate({
                target: [audioBlobStorage.username, audioBlobStorage.repo],
                set: {
                    audioBase64,
                    webVtt, // Update webVtt column if conflict occurs
                    updatedAt: new Date(),
                },
            });
    } catch (error) {
        console.error("Error caching audio and WebVTT data:", error);
    }
}
