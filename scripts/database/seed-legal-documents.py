#!/usr/bin/env python
"""
Seed legal documents for production readiness.

This script creates initial legal documents (Terms of Service and Privacy Policy)
in the database.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path for Django imports
backend_path = Path(__file__).parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))

from prisma import Prisma
from datetime import datetime


async def seed_legal_documents():
    """Create initial legal documents."""
    db = Prisma()
    await db.connect()
    
    try:
        # Check if documents already exist
        existing_terms = await db.legaldocument.find_first(
            where={'document_type': 'TOS', 'is_active': True}
        )
        
        existing_privacy = await db.legaldocument.find_first(
            where={'document_type': 'PRIVACY', 'is_active': True}
        )
        
        # Create Terms of Service if it doesn't exist
        if not existing_terms:
            terms_content = """
# Terms of Service

**Effective Date:** February 18, 2026

## 1. Acceptance of Terms

By accessing and using MueJam Library ("the Service"), you accept and agree to be bound by the terms and provision of this agreement.

## 2. Age Requirement

You must be at least 13 years old to use this Service. By using the Service, you represent and warrant that you are at least 13 years of age.

## 3. User Content

### 3.1 Your Content
You retain all rights to the content you post on the Service. By posting content, you grant us a worldwide, non-exclusive, royalty-free license to use, reproduce, and display your content on the Service.

### 3.2 Content Guidelines
You agree not to post content that:
- Violates any law or regulation
- Infringes on intellectual property rights
- Contains hate speech, harassment, or threats
- Contains explicit sexual content involving minors
- Contains spam or malicious links

### 3.3 Content Moderation
We reserve the right to remove any content that violates these terms or our community guidelines.

## 4. DMCA Copyright Policy

We respect intellectual property rights. If you believe your work has been copied in a way that constitutes copyright infringement, please contact our DMCA agent.

## 5. Account Termination

We reserve the right to suspend or terminate your account for violations of these terms.

## 6. Limitation of Liability

The Service is provided "as is" without warranties of any kind. We are not liable for any damages arising from your use of the Service.

## 7. Changes to Terms

We may modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the new terms.

## 8. Contact

For questions about these terms, contact us at legal@muejam.com
"""
            
            await db.legaldocument.create(
                data={
                    'document_type': 'TOS',
                    'version': '1.0',
                    'content': terms_content,
                    'effective_date': datetime.now(),
                    'is_active': True
                }
            )
            print("✅ Created Terms of Service document")
        else:
            print("ℹ️  Terms of Service already exists")
        
        # Create Privacy Policy if it doesn't exist
        if not existing_privacy:
            privacy_content = """
# Privacy Policy

**Effective Date:** February 18, 2026

## 1. Information We Collect

### 1.1 Account Information
When you create an account, we collect:
- Email address
- Display name
- Password (encrypted)
- Date of birth (for age verification)

### 1.2 Content
We store the stories, chapters, comments, and other content you create on the Service.

### 1.3 Usage Information
We collect information about how you use the Service, including:
- Reading history
- Search queries
- IP address
- Browser type and version

### 1.4 Cookies
We use cookies and similar technologies to:
- Keep you logged in
- Remember your preferences
- Analyze site usage

## 2. How We Use Your Information

We use your information to:
- Provide and improve the Service
- Personalize your experience
- Send you notifications about your account
- Detect and prevent abuse
- Comply with legal obligations

## 3. Information Sharing

We do not sell your personal information. We may share information:
- With service providers who help us operate the Service
- When required by law
- To protect our rights or the safety of users

## 4. Your Rights

You have the right to:
- Access your personal data
- Correct inaccurate data
- Request deletion of your data
- Export your data
- Opt out of marketing communications

## 5. Data Retention

We retain your data for as long as your account is active. After account deletion, we retain data for 30 days before permanent deletion.

## 6. Security

We implement appropriate security measures to protect your data, including:
- Encryption of sensitive data
- Secure authentication
- Regular security audits

## 7. Children's Privacy

We comply with COPPA. Users under 13 are not permitted to use the Service. We do not knowingly collect information from children under 13.

## 8. International Users

Your information may be transferred to and processed in countries other than your own. By using the Service, you consent to such transfers.

## 9. Changes to Privacy Policy

We may update this policy from time to time. We will notify you of significant changes.

## 10. Contact

For privacy questions or to exercise your rights, contact us at privacy@muejam.com

For GDPR-related requests, contact our Data Protection Officer at dpo@muejam.com
"""
            
            await db.legaldocument.create(
                data={
                    'document_type': 'PRIVACY',
                    'version': '1.0',
                    'content': privacy_content,
                    'effective_date': datetime.now(),
                    'is_active': True
                }
            )
            print("✅ Created Privacy Policy document")
        else:
            print("ℹ️  Privacy Policy already exists")
        
        print("\n✅ Legal documents seeding complete!")
        
    except Exception as e:
        print(f"❌ Error seeding legal documents: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == '__main__':
    asyncio.run(seed_legal_documents())
