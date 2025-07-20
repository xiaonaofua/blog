import os
import json
import shutil
from datetime import datetime

# --- Configuration ---
CONTENT_DIR = 'content'
TEMPLATE_DIR = 'templates'
OUTPUT_DIR = 'docs'
POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')

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

    # Process content files
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith('.txt'):
            filepath = os.path.join(CONTENT_DIR, filename)
            content_raw = read_file(filepath)
            
            # Simple content format: first line is title, rest is body
            lines = content_raw.strip().split('\n')
            title = lines[0]
            body = '\n'.join(lines[1:]).strip()
            
            # Prepare metadata
            post_slug = os.path.splitext(filename)[0]
            post_path = f'posts/{post_slug}.html' # Use relative path without leading ./
            post_date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')

            post_info = {
                'title': title,
                'path': post_path,
                'date': post_date,
                'content': body
            }
            posts_metadata.append(post_info)



    # Sort posts by date, newest first
    posts_metadata.sort(key=lambda p: p['date'], reverse=True)

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
    index_html = base_template.replace('{{ title }}', '我的極簡博客')\
                              .replace('{{ content }}', index_content)\
                              .replace('{{ base_path }}', '')

    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_html)
    
    # --- Generate Posts Index Page ---
    # 子目錄頁面需要使用 ../ 作為基礎路徑
    posts_index_html = base_template.replace('{{ title }}', '所有文章')\
                                   .replace('{{ content }}', index_content)\
                                   .replace('{{ base_path }}', '../')

    write_file(os.path.join(POSTS_DIR, 'index.html'), posts_index_html)
    




    print(f"Build successful! {len(posts_metadata)} posts generated.")
    print(f"Site generated in: {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
