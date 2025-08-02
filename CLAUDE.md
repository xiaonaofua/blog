# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Build the static site
```bash
python build.py
```

### Deploy to GitHub Pages
```bash
python build.py
git add .
git commit -m "new txt"
git push origin main
```

## Architecture Overview

This is a minimal static blog generator built in Python that converts text files to HTML pages.

### Core Components

- **build.py**: Main build script that processes content and generates static HTML
- **content/**: Directory containing blog posts as `.txt` files with specific format
- **templates/**: HTML templates with placeholder substitution
  - `base.html`: Main page layout with Chinese localization
  - `post.html`: Individual post template
- **static/**: CSS and JS assets copied to output
- **docs/**: Generated output directory for GitHub Pages

### Content Format

Blog posts are written as `.txt` files in `content/` directory:
- First line: Title (automatically extracted)
- Second line: Empty
- Remaining lines: Post content
- File modification time is used for sorting (newest first)

### Build Process

1. Cleans and recreates `docs/` output directory
2. Copies static assets from `static/` to `docs/static/`
3. Processes all `.txt` files in `content/`:
   - Removes `title:` and `date:` metadata prefixes from content
   - Uses file modification time for post ordering
   - Generates individual post HTML pages
4. Creates index pages with post listings
5. Handles relative paths for subdirectory navigation

### Template System

Simple string replacement templating:
- `{{ title }}`: Post/page title
- `{{ content }}`: Main content area
- `{{ date }}`: Post date from file modification time
- `{{ base_path }}`: Relative path for assets (empty for root, `../` for subdirs)

### Deployment

Site is deployed to GitHub Pages from the `docs/` directory. Live URL: https://co2sou.github.io/blog