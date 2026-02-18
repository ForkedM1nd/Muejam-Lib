# Archive

This directory contains historical artifacts and documentation that are no longer actively maintained but are preserved for reference purposes.

## Purpose

The archive serves as a repository for:
- AI-generated documentation artifacts from development sessions
- Deprecated documentation that may contain useful historical context
- Task summaries and implementation notes from specific features
- Test files and schemas from development iterations

## Retention Policy

Files in this archive are preserved indefinitely to maintain project history and context. While these files are not actively maintained, they may contain valuable information about:
- Design decisions made during development
- Implementation approaches that were tried
- Historical context for features and systems
- Development workflows and processes

## Organization

- **ai-artifacts/**: AI-generated documentation files (TASK_*.md, *_SUMMARY.md, etc.)
- **INDEX.md**: Complete listing of all archived content with descriptions

## When to Archive

Files should be moved to the archive when they:
- Are AI-generated artifacts that served a temporary purpose during development
- Contain information that has been consolidated into official documentation
- Are no longer relevant to current development but may have historical value
- Would clutter the main codebase but shouldn't be deleted

## When to Delete vs Archive

**Archive** files that:
- May contain useful historical context
- Document specific implementation decisions
- Could be referenced for understanding past approaches

**Delete** files that:
- Are truly temporary (cache, logs, build artifacts)
- Contain no unique information
- Are duplicates of information elsewhere
- Have no historical or reference value

## Accessing Archived Content

All archived files are tracked in git history, so even if removed from the archive, they can be recovered. The INDEX.md file provides a quick reference to what's available in the archive and why it was archived.
