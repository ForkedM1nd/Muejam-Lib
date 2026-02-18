#!/bin/bash
# Create a new release with semantic versioning
# Usage: ./scripts/create-release.sh <major|minor|patch> [message]
# Example: ./scripts/create-release.sh minor "Add new feature"

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
VERSION_TYPE="${1:-patch}"
RELEASE_MESSAGE="${2:-Release}"

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED}Error: Invalid version type '$VERSION_TYPE'${NC}"
    echo "Usage: $0 <major|minor|patch> [message]"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "Current version: $CURRENT_VERSION"

# Parse version numbers
VERSION_NUMBERS=$(echo "$CURRENT_VERSION" | sed 's/v//')
MAJOR=$(echo "$VERSION_NUMBERS" | cut -d. -f1)
MINOR=$(echo "$VERSION_NUMBERS" | cut -d. -f2)
PATCH=$(echo "$VERSION_NUMBERS" | cut -d. -f3)

# Increment version based on type
case "$VERSION_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"
echo "New version: $NEW_VERSION"
echo ""

# Confirm
read -p "Create release $NEW_VERSION? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Release cancelled"
    exit 0
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Uncommitted changes detected${NC}"
    git status --short
    exit 1
fi

# Update CHANGELOG.md
echo -e "${YELLOW}Updating CHANGELOG.md...${NC}"

# Get date
RELEASE_DATE=$(date +%Y-%m-%d)

# Update unreleased section to new version
sed -i.bak "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $RELEASE_DATE/" CHANGELOG.md
rm CHANGELOG.md.bak

# Commit changelog
git add CHANGELOG.md
git commit -m "Update CHANGELOG for $NEW_VERSION"

# Create git tag (Requirement 29.13)
echo -e "${YELLOW}Creating git tag...${NC}"
git tag -a "$NEW_VERSION" -m "$RELEASE_MESSAGE"

echo -e "${GREEN}✓ Release $NEW_VERSION created${NC}"
echo ""
echo "Next steps:"
echo "1. Review the changes: git show $NEW_VERSION"
echo "2. Push to remote: git push origin main --tags"
echo "3. Deploy to staging: ./scripts/deploy.sh staging"
echo "4. Deploy to production: ./scripts/deploy.sh production"
