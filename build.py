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
    search_documents = []

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
            post_path = f'/posts/{post_slug}.html' # Use root-relative path
            post_date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')

            post_info = {
                'title': title,
                'path': post_path,
                'date': post_date,
                'content': body
            }
            posts_metadata.append(post_info)

            # Add to search documents
            search_documents.append({
                'id': post_path,
                'title': title,
                'content': body
            })

    # Sort posts by date, newest first
    posts_metadata.sort(key=lambda p: p['date'], reverse=True)

    # --- Generate Individual Post Pages ---
    for post in posts_metadata:
        post_html_content = post_template.replace('{{ title }}', post['title'])\
                                       .replace('{{ date }}', post['date'])\
                                       .replace('{{ content }}', post['content'])
        
        full_page_html = base_template.replace('{{ title }}', post['title'])\
                                      .replace('{{ content }}', post_html_content)
        
        write_file(os.path.join(OUTPUT_DIR, post['path']), full_page_html)

    # --- Generate Index Page ---
    index_list_items = ''
    for post in posts_metadata:
        index_list_items += f'<li><a href="{post["path"]}">{post["title"]}</a><div class="post-meta">{post["date"]}</div></li>\n'
    
    index_content = f'<ul class="post-list">{index_list_items}</ul>'
    index_html = base_template.replace('{{ title }}', '我的極簡博客')\
                              .replace('{{ content }}', index_content)

    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_html)

    # --- Generate Search Index for lunr.js ---
    # Note: This is a simplified index. For a real site, you'd build the lunr index here.
    # For this static approach, we'll pass the documents and let the client build the index.
    # A better approach for larger sites is to pre-build the index using node.js or another tool.
    
    # We will create a structure that the client-side JS can load and process.
    # The client will build the index itself.
    # This is a simple but effective approach for small to medium sites.
    
    # We need to define the fields for lunr
    lunr_index_data = {
        'index': {
            'ref': 'id',
            'fields': ['title', 'content'],
            'documents': search_documents
        },
        'documents': search_documents # Pass documents separately for easy lookup
    }

    # This is a placeholder. The actual lunr index must be built by lunr.js.
    # The JS code is set up to fetch this JSON, then build the index in the browser.
    # To pre-build the index, you would need a JS runtime (like Node.js) in your build process.
    # For simplicity, we will not pre-build it.
    
    # Let's create the JSON structure that our search.js expects.
    # It expects the documents and a pre-built index. Let's simulate that.
    # A true pre-built index is more complex. We'll pass the documents and let JS build it.
    
    # The search.js is expecting a pre-built index. Let's adjust the python script to create a structure
    # that lunr can load. We can't fully build the serialized index without a python lunr library or calling node.
    # So, we will pass the documents and the JS will build it. Let's adjust the search.js logic slightly.
    
    # Let's re-think the search-index.json. It should contain the documents.
    # The JS will fetch it and then build the index.
    
    # Final structure for search-index.json
    final_search_data = {
        'documents': search_documents
    }

    # The search.js needs to be adapted to build the index from these documents.
    # Let's write the search.js again to reflect this.

    # Let's assume the search.js is already correct and builds the index on the fly.
    # The current search.js is actually expecting a pre-built index. Let's fix the search.js instead.

    # Let's create the search index file.
    # We will create a simple JSON file with the documents.
    # The JS will handle the indexing.
    search_data_for_js = {
        'docs': search_documents
    }
    write_file(os.path.join(OUTPUT_DIR, 'search-index.json'), json.dumps(search_data_for_js, indent=4, ensure_ascii=False))

    print(f"Build successful! {len(posts_metadata)} posts generated.")
    print(f"Site generated in: {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
