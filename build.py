import os
import json
import shutil
import re
import hashlib
import sys
import argparse
from datetime import datetime
from xml.sax.saxutils import escape

# --- Configuration ---
CONTENT_DIR = 'content'
THEMES_DIR = 'themes'
OUTPUT_DIR = 'docs'
POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')
CACHE_FILE = '.build_cache.json'
POSTS_PER_PAGE = 10

# Theme Configuration
THEME_CONFIG = {
    'pixel': {
        'name': '像素風',
        'description': '賽博朋克終端風格 - 黑色背景綠色文字'
    },
    'minimal': {
        'name': '極簡風',
        'description': '優雅現代極簡風格 - 白色背景優雅排版'
    }
}
DEFAULT_THEME = 'pixel'

# --- Helper Functions ---
def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_available_themes():
    """獲取可用主題列表"""
    themes = []
    if os.path.exists(THEMES_DIR):
        for item in os.listdir(THEMES_DIR):
            theme_path = os.path.join(THEMES_DIR, item)
            if os.path.isdir(theme_path) and item in THEME_CONFIG:
                themes.append(item)
    return themes

def validate_theme(theme_name):
    """驗證主題完整性"""
    if theme_name not in THEME_CONFIG:
        return False
    
    theme_path = os.path.join(THEMES_DIR, theme_name)
    required_files = [
        os.path.join(theme_path, 'templates', 'base.html'),
        os.path.join(theme_path, 'templates', 'post.html'),
        os.path.join(theme_path, 'static', 'css', 'style.css')
    ]
    
    return all(os.path.exists(f) for f in required_files)

def select_theme_interactive():
    """交互式主題選擇"""
    available_themes = get_available_themes()
    
    if not available_themes:
        print(f"Warning: No themes found, using default theme: {DEFAULT_THEME}")
        return DEFAULT_THEME
    
    print("\n" + "="*50)
    print("選擇博客主題")
    print("="*50)
    
    for i, theme in enumerate(available_themes, 1):
        config = THEME_CONFIG[theme]
        print(f"{i}. {config['name']}")
        print(f"   {config['description']}")
        print()
    
    while True:
        try:
            choice = input(f"請選擇主題 (1-{len(available_themes)}) [預設: {DEFAULT_THEME}]: ").strip()
            
            if not choice:
                return DEFAULT_THEME
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(available_themes):
                selected_theme = available_themes[choice_num - 1]
                if validate_theme(selected_theme):
                    print(f"已選擇主題: {THEME_CONFIG[selected_theme]['name']}")
                    return selected_theme
                else:
                    print(f"錯誤: 主題 {selected_theme} 檔案不完整!")
            else:
                print("錯誤: 請輸入有效的選項編號!")
        except ValueError:
            print("錯誤: 請輸入數字!")
        except KeyboardInterrupt:
            print(f"\n使用預設主題: {DEFAULT_THEME}")
            return DEFAULT_THEME

def copy_theme_static_files(theme_name):
    """複製主題特定的靜態文件"""
    theme_static_dir = os.path.join(THEMES_DIR, theme_name, 'static')
    if os.path.exists(theme_static_dir):
        shutil.copytree(theme_static_dir, os.path.join(OUTPUT_DIR, 'static'), dirs_exist_ok=True)
        print(f"已複製 {theme_name} 主題靜態文件")
    else:
        print(f"Warning: Theme {theme_name} static files not found")

def load_theme_templates(theme_name):
    """載入指定主題的模板"""
    theme_templates_dir = os.path.join(THEMES_DIR, theme_name, 'templates')
    
    base_template_path = os.path.join(theme_templates_dir, 'base.html')
    post_template_path = os.path.join(theme_templates_dir, 'post.html')
    
    if not os.path.exists(base_template_path) or not os.path.exists(post_template_path):
        print(f"Warning: Theme {theme_name} templates not found, using default")
        # Fallback to default templates
        base_template_path = os.path.join(THEMES_DIR, DEFAULT_THEME, 'templates', 'base.html')
        post_template_path = os.path.join(THEMES_DIR, DEFAULT_THEME, 'templates', 'post.html')
    
    base_template = read_file(base_template_path)
    post_template = read_file(post_template_path)
    
    print(f"已載入 {theme_name} 主題模板")
    return base_template, post_template

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
    # Strip leading and trailing whitespace/newlines first
    text = text.strip()
    
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

def generate_pagination_html(current_page, total_pages, base_path=''):
    """Generate pagination navigation HTML."""
    if total_pages <= 1:
        return ''
    
    pagination_html = '<div class="pagination">'
    
    # Previous page link
    if current_page > 1:
        prev_page = current_page - 1
        if prev_page == 1:
            pagination_html += f'<a href="{base_path}index.html" class="page-link">← 上一页</a>'
        else:
            pagination_html += f'<a href="{base_path}page{prev_page}.html" class="page-link">← 上一页</a>'
    else:
        pagination_html += '<span class="page-link disabled">← 上一页</span>'
    
    # Page numbers
    pagination_html += '<span class="page-numbers">'
    for page in range(1, total_pages + 1):
        if page == current_page:
            pagination_html += f'<span class="current-page">{page}</span>'
        else:
            if page == 1:
                pagination_html += f'<a href="{base_path}index.html" class="page-number">{page}</a>'
            else:
                pagination_html += f'<a href="{base_path}page{page}.html" class="page-number">{page}</a>'
    pagination_html += '</span>'
    
    # Next page link
    if current_page < total_pages:
        next_page = current_page + 1
        pagination_html += f'<a href="{base_path}page{next_page}.html" class="page-link">下一页 →</a>'
    else:
        pagination_html += '<span class="page-link disabled">下一页 →</span>'
    
    pagination_html += '</div>'
    return pagination_html

def parse_navigation_file():
    """Parse navigation.txt file and return navigation data."""
    navi_file = os.path.join(CONTENT_DIR, 'navi.txt')
    navigation_items = []
    
    if not os.path.exists(navi_file):
        # 如果navi.txt不存在，返回默认导航
        return [
            {'name': 'AWS英語指南', 'url': 'https://xiaonaofua.github.io/aws-english', 'date': '2025.07.22'},
            {'name': '匯率轉換器', 'url': 'https://xiaonaofua.github.io/exchangeRates/', 'date': '2025.06.15'},
            {'name': '網址導航', 'url': 'https://xiaonaofua.github.io/hao123/', 'date': '2025.05.10'},
            {'name': '詞彙學習', 'url': 'https://xiaonaofua.github.io/wordList/', 'date': '2025.04.08'}
        ]
    
    try:
        with open(navi_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释
                    parts = line.split(' | ')
                    if len(parts) >= 3:
                        navigation_items.append({
                            'name': parts[0].strip(),
                            'url': parts[1].strip(),
                            'date': parts[2].strip()
                        })
    except Exception as e:
        print(f"Warning: Could not parse navi.txt: {e}")
        # 返回默认导航
        return [
            {'name': 'AWS英語指南', 'url': 'https://xiaonaofua.github.io/aws-english', 'date': '2025.07.22'},
            {'name': '匯率轉換器', 'url': 'https://xiaonaofua.github.io/exchangeRates/', 'date': '2025.06.15'},
            {'name': '網址導航', 'url': 'https://xiaonaofua.github.io/hao123/', 'date': '2025.05.10'},
            {'name': '詞彙學習', 'url': 'https://xiaonaofua.github.io/wordList/', 'date': '2025.04.08'}
        ]
    
    return navigation_items

def generate_navigation_html(navigation_items):
    """Generate navigation HTML from navigation items."""
    nav_html = '<div class="external-nav">'
    for item in navigation_items:
        nav_html += f'<a href="{item["url"]}" target="_blank" rel="noopener">{item["name"]}({item["date"]})</a>'
    nav_html += '</div>'
    return nav_html

# --- Main Build Logic ---
def main():
    print("Starting blog build...")

    # Clean and recreate output directory
    if os.path.exists(OUTPUT_DIR):
        try:
            shutil.rmtree(OUTPUT_DIR)
        except PermissionError:
            print(f"Warning: Could not remove {OUTPUT_DIR}. Trying to clean contents...")
            for item in os.listdir(OUTPUT_DIR):
                item_path = os.path.join(OUTPUT_DIR, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except PermissionError:
                    print(f"Warning: Could not remove {item_path}")
    os.makedirs(POSTS_DIR, exist_ok=True)

    # Determine theme to use
    selected_theme = DEFAULT_THEME
    
    # Check for command line theme argument
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == '--theme' and i + 1 < len(sys.argv):
                theme_arg = sys.argv[i + 1]
                if validate_theme(theme_arg):
                    selected_theme = theme_arg
                    print(f"主題: 使用命令行指定主題: {THEME_CONFIG[selected_theme]['name']}")
                else:
                    print(f"錯誤: 指定的主題 '{theme_arg}' 無效或不完整")
                break
    
    # Check for environment variable theme
    env_theme = os.getenv('BLOG_THEME')
    if env_theme and validate_theme(env_theme):
        selected_theme = env_theme
        print(f"主題: 使用環境變數指定主題: {THEME_CONFIG[selected_theme]['name']}")
    
    # Interactive theme selection if not specified
    if selected_theme == DEFAULT_THEME and os.getenv('THEME_INTERACTIVE', '').lower() == 'true':
        selected_theme = select_theme_interactive()
    
    print(f"主題: 當前使用主題: {THEME_CONFIG[selected_theme]['name']}")
    print()

    # Copy theme static files
    copy_theme_static_files(selected_theme)

    # Load theme templates
    base_template, post_template = load_theme_templates(selected_theme)

    # Parse navigation from navi.txt
    navigation_items = parse_navigation_file()
    navigation_html = generate_navigation_html(navigation_items)

    posts_metadata = []

    # Load cache for change detection
    cache = load_cache()
    current_cache = {}
    
    # Process content files
    for filename in os.listdir(CONTENT_DIR):
        if (filename.endswith('.txt') or filename.endswith('.md')) and filename != 'navi.txt':
            filepath = os.path.join(CONTENT_DIR, filename)
            
            # Check if file has changed
            file_hash = get_file_hash(filepath)
            current_cache[filename] = file_hash
            
            if filename in cache and cache[filename] == file_hash:
                print(f"Skipped {filename}: no changes")
                # Still need to load for index generation
            
            content_raw = read_file(filepath)
            is_markdown = filename.endswith('.md')

            # Get file creation and modification times
            file_ctime = os.path.getctime(filepath)  # Creation time
            file_mtime = os.path.getmtime(filepath)  # Modification time
            file_create_datetime = datetime.fromtimestamp(file_ctime)
            file_modify_datetime = datetime.fromtimestamp(file_mtime)

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
                # For txt files, preserve original formatting with pre tag
                body = body.strip()
                # Escape HTML characters to prevent issues
                import html
                body = html.escape(body)
                # Wrap in pre tag to preserve whitespace and formatting
                body = f'<pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{body}</pre>'
            
            # Calculate reading time and word count
            word_count = len(body.split())
            reading_time = estimate_reading_time(body)

            # Prepare metadata
            post_slug = os.path.splitext(filename)[0]
            post_path = f'posts/{post_slug}.html' # Use relative path without leading ./

            # Generate summary (first 140 characters)
            # Remove HTML tags for summary generation
            clean_content = re.sub(r'<[^>]+>', '', body)
            summary = clean_content[:140].strip()
            if len(clean_content) > 140:
                summary += '...'

            post_info = {
                'title': title,
                'path': post_path,
                'file_create_datetime': file_create_datetime,  # Creation time for sorting
                'file_modify_datetime': file_modify_datetime,  # Modification time
                'create_date': file_create_datetime.strftime('%Y-%m-%d %H:%M:%S'),  # Creation date display
                'modify_date': file_modify_datetime.strftime('%Y-%m-%d %H:%M:%S'),   # Modification date display
                'content': body,
                'summary': summary,
                'word_count': word_count,
                'reading_time': reading_time
            }
            posts_metadata.append(post_info)



    # Sort posts by file creation time, newest first
    posts_metadata.sort(key=lambda p: p['file_create_datetime'], reverse=True)

    # --- Generate Individual Post Pages ---
    for i, post in enumerate(posts_metadata):
        # Generate navigation for previous/next posts
        nav_html = '<div class="post-navigation">'
        
        # Previous post (newer)
        if i > 0:
            prev_post = posts_metadata[i - 1]
            nav_html += f'<div class="nav-previous"><a href="../{prev_post["path"]}">← 上一篇: {prev_post["title"]}</a></div>'
        else:
            nav_html += '<div class="nav-previous"></div>'
        
        # Next post (older)
        if i < len(posts_metadata) - 1:
            next_post = posts_metadata[i + 1]
            nav_html += f'<div class="nav-next"><a href="../{next_post["path"]}">下一篇: {next_post["title"]} →</a></div>'
        else:
            nav_html += '<div class="nav-next"></div>'
        
        nav_html += '</div>'
        
        post_html_content = post_template.replace('{{ title }}', post['title'])\
                                       .replace('{{ create_date }}', post['create_date'])\
                                       .replace('{{ modify_date }}', post['modify_date'])\
                                       .replace('{{ content }}', post['content'] + nav_html)
        
        # 子目錄頁面需要使用 ../ 作為基礎路徑
        full_page_html = base_template.replace('{{ title }}', post['title'])\
                                      .replace('{{ content }}', post_html_content)\
                                      .replace('{{ base_path }}', '../')\
                                      .replace('{{ navigation }}', navigation_html)
        
        write_file(os.path.join(OUTPUT_DIR, post['path']), full_page_html)

    # --- Generate Index Pages with Pagination ---
    total_posts = len(posts_metadata)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE  # Ceiling division
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * POSTS_PER_PAGE
        end_idx = min(start_idx + POSTS_PER_PAGE, total_posts)
        page_posts = posts_metadata[start_idx:end_idx]
        
        # Generate post list for this page
        index_list_items = ''
        for post in page_posts:
            index_list_items += f'<li><div class="post-header"><a href="{post["path"]}">{post["title"]}</a><div class="post-meta">創建: {post["create_date"]}</div></div><div class="post-summary">{post["summary"]}</div></li>\n'
        
        post_list_html = f'<ul class="post-list">{index_list_items}</ul>'
        
        # Generate pagination navigation
        pagination_html = generate_pagination_html(page_num, total_pages, '')
        
        # Combine content
        index_content = post_list_html + pagination_html
        
        # Generate page title
        if page_num == 1:
            page_title = '小腦斧啊的博客'
        else:
            page_title = f'小腦斧啊的博客 - 第{page_num}页'
        
        # 根目錄頁面的基礎路徑為空字符串
        index_html = base_template.replace('{{ title }}', page_title)\
                                  .replace('{{ content }}', index_content)\
                                  .replace('{{ base_path }}', '')\
                                  .replace('{{ navigation }}', navigation_html)
        
        # Write the page
        if page_num == 1:
            write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_html)
        else:
            write_file(os.path.join(OUTPUT_DIR, f'page{page_num}.html'), index_html)
    
    # --- Generate Posts Index Pages with Pagination ---
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * POSTS_PER_PAGE
        end_idx = min(start_idx + POSTS_PER_PAGE, total_posts)
        page_posts = posts_metadata[start_idx:end_idx]
        
        # Generate post list for this page
        posts_list_items = ''
        for post in page_posts:
            posts_list_items += f'<li><div class="post-header"><a href="{post["path"].replace("posts/", "")}">{post["title"]}</a><div class="post-meta">創建: {post["create_date"]}</div></div><div class="post-summary">{post["summary"]}</div></li>\n'
        
        post_list_html = f'<ul class="post-list">{posts_list_items}</ul>'
        
        # Generate pagination navigation (for subdirectory)
        pagination_html = generate_pagination_html(page_num, total_pages, '')
        
        # Combine content
        posts_index_content = post_list_html + pagination_html
        
        # Generate page title
        if page_num == 1:
            page_title = '所有文章'
        else:
            page_title = f'所有文章 - 第{page_num}页'
        
        # 子目錄頁面需要使用 ../ 作為基礎路徑
        posts_index_html = base_template.replace('{{ title }}', page_title)\
                                       .replace('{{ content }}', posts_index_content)\
                                       .replace('{{ base_path }}', '../')\
                                       .replace('{{ navigation }}', navigation_html)
        
        # Write the page
        if page_num == 1:
            write_file(os.path.join(POSTS_DIR, 'index.html'), posts_index_html)
        else:
            write_file(os.path.join(POSTS_DIR, f'page{page_num}.html'), posts_index_html)
    
    # --- Generate RSS Feed ---
    rss_items = ''
    for post in posts_metadata[:10]:  # Latest 10 posts
        rss_items += f'''<item>
            <title>{escape(post['title'])}</title>
            <link>https://xiaonaofua.github.io/blog/{post['path']}</link>
            <description>{escape(post['content'][:200])}...</description>
            <pubDate>{post['file_create_datetime'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
            <guid>https://xiaonaofua.github.io/blog/{post['path']}</guid>
        </item>\n'''
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>小腦斧啊的博客</title>
        <link>https://xiaonaofua.github.io/blog</link>
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
