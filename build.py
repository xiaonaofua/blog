import os
import yaml
import feedparser
from jinja2 import Environment, FileSystemLoader

def extract_metadata(content):
    """Extract metadata from YAML front matter."""
    if content.startswith('---'):
        end_index = content.find('---', 3)
        if end_index != -1:
            metadata = yaml.safe_load(content[3:end_index])
            return metadata if isinstance(metadata, dict) else {}
    return {}

def generate_rss(posts):
    """Generate RSS feed."""
    rss_items = []
    for post in posts:
        rss_items.append({
            'title': post.get('title'),
            'link': f"http://yourblog.com/{post['slug']}",
            'description': post.get('description'),
            'author': post.get('author'),
        })
    return rss_items

def render_html(template_name, context):
    """Render HTML using Jinja2 template."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_name)
    return template.render(context)

def build_blog():
    """Main function to build the blog."""
    posts = []
    
    # Loop through content files
    content_dir = 'content'
    for filename in os.listdir(content_dir):
        with open(os.path.join(content_dir, filename), 'r') as file:
            content = file.read()
            metadata = extract_metadata(content)
            if metadata:
                posts.append(metadata)
    
    # Generate RSS
    rss_feed = generate_rss(posts)
    
    # Render RSS and other HTML files
    with open('rss_feed.xml', 'w') as file:
        file.write(render_html('rss_template.xml', {'items': rss_feed}))

    print("Blog build completed with SEO metadata and RSS generation.")

if __name__ == "__main__":
    build_blog()