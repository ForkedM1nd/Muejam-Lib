# CloudFront CDN Configuration

This document describes the CloudFront CDN setup for the MueJam Library platform.

## Requirements

Implements Requirements 27.1-27.12:

### CDN Requirements (27.x)
- 27.1: Serve all static assets through CloudFront CDN
- 27.2: Configure edge locations in North America, Europe, and Asia
- 27.3: Set cache headers (1 year for versioned assets, 1 hour for HTML)
- 27.4: Implement cache busting using content hashes
- 27.5: Serve user-uploaded images from S3 through CloudFront
- 27.6: Configure compression (gzip and brotli)
- 27.7: Implement image optimization (format conversion, resizing, compression)
- 27.8: Generate multiple image sizes (thumbnail, small, medium, large)
- 27.9: Implement lazy loading for images
- 27.10: Configure custom error pages (404, 500)
- 27.11: Monitor CDN performance (cache hit rate, origin requests, bandwidth)
- 27.12: Invalidate CDN cache automatically on deployment

## Components

### CDNCacheService

Python service for managing CloudFront cache invalidation.

**Methods:**
- `invalidate_paths(paths)`: Invalidate specific paths
- `invalidate_all()`: Invalidate entire cache
- `invalidate_static_assets()`: Invalidate CSS, JS, images, fonts
- `invalidate_on_deployment(version)`: Invalidate cache for deployment
- `get_invalidation_status(invalidation_id)`: Check invalidation status
- `get_distribution_config()`: Get CloudFront configuration
- `get_cache_statistics()`: Get cache performance metrics

**Features:**
- Automatic cache invalidation on deployment
- Path-based invalidation
- Status tracking
- Performance monitoring

### Terraform Configuration

Infrastructure as Code for CloudFront setup.

**Resources:**
- CloudFront Distribution with multiple origins
- S3 buckets for static assets and user uploads
- Origin Access Identity for secure S3 access
- Custom error pages
- CloudWatch alarms for monitoring

## CloudFront Distribution

### Origins

1. **Static Assets (S3)**
   - CSS, JavaScript, images, fonts
   - Cache TTL: 1 year (versioned assets)
   - Compression: gzip and brotli

2. **User Uploads (S3)**
   - User-uploaded images
   - Cache TTL: 1 day
   - Query string forwarding for image transformations

3. **Application Server (ALB)**
   - API endpoints
   - No caching
   - All HTTP methods supported

### Cache Behaviors

#### Default Behavior (Static Assets)
- **Path**: `/*`
- **Methods**: GET, HEAD, OPTIONS
- **TTL**: 1 year (31,536,000 seconds)
- **Compression**: Enabled
- **Query strings**: Disabled

#### HTML Files
- **Path**: `*.html`
- **Methods**: GET, HEAD, OPTIONS
- **TTL**: 1 hour (3,600 seconds)
- **Compression**: Enabled
- **Query strings**: Disabled

#### User Uploads
- **Path**: `/uploads/*`
- **Methods**: GET, HEAD, OPTIONS
- **TTL**: 1 day (86,400 seconds)
- **Compression**: Enabled
- **Query strings**: Enabled (for transformations)

#### API Requests
- **Path**: `/api/*`
- **Methods**: All HTTP methods
- **TTL**: 0 (no caching)
- **Compression**: Enabled
- **Headers**: All forwarded
- **Cookies**: All forwarded

### Custom Error Pages

- **404 Not Found**: `/404.html`
- **500 Internal Server Error**: `/500.html`
- **503 Service Unavailable**: `/503.html`

## Usage

### Cache Invalidation

#### Invalidate Specific Paths

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Invalidate specific files
result = cdn.invalidate_paths([
    '/static/css/main.css',
    '/static/js/app.js'
])

print(f"Invalidation ID: {result['invalidation_id']}")
print(f"Status: {result['invalidation_status']}")
```

#### Invalidate Static Assets

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Invalidate all static assets
result = cdn.invalidate_static_assets()

print(f"Invalidated: {result['paths']}")
```

#### Invalidate on Deployment

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Invalidate cache for deployment
result = cdn.invalidate_on_deployment(version='v1.2.3')

if result['status'] == 'success':
    print(f"Cache invalidated for deployment v1.2.3")
    print(f"Invalidation ID: {result['invalidation_id']}")
```

#### Check Invalidation Status

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Check status
status = cdn.get_invalidation_status('INVALIDATION_ID')

print(f"Status: {status['invalidation_status']}")
print(f"Paths: {status['paths']}")
```

### Cache Statistics

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Get cache statistics
stats = cdn.get_cache_statistics()

print(f"Cache Hit Rate: {stats['cache_hit_rate']}%")
print(f"Total Requests: {stats['total_requests']}")
print(f"Bandwidth: {stats['total_bandwidth_gb']} GB")
```

### Distribution Configuration

```python
from infrastructure.cdn_cache_service import CDNCacheService

cdn = CDNCacheService()

# Get distribution config
config = cdn.get_distribution_config()

print(f"Distribution ID: {config['distribution_id']}")
print(f"Domain Name: {config['domain_name']}")
print(f"Status: {config['status']}")
print(f"Origins: {config['origins']}")
```

## Deployment Integration

### Automatic Cache Invalidation

Add to your deployment script:

```bash
#!/bin/bash

# Deploy application
./deploy.sh

# Invalidate CloudFront cache
python manage.py shell << EOF
from infrastructure.cdn_cache_service import CDNCacheService
cdn = CDNCacheService()
result = cdn.invalidate_on_deployment(version='$VERSION')
print(f"Cache invalidated: {result['invalidation_id']}")
EOF
```

### Django Management Command

Create a management command for cache invalidation:

```python
# management/commands/invalidate_cdn.py
from django.core.management.base import BaseCommand
from infrastructure.cdn_cache_service import CDNCacheService

class Command(BaseCommand):
    help = 'Invalidate CloudFront CDN cache'

    def add_arguments(self, parser):
        parser.add_argument('--paths', nargs='+', help='Paths to invalidate')
        parser.add_argument('--all', action='store_true', help='Invalidate all')
        parser.add_argument('--static', action='store_true', help='Invalidate static assets')

    def handle(self, *args, **options):
        cdn = CDNCacheService()
        
        if options['all']:
            result = cdn.invalidate_all()
        elif options['static']:
            result = cdn.invalidate_static_assets()
        elif options['paths']:
            result = cdn.invalidate_paths(options['paths'])
        else:
            self.stdout.write(self.style.ERROR('Specify --paths, --static, or --all'))
            return
        
        if result['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(
                f"Invalidation created: {result['invalidation_id']}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Invalidation failed: {result.get('error')}"
            ))
```

Usage:

```bash
# Invalidate specific paths
python manage.py invalidate_cdn --paths /static/css/* /static/js/*

# Invalidate all static assets
python manage.py invalidate_cdn --static

# Invalidate everything
python manage.py invalidate_cdn --all
```

## Configuration

### Required Settings

```python
# settings.py

# CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID = os.getenv('CLOUDFRONT_DISTRIBUTION_ID')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', 'd123456789.cloudfront.net')

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Static files served through CloudFront
STATIC_URL = f'https://{CLOUDFRONT_DOMAIN}/static/'
MEDIA_URL = f'https://{CLOUDFRONT_DOMAIN}/uploads/'
```

### Environment Variables

```bash
# .env

CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC
CLOUDFRONT_DOMAIN=d123456789.cloudfront.net
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## Terraform Deployment

### Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### Plan Deployment

```bash
terraform plan -var="environment=production"
```

### Apply Configuration

```bash
terraform apply -var="environment=production"
```

### Get Outputs

```bash
# Get CloudFront distribution ID
terraform output cloudfront_distribution_id

# Get CloudFront domain name
terraform output cloudfront_domain_name

# Get S3 bucket names
terraform output static_assets_bucket
terraform output user_uploads_bucket
```

## Monitoring

### CloudWatch Metrics

CloudFront provides the following metrics:

1. **CacheHitRate**: Percentage of requests served from cache
2. **Requests**: Total number of requests
3. **BytesDownloaded**: Total bytes downloaded
4. **BytesUploaded**: Total bytes uploaded
5. **4xxErrorRate**: Percentage of 4xx errors
6. **5xxErrorRate**: Percentage of 5xx errors

### CloudWatch Alarms

Two alarms are configured:

1. **Low Cache Hit Rate**: Triggers when cache hit rate < 80%
2. **High Error Rate**: Triggers when 5xx error rate > 5%

### Monitoring Dashboard

View metrics in CloudWatch:

```bash
# AWS Console
https://console.aws.amazon.com/cloudwatch/

# Navigate to: CloudWatch > Dashboards > CloudFront
```

### Performance Targets

- **Cache Hit Rate**: > 80%
- **Origin Requests**: < 20% of total requests
- **Error Rate**: < 1%
- **Response Time**: < 100ms (from edge locations)

## Cache Busting

### Versioned Assets

Use content hashes in filenames for automatic cache busting:

```html
<!-- Before build -->
<link rel="stylesheet" href="/static/css/main.css">

<!-- After build with hash -->
<link rel="stylesheet" href="/static/css/main.a1b2c3d4.css">
```

### Webpack Configuration

```javascript
// webpack.config.js
module.exports = {
  output: {
    filename: '[name].[contenthash].js',
    path: path.resolve(__dirname, 'dist'),
  },
};
```

### Django Static Files

```python
# settings.py

# Enable ManifestStaticFilesStorage for cache busting
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

## Image Optimization

### Responsive Images

Generate multiple sizes for responsive images:

```python
from PIL import Image

def generate_responsive_images(image_path):
    """Generate multiple image sizes."""
    img = Image.open(image_path)
    
    sizes = {
        'thumbnail': (150, 150),
        'small': (400, 400),
        'medium': (800, 800),
        'large': (1200, 1200)
    }
    
    for size_name, dimensions in sizes.items():
        img_copy = img.copy()
        img_copy.thumbnail(dimensions, Image.LANCZOS)
        img_copy.save(f'{image_path}_{size_name}.jpg', 'JPEG', quality=85)
```

### WebP Conversion

Convert images to WebP for better compression:

```python
from PIL import Image

def convert_to_webp(image_path):
    """Convert image to WebP format."""
    img = Image.open(image_path)
    webp_path = image_path.rsplit('.', 1)[0] + '.webp'
    img.save(webp_path, 'WEBP', quality=85)
    return webp_path
```

### Lazy Loading

Implement lazy loading in frontend:

```html
<img 
  src="placeholder.jpg" 
  data-src="https://cdn.muejam.com/uploads/image.jpg"
  loading="lazy"
  alt="Description"
>
```

## Security

### Origin Access Identity

CloudFront uses Origin Access Identity (OAI) to securely access S3:

- S3 buckets are not publicly accessible
- Only CloudFront can access S3 content
- Prevents direct S3 URL access

### HTTPS Only

All content is served over HTTPS:

- Viewer protocol policy: `redirect-to-https`
- Minimum TLS version: TLSv1.2
- SSL certificate from AWS Certificate Manager

### Signed URLs (Optional)

For private content, use signed URLs:

```python
import boto3
from datetime import datetime, timedelta

def generate_signed_url(object_key, expiration=3600):
    """Generate CloudFront signed URL."""
    cloudfront_client = boto3.client('cloudfront')
    
    url = f"https://{CLOUDFRONT_DOMAIN}/{object_key}"
    
    expires = datetime.utcnow() + timedelta(seconds=expiration)
    
    # Generate signed URL
    signed_url = cloudfront_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': object_key},
        ExpiresIn=expiration
    )
    
    return signed_url
```

## Troubleshooting

### Cache Not Invalidating

1. Check distribution ID is correct
2. Verify AWS credentials have CloudFront permissions
3. Check invalidation status
4. Wait for invalidation to complete (can take 10-15 minutes)

### Low Cache Hit Rate

1. Check cache headers are set correctly
2. Verify query strings are not preventing caching
3. Review cache behaviors configuration
4. Check if content is cacheable

### High Origin Requests

1. Increase cache TTL for static assets
2. Implement cache busting for versioned assets
3. Review cache invalidation frequency
4. Check if cache behaviors are configured correctly

### Slow Performance

1. Check edge location coverage
2. Review origin response times
3. Enable compression
4. Optimize image sizes

## Cost Optimization

### Reduce Data Transfer

- Enable compression for text assets
- Optimize image sizes
- Use WebP format for images
- Implement lazy loading

### Reduce Origin Requests

- Increase cache TTL
- Implement proper cache busting
- Reduce cache invalidations

### Price Class

Choose appropriate price class:

- **PriceClass_All**: All edge locations (highest cost, best performance)
- **PriceClass_200**: North America, Europe, Asia, Middle East, Africa
- **PriceClass_100**: North America and Europe only (lowest cost)

## Support

For issues with CloudFront:

- Check AWS CloudFront documentation
- Review CloudWatch metrics and alarms
- Check CloudFront access logs
- Contact AWS Support for infrastructure issues
- Review Terraform state for configuration issues

