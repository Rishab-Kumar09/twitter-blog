from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import sys
from datetime import datetime, timedelta
import threading
import time

# Import existing functionality
from gauntlet_blog_system import GauntletBlogSystem

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'unified_twitter_blog_system_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
blog_system = None
scraping_in_progress = False
blog_generation_in_progress = False

# Initialize blog system with API keys
def initialize_blog_system():
    global blog_system
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        hubspot_key = os.getenv('HUBSPOT_API_KEY')
        
        # If not found in environment, try extracting from .env file with UTF-16 encoding
        if not openai_key or not openai_key.startswith('sk-'):
            try:
                with open('.env', 'r', encoding='utf-16') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'OPENAI_API_KEY' in line and '=' in line:
                            openai_key = line.split('=', 1)[1].strip()
                            os.environ['OPENAI_API_KEY'] = openai_key
                            print("✅ Extracted OpenAI API key from .env file (UTF-16)")
                            break
                    for line in content.split('\n'):
                        if 'HUBSPOT_API_KEY' in line and '=' in line:
                            hubspot_key = line.split('=', 1)[1].strip()
                            os.environ['HUBSPOT_API_KEY'] = hubspot_key
                            print("✅ Extracted HubSpot API key from .env file (UTF-16)")
                            break
            except Exception as env_error:
                print(f"⚠️ Could not read .env file: {env_error}")
        
        # Check if we have valid API keys
        if openai_key and openai_key.startswith('sk-') and len(openai_key) > 20:
            blog_system = GauntletBlogSystem(
                openai_api_key=openai_key,
                hubspot_api_key=hubspot_key if hubspot_key and hubspot_key.startswith('pat-') else None
            )
            print(f"✅ Blog system initialized with API keys")
            print(f"   - OpenAI: ✅ Configured (GPT-4 ready)")
            print(f"   - HubSpot: {'✅ Configured' if hubspot_key and hubspot_key.startswith('pat-') else '❌ Missing'}")
        else:
            print(f"⚠️ OpenAI API key not found in environment variables or .env file")
            blog_system = None
    except Exception as e:
        print(f"⚠️ Could not load API keys: {e}")
        blog_system = None

# Initialize on startup
initialize_blog_system()

@app.route('/')
def index():
    return render_template('unified_index.html')

@app.route('/scrape', methods=['POST'])
def scrape_tweets():
    global scraping_in_progress
    
    if scraping_in_progress:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        keywords = data.get('keywords', '').strip()
        start_date = data.get('startDate', '')
        num_blogs = int(data.get('numBlogs', 3))  # Default to 3 if not provided
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        scraping_in_progress = True
        
        # Create blogs directory if it doesn't exist
        blogs_dir = 'generated_blogs'
        if not os.path.exists(blogs_dir):
            os.makedirs(blogs_dir)
            socketio.emit('progress', {'message': f'📁 Created blogs directory: {blogs_dir}'})
        
        def progress_callback(message):
            socketio.emit('progress', {'message': message})
        
        # Start scraping in a separate thread
        def scrape_and_generate():
            global scraping_in_progress
            try:
                # Import the scraping function from app.py
                from app import scrape_twitter_profile
                
                progress_callback("🚀 Starting Twitter scraping...")
                
                # Run Twitter scraping
                result = scrape_twitter_profile(username, keywords, start_date, progress_callback)
                
                if result and result.get('success'):
                    tweet_count = result.get('tweet_count', 0)
                    progress_callback(f"✅ Scraping complete! Found {tweet_count} tweets.")
                    
                    # If keywords provided, automatically generate blogs
                    if keywords and tweet_count > 0:
                        progress_callback("🔥 Starting automated blog generation...")
                        
                        # Get the latest tweet file for analysis
                        tweet_files = [f for f in os.listdir('tweets') if f.endswith('.xlsx')]
                        if tweet_files:
                            latest_file = os.path.join('tweets', max(tweet_files, key=lambda f: os.path.getctime(os.path.join('tweets', f))))
                            
                            socketio.emit('progress', {'message': '📊 PHASE 1: Analyzing tweets for themes...'})
                            
                            # Use the blog system to analyze and generate
                            topics = blog_system.analyze_tweets_for_themes(latest_file)
                            
                            if len(topics) > 0:
                                socketio.emit('progress', {'message': f'✅ Found {len(topics)} blog topics'})
                                socketio.emit('progress', {'message': f'⚡ PHASE 2: Generating {num_blogs} blog posts with ChatGPT...'})
                                
                                generated_count = 0
                                for i, topic in enumerate(topics[:num_blogs]):
                                    socketio.emit('progress', {'message': f'🤖 Generating blog {i+1}/{num_blogs}: {topic.canonical_question}'})
                                    
                                    # Generate blog and save to dedicated folder
                                    blog_post = blog_system.generate_blog_post(topic)
                                    if blog_post:
                                        # Save directly to blogs directory
                                        filename = blog_system._save_blog_locally(blog_post, blogs_dir)
                                        if filename:
                                            socketio.emit('progress', {'message': f'✅ Blog {i+1}/{num_blogs} saved: {filename}'})
                                            generated_count += 1
                                        else:
                                            socketio.emit('progress', {'message': f'❌ Failed to save blog {i+1}/{num_blogs}'})
                                    else:
                                        socketio.emit('progress', {'message': f'❌ Failed to generate blog {i+1}/{num_blogs}'})
                                
                                socketio.emit('progress', {'message': '🤖 PHASE 3: Finalizing...'})
                                blog_system.generate_robots_txt()
                                socketio.emit('progress', {'message': '🤖 Generated robots.txt for SEO optimization'})
                                
                                socketio.emit('workflow_complete', {
                                    'message': f'🎉 Generated {generated_count} AI-powered blogs from your tweets!',
                                    'blogs_folder': blogs_dir
                                })
                            else:
                                socketio.emit('progress', {'message': '⚠️ No blog topics found from tweets'})
                                socketio.emit('workflow_complete', {
                                    'message': 'Generated 0 AI-powered blogs from your tweets',
                                    'blogs_folder': blogs_dir
                                })
                        else:
                            socketio.emit('progress', {'message': '❌ No tweet files found for analysis'})
                            socketio.emit('workflow_complete', {
                                'message': 'No tweet files found for blog generation',
                                'blogs_folder': None
                            })
                    else:
                        socketio.emit('workflow_complete', {
                            'message': f'Twitter scraping complete! Found {tweet_count} tweets.',
                            'blogs_folder': None
                        })
                else:
                    progress_callback("❌ No tweets found or scraping failed")
                    socketio.emit('workflow_complete', {
                        'message': result.get('message', 'Scraping failed'),
                        'blogs_folder': None
                    })
            
            except Exception as e:
                progress_callback(f"❌ Error: {str(e)}")
                socketio.emit('workflow_complete', {
                    'message': f'Error: {str(e)}',
                    'blogs_folder': None
                })
            finally:
                scraping_in_progress = False
        
        # Start the process in a background thread
        import threading
        thread = threading.Thread(target=scrape_and_generate)
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Scraping started successfully'})
    
    except Exception as e:
        scraping_in_progress = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-blogs')
def list_blogs():
    """List all generated blog files from the blogs directory"""
    try:
        blog_files = []
        blogs_dir = 'generated_blogs'
        
        # Check both main directory and blogs directory
        directories_to_check = ['.', blogs_dir] if os.path.exists(blogs_dir) else ['.']
        
        for directory in directories_to_check:
            for file in os.listdir(directory):
                if file.startswith('blog_') and (file.endswith('.html') or file.endswith('.txt')):
                    file_path = os.path.join(directory, file)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    title = file.replace('blog_', '').replace('.html', '').replace('.txt', '').replace('_', ' ').title()
                    
                    blog_files.append({
                        'filename': file,
                        'filepath': file_path,
                        'title': title,
                        'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'HTML' if file.endswith('.html') else 'TXT',
                        'location': 'Blogs Folder' if directory == blogs_dir else 'Main Directory'
                    })
        
        blog_files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'success': True, 'blogs': blog_files})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error listing blogs: {e}'}), 500

@app.route('/api/get-blog-content/<filename>')
def get_blog_content(filename):
    """Get content of a specific blog file"""
    try:
        if not filename.startswith('blog_') or not (filename.endswith('.html') or filename.endswith('.txt')):
            return jsonify({'success': False, 'error': 'Invalid filename'}), 404
        
        file_path = os.path.join('.', filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up content for display
        if filename.endswith('.html'):
            from html import unescape
            import re
            # Remove HTML tags and decode entities
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = unescape(text_content)
            # Clean up extra whitespace
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content.strip())
        else:
            text_content = content
        
        title = filename.replace('blog_', '').replace('.html', '').replace('.txt', '').replace('_', ' ').title()
        
        return jsonify({
            'success': True,
            'title': title,
            'content': text_content,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'scraping_in_progress': scraping_in_progress,
        'blog_generation_in_progress': blog_generation_in_progress,
        'blog_system_ready': blog_system is not None,
        'openai_configured': blog_system.openai_api_key is not None if blog_system else False,
        'hubspot_configured': blog_system.hubspot_api_key is not None if blog_system else False
    })

if __name__ == '__main__':
    print("🚀 Starting Unified Twitter Scraper & Blog Generator")
    print("📊 Dashboard: http://localhost:3000")
    print("✨ Features: Twitter Scraping + AI Blog Generation in one interface!")
    socketio.run(app, debug=True, port=3000, load_dotenv=False) 