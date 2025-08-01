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
    
    data = request.json
    username = data.get('username', '').strip()
    keywords = data.get('keywords', '').strip()
    start_date = data.get('startDate', '')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # Start scraping in background thread
    scraping_in_progress = True
    thread = threading.Thread(target=run_twitter_scraping, args=(username, keywords, start_date))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started'}), 200

def run_twitter_scraping(username, keywords, start_date):
    """Run Twitter scraping in background thread"""
    global scraping_in_progress
    
    try:
        # Import and run the existing Twitter scraping logic
        from app import scrape_twitter_profile
        
        # Emit progress updates
        def emit_progress(message):
            socketio.emit('scraping_progress', {'message': message})
        
        # Run the scraping
        result = scrape_twitter_profile(username, keywords, start_date, emit_progress)
        
        if result and result.get('success'):
            # Get the latest tweet file
            tweet_files = [f for f in os.listdir('.') if f.startswith('tweets_') and f.endswith('.xlsx')]
            if tweet_files:
                latest_file = max(tweet_files, key=os.path.getctime)
                
                # Automatically trigger blog generation if keywords were used
                if keywords.strip():
                    socketio.emit('scraping_complete', {
                        'success': True, 
                        'file': latest_file,
                        'auto_blog': True,
                        'message': f'✅ Scraping complete! Found {result.get("tweet_count", 0)} tweets. Starting blog generation...'
                    })
                    
                    # Start blog generation automatically
                    time.sleep(2)  # Brief pause
                    run_blog_generation(latest_file)
                else:
                    socketio.emit('scraping_complete', {
                        'success': True, 
                        'file': latest_file,
                        'auto_blog': False,
                        'message': f'✅ Scraping complete! Found {result.get("tweet_count", 0)} tweets.'
                    })
            else:
                socketio.emit('scraping_complete', {'success': False, 'message': 'No tweet file generated'})
        else:
            socketio.emit('scraping_complete', {'success': False, 'message': 'Scraping failed'})
            
    except Exception as e:
        socketio.emit('scraping_complete', {'success': False, 'message': f'Error: {str(e)}'})
    finally:
        scraping_in_progress = False

def run_blog_generation(tweet_file):
    """Run blog generation in background"""
    global blog_generation_in_progress
    
    if blog_generation_in_progress:
        return
        
    blog_generation_in_progress = True
    
    try:
        if not blog_system:
            socketio.emit('blog_progress', {'message': '⚠️ Blog system not initialized - no OpenAI API key'})
            return
            
        def emit_progress(message):
            socketio.emit('blog_progress', {'message': message})
        
        emit_progress('🚀 Starting automated blog generation...')
        emit_progress('📊 PHASE 1: Analyzing tweets for themes...')
        
        # Phase 1: Theme Analysis
        blog_topics = blog_system.analyze_tweets_for_themes(tweet_file)
        csv_path = blog_system.generate_topic_csv(blog_topics)
        
        emit_progress(f'✅ Found {len(blog_topics)} blog topics')
        emit_progress('✍️ PHASE 2: Generating blog posts with ChatGPT...')
        
        # Phase 2: Generate 3 blogs
        num_blogs = min(3, len(blog_topics))
        generated_blogs = []
        
        for i, topic in enumerate(blog_topics[:num_blogs]):
            emit_progress(f'🤖 Generating blog {i+1}/{num_blogs}: {topic.canonical_question}')
            
            blog_post = generate_blog_with_updates(topic, emit_progress)
            if blog_post:
                generated_blogs.append(blog_post)
                
        emit_progress('🚀 PHASE 3: Saving blogs locally...')
        
        # Save blogs locally
        blog_files = []
        for blog_post in generated_blogs:
            filename = blog_system._save_blog_locally(blog_post)
            if filename:
                blog_files.append(filename)
                emit_progress(f'💾 Saved: {filename}')
        
        # Generate robots.txt
        blog_system.generate_robots_txt()
        emit_progress('🤖 Generated robots.txt for SEO optimization')
        
        # Complete
        socketio.emit('blog_generation_complete', {
            'success': True,
            'blogs_generated': len(generated_blogs),
            'blog_files': blog_files,
            'topics_csv': csv_path,
            'message': f'🎉 Complete! Generated {len(generated_blogs)} blogs from your tweets!'
        })
        
    except Exception as e:
        socketio.emit('blog_generation_complete', {
            'success': False,
            'message': f'❌ Blog generation failed: {str(e)}'
        })
    finally:
        blog_generation_in_progress = False

def generate_blog_with_updates(topic, emit_progress):
    """Generate blog with real-time updates"""
    try:
        emit_progress(f'🤖 Initializing ChatGPT for: {topic.canonical_question}')
        
        if not blog_system.openai_api_key:
            emit_progress(f'⚠️ No OpenAI API key - using template generation')
            return blog_system._generate_blog_template(topic)
        
        emit_progress(f'📝 Sending prompt to GPT-4...')
        
        # Generate blog using existing system
        blog_post = blog_system.generate_blog_post(topic)
        
        if blog_post:
            emit_progress(f'✅ Generated: {blog_post.title}')
            return blog_post
        else:
            emit_progress(f'⚠️ Failed to generate blog for: {topic.canonical_question}')
            return None
            
    except Exception as e:
        emit_progress(f'❌ Error generating blog: {str(e)}')
        return None

@app.route('/api/list-blogs')
def list_blogs():
    """List all generated blog files"""
    try:
        blog_files = []
        for file in os.listdir('.'):
            if file.startswith('blog_') and (file.endswith('.html') or file.endswith('.txt')):
                file_path = os.path.join('.', file)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                title = file.replace('blog_', '').replace('.html', '').replace('.txt', '').replace('_', ' ').title()
                file_type = 'HTML' if file.endswith('.html') else 'TXT'
                
                blog_files.append({
                    'filename': file,
                    'title': title,
                    'type': file_type,
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modification time (newest first)
        blog_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'success': True, 'blogs': blog_files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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