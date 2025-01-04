// Example model schema from the Drizzle docs
// https://orm.drizzle.team/docs/sql-schema-declaration

import { sql } from "drizzle-orm";
import {
  pgTableCreator,
  timestamp,
  varchar,
  integer,
  text,
  primaryKey,
} from "drizzle-orm/pg-core";

/**
 * This is an example of how to use the multi-project schema feature of Drizzle ORM. Use the same
 * database instance for multiple projects.
 *
 * @see https://orm.drizzle.team/docs/goodies#multi-project-schema
 */
export const createTable = pgTableCreator((name) => `gitdiagram_${name}`);

export const diagramCache = createTable(
  "diagram_cache",
  {
    username: varchar("username", { length: 256 }).notNull(),
    repo: varchar("repo", { length: 256 }).notNull(),
    diagram: varchar("diagram", { length: 10000 }).notNull(), // Adjust length as needed
    explanation: varchar("explanation", { length: 10000 })
      .notNull()
      .default("No explanation provided"), // Default explanation to avoid data loss of existing rows
    createdAt: timestamp("created_at", { withTimezone: true })
      .default(sql`CURRENT_TIMESTAMP`)
      .notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).$onUpdate(
      () => new Date(),
    ),
  },
  (table) => ({
    pk: primaryKey({ columns: [table.username, table.repo] }),
  }),
);

export const audioBlobStorage = createTable(
    "audio_blob_storage",
    {
      username: varchar("username", { length: 256 }).notNull(),
      repo: varchar("repo", { length: 256 }).notNull(),
      audioBase64: text("audio_base64").notNull(), // Storing the actual audio data
      duration: integer("duration"), // Duration of the audio in seconds
      format: varchar("format", { length: 50 }),
      webVtt: text("webvtt"), // Format of the audio file (e.g., mp3, wav)
      createdAt: timestamp("created_at", { withTimezone: true })
        .default(sql`CURRENT_TIMESTAMP`)
        .notNull(),
      updatedAt: timestamp("updated_at", { withTimezone: true }).$onUpdate(
        () => new Date(),
      ),
    },
    (table) => ({
      pk: primaryKey({ columns: [table.username, table.repo] }),
    }),
  );