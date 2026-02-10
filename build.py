import os
import json
import shutil
import re
import hashlib
import sys
import argparse
from datetime import datetime
from xml.sax.saxutils import escape
import yaml

# --- Configuration ---
CONTENT_DIR = 'content'
THEMES_DIR = 'themes'
OUTPUT_DIR = 'docs'
POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')
CACHE_FILE = '.build_cache.json'
POSTS_PER_PAGE = 10
BLOG_URL = 'https://xiaonaofua.github.io/blog'
BLOG_TITLE = '小腦斧啊的博客'
BLOG_DESCRIPTION = 'Simple and elegant blog'
BLOG_AUTHOR = 'xiaonaofua'

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

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_yaml_frontmatter(content):
    """從文章內容提取YAML前置物"""
    if content.startswith('---'):
        try:
            end_index = content.find('---', 3)
            if end_index != -1:
                yaml_content = content[3:end_index].strip()
                metadata = yaml.safe_load(yaml_content)
                body = content[end_index + 3:].strip()
                return metadata if isinstance(metadata, dict) else {}, body
        except yaml.YAMLError:
            pass
    return {}, content

def generate_seo_tags(post_data, post_url):
    """生成SEO元數據標籤"""
    title = post_data.get('title', 'Untitled')
    description = post_data.get('description') or post_data.get('summary', '')[:160]
    keywords = post_data.get('keywords', '')
    image = post_data.get('image', f'{BLOG_URL}/default-og-image.png')
    
    seo_html = f'''    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{escape(description)}">
    <meta name="keywords" content="{escape(keywords)}">
    <meta name="author" content="{BLOG_AUTHOR}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{escape(post_url)}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(description)}">
    <meta property="og:image" content="{escape(image)}">
    <meta property="og:site_name" content="{BLOG_TITLE}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{escape(post_url)}">
    <meta property="twitter:title" content="{escape(title)}">
    <meta property="twitter:description" content="{escape(description)}">
    <meta property="twitter:image" content="{escape(image)}">
    
    <!-- 微信和QQ分享 -->
    <meta property="article:published_time" content="{post_data.get('date', datetime.now().isoformat())}">
    <meta property="article:author" content="{BLOG_AUTHOR}">
'''    
    return seo_html

def get_available_themes():
    themes = []
    if os.path.exists(THEMES_DIR):
        for item in os.listdir(THEMES_DIR):
            theme_path = os.path.join(THEMES_DIR, item)
            if os.path.isdir(theme_path) and item in THEME_CONFIG:
                themes.append(item)
    return themes

def validate_theme(theme_name):
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
    theme_static_dir = os.path.join(THEMES_DIR, theme_name, 'static')
    if os.path.exists(theme_static_dir):
        shutil.copytree(theme_static_dir, os.path.join(OUTPUT_DIR, 'static'), dirs_exist_ok=True)
        print(f"已複製 {theme_name} 主題靜態文件")
    else:
        print(f"Warning: Theme {theme_name} static files not found")

def load_theme_templates(theme_name):
    theme_templates_dir = os.path.join(THEMES_DIR, theme_name, 'templates')
    
    base_template_path = os.path.join(theme_templates_dir, 'base.html')
    post_template_path = os.path.join(theme_templates_dir, 'post.html')
    
    if not os.path.exists(base_template_path) or not os.path.exists(post_template_path):
        print(f"Warning: Theme {theme_name} templates not found, using default")
        base_template_path = os.path.join(THEMES_DIR, DEFAULT_THEME, 'templates', 'base.html')
        post_template_path = os.path.join(THEMES_DIR, DEFAULT_THEME, 'templates', 'post.html')
    
    base_template = read_file(base_template_path)
    post_template = read_file(post_template_path)
    
    print(f"已載入 {theme_name} 主題模板")
    return base_template, post_template

def get_file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def markdown_to_html(text):
    text = text.strip()
    
    text = re.sub(r'^### (.*$)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*$)', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*$)', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    
    text = re.sub(r'```([\s\S]*?)```', r'<pre><code>\1</code></pre>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    text = text.replace('\n', '<br>\n')
    
    return text

def estimate_reading_time(content):
    words = len(content.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"

def generate_pagination_html(current_page, total_pages, base_path=''):
    if total_pages <= 1:
        return ''
    
    pagination_html = '<div class="pagination">'
    
    if current_page > 1:
        prev_page = current_page - 1
        if prev_page == 1:
            pagination_html += f'<a href="{base_path}index.html" class="page-link">← 上一页</a>'
        else:
            pagination_html += f'<a href="{base_path}page{prev_page}.html" class="page-link">← 上一页</a>'
    else:
        pagination_html += '<span class="page-link disabled">← 上一页</span>'
    
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
    
    if current_page < total_pages:
        next_page = current_page + 1
        pagination_html += f'<a href="{base_path}page{next_page}.html" class="page-link">下一页 →</a>'
    else:
        pagination_html += '<span class="page-link disabled">下一页 →</span>'
    
    pagination_html += '</div>'
    return pagination_html

def parse_navigation_file():
    navi_file = os.path.join(CONTENT_DIR, 'navi.txt')
    navigation_items = []
    
    if not os.path.exists(navi_file):
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
                if line and not line.startswith('#'):
                    parts = line.split(' | ')
                    if len(parts) >= 3:
                        navigation_items.append({
                            'name': parts[0].strip(),
                            'url': parts[1].strip(),
                            'date': parts[2].strip()
                        })
    except Exception as e:
        print(f"Warning: Could not parse navi.txt: {e}")
        return [
            {'name': 'AWS英語指南', 'url': 'https://xiaonaofua.github.io/aws-english', 'date': '2025.07.22'},
            {'name': '匯率轉換器', 'url': 'https://xiaonaofua.github.io/exchangeRates/', 'date': '2025.06.15'},
            {'name': '網址導航', 'url': 'https://xiaonaofua.github.io/hao123/', 'date': '2025.05.10'},
            {'name': '詞彙學習', 'url': 'https://xiaonaofua.github.io/wordList/', 'date': '2025.04.08'}
        ]
    
    return navigation_items

def generate_navigation_html(navigation_items):
    nav_html = '<div class="external-nav">'
    for item in navigation_items:
        nav_html += f'<a href="{item["url"]}" target="_blank" rel="noopener">{item["name"]}({item["date"]})</a>'
    nav_html += '</div>'
    return nav_html

def generate_rss_feed(posts_metadata):
    """生成RSS源"""
    rss_items = ''
    for post in posts_metadata[:20]:
        post_url = f'{BLOG_URL}/{post["path"]}'
        description = re.sub(r'<[^>]+>', '', post['content'])[:300]
        
        rss_items += f'''    <item>
        <title>{escape(post['title'])}</title>
        <link>{escape(post_url)}</link>
        <guid>{escape(post_url)}</guid>
        <description>{escape(description)}</description>
        <pubDate>{post['file_create_datetime'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
        <author>{BLOG_AUTHOR}</author>
        <category>{post.get('category', '未分類')}</category>
    </item>
'''
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{escape(BLOG_TITLE)}</title>
        <link>{BLOG_URL}</link>
        <description>{escape(BLOG_DESCRIPTION)}</description>
        <language>zh-CN</language>
        <copyright>Copyright {datetime.now().year} {BLOG_AUTHOR}</copyright>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
        <docs>http://www.rssboard.org/rss-specification</docs>
{rss_items}    </channel>
</rss>'''
    
    return rss_content

def main():
    print("Starting blog build...")

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

    selected_theme = DEFAULT_THEME
    
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
    
    env_theme = os.getenv('BLOG_THEME')
    if env_theme and validate_theme(env_theme):
        selected_theme = env_theme
        print(f"主題: 使用環境變數指定主題: {THEME_CONFIG[selected_theme]['name']}")
    
    if selected_theme == DEFAULT_THEME and os.getenv('THEME_INTERACTIVE', '').lower() == 'true':
        selected_theme = select_theme_interactive()
    
    print(f"主題: 當前使用主題: {THEME_CONFIG[selected_theme]['name']}")
    print()

    copy_theme_static_files(selected_theme)
    base_template, post_template = load_theme_templates(selected_theme)

    navigation_items = parse_navigation_file()
    navigation_html = generate_navigation_html(navigation_items)

    posts_metadata = []
    cache = load_cache()
    current_cache = {}
    
    for filename in os.listdir(CONTENT_DIR):
        if (filename.endswith('.txt') or filename.endswith('.md')) and filename != 'navi.txt':
            filepath = os.path.join(CONTENT_DIR, filename)
            
            file_hash = get_file_hash(filepath)
            current_cache[filename] = file_hash
            
            if filename in cache and cache[filename] == file_hash:
                print(f"Skipped {filename}: no changes")
            
            content_raw = read_file(filepath)
            is_markdown = filename.endswith('.md')

            file_ctime = os.path.getctime(filepath)
            file_mtime = os.path.getmtime(filepath)
            file_create_datetime = datetime.fromtimestamp(file_ctime)
            file_modify_datetime = datetime.fromtimestamp(file_mtime)

            yaml_metadata, body_content = extract_yaml_frontmatter(content_raw)
            
            lines = body_content.strip().split('\n')
            title = yaml_metadata.get('title', 'Untitled')
            
            if not title and lines:
                title = lines[0].strip()
                body = '\n'.join(lines[1:]).strip()
            else:
                body = body_content.strip()
            
            if is_markdown:
                body = markdown_to_html(body)
            else:
                body = body.strip()
                import html
                body = html.escape(body)
                body = f'<pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">{body}</pre>'
            
            word_count = len(body.split())
            reading_time = estimate_reading_time(body)

            post_slug = os.path.splitext(filename)[0]
            post_path = f'posts/{post_slug}.html'

            clean_content = re.sub(r'<[^>]+>', '', body)
            summary = clean_content[:140].strip()
            if len(clean_content) > 140:
                summary += '...'

            post_info = {
                'title': title,
                'path': post_path,
                'file_create_datetime': file_create_datetime,
                'file_modify_datetime': file_modify_datetime,
                'create_date': file_create_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'modify_date': file_modify_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                'content': body,
                'summary': summary,
                'word_count': word_count,
                'reading_time': reading_time,
                'yaml_metadata': yaml_metadata
            }
            posts_metadata.append(post_info)

    posts_metadata.sort(key=lambda p: p['file_create_datetime'], reverse=True)

    for i, post in enumerate(posts_metadata):
        nav_html = '<div class="post-navigation">'
        
        if i > 0:
            prev_post = posts_metadata[i - 1]
            nav_html += f'<div class="nav-previous"><a href="../{prev_post["path"]}">← 上一篇: {prev_post["title"]}</a></div>'
        else:
            nav_html += '<div class="nav-previous"></div>'
        
        if i < len(posts_metadata) - 1:
            next_post = posts_metadata[i + 1]
            nav_html += f'<div class="nav-next"><a href="../{next_post["path"]}">下一篇: {next_post["title"]} →</a></div>'
        else:
            nav_html += '<div class="nav-next"></div>'
        
        nav_html += '</div>'
        
        post_url = f'{BLOG_URL}/{post["path"]}'
        seo_tags = generate_seo_tags(post['yaml_metadata'] or {'title': post['title'], 'summary': post['summary']}, post_url)
        
        post_html_content = post_template.replace('{{ title }}', post['title'])\
                                       .replace('{{ create_date }}', post['create_date'])\
                                       .replace('{{ modify_date }}', post['modify_date'])\
                                       .replace('{{ content }}', post['content'] + nav_html)
        
        full_page_html = base_template.replace('{{ title }}', post['title'])\
                                      .replace('{{ seo_tags }}', seo_tags)\
                                      .replace('{{ content }}', post_html_content)\
                                      .replace('{{ base_path }}', '../')\
                                      .replace('{{ navigation }}', navigation_html)
        
        write_file(os.path.join(OUTPUT_DIR, post['path']), full_page_html)

    total_posts = len(posts_metadata)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * POSTS_PER_PAGE
        end_idx = min(start_idx + POSTS_PER_PAGE, total_posts)
        page_posts = posts_metadata[start_idx:end_idx]
        
        index_list_items = ''
        for post in page_posts:
            index_list_items += f'<li><div class="post-header"><a href="{post["path"]}">{post["title"]}</a><div class="post-meta">創建: {post["create_date"]}</div></div><div class="post-summary">{post["summary"]}</div></li>\n'
        
        post_list_html = f'<ul class="post-list">{index_list_items}</ul>'
        pagination_html_page = generate_pagination_html(page_num, total_pages, '')
        index_content = post_list_html + pagination_html_page
        
        if page_num == 1:
            page_title = BLOG_TITLE
        else:
            page_title = f'{BLOG_TITLE} - 第{page_num}页'
        
        seo_tags = generate_seo_tags({'title': page_title, 'description': BLOG_DESCRIPTION}, BLOG_URL)
        
        index_html = base_template.replace('{{ title }}', page_title)\
                                  .replace('{{ seo_tags }}', seo_tags)\
                                  .replace('{{ content }}', index_content)\
                                  .replace('{{ base_path }}', '')\
                                  .replace('{{ navigation }}', navigation_html)
        
        if page_num == 1:
            write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_html)
        else:
            write_file(os.path.join(OUTPUT_DIR, f'page{page_num}.html'), index_html)
    
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * POSTS_PER_PAGE
        end_idx = min(start_idx + POSTS_PER_PAGE, total_posts)
        page_posts = posts_metadata[start_idx:end_idx]
        
        posts_list_items = ''
        for post in page_posts:
            posts_list_items += f'<li><div class="post-header"><a href="{post["path"].replace("posts/", "")}">{post["title"]}</a><div class="post-meta">創建: {post["create_date"]}</div></div><div class="post-summary">{post["summary"]}</div></li>\n'
        
        post_list_html = f'<ul class="post-list">{posts_list_items}</ul>'
        pagination_html_page = generate_pagination_html(page_num, total_pages, '')
        posts_index_content = post_list_html + pagination_html_page
        
        if page_num == 1:
            page_title = '所有文章'
        else:
            page_title = f'所有文章 - 第{page_num}页'
        
        seo_tags = generate_seo_tags({'title': page_title, 'description': '所有博客文章列表'}, f'{BLOG_URL}/posts/')
        
        posts_index_html = base_template.replace('{{ title }}', page_title)\
                                       .replace('{{ seo_tags }}', seo_tags)\
                                       .replace('{{ content }}', posts_index_content)\
                                       .replace('{{ base_path }}', '../')\
                                       .replace('{{ navigation }}', navigation_html)
        
        if page_num == 1:
            write_file(os.path.join(POSTS_DIR, 'index.html'), posts_index_html)
        else:
            write_file(os.path.join(POSTS_DIR, f'page{page_num}.html'), posts_index_html)
    
    rss_content = generate_rss_feed(posts_metadata)
    write_file(os.path.join(OUTPUT_DIR, 'rss.xml'), rss_content)
    
    sitemap_urls = [
        f'{BLOG_URL}/\n',
        f'{BLOG_URL}/posts/\n'
    ]
    for post in posts_metadata:
        sitemap_urls.append(f'{BLOG_URL}/{post["path"]}\n')
    
    sitemap_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    for url in sitemap_urls:
        sitemap_content += f'''    <url>
        <loc>{escape(url.strip())}</loc>
        <lastmod>{datetime.now().isoformat()}</lastmod>
    </url>
'''
    sitemap_content += '</urlset>'
    
    write_file(os.path.join(OUTPUT_DIR, 'sitemap.xml'), sitemap_content)
    
    save_cache(current_cache)
    
    print(f"✅ Build successful! {len(posts_metadata)} posts generated.")
    print(f"📁 Site generated in: {OUTPUT_DIR}/")
    print(f"📡 RSS feed generated: {OUTPUT_DIR}/rss.xml")
    print(f"🗺️  Sitemap generated: {OUTPUT_DIR}/sitemap.xml")

if __name__ == '__main__':
    main()