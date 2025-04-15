import { pgTable, text, serial, integer, boolean, jsonb, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// YouTube video schema
export const videos = pgTable("videos", {
  id: text("id").primaryKey(), // YouTube video ID
  title: text("title").notNull(),
  description: text("description"),
  channelId: text("channel_id"),
  channelTitle: text("channel_title"),
  publishedAt: text("published_at"),
  thumbnail: text("thumbnail"),
  duration: text("duration"),
  viewCount: text("view_count"),
  likeCount: text("like_count"),
  commentCount: text("comment_count"),
  tags: text("tags").array(),
  categoryId: text("category_id"),
});

export const insertVideoSchema = createInsertSchema(videos).omit({
  id: true,
});

export type InsertVideo = z.infer<typeof insertVideoSchema>;
export type Video = typeof videos.$inferSelect;

// Watch history schema
export const watchHistory = pgTable("watch_history", {
  id: serial("id").primaryKey(),
  userId: integer("user_id"),
  videoId: text("video_id").notNull(),
  watchedAt: timestamp("watched_at").notNull().defaultNow(),
  watchedPercentage: integer("watched_percentage").default(0),
});

export const insertWatchHistorySchema = createInsertSchema(watchHistory).omit({
  id: true,
});

export type InsertWatchHistory = z.infer<typeof insertWatchHistorySchema>;
export type WatchHistory = typeof watchHistory.$inferSelect;

// Frontend types that aren't stored in DB
export const videoSearchRequestSchema = z.object({
  query: z.string().min(1),
  maxResults: z.number().optional().default(10),
  categoryId: z.string().optional(),
});

export type VideoSearchRequest = z.infer<typeof videoSearchRequestSchema>;

export const videoRecommendationRequestSchema = z.object({
  videoId: z.string().optional(),
  userId: z.number().optional(),
  maxResults: z.number().optional().default(8),
  categoryId: z.string().optional(),
});

export type VideoRecommendationRequest = z.infer<typeof videoRecommendationRequestSchema>;

export const categorySchema = z.object({
  id: z.string(),
  title: z.string(),
});

export type Category = z.infer<typeof categorySchema>;
