#!/usr/bin/env python3
import os
import sys
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import time

OUTPUT_DIR = 'docs'
PORT = 8000

class BlogHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)
    
    def do_GET(self):
        # Auto-rebuild when accessing the site
        if self.path == '/' or self.path.startswith('/posts'):
            print("🔄 Auto-rebuilding...")
            try:
                subprocess.run([sys.executable, 'build.py'], check=True, capture_output=True)
                print("✅ Rebuild complete")
            except subprocess.CalledProcessError as e:
                print(f"❌ Build failed: {e}")
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        # Reduce console noise
        if not args[1].startswith('200'):
            print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

def start_server():
    """Start the local development server."""
    # Initial build
    print("🔨 Initial build...")
    try:
        subprocess.run([sys.executable, 'build.py'], check=True)
        print("✅ Build successful")
    except subprocess.CalledProcessError as e:
        print(f"❌ Initial build failed: {e}")
        sys.exit(1)
    
    if not os.path.exists(OUTPUT_DIR):
        print(f"❌ Output directory {OUTPUT_DIR} not found!")
        sys.exit(1)
    
    # Find available port
    port = PORT
    while port < PORT + 10:
        try:
            server = HTTPServer(('localhost', port), BlogHandler)
            break
        except OSError:
            port += 1
    else:
        print("❌ Could not find available port!")
        sys.exit(1)
    
    url = f"http://localhost:{port}"
    print(f"🚀 Starting development server at {url}")
    print(f"📁 Serving files from: {OUTPUT_DIR}/")
    print("💡 The site will auto-rebuild when you visit pages")
    print("🛑 Press Ctrl+C to stop the server")
    
    # Open browser
    def open_browser():
        time.sleep(1)  # Wait for server to start
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser: {e}")
    
    Thread(target=open_browser, daemon=True).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()

def watch_mode():
    """Watch for file changes and auto-rebuild."""
    print("👀 Watching for file changes...")
    print("💡 Edit files in content/ and refresh browser to see changes")
    print("🛑 Press Ctrl+C to stop watching")
    
    try:
        import watchdog
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class ChangeHandler(FileSystemEventHandler):
            def __init__(self):
                self.last_build = 0
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                if not (event.src_path.endswith('.txt') or event.src_path.endswith('.md')):
                    return
                
                now = time.time()
                if now - self.last_build < 1:  # Debounce
                    return
                
                self.last_build = now
                print(f"📝 File changed: {event.src_path}")
                try:
                    subprocess.run([sys.executable, 'build.py'], check=True, capture_output=True)
                    print("✅ Auto-rebuild complete")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Build failed: {e}")
        
        observer = Observer()
        observer.schedule(ChangeHandler(), 'content', recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        
    except ImportError:
        print("📦 watchdog not installed. Install with: pip install watchdog")
        print("🔄 Using manual refresh mode instead")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'watch':
            watch_mode()
        elif command == '--help':
            print("Usage:")
            print("  python serve.py        - Start development server")
            print("  python serve.py watch  - Watch for file changes")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        start_server()

if __name__ == "__main__":
    main()