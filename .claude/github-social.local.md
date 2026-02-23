---
# Image generation provider
provider: svg

# SVG-specific settings
svg_style: illustrated

# Dark mode support
# false = light mode only, true = dark mode only, both = generate both variants
dark_mode: both

# Output settings
output_path: .github/social-preview.svg
dimensions: 1280x640
include_text: true
colors: auto

# README infographic settings
infographic_output: .github/readme-infographic.svg
infographic_style: hybrid

# Upload to repository (requires gh CLI or GITHUB_TOKEN)
upload_to_repo: false
---

# GitHub Social Plugin Configuration

This configuration was created by `/github-social:setup`.

## Provider: SVG

Claude generates clean SVG graphics directly. No API key required.
- **Pros**: Free, instant, editable, small file size (10-50KB)
- **Best for**: Professional, predictable results

## Style: Illustrated

Organic paths with hand-drawn aesthetic and warm colors. Uses flowing SVG paths
for a friendly, approachable feel.

## Dark Mode: Both

Generates both light and dark variants:
- `.github/social-preview.svg` (light)
- `.github/social-preview-dark.svg` (dark)

## Commands

- Generate social preview: `/github-social:social-preview`
- Enhance README: `/github-social:readme-enhance`
- Update repo metadata: `/github-social:repo-metadata`
- Run all: `/github-social:all`
- Reconfigure: `/github-social:setup`
