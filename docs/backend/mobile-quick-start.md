# Mobile API Quick Start Guide

## Overview

This guide helps mobile developers quickly integrate with the MueJam Library API. For comprehensive documentation, see [Mobile API Documentation](mobile-api.md).

## Prerequisites

- Clerk account for authentication
- Firebase Cloud Messaging (FCM) for Android push notifications
- Apple Push Notification service (APNs) for iOS push notifications
- API base URL: `https://api.muejam.com/v1`

## Step 1: Add Client Type Header

Include the `X-Client-Type` header in all requests:

**iOS:**
```swift
var request = URLRequest(url: url)
request.setValue("mobile-ios", forHTTPHeaderField: "X-Client-Type")
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
```

**Android (Kotlin):**
```kotlin
val request = Request.Builder()
    .url(url)
    .addHeader("X-Client-Type", "mobile-android")
    .addHeader("Authorization", "Bearer $token")
    .build()
```

## Step 2: Register for Push Notifications

**iOS:**
```swift
// Get device token from APNs
func application(_ application: UIApplication, 
                didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    
    // Register with backend
    let body = [
        "token": token,
        "platform": "ios",
        "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String
    ]
    
    // POST to /v1/devices/register
}
```

**Android (Kotlin):**
```kotlin
// Get device token from FCM
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        
        // Register with backend
        val body = JSONObject().apply {
            put("token", token)
            put("platform", "android")
            put("app_version", BuildConfig.VERSION_NAME)
        }
        
        // POST to /v1/devices/register
    }
}
```

## Step 3: Handle Deep Links

**iOS (AppDelegate.swift):**
```swift
func application(_ app: UIApplication, 
                open url: URL, 
                options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
    guard url.scheme == "muejam" else { return false }
    
    let path = url.host ?? ""
    let id = url.lastPathComponent
    
    switch path {
    case "story":
        navigateToStory(id: id)
    case "chapter":
        navigateToChapter(id: id)
    case "whisper":
        navigateToWhisper(id: id)
    case "profile":
        navigateToProfile(id: id)
    default:
        return false
    }
    
    return true
}
```

**Android (MainActivity.kt):**
```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    handleDeepLink(intent)
}

override fun onNewIntent(intent: Intent?) {
    super.onNewIntent(intent)
    handleDeepLink(intent)
}

private fun handleDeepLink(intent: Intent?) {
    val data = intent?.data ?: return
    
    when (data.host) {
        "story" -> navigateToStory(data.lastPathSegment)
        "chapter" -> navigateToChapter(data.lastPathSegment)
        "whisper" -> navigateToWhisper(data.lastPathSegment)
        "profile" -> navigateToProfile(data.lastPathSegment)
    }
}
```

## Step 4: Implement Offline Support

**iOS:**
```swift
// Add ETag to cache
func cacheResponse(_ response: HTTPURLResponse, data: Data, for url: URL) {
    if let etag = response.allHeaderFields["ETag"] as? String {
        UserDefaults.standard.set(etag, forKey: "etag_\(url.absoluteString)")
        // Cache data
    }
}

// Use conditional request
func makeConditionalRequest(url: URL) {
    var request = URLRequest(url: url)
    
    if let etag = UserDefaults.standard.string(forKey: "etag_\(url.absoluteString)") {
        request.setValue(etag, forHTTPHeaderField: "If-None-Match")
    }
    
    // If response is 304, use cached data
}
```

**Android (Kotlin):**
```kotlin
// Add ETag to cache
fun cacheResponse(response: Response, url: String) {
    val etag = response.header("ETag")
    if (etag != null) {
        sharedPreferences.edit()
            .putString("etag_$url", etag)
            .apply()
        // Cache response body
    }
}

// Use conditional request
fun makeConditionalRequest(url: String): Request {
    val builder = Request.Builder().url(url)
    
    val etag = sharedPreferences.getString("etag_$url", null)
    if (etag != null) {
        builder.addHeader("If-None-Match", etag)
    }
    
    return builder.build()
    // If response is 304, use cached data
}
```

## Step 5: Handle Errors

**iOS:**
```swift
struct APIError: Codable {
    let error: ErrorDetails
}

struct ErrorDetails: Codable {
    let code: String
    let message: String
    let details: [String: AnyCodable]?
    let retryGuidance: String?
    
    enum CodingKeys: String, CodingKey {
        case code, message, details
        case retryGuidance = "retry_guidance"
    }
}

func handleError(_ error: APIError) {
    switch error.error.code {
    case "TOKEN_EXPIRED":
        // Refresh token and retry
        refreshToken()
    case "RATE_LIMIT_EXCEEDED":
        // Wait and retry
        if let retryAfter = error.error.details?["retry_after"]?.value as? Int {
            DispatchQueue.main.asyncAfter(deadline: .now() + .seconds(retryAfter)) {
                // Retry request
            }
        }
    case "SYNC_CONFLICT":
        // Fetch latest and reapply changes
        resolveConflict()
    default:
        // Show error message to user
        showAlert(message: error.error.message)
    }
}
```

**Android (Kotlin):**
```kotlin
data class APIError(
    val error: ErrorDetails
)

data class ErrorDetails(
    val code: String,
    val message: String,
    val details: Map<String, Any>?,
    @SerializedName("retry_guidance")
    val retryGuidance: String?
)

fun handleError(error: APIError) {
    when (error.error.code) {
        "TOKEN_EXPIRED" -> {
            // Refresh token and retry
            refreshToken()
        }
        "RATE_LIMIT_EXCEEDED" -> {
            // Wait and retry
            val retryAfter = error.error.details?.get("retry_after") as? Int ?: 60
            Handler(Looper.getMainLooper()).postDelayed({
                // Retry request
            }, retryAfter * 1000L)
        }
        "SYNC_CONFLICT" -> {
            // Fetch latest and reapply changes
            resolveConflict()
        }
        else -> {
            // Show error message to user
            showError(error.error.message)
        }
    }
}
```

## Common Patterns

### Fetch Stories with Deep Links

**Request:**
```http
GET /v1/stories HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <token>
X-Client-Type: mobile-ios
```

**Response includes deep links:**
```json
{
  "data": [
    {
      "id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "title": "The Midnight Garden",
      "deep_link": "muejam://story/clx1a2b3c4d5e6f7g8h9i0j1"
    }
  ]
}
```

### Upload Image

**iOS:**
```swift
func uploadImage(_ image: UIImage) {
    guard let imageData = image.jpegData(compressionQuality: 0.8) else { return }
    
    var request = URLRequest(url: URL(string: "https://api.muejam.com/v1/uploads/media")!)
    request.httpMethod = "POST"
    request.setValue("mobile-ios", forHTTPHeaderField: "X-Client-Type")
    request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    
    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(imageData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    // Send request
}
```

**Android (Kotlin):**
```kotlin
fun uploadImage(bitmap: Bitmap) {
    val stream = ByteArrayOutputStream()
    bitmap.compress(Bitmap.CompressFormat.JPEG, 80, stream)
    val imageData = stream.toByteArray()
    
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart(
            "file",
            "image.jpg",
            imageData.toRequestBody("image/jpeg".toMediaType())
        )
        .build()
    
    val request = Request.Builder()
        .url("https://api.muejam.com/v1/uploads/media")
        .addHeader("X-Client-Type", "mobile-android")
        .addHeader("Authorization", "Bearer $token")
        .post(requestBody)
        .build()
    
    // Send request
}
```

### Sync Data

**Request:**
```http
GET /v1/sync/stories?since=2024-01-15T10:30:00Z HTTP/1.1
Host: api.muejam.com
Authorization: Bearer <token>
X-Client-Type: mobile-android
```

**Response:**
```json
{
  "data": [
    {
      "id": "clx1a2b3c4d5e6f7g8h9i0j1",
      "title": "Updated Story",
      "updated_at": "2024-01-15T11:45:00Z"
    }
  ],
  "sync_timestamp": "2024-01-15T12:00:00Z"
}
```

## Rate Limiting

Mobile clients get 150 requests per minute (300 when authenticated).

**Handle rate limits:**
```swift
// iOS
if response.statusCode == 429 {
    if let retryAfter = response.allHeaderFields["Retry-After"] as? String,
       let seconds = Int(retryAfter) {
        DispatchQueue.main.asyncAfter(deadline: .now() + .seconds(seconds)) {
            // Retry request
        }
    }
}
```

```kotlin
// Android
if (response.code == 429) {
    val retryAfter = response.header("Retry-After")?.toIntOrNull() ?: 60
    Handler(Looper.getMainLooper()).postDelayed({
        // Retry request
    }, retryAfter * 1000L)
}
```

## Testing

Use test endpoints to verify integration:

**Test Push Notification:**
```http
POST /v1/test/push-notification HTTP/1.1
Content-Type: application/json

{
  "token": "your_device_token",
  "platform": "ios"
}
```

**Verify Deep Link:**
```http
GET /v1/test/deep-link?type=story&id=clx1a2b3c4d5e6f7g8h9i0j1 HTTP/1.1
X-Client-Type: mobile-ios
```

## Next Steps

1. Review [Mobile API Documentation](mobile-api.md) for complete details
2. Implement authentication with Clerk
3. Set up push notification certificates (APNs) or keys (FCM)
4. Configure deep link handling in your app
5. Implement offline support with caching
6. Test error handling scenarios
7. Monitor rate limits and optimize API usage

## Resources

- [Full Mobile API Documentation](mobile-api.md)
- [Main API Documentation](../architecture/api.md)
- [Clerk Authentication](https://clerk.com/docs)
- [FCM Documentation](https://firebase.google.com/docs/cloud-messaging)
- [APNs Documentation](https://developer.apple.com/documentation/usernotifications)

## Support

- Email: mobile-support@muejam.com
- Documentation: https://docs.muejam.com
- Status: https://status.muejam.com
