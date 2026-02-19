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
  author: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url" | "is_blocked">;
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
  author: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url" | "is_blocked">;
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
  actor?: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url" | "is_blocked">;
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
  status?: number;
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

// ── Admin Types ──
export interface AuditLog {
  id: string;
  user_id: string;
  user_handle: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  user_agent: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SuspiciousPattern {
  pattern_type: string;
  description: string;
  occurrences: number;
  severity: "low" | "medium" | "high" | "critical";
  first_seen: string;
  last_seen: string;
}

export interface AlertRequest {
  alert_type: string;
  message: string;
  severity: "low" | "medium" | "high" | "critical";
}

export interface AuditLogParams {
  action?: string;
  user_id?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  cursor?: string;
  page_size?: number;
}

// ── Analytics Types ──
export interface AnalyticsDashboard {
  total_views: number;
  total_reads: number;
  total_followers: number;
  engagement_rate: number;
  top_stories: StoryMetrics[];
  recent_activity: ActivityMetric[];
}

export interface StoryMetrics {
  story_id: string;
  story_title: string;
  views: number;
  reads: number;
  engagement: number;
}

export interface ActivityMetric {
  date: string;
  views: number;
  reads: number;
  engagement: number;
}

export interface DateRangeParams {
  start_date?: string;
  end_date?: string;
}

export interface FollowerGrowthData {
  data_points: Array<{
    date: string;
    followers: number;
    new_followers: number;
    unfollows: number;
  }>;
  total_growth: number;
  growth_rate: number;
}

export interface MobileMetrics {
  ios_users: number;
  android_users: number;
  mobile_engagement_rate: number;
  app_version_distribution: Record<string, number>;
  device_types: Record<string, number>;
}

export interface StoryAnalytics {
  story_id: string;
  views: number;
  unique_readers: number;
  completion_rate: number;
  average_read_time: number;
  engagement_score: number;
  demographics: Demographics;
  traffic_sources: TrafficSource[];
  chapter_performance: ChapterMetrics[];
  time_series: TimeSeriesData[];
}

export interface Demographics {
  age_groups: Record<string, number>;
  locations: Record<string, number>;
}

export interface TrafficSource {
  source: string;
  visits: number;
  percentage: number;
}

export interface ChapterMetrics {
  chapter_id: string;
  chapter_title: string;
  views: number;
  completion_rate: number;
}

export interface TimeSeriesData {
  date: string;
  value: number;
}

// ── GDPR Types ──
export interface PrivacySettings {
  profile_visibility: "public" | "followers" | "private";
  show_reading_activity: boolean;
  show_followers: boolean;
  show_following: boolean;
  allow_story_recommendations: boolean;
  allow_personalized_ads: boolean;
  allow_analytics_tracking: boolean;
  allow_email_notifications: boolean;
}

export interface ConsentRecord {
  consent_type: string;
  granted: boolean;
  granted_at: string;
  withdrawn_at?: string;
  ip_address: string;
}

export interface ExportRequest {
  export_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  requested_at: string;
  completed_at?: string;
  download_url?: string;
  expires_at?: string;
}

export interface ExportStatus {
  export_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  download_url?: string;
  expires_at?: string;
}

export interface DeletionRequest {
  deletion_id: string;
  status: "pending" | "processing" | "completed" | "cancelled";
  requested_at: string;
  scheduled_for: string;
  completed_at?: string;
  can_cancel: boolean;
}

export interface DeletionStatus {
  deletion_id: string;
  status: "pending" | "processing" | "completed" | "cancelled";
  scheduled_for: string;
  can_cancel: boolean;
}

// ── Security Types ──
export interface TwoFactorStatus {
  enabled: boolean;
  method: "totp" | "sms" | null;
  backup_codes_remaining: number;
}

export interface TwoFactorSetup {
  secret: string;
  qr_code_url: string;
  backup_codes: string[];
}

export interface TrustedDevice {
  device_id: string;
  device_name: string;
  device_type: "desktop" | "mobile" | "tablet";
  platform: string;
  browser: string;
  last_active: string;
  trusted_at: string;
  ip_address: string;
}

// ── Moderation Types ──
export interface ModerationItem {
  id: string;
  content_type: "story" | "chapter" | "whisper" | "user";
  content_id: string;
  content_preview: string;
  reporter_id: string;
  report_reason: string;
  report_details: string;
  severity: "low" | "medium" | "high";
  status: "pending" | "reviewing" | "resolved" | "escalated";
  created_at: string;
  assigned_to?: string;
}

export interface ModerationAction {
  action: "approve" | "hide" | "warn" | "ban" | "escalate";
  reason: string;
  duration?: number;
  notes?: string;
}

export interface ModerationHistory {
  action: string;
  moderator_id: string;
  moderator_handle: string;
  reason: string;
  created_at: string;
}

export interface ModerationMetrics {
  pending_items: number;
  resolved_today: number;
  average_resolution_time: number;
  items_by_severity: Record<string, number>;
  items_by_type: Record<string, number>;
}

// ── Admin Metrics Types ──
export interface BusinessMetrics {
  total_users: number;
  active_users_today: number;
  total_stories: number;
  stories_published_today: number;
  total_chapters: number;
  chapters_published_today: number;
  total_whispers: number;
  whispers_today: number;
  user_growth_rate: number;
  content_growth_rate: number;
}

export interface RealTimeMetrics {
  active_users_now: number;
  active_readers: number;
  active_writers: number;
  requests_per_minute: number;
  average_response_time: number;
  error_rate: number;
}

export interface QueueParams {
  content_type?: string;
  severity?: string;
  status?: string;
  cursor?: string;
  page_size?: number;
}

// ── Discovery Types ──
export interface DiscoveryParams {
  genre?: string;
  tags?: string;
  length?: string;
  cursor?: string;
  page_size?: number;
}

export interface PaginationParams {
  cursor?: string;
  page_size?: number;
}

// ── Device Types ──
export interface DeviceToken {
  token: string;
  platform: "ios" | "android" | "web";
  device_name: string;
}

export interface RegisteredDevice {
  device_id: string;
  device_name: string;
  platform: string;
  registered_at: string;
  last_active: string;
}

export interface NotificationPreferences {
  enabled: boolean;
  follows: boolean;
  likes: boolean;
  replies: boolean;
  chapters: boolean;
  stories: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

// ── Help Types ──
export interface HelpCategory {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  article_count: number;
  order: number;
}

export interface HelpArticle {
  id: string;
  category_id: string;
  title: string;
  slug: string;
  content: string;
  helpful_count: number;
  not_helpful_count: number;
  related_articles: Array<Pick<HelpArticle, "id" | "title" | "slug">>;
  created_at: string;
  updated_at: string;
}

export interface ContactForm {
  name: string;
  email: string;
  subject: string;
  message: string;
  category: string;
}

// ── Status Types ──
export interface HealthStatus {
  status: "healthy" | "degraded" | "down";
  database: ComponentStatus;
  cache: ComponentStatus;
  storage: ComponentStatus;
  websocket: ComponentStatus;
  timestamp: string;
}

export interface ComponentStatus {
  status: "operational" | "degraded" | "down";
  response_time?: number;
  error?: string;
}

export interface SystemStatus {
  overall_status: "operational" | "degraded" | "maintenance" | "major_outage";
  components: Array<{
    name: string;
    status: ComponentStatus;
  }>;
  incidents: Incident[];
  scheduled_maintenance: MaintenanceWindow[];
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: "investigating" | "identified" | "monitoring" | "resolved";
  severity: "minor" | "major" | "critical";
  started_at: string;
  resolved_at?: string;
  updates: IncidentUpdate[];
}

export interface IncidentUpdate {
  message: string;
  status: string;
  created_at: string;
}

export interface MaintenanceWindow {
  id: string;
  title: string;
  description: string;
  scheduled_start: string;
  scheduled_end: string;
  affected_components: string[];
}

// ── Activity Feed Types ──
export interface ActivityFeedItem {
  id: string;
  type: "story_published" | "chapter_published" | "whisper_created" | "user_followed";
  actor: Pick<UserProfile, "id" | "handle" | "display_name" | "avatar_url" | "is_blocked">;
  target?: {
    type: "story" | "chapter" | "whisper" | "user";
    id: string;
    title?: string;
    slug?: string;
    content?: string;
  };
  created_at: string;
}

// ── Legal Types ──
export interface LegalDocument {
  id: string;
  document_type: "terms" | "privacy" | "cookies" | "guidelines" | "copyright";
  title: string;
  content: string; // markdown
  version: string;
  last_updated: string;
  effective_date: string;
}

export interface TermsAcceptance {
  user_id: string;
  document_type: string;
  version: string;
  accepted_at: string;
  requires_acceptance: boolean;
  latest_version: string;
}

// ── WebSocket Types ──
export type WebSocketMessageType =
  | "notification"
  | "whisper_reply"
  | "story_update"
  | "follow"
  | "system";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload: unknown;
  timestamp: string;
}

export interface StoryUpdate {
  story_id: string;
  action: "published" | "updated" | "deleted";
  story?: Story;
}

export interface FollowEvent {
  follower_id: string;
  follower_handle: string;
  follower_display_name: string;
  follower_avatar_url?: string;
  followed_at: string;
}

// ── Content Reporting ──

export type ReportReason =
  | "spam"
  | "harassment"
  | "hate_speech"
  | "violence"
  | "sexual_content"
  | "copyright"
  | "misinformation"
  | "other";

export type ReportStatus = "pending" | "under_review" | "resolved" | "dismissed";

export type ReportableContentType = "story" | "whisper" | "user" | "comment";

export interface ReportRequest {
  content_type: ReportableContentType;
  content_id: string;
  reason: ReportReason;
  additional_context?: string;
}

export interface Report {
  id: string;
  content_type: ReportableContentType;
  content_id: string;
  reason: ReportReason;
  additional_context?: string;
  status: ReportStatus;
  reporter_id: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolution_note?: string;
}

export interface ReportListParams {
  status?: ReportStatus;
  content_type?: ReportableContentType;
  cursor?: string;
  limit?: number;
}
