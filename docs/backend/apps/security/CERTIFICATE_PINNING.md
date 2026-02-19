# Certificate Pinning Implementation Guide

## Overview

Certificate pinning is a security technique that protects mobile applications against man-in-the-middle (MITM) attacks by validating that the server's SSL/TLS certificate matches a known, trusted certificate. This document describes how to implement certificate pinning in mobile clients using the MueJam API.

**Requirements:** 11.1, 11.2

## What is Certificate Pinning?

Certificate pinning works by "pinning" a server's certificate or public key in the mobile application. When the app connects to the server, it verifies that the server's certificate matches the pinned certificate. If the certificates don't match, the connection is rejected, even if the certificate is signed by a trusted Certificate Authority.

This protects against:
- Compromised Certificate Authorities
- Rogue certificates issued by attackers
- Man-in-the-middle attacks on public networks
- SSL/TLS interception by malicious proxies

## API Endpoints

### Get Certificate Fingerprints

**Endpoint:** `GET /v1/security/certificate/fingerprints`

**Authentication:** None required (public endpoint)

**Description:** Retrieves the current SSL/TLS certificate fingerprints for the API server.

**Response:**
```json
{
  "sha256": [
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
  ],
  "sha1": [
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD"
  ],
  "domain": "api.muejam.com",
  "valid_until": "2025-12-31T23:59:59Z",
  "subject": {
    "CN": "api.muejam.com"
  },
  "issuer": {
    "CN": "Let's Encrypt Authority X3"
  }
}
```

**Response Fields:**
- `sha256`: Array of SHA-256 certificate fingerprints (primary + backup certificates)
- `sha1`: Array of SHA-1 certificate fingerprints (for legacy support)
- `domain`: The domain name of the API server
- `valid_until`: Certificate expiration date
- `subject`: Certificate subject information
- `issuer`: Certificate issuer information

### Verify Certificate Fingerprint

**Endpoint:** `POST /v1/security/certificate/verify`

**Authentication:** None required (public endpoint)

**Description:** Verifies a provided fingerprint against the current server certificate. Useful for testing certificate pinning implementations.

**Request Body:**
```json
{
  "fingerprint": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99",
  "algorithm": "sha256"
}
```

**Request Fields:**
- `fingerprint`: The certificate fingerprint to verify (required)
- `algorithm`: Hash algorithm used - "sha256" or "sha1" (optional, defaults to "sha256")

**Response:**
```json
{
  "valid": true,
  "algorithm": "sha256",
  "message": "Fingerprint matches current certificate"
}
```

## Implementation Guide

### iOS Implementation (Swift)

#### 1. Retrieve Certificate Fingerprints

First, fetch the certificate fingerprints from the API:

```swift
func fetchCertificateFingerprints(completion: @escaping ([String]?) -> Void) {
    let url = URL(string: "https://api.muejam.com/v1/security/certificate/fingerprints")!
    
    URLSession.shared.dataTask(with: url) { data, response, error in
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let sha256Fingerprints = json["sha256"] as? [String] else {
            completion(nil)
            return
        }
        
        completion(sha256Fingerprints)
    }.resume()
}
```

#### 2. Implement Certificate Pinning

Use `URLSessionDelegate` to validate the server certificate:

```swift
class CertificatePinningDelegate: NSObject, URLSessionDelegate {
    private let pinnedFingerprints: Set<String>
    
    init(fingerprints: [String]) {
        // Remove colons and convert to uppercase for comparison
        self.pinnedFingerprints = Set(fingerprints.map { 
            $0.replacingOccurrences(of: ":", with: "").uppercased() 
        })
    }
    
    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust,
              let certificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Get certificate data
        let certificateData = SecCertificateCopyData(certificate) as Data
        
        // Calculate SHA-256 fingerprint
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        certificateData.withUnsafeBytes {
            _ = CC_SHA256($0.baseAddress, CC_LONG(certificateData.count), &hash)
        }
        
        let fingerprint = hash.map { String(format: "%02X", $0) }.joined()
        
        // Verify fingerprint matches pinned fingerprints
        if pinnedFingerprints.contains(fingerprint) {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            print("Certificate pinning failed: fingerprint mismatch")
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

#### 3. Use the Pinning Delegate

```swift
// Fetch fingerprints on app launch
fetchCertificateFingerprints { fingerprints in
    guard let fingerprints = fingerprints else {
        print("Failed to fetch certificate fingerprints")
        return
    }
    
    // Create session with pinning delegate
    let delegate = CertificatePinningDelegate(fingerprints: fingerprints)
    let session = URLSession(
        configuration: .default,
        delegate: delegate,
        delegateQueue: nil
    )
    
    // Use this session for all API requests
    // Store in a singleton or dependency injection container
}
```

### Android Implementation (Kotlin)

#### 1. Retrieve Certificate Fingerprints

```kotlin
data class CertificateFingerprints(
    val sha256: List<String>,
    val sha1: List<String>,
    val domain: String,
    val validUntil: String
)

suspend fun fetchCertificateFingerprints(): CertificateFingerprints? {
    return withContext(Dispatchers.IO) {
        try {
            val url = URL("https://api.muejam.com/v1/security/certificate/fingerprints")
            val connection = url.openConnection() as HttpURLConnection
            
            val response = connection.inputStream.bufferedReader().readText()
            val json = JSONObject(response)
            
            CertificateFingerprints(
                sha256 = json.getJSONArray("sha256").let { array ->
                    (0 until array.length()).map { array.getString(it) }
                },
                sha1 = json.getJSONArray("sha1").let { array ->
                    (0 until array.length()).map { array.getString(it) }
                },
                domain = json.getString("domain"),
                validUntil = json.getString("valid_until")
            )
        } catch (e: Exception) {
            Log.e("CertPinning", "Failed to fetch fingerprints", e)
            null
        }
    }
}
```

#### 2. Implement Certificate Pinning with OkHttp

```kotlin
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient
import java.security.MessageDigest
import java.security.cert.X509Certificate
import javax.net.ssl.X509TrustManager

class CertificatePinningManager(private val fingerprints: List<String>) {
    
    fun createPinnedClient(): OkHttpClient {
        // Create certificate pinner
        val certificatePinner = CertificatePinner.Builder()
            .apply {
                fingerprints.forEach { fingerprint ->
                    // Convert fingerprint format: AA:BB:CC -> sha256/base64hash
                    add("api.muejam.com", "sha256/${convertFingerprintToBase64(fingerprint)}")
                }
            }
            .build()
        
        return OkHttpClient.Builder()
            .certificatePinner(certificatePinner)
            .build()
    }
    
    private fun convertFingerprintToBase64(fingerprint: String): String {
        // Remove colons and convert hex to bytes
        val bytes = fingerprint.replace(":", "")
            .chunked(2)
            .map { it.toInt(16).toByte() }
            .toByteArray()
        
        // Convert to base64
        return android.util.Base64.encodeToString(
            bytes,
            android.util.Base64.NO_WRAP
        )
    }
}
```

#### 3. Use the Pinned Client

```kotlin
// In your Application class or dependency injection setup
class MyApplication : Application() {
    lateinit var apiClient: OkHttpClient
    
    override fun onCreate() {
        super.onCreate()
        
        // Fetch fingerprints on app launch
        lifecycleScope.launch {
            val fingerprints = fetchCertificateFingerprints()
            if (fingerprints != null) {
                val pinningManager = CertificatePinningManager(fingerprints.sha256)
                apiClient = pinningManager.createPinnedClient()
            } else {
                Log.e("App", "Failed to setup certificate pinning")
            }
        }
    }
}
```

## Best Practices

### 1. Backup Pins

Always include backup certificate fingerprints to prevent app lockout when certificates are rotated:

```swift
// iOS
let primaryFingerprint = "AA:BB:CC:..."
let backupFingerprint = "DD:EE:FF:..."
let pinnedFingerprints = Set([primaryFingerprint, backupFingerprint])
```

### 2. Certificate Rotation

When rotating certificates:
1. Deploy the new certificate to the server
2. Update the API to return both old and new fingerprints
3. Wait for all mobile clients to update their pins
4. Remove the old certificate from the server

### 3. Fallback Strategy

Implement a fallback mechanism for certificate pinning failures:

```swift
func handlePinningFailure() {
    // Log the failure for security monitoring
    logSecurityEvent("certificate_pinning_failure")
    
    // Option 1: Fail closed (recommended for high security)
    showError("Unable to establish secure connection")
    
    // Option 2: Fail open with user warning (not recommended)
    // showWarning("Certificate validation failed. Continue anyway?")
}
```

### 4. Testing

Use the verification endpoint to test your implementation:

```swift
func testCertificatePinning(fingerprint: String) {
    let url = URL(string: "https://api.muejam.com/v1/security/certificate/verify")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = [
        "fingerprint": fingerprint,
        "algorithm": "sha256"
    ]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let valid = json["valid"] as? Bool else {
            print("Verification request failed")
            return
        }
        
        print("Fingerprint valid: \(valid)")
    }.resume()
}
```

### 5. Monitoring

Monitor certificate pinning failures in your app:

```swift
func logPinningFailure(fingerprint: String) {
    // Send to analytics
    Analytics.logEvent("certificate_pinning_failure", parameters: [
        "fingerprint": fingerprint,
        "expected_domain": "api.muejam.com"
    ])
    
    // Alert security team
    SecurityMonitoring.alert("Potential MITM attack detected")
}
```

## Security Considerations

### 1. Initial Fingerprint Retrieval

The first time your app retrieves fingerprints, it's vulnerable to MITM attacks. Mitigate this by:
- Hardcoding initial fingerprints in the app bundle
- Using the API endpoint only for updates
- Requiring multiple successful retrievals before updating pins

### 2. Fingerprint Storage

Store fingerprints securely:
- iOS: Use Keychain Services
- Android: Use EncryptedSharedPreferences

```swift
// iOS Keychain storage
func storeFingerprintsInKeychain(_ fingerprints: [String]) {
    let data = try? JSONEncoder().encode(fingerprints)
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: "certificate_fingerprints",
        kSecValueData as String: data as Any
    ]
    
    SecItemDelete(query as CFDictionary)
    SecItemAdd(query as CFDictionary, nil)
}
```

### 3. Certificate Expiration

Monitor certificate expiration dates and update pins before expiration:

```swift
func checkCertificateExpiration(validUntil: String) {
    let dateFormatter = ISO8601DateFormatter()
    guard let expirationDate = dateFormatter.date(from: validUntil) else {
        return
    }
    
    let daysUntilExpiration = Calendar.current.dateComponents(
        [.day],
        from: Date(),
        to: expirationDate
    ).day ?? 0
    
    if daysUntilExpiration < 30 {
        // Fetch updated fingerprints
        fetchCertificateFingerprints { newFingerprints in
            // Update stored fingerprints
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Pinning Failure on Valid Certificate**
   - Verify fingerprint format (colons, uppercase)
   - Check that you're using the correct hash algorithm
   - Ensure you're comparing the leaf certificate, not intermediate certificates

2. **App Cannot Connect After Certificate Rotation**
   - Implement backup pins
   - Add certificate rotation monitoring
   - Test certificate updates in staging environment first

3. **Development vs Production**
   - Use different fingerprints for development and production
   - Consider disabling pinning in debug builds
   - Use the mock fingerprints endpoint for local development

### Debug Logging

Enable detailed logging during development:

```swift
func debugCertificateChain(serverTrust: SecTrust) {
    let certificateCount = SecTrustGetCertificateCount(serverTrust)
    print("Certificate chain length: \(certificateCount)")
    
    for i in 0..<certificateCount {
        if let cert = SecTrustGetCertificateAtIndex(serverTrust, i) {
            let data = SecCertificateCopyData(cert) as Data
            var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
            data.withUnsafeBytes {
                _ = CC_SHA256($0.baseAddress, CC_LONG(data.count), &hash)
            }
            let fingerprint = hash.map { String(format: "%02X", $0) }.joined()
            print("Certificate \(i) fingerprint: \(fingerprint)")
        }
    }
}
```

## Additional Resources

- [OWASP Certificate Pinning Guide](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning)
- [Apple's App Transport Security](https://developer.apple.com/documentation/security/preventing_insecure_network_connections)
- [Android Network Security Configuration](https://developer.android.com/training/articles/security-config)
- [OkHttp Certificate Pinning](https://square.github.io/okhttp/4.x/okhttp/okhttp3/-certificate-pinner/)

## Support

For questions or issues with certificate pinning implementation:
- Email: security@muejam.com
- Documentation: https://docs.muejam.com/security/certificate-pinning
- API Status: https://status.muejam.com
