"""
CDN Cache Service.

Provides CloudFront cache invalidation and management.
Implements Requirements 27.1, 27.12.
"""
import boto3
import logging
from typing import List, Dict, Any
from django.conf import settings
import time

logger = logging.getLogger(__name__)


class CDNCacheService:
    """
    Service for managing CloudFront CDN cache.
    
    Implements Requirements:
    - 27.1: Serve static assets through CloudFront CDN
    - 27.12: Invalidate CDN cache automatically on deployment
    """
    
    def __init__(self):
        """Initialize AWS CloudFront client."""
        self.cloudfront_client = boto3.client(
            'cloudfront',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        self.distribution_id = getattr(settings, 'CLOUDFRONT_DISTRIBUTION_ID', None)
        
        if not self.distribution_id:
            logger.warning("CLOUDFRONT_DISTRIBUTION_ID not configured")
    
    def invalidate_paths(self, paths: List[str], caller_reference: str = None) -> Dict[str, Any]:
        """
        Invalidate specific paths in CloudFront cache.
        
        Implements Requirement 27.12: Invalidate CDN cache for updated assets.
        
        Args:
            paths: List of paths to invalidate (e.g., ['/static/css/*', '/images/*'])
            caller_reference: Unique identifier for this invalidation (optional)
        
        Returns:
            Dict containing:
            - invalidation_id: CloudFront invalidation ID
            - status: Invalidation status
            - paths: List of invalidated paths
        """
        if not self.distribution_id:
            logger.error("Cannot invalidate cache: CLOUDFRONT_DISTRIBUTION_ID not configured")
            return {
                'status': 'error',
                'error': 'CloudFront distribution ID not configured'
            }
        
        try:
            # Generate caller reference if not provided
            if not caller_reference:
                caller_reference = f"invalidation-{int(time.time())}"
            
            # Create invalidation
            response = self.cloudfront_client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': caller_reference
                }
            )
            
            invalidation = response['Invalidation']
            
            logger.info(f"Created CloudFront invalidation {invalidation['Id']} for {len(paths)} paths")
            
            return {
                'status': 'success',
                'invalidation_id': invalidation['Id'],
                'invalidation_status': invalidation['Status'],
                'paths': paths,
                'caller_reference': caller_reference,
                'create_time': invalidation['CreateTime'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to invalidate CloudFront cache: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def invalidate_all(self) -> Dict[str, Any]:
        """
        Invalidate all cached content in CloudFront.
        
        Use with caution - this invalidates the entire cache.
        
        Returns:
            Dict containing invalidation details
        """
        return self.invalidate_paths(['/*'])
    
    def invalidate_static_assets(self) -> Dict[str, Any]:
        """
        Invalidate all static assets (CSS, JS, images).
        
        Implements Requirement 27.12: Invalidate cache on deployment.
        
        Returns:
            Dict containing invalidation details
        """
        paths = [
            '/static/css/*',
            '/static/js/*',
            '/static/images/*',
            '/static/fonts/*'
        ]
        
        return self.invalidate_paths(paths, caller_reference=f"static-assets-{int(time.time())}")
    
    def invalidate_on_deployment(self, version: str = None) -> Dict[str, Any]:
        """
        Invalidate cache for deployment.
        
        Implements Requirement 27.12: Automatic cache invalidation on deployment.
        
        Args:
            version: Deployment version (optional)
        
        Returns:
            Dict containing invalidation details
        """
        # Invalidate HTML files and static assets
        paths = [
            '/index.html',
            '/',
            '/static/*'
        ]
        
        caller_reference = f"deployment-{version or int(time.time())}"
        
        result = self.invalidate_paths(paths, caller_reference=caller_reference)
        
        if result['status'] == 'success':
            logger.info(f"Invalidated CloudFront cache for deployment {version or 'unknown'}")
        
        return result
    
    def get_invalidation_status(self, invalidation_id: str) -> Dict[str, Any]:
        """
        Get status of a CloudFront invalidation.
        
        Args:
            invalidation_id: CloudFront invalidation ID
        
        Returns:
            Dict containing invalidation status
        """
        if not self.distribution_id:
            return {
                'status': 'error',
                'error': 'CloudFront distribution ID not configured'
            }
        
        try:
            response = self.cloudfront_client.get_invalidation(
                DistributionId=self.distribution_id,
                Id=invalidation_id
            )
            
            invalidation = response['Invalidation']
            
            return {
                'status': 'success',
                'invalidation_id': invalidation['Id'],
                'invalidation_status': invalidation['Status'],
                'create_time': invalidation['CreateTime'].isoformat(),
                'paths': invalidation['InvalidationBatch']['Paths']['Items']
            }
            
        except Exception as e:
            logger.error(f"Failed to get invalidation status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_distribution_config(self) -> Dict[str, Any]:
        """
        Get CloudFront distribution configuration.
        
        Returns:
            Dict containing distribution configuration
        """
        if not self.distribution_id:
            return {
                'status': 'error',
                'error': 'CloudFront distribution ID not configured'
            }
        
        try:
            response = self.cloudfront_client.get_distribution(
                Id=self.distribution_id
            )
            
            distribution = response['Distribution']
            config = distribution['DistributionConfig']
            
            return {
                'status': 'success',
                'distribution_id': distribution['Id'],
                'domain_name': distribution['DomainName'],
                'enabled': config['Enabled'],
                'origins': [
                    {
                        'id': origin['Id'],
                        'domain_name': origin['DomainName']
                    }
                    for origin in config['Origins']['Items']
                ],
                'cache_behaviors': config.get('CacheBehaviors', {}).get('Quantity', 0),
                'price_class': config['PriceClass'],
                'status': distribution['Status']
            }
            
        except Exception as e:
            logger.error(f"Failed to get distribution config: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get CloudFront cache statistics.
        
        Implements Requirement 27.11: Monitor CDN performance.
        
        Returns:
            Dict containing cache statistics
        """
        if not self.distribution_id:
            return {
                'status': 'error',
                'error': 'CloudFront distribution ID not configured'
            }
        
        try:
            # Get CloudWatch metrics for CloudFront
            cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')  # CloudFront metrics are in us-east-1
            
            from datetime import datetime, timedelta
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            # Get cache hit rate
            cache_hit_rate = cloudwatch.get_metric_statistics(
                Namespace='AWS/CloudFront',
                MetricName='CacheHitRate',
                Dimensions=[
                    {'Name': 'DistributionId', 'Value': self.distribution_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            # Get requests
            requests = cloudwatch.get_metric_statistics(
                Namespace='AWS/CloudFront',
                MetricName='Requests',
                Dimensions=[
                    {'Name': 'DistributionId', 'Value': self.distribution_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Get bytes downloaded
            bytes_downloaded = cloudwatch.get_metric_statistics(
                Namespace='AWS/CloudFront',
                MetricName='BytesDownloaded',
                Dimensions=[
                    {'Name': 'DistributionId', 'Value': self.distribution_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Calculate averages
            avg_cache_hit_rate = 0
            if cache_hit_rate['Datapoints']:
                avg_cache_hit_rate = sum(dp['Average'] for dp in cache_hit_rate['Datapoints']) / len(cache_hit_rate['Datapoints'])
            
            total_requests = sum(dp['Sum'] for dp in requests['Datapoints'])
            total_bytes = sum(dp['Sum'] for dp in bytes_downloaded['Datapoints'])
            
            return {
                'status': 'success',
                'distribution_id': self.distribution_id,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'cache_hit_rate': round(avg_cache_hit_rate, 2),
                'total_requests': int(total_requests),
                'total_bytes_downloaded': int(total_bytes),
                'total_bandwidth_gb': round(total_bytes / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
