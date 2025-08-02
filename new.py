#!/usr/bin/env python3
import os
import sys
from datetime import datetime

CONTENT_DIR = 'content'

def create_new_post():
    # Get title from command line or prompt
    if len(sys.argv) > 1:
        title = " ".join(sys.argv[1:])
    else:
        title = input("Enter post title: ").strip()
    
    if not title:
        print("Title cannot be empty!")
        sys.exit(1)
    
    # Generate filename from title
    # Remove special characters and replace spaces with hyphens
    import re
    filename_base = re.sub(r'[^\w\s-]', '', title.lower())
    filename_base = re.sub(r'[-\s]+', '-', filename_base).strip('-')
    
    # Find next available number prefix
    existing_files = [f for f in os.listdir(CONTENT_DIR) if f.endswith(('.txt', '.md'))]
    numbers = []
    for f in existing_files:
        match = re.match(r'^(\d+)\.', f)
        if match:
            numbers.append(int(match.group(1)))
    
    next_num = max(numbers, default=0) + 1
    
    # Ask for file format
    format_choice = input("File format (1=txt, 2=md) [default: txt]: ").strip()
    extension = '.md' if format_choice == '2' else '.txt'
    
    filename = f"{next_num:02d}.{filename_base}{extension}"
    filepath = os.path.join(CONTENT_DIR, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        overwrite = input(f"File {filename} already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            print("Aborted.")
            sys.exit(1)
    
    # Create content template
    if extension == '.md':
        content = f"""{title}

在這裡寫你的文章內容...

## 小節標題

- 列表項目
- **粗體文字**
- *斜體文字*
- [鏈接文字](https://example.com)

```
代碼塊
```
"""
    else:
        content = f"""{title}

在這裡寫你的文章內容...
"""
    
    # Write the file
    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created new post: {filepath}")
    print(f"📝 Edit the file and then run: python publish.py \"{title}\"")
    
    # Optionally open in default editor
    open_editor = input("Open in default editor? (y/N): ").strip()
    if open_editor.lower() == 'y':
        import subprocess
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(['open', filepath])
        except Exception as e:
            print(f"Could not open editor: {e}")

if __name__ == "__main__":
    create_new_post()