// ── MueJam Library — TypeScript Interfaces ──

export interface UserProfile {
  id: string;
  handle: string;
  display_name: string;
  avatar_url?: string;
  avatar_key?: string;
  bio?: string;
  follower_count: number;
  following_count: number;
  is_following?: boolean;
  is_blocked?: boolean;
  created_at: string;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
  story_count?: number;
}

export interface Story {
  id: string;
  slug: string;
  title: string;
  blurb?: string;
  cover_url?: string;
  cover_key?: string;
  author: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url">;
  tags: Tag[];
  chapter_count: number;
  status: "draft" | "published";
  created_at: string;
  updated_at: string;
}

export interface Chapter {
  id: string;
  story_id: string;
  title: string;
  content?: string; // markdown
  order: number;
  word_count: number;
  status: "draft" | "published";
  created_at: string;
  updated_at: string;
}

export interface Whisper {
  id: string;
  author: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url">;
  body: string;
  media_url?: string;
  scope: "GLOBAL" | "STORY" | "HIGHLIGHT";
  story_id?: string;
  highlight_id?: string;
  quote_text?: string;
  like_count: number;
  reply_count: number;
  is_liked?: boolean;
  parent_id?: string;
  created_at: string;
}

export interface Highlight {
  id: string;
  chapter_id: string;
  user_id: string;
  quote_text: string;
  start_offset: number;
  end_offset: number;
  created_at: string;
}

export interface Shelf {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  story_count: number;
  created_at: string;
}

export interface ShelfItem {
  story: Story;
  added_at: string;
}

export interface Notification {
  id: string;
  type: "follow" | "like" | "reply" | "chapter" | "story" | "shelf";
  message: string;
  actor?: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url">;
  target_url?: string;
  is_read: boolean;
  created_at: string;
}

export interface SearchSuggestion {
  stories: Pick<Story, "id" | "slug" | "title" | "cover_url" | "author">[];
  tags: Pick<Tag, "id" | "name" | "slug" | "story_count">[];
  authors: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url">[];
}

export interface CursorPage<T> {
  results: T[];
  next_cursor?: string | null;
  has_more: boolean;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface PresignResponse {
  object_key: string;
  upload_url: string;
  fields?: Record<string, string>;
  public_url?: string;
}

export interface ReaderSettings {
  theme: "light" | "dark";
  fontSize: number;
  lineWidth: "narrow" | "medium" | "wide";
}

export const DEFAULT_READER_SETTINGS: ReaderSettings = {
  theme: "light",
  fontSize: 18,
  lineWidth: "medium",
};
