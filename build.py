import os
import json
import shutil
import re
import hashlib
from datetime import datetime
from xml.sax.saxutils import escape

# --- Configuration ---
CONTENT_DIR = 'content'
TEMPLATE_DIR = 'templates'
OUTPUT_DIR = 'docs'
POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')
CACHE_FILE = '.build_cache.json'

# --- Helper Functions ---
def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def copy_static_files():
    static_dir = 'static'
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(OUTPUT_DIR, 'static'), dirs_exist_ok=True)

def get_file_hash(filepath):
    """Get MD5 hash of file for change detection."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache():
    """Load build cache."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save build cache."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def markdown_to_html(text):
    """Simple Markdown to HTML converter."""
    # Headers
    text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    
    # Code blocks
    text = re.sub(r'```([\s\S]*?)```', r'<pre><code>\1</code></pre>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Line breaks
    text = text.replace('\n', '<br>\n')
    
    return text

def estimate_reading_time(content):
    """Estimate reading time in minutes."""
    words = len(content.split())
    # Assume 200 words per minute reading speed
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"

# --- Main Build Logic ---
def main():
    print("Starting blog build...")

    # Clean and recreate output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(POSTS_DIR)

    # Copy static files
    copy_static_files()

    # Load templates
    base_template = read_file(os.path.join(TEMPLATE_DIR, 'base.html'))
    post_template = read_file(os.path.join(TEMPLATE_DIR, 'post.html'))

    posts_metadata = []

    # Load cache for change detection
    cache = load_cache()
    current_cache = {}
    
    # Process content files
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.txt') or filename.endswith('.md'):
            filepath = os.path.join(CONTENT_DIR, filename)
            
            # Check if file has changed
            file_hash = get_file_hash(filepath)
            current_cache[filename] = file_hash
            
            if filename in cache and cache[filename] == file_hash:
                print(f"Skipped {filename}: no changes")
                # Still need to load for index generation
            
            content_raw = read_file(filepath)
            is_markdown = filename.endswith('.md')

            # Get file modification time for sorting
            file_mtime = os.path.getmtime(filepath)
            file_datetime = datetime.fromtimestamp(file_mtime)

            # Process and modify the txt file content
            lines = content_raw.strip().split('\n')
            modified_lines = []
            title = 'Untitled'
            content_modified = False

            for line in lines:
                if line.strip().startswith('title:'):
                    # Remove "title: " prefix and use the rest as title
                    title_content = line.strip()[6:].strip()  # Remove "title:" and whitespace
                    if title_content:
                        title = title_content
                        modified_lines.append(title_content)  # Add title without prefix
                        content_modified = True
                    else:
                        content_modified = True  # Still modified even if empty
                elif line.strip().startswith('date:'):
                    # Skip date lines entirely
                    content_modified = True
                else:
                    modified_lines.append(line)

            # Write back the modified content to the txt file if changes were made
            if content_modified:
                modified_content = '\n'.join(modified_lines)
                write_file(filepath, modified_content)
                print(f"Modified {filename}: removed metadata prefixes")

            # Use first line as title if we have content
            if modified_lines and modified_lines[0].strip():
                title = modified_lines[0].strip()
                body = '\n'.join(modified_lines[1:]).strip()
            else:
                body = '\n'.join(modified_lines).strip()
            
            # Convert Markdown to HTML if needed
            if is_markdown:
                body = markdown_to_html(body)
            else:
                # For txt files, preserve line breaks
                body = body.replace('\n', '<br>\n')
            
            # Calculate reading time and word count
            word_count = len(body.split())
            reading_time = estimate_reading_time(body)

            # Prepare metadata
            post_slug = os.path.splitext(filename)[0]
            post_path = f'posts/{post_slug}.html' # Use relative path without leading ./

            post_info = {
                'title': title,
                'path': post_path,
                'file_datetime': file_datetime,  # Use file modification time for sorting
                'date': file_datetime.strftime('%Y-%m-%d %H:%M:%S'),  # Display format with time
                'content': body,
                'word_count': word_count,
                'reading_time': reading_time
            }
            posts_metadata.append(post_info)



    # Sort posts by file modification time, newest first
    posts_metadata.sort(key=lambda p: p['file_datetime'], reverse=True)

    # --- Generate Individual Post Pages ---
    for post in posts_metadata:
        post_html_content = post_template.replace('{{ title }}', post['title'])\
                                       .replace('{{ date }}', post['date'])\
                                       .replace('{{ content }}', post['content'])
        
        # 子目錄頁面需要使用 ../ 作為基礎路徑
        full_page_html = base_template.replace('{{ title }}', post['title'])\
                                      .replace('{{ content }}', post_html_content)\
                                      .replace('{{ base_path }}', '../')
        
        write_file(os.path.join(OUTPUT_DIR, post['path']), full_page_html)

    # --- Generate Index Page ---
    index_list_items = ''
    for post in posts_metadata:
        index_list_items += f'<li><a href="{post["path"]}">{post["title"]}</a><div class="post-meta">{post["date"]}</div></li>\n'
    
    index_content = f'<ul class="post-list">{index_list_items}</ul>'
    
    # 根目錄頁面的基礎路徑為空字符串
    index_html = base_template.replace('{{ title }}', '我的博客')\
                              .replace('{{ content }}', index_content)\
                              .replace('{{ base_path }}', '')

    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_html)
    
    # --- Generate Posts Index Page ---
    # 子目錄頁面需要使用 ../ 作為基礎路徑
    posts_index_html = base_template.replace('{{ title }}', '所有文章')\
                                   .replace('{{ content }}', index_content)\
                                   .replace('{{ base_path }}', '../')

    write_file(os.path.join(POSTS_DIR, 'index.html'), posts_index_html)
    
    # --- Generate RSS Feed ---
    rss_items = ''
    for post in posts_metadata[:10]:  # Latest 10 posts
        rss_items += f'''<item>
            <title>{escape(post['title'])}</title>
            <link>https://co2sou.github.io/blog/{post['path']}</link>
            <description>{escape(post['content'][:200])}...</description>
            <pubDate>{post['file_datetime'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
            <guid>https://co2sou.github.io/blog/{post['path']}</guid>
        </item>\n'''
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>我的博客</title>
        <link>https://co2sou.github.io/blog</link>
        <description>Simple and elegant blog</description>
        <language>zh-CN</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        {rss_items}
    </channel>
</rss>'''
    
    write_file(os.path.join(OUTPUT_DIR, 'rss.xml'), rss_content)
    
    # Save cache
    save_cache(current_cache)
    
    print(f"Build successful! {len(posts_metadata)} posts generated.")
    print(f"Site generated in: {OUTPUT_DIR}/")
    print(f"RSS feed generated: {OUTPUT_DIR}/rss.xml")

if __name__ == '__main__':
    main()
