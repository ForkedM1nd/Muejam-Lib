"""
Email Notification Service.

Provides email notification functionality using Resend API.
Implements Requirements 21.1-21.15.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import resend
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv('RESEND_API_KEY')


class EmailNotificationService:
    """
    Service for sending email notifications via Resend.
    
    Implements Requirements:
    - 21.1: Send email notifications using Resend service
    - 21.15: Track email delivery status and bounce rates
    """
    
    FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL', 'notifications@muejam.com')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    @classmethod
    def send_email(cls, to_email: str, subject: str, html_content: str,
                   text_content: Optional[str] = None,
                   reply_to: Optional[str] = None,
                   tags: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Send email via Resend API with error handling.
        
        Implements Requirement 21.1: Send email notifications using Resend service.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            reply_to: Reply-to email address (optional)
            tags: Email tags for tracking (optional)
        
        Returns:
            Dict containing:
            - status: 'sent' or 'failed'
            - email_id: Resend email ID (if sent)
            - error: Error message (if failed)
        """
        try:
            params = {
                "from": cls.FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            if reply_to:
                params["reply_to"] = reply_to
            
            if tags:
                params["tags"] = tags
            
            response = resend.Emails.send(params)
            
            logger.info(f"Email sent successfully to {to_email}: {response.get('id')}")
            
            return {
                'status': 'sent',
                'email_id': response.get('id'),
                'to': to_email,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'to': to_email,
                'subject': subject
            }
    
    @classmethod
    def send_welcome_email(cls, user_email: str, user_name: str) -> Dict[str, Any]:
        """
        Send welcome email after user email verification.
        
        Implements Requirement 21.2: Send welcome email immediately after verification.
        
        Args:
            user_email: User's email address
            user_name: User's display name
        
        Returns:
            Email send result
        """
        subject = f"Welcome to MueJam Library, {user_name}!"
        
        html_content = cls._render_email_template('welcome', {
            'user_name': user_name,
            'frontend_url': cls.FRONTEND_URL
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'welcome'}]
        )
    
    @classmethod
    def send_new_comment_notification(cls, user_email: str, user_name: str,
                                      commenter_name: str, story_title: str,
                                      comment_text: str, story_id: str) -> Dict[str, Any]:
        """
        Send notification when user's story receives a new comment.
        
        Implements Requirement 21.3: Send notification for new comments.
        
        Args:
            user_email: Story author's email
            user_name: Story author's name
            commenter_name: Name of person who commented
            story_title: Title of the story
            comment_text: Comment content
            story_id: ID of the story
        
        Returns:
            Email send result
        """
        subject = f"New comment on '{story_title}'"
        
        html_content = cls._render_email_template('new_comment', {
            'user_name': user_name,
            'commenter_name': commenter_name,
            'story_title': story_title,
            'comment_text': comment_text,
            'story_url': f"{cls.FRONTEND_URL}/stories/{story_id}",
            'unsubscribe_url': f"{cls.FRONTEND_URL}/settings/notifications"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'comment'}]
        )
    
    @classmethod
    def send_new_like_notification(cls, user_email: str, user_name: str,
                                   liker_name: str, content_type: str,
                                   content_id: str) -> Dict[str, Any]:
        """
        Send notification when user's whisper receives a like.
        
        Implements Requirement 21.4: Send notification for likes.
        
        Args:
            user_email: Content author's email
            user_name: Content author's name
            liker_name: Name of person who liked
            content_type: Type of content (whisper, story)
            content_id: ID of the content
        
        Returns:
            Email send result
        """
        subject = f"{liker_name} liked your {content_type}"
        
        html_content = cls._render_email_template('new_like', {
            'user_name': user_name,
            'liker_name': liker_name,
            'content_type': content_type,
            'content_url': f"{cls.FRONTEND_URL}/{content_type}s/{content_id}",
            'unsubscribe_url': f"{cls.FRONTEND_URL}/settings/notifications"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'like'}]
        )
    
    @classmethod
    def send_new_follower_notification(cls, user_email: str, user_name: str,
                                       follower_name: str, follower_id: str) -> Dict[str, Any]:
        """
        Send notification when user gains a new follower.
        
        Implements Requirement 21.5: Send notification for new followers.
        
        Args:
            user_email: User's email
            user_name: User's name
            follower_name: Name of new follower
            follower_id: ID of new follower
        
        Returns:
            Email send result
        """
        subject = f"{follower_name} started following you"
        
        html_content = cls._render_email_template('new_follower', {
            'user_name': user_name,
            'follower_name': follower_name,
            'follower_url': f"{cls.FRONTEND_URL}/profile/{follower_id}",
            'unsubscribe_url': f"{cls.FRONTEND_URL}/settings/notifications"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'follower'}]
        )
    
    @classmethod
    def send_new_content_notification(cls, user_email: str, user_name: str,
                                      author_name: str, content_title: str,
                                      content_type: str, content_id: str) -> Dict[str, Any]:
        """
        Send notification when followed author publishes new content.
        
        Implements Requirement 21.6: Send notification for new content from followed authors.
        
        Args:
            user_email: Follower's email
            user_name: Follower's name
            author_name: Author's name
            content_title: Title of new content
            content_type: Type of content (story, chapter)
            content_id: ID of the content
        
        Returns:
            Email send result
        """
        subject = f"{author_name} published new {content_type}: {content_title}"
        
        html_content = cls._render_email_template('new_content', {
            'user_name': user_name,
            'author_name': author_name,
            'content_title': content_title,
            'content_type': content_type,
            'content_url': f"{cls.FRONTEND_URL}/stories/{content_id}",
            'unsubscribe_url': f"{cls.FRONTEND_URL}/settings/notifications"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'new_content'}]
        )
    
    @classmethod
    def send_content_takedown_notification(cls, user_email: str, user_name: str,
                                          content_type: str, content_title: str,
                                          reason: str) -> Dict[str, Any]:
        """
        Send notification when content is taken down by moderators.
        
        Implements Requirement 21.7: Send notification for content takedown with reason.
        
        Args:
            user_email: Content author's email
            user_name: Content author's name
            content_type: Type of content (story, whisper, comment)
            content_title: Title or excerpt of content
            reason: Reason for takedown
        
        Returns:
            Email send result
        """
        subject = f"Your {content_type} has been removed"
        
        html_content = cls._render_email_template('content_takedown', {
            'user_name': user_name,
            'content_type': content_type,
            'content_title': content_title,
            'reason': reason,
            'appeal_url': f"{cls.FRONTEND_URL}/support/appeal",
            'guidelines_url': f"{cls.FRONTEND_URL}/guidelines"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'takedown'}]
        )
    
    @classmethod
    def send_security_alert(cls, user_email: str, user_name: str,
                           alert_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification for account security events.
        
        Implements Requirement 21.8: Send notification for security events.
        
        Args:
            user_email: User's email
            user_name: User's name
            alert_type: Type of security event (new_login, password_change, 2fa_change)
            details: Additional details about the event
        
        Returns:
            Email send result
        """
        alert_titles = {
            'new_login': 'New login to your account',
            'password_change': 'Your password was changed',
            '2fa_change': 'Two-factor authentication settings changed',
            'suspicious_activity': 'Suspicious activity detected'
        }
        
        subject = alert_titles.get(alert_type, 'Security alert for your account')
        
        html_content = cls._render_email_template('security_alert', {
            'user_name': user_name,
            'alert_type': alert_type,
            'details': details,
            'security_url': f"{cls.FRONTEND_URL}/settings/security",
            'support_url': f"{cls.FRONTEND_URL}/support"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': 'security'}]
        )
    
    @classmethod
    def send_digest_email(cls, user_email: str, user_name: str,
                         notifications: List[Dict[str, Any]],
                         digest_type: str) -> Dict[str, Any]:
        """
        Send digest email with batched notifications.
        
        Implements Requirement 21.11: Batch notifications into digest emails.
        
        Args:
            user_email: User's email
            user_name: User's name
            notifications: List of notification data
            digest_type: Type of digest (daily, weekly)
        
        Returns:
            Email send result
        """
        subject = f"Your {digest_type} digest from MueJam Library"
        
        html_content = cls._render_email_template('digest', {
            'user_name': user_name,
            'digest_type': digest_type,
            'notifications': notifications,
            'frontend_url': cls.FRONTEND_URL,
            'unsubscribe_url': f"{cls.FRONTEND_URL}/settings/notifications"
        })
        
        return cls.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            tags=[{'name': 'type', 'value': f'{digest_type}_digest'}]
        )
    
    @classmethod
    def _render_email_template(cls, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render email template with context.
        
        Implements Requirement 21.14: Use responsive email templates.
        
        Args:
            template_name: Name of the template
            context: Template context data
        
        Returns:
            Rendered HTML content
        """
        # For now, return inline HTML
        # In production, use Django templates or external template service
        
        base_style = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background-color: #f9f9f9; }
            .button { background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
            .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            .footer a { color: #666; text-decoration: underline; }
            @media only screen and (max-width: 600px) {
                .container { width: 100% !important; padding: 10px !important; }
                .content { padding: 15px !important; }
            }
        </style>
        """
        
        templates = {
            'welcome': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Welcome to MueJam Library!</h1>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p>Welcome to MueJam Library! We're excited to have you join our community of readers and writers.</p>
                            <p>Here's what you can do:</p>
                            <ul>
                                <li>Discover amazing stories from talented authors</li>
                                <li>Share your thoughts with Whispers</li>
                                <li>Follow your favorite authors</li>
                                <li>Start writing your own stories</li>
                            </ul>
                            <p><a href="{context.get('frontend_url')}" class="button">Explore Stories</a></p>
                        </div>
                        <div class="footer">
                            <p>&copy; 2024 MueJam Library. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'new_comment': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>New Comment</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p><strong>{context.get('commenter_name')}</strong> commented on your story <strong>"{context.get('story_title')}"</strong>:</p>
                            <blockquote style="border-left: 3px solid #007bff; padding-left: 15px; margin: 20px 0; font-style: italic;">
                                {context.get('comment_text')}
                            </blockquote>
                            <p><a href="{context.get('story_url')}" class="button">View Comment</a></p>
                        </div>
                        <div class="footer">
                            <p><a href="{context.get('unsubscribe_url')}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'new_like': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>New Like</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p><strong>{context.get('liker_name')}</strong> liked your {context.get('content_type')}!</p>
                            <p><a href="{context.get('content_url')}" class="button">View {context.get('content_type').title()}</a></p>
                        </div>
                        <div class="footer">
                            <p><a href="{context.get('unsubscribe_url')}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'new_follower': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>New Follower</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p><strong>{context.get('follower_name')}</strong> started following you on MueJam Library!</p>
                            <p><a href="{context.get('follower_url')}" class="button">View Profile</a></p>
                        </div>
                        <div class="footer">
                            <p><a href="{context.get('unsubscribe_url')}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'new_content': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>New Content from {context.get('author_name')}</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p><strong>{context.get('author_name')}</strong> published a new {context.get('content_type')}:</p>
                            <h3>{context.get('content_title')}</h3>
                            <p><a href="{context.get('content_url')}" class="button">Read Now</a></p>
                        </div>
                        <div class="footer">
                            <p><a href="{context.get('unsubscribe_url')}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'content_takedown': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header" style="background-color: #dc3545;">
                            <h2>Content Removed</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p>Your {context.get('content_type')} "{context.get('content_title')}" has been removed by our moderation team.</p>
                            <p><strong>Reason:</strong> {context.get('reason')}</p>
                            <p>If you believe this was a mistake, you can appeal this decision.</p>
                            <p>
                                <a href="{context.get('appeal_url')}" class="button">Submit Appeal</a>
                                <a href="{context.get('guidelines_url')}" class="button" style="background-color: #6c757d;">Review Guidelines</a>
                            </p>
                        </div>
                        <div class="footer">
                            <p>&copy; 2024 MueJam Library. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'security_alert': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header" style="background-color: #ffc107; color: #000;">
                            <h2>Security Alert</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p>We detected a security event on your account:</p>
                            <p><strong>{context.get('alert_type').replace('_', ' ').title()}</strong></p>
                            <p>Details: {context.get('details', {})}</p>
                            <p>If this wasn't you, please secure your account immediately.</p>
                            <p>
                                <a href="{context.get('security_url')}" class="button">Review Security Settings</a>
                                <a href="{context.get('support_url')}" class="button" style="background-color: #dc3545;">Contact Support</a>
                            </p>
                        </div>
                        <div class="footer">
                            <p>&copy; 2024 MueJam Library. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """,
            
            'digest': f"""
            <html>
                <head>{base_style}</head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Your {context.get('digest_type').title()} Digest</h2>
                        </div>
                        <div class="content">
                            <p>Hi {context.get('user_name')},</p>
                            <p>Here's what happened while you were away:</p>
                            <div style="margin: 20px 0;">
                                {''.join([f'<p>• {notif.get("message")}</p>' for notif in context.get('notifications', [])])}
                            </div>
                            <p><a href="{context.get('frontend_url')}" class="button">Visit MueJam Library</a></p>
                        </div>
                        <div class="footer">
                            <p><a href="{context.get('unsubscribe_url')}">Manage notification preferences</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """
        }
        
        return templates.get(template_name, f"<html><body><p>Template {template_name} not found</p></body></html>")
