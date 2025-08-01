#!/usr/bin/env python3
"""
Gauntlet AI Blog Management Web Interface
========================================

Web interface for managing the automated blog generation system:
- Configure API keys (OpenAI, HubSpot)
- Run theme analysis
- Generate and preview blogs
- Publish to HubSpot
- Monitor blog performance
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import os
import json
from datetime import datetime
from gauntlet_blog_system import GauntletBlogSystem
import pandas as pd

# Skip dotenv loading due to UTF-16 encoding issues - we'll handle .env manually

app = Flask(__name__)
app.secret_key = 'gauntlet_ai_blog_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global blog system instance
blog_system = None

def generate_blog_with_updates(topic):
    """Generate blog with real-time WebSocket updates - saves as text files"""
    try:
        socketio.emit('blog_generation_update', {
            'message': f'🤖 Initializing OpenAI GPT-4...'
        })
        
        if not blog_system.openai_api_key:
            socketio.emit('blog_generation_update', {
                'message': f'⚠️ No OpenAI API key - using template generation'
            })
            return blog_system._generate_blog_template(topic)
        
        socketio.emit('blog_generation_update', {
            'message': f'📝 Preparing prompt for GPT-4...'
        })
        
        # Generate the blog post with custom logging
        import re
        from openai import OpenAI
        from datetime import datetime
        
        # Simple text-based blog generation prompt (no JSON to avoid parsing issues)
        prompt = f"""
        Write a comprehensive blog post for Gauntlet AI targeting AI engineers and technical decision makers.

        Topic: {topic.canonical_question}
        Keywords to include naturally: {', '.join(topic.keywords)}
        
        Requirements:
        - 800-1200 words
        - SEO optimized with natural keyword usage
        - GEO optimized (answer-focused for AI search engines)
        - Professional but engaging tone
        - Include specific examples and actionable insights
        - Structure: Hook, Problem, Solution, Benefits, Call-to-Action
        - Use HTML formatting: <h2>, <h3>, <p>, <ul>, <li> tags
        
        Format your response EXACTLY like this:

        TITLE: [Write an SEO-optimized title here (60 characters max)]

        META_DESCRIPTION: [Write a compelling meta description here (150-160 characters)]

        CONTENT:
        [Write the full blog post content here using proper HTML formatting with headings, paragraphs, and lists]

        Now write the blog post:
        """
        
        socketio.emit('blog_generation_update', {
            'message': f'🚀 Sending request to GPT-4... (this may take 30-90 seconds)'
        })
        
        client = OpenAI(api_key=blog_system.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2500
        )
        
        socketio.emit('blog_generation_update', {
            'message': f'✅ GPT-4 response received ({len(response.choices[0].message.content)} characters)'
        })
        
        # Parse the text response (no JSON parsing!)
        raw_content = response.choices[0].message.content
        socketio.emit('blog_generation_update', {
            'message': f'📝 Extracting title, meta description, and content...'
        })
        
        # Extract title, meta description, and content using regex
        title_match = re.search(r'TITLE:\s*(.+?)(?:\n\n|\nMETA_DESCRIPTION)', raw_content, re.IGNORECASE | re.DOTALL)
        meta_match = re.search(r'META_DESCRIPTION:\s*(.+?)(?:\n\n|\nCONTENT)', raw_content, re.IGNORECASE | re.DOTALL)
        content_match = re.search(r'CONTENT:\s*(.+)', raw_content, re.IGNORECASE | re.DOTALL)
        
        title = title_match.group(1).strip() if title_match else f"AI Strategy: {topic.canonical_question}"
        meta_description = meta_match.group(1).strip() if meta_match else f"Expert insights on {topic.canonical_question} for AI engineers and decision makers."
        content = content_match.group(1).strip() if content_match else raw_content
        
        socketio.emit('blog_generation_update', {
            'message': f'✅ Blog parsed successfully: "{title[:50]}..."'
        })
        
        # Save as text file immediately (PRD requirement: local storage first)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_').replace('-', '_')[:50]
        filename = f"blog_{timestamp}_{safe_title}.txt"
        
        blog_content = f"""=== GAUNTLET AI BLOG POST ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Topic: {topic.canonical_question}
Keywords: {', '.join(topic.keywords)}

TITLE:
{title}

META_DESCRIPTION:
{meta_description}

CONTENT:
{content}

=== METADATA ===
Author: Austin (Gauntlet AI)
Category: AI Strategy
Tags: {', '.join(topic.keywords)}
Status: Ready for HubSpot publishing

=== END ===
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(blog_content)
        
        socketio.emit('blog_generation_update', {
            'message': f'💾 Blog saved as text file: {filename}'
        })
        
        socketio.emit('blog_generation_update', {
            'message': f'📊 Word count: ~{len(content.split())} words'
        })
        
        # Create blog post object for consistency with existing code
        from gauntlet_blog_system import BlogPost
        blog_post = BlogPost(
            title=title,
            content=content,
            meta_description=meta_description,
            keywords=topic.keywords,
            schema_markup="",  # Will add when posting to HubSpot
            hubspot_properties={"blog_author": "Austin", "content_type": "AI Strategy", "category": "AI Automation"}
        )
        
        return blog_post
        
    except Exception as e:
        socketio.emit('blog_generation_error', {
            'message': f'Blog generation failed: {str(e)}'
        })
        socketio.emit('blog_generation_update', {
            'message': f'🔧 Falling back to template generation...'
        })
        return blog_system._generate_blog_template(topic)

# Try to initialize with environment variables
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
        print(f"💡 You can configure API keys through the web interface")
        blog_system = None
except Exception as e:
    print(f"⚠️ Could not load API keys: {e}")
    blog_system = None

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('blog_dashboard.html')

@app.route('/api/configure', methods=['POST'])
def configure_api_keys():
    """Configure API keys"""
    global blog_system
    
    data = request.json
    openai_key = data.get('openai_api_key', '').strip()
    hubspot_key = data.get('hubspot_api_key', '').strip()
    
    # Initialize blog system with new keys
    blog_system = GauntletBlogSystem(
        openai_api_key=openai_key if openai_key else None,
        hubspot_api_key=hubspot_key if hubspot_key else None
    )
    
    # Save to environment (for session)
    if openai_key:
        os.environ['OPENAI_API_KEY'] = openai_key
    if hubspot_key:
        os.environ['HUBSPOT_API_KEY'] = hubspot_key
    
    return jsonify({
        'success': True,
        'message': 'API keys configured successfully',
        'openai_configured': bool(openai_key),
        'hubspot_configured': bool(hubspot_key)
    })

@app.route('/api/analyze-themes', methods=['POST'])
def analyze_themes():
    """Analyze tweets for themes"""
    global blog_system
    
    if not blog_system:
        return jsonify({'error': 'Please configure API keys first'}), 400
    
    try:
        # Find latest tweet file
        tweet_files = [f for f in os.listdir('tweets') if f.endswith('.xlsx')]
        if not tweet_files:
            return jsonify({'error': 'No tweet files found'}), 400
        
        latest_tweet_file = "tweets/Austen_20250728_162654.xlsx"
        
        # Analyze themes
        socketio.emit('analysis_update', {'message': '🔍 Analyzing Austin\'s tweets for Gauntlet AI themes...'})
        blog_topics = blog_system.analyze_tweets_for_themes(latest_tweet_file)
        
        # Generate CSV
        csv_path = blog_system.generate_topic_csv(blog_topics)
        
        # Convert topics to JSON for frontend
        topics_data = []
        for topic in blog_topics:
            topics_data.append({
                'topic_id': topic.topic_id,
                'question': topic.canonical_question,
                'keywords': topic.keywords,
                'priority': topic.priority,
                'volume_score': topic.volume_score,
                'tweet_count': len(topic.tweet_refs)
            })
        
        socketio.emit('analysis_complete', {
            'topics': topics_data,
            'csv_path': csv_path
        })
        
        return jsonify({
            'success': True,
            'topics': topics_data,
            'csv_path': csv_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-blog', methods=['POST'])
def generate_blog():
    """Generate a single blog post"""
    global blog_system
    
    if not blog_system:
        return jsonify({'error': 'Please configure API keys first'}), 400
    
    data = request.json
    topic_data = data.get('topic')
    
    if not topic_data:
        return jsonify({'error': 'No topic provided'}), 400
    
    try:
        # Create BlogTopic object
        from gauntlet_blog_system import BlogTopic
        topic = BlogTopic(
            topic_id=topic_data['topic_id'],
            canonical_question=topic_data['question'],
            tweet_refs=[],  # Not needed for generation
            volume_score=topic_data['volume_score'],
            keywords=topic_data['keywords'],
            priority=topic_data['priority']
        )
        
        socketio.emit('blog_generation_update', {
            'message': f'✍️ Starting blog generation: {topic.canonical_question}'
        })
        
        # Generate blog post with real-time updates
        blog_post = generate_blog_with_updates(topic)
        
        if blog_post:
            socketio.emit('blog_generation_update', {
                'message': f'💾 Saving blog locally...'
            })
            
            # Save locally
            blog_system._save_blog_locally(blog_post)
            
            socketio.emit('blog_generation_complete', {
                'title': blog_post.title,
                'content': blog_post.content,
                'meta_description': blog_post.meta_description,
                'keywords': blog_post.keywords
            })
        else:
            socketio.emit('blog_generation_error', {
                'message': 'Blog generation failed completely'
            })
        
        return jsonify({
            'success': True,
            'blog': {
                'title': blog_post.title,
                'content': blog_post.content,
                'meta_description': blog_post.meta_description,
                'keywords': blog_post.keywords,
                'schema_markup': blog_post.schema_markup
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/publish-blog', methods=['POST'])
def publish_blog():
    """Publish blog to HubSpot"""
    global blog_system
    
    if not blog_system:
        return jsonify({'error': 'Please configure API keys first'}), 400
    
    data = request.json
    blog_data = data.get('blog')
    
    if not blog_data:
        return jsonify({'error': 'No blog data provided'}), 400
    
    try:
        # Create BlogPost object
        from gauntlet_blog_system import BlogPost
        blog_post = BlogPost(
            title=blog_data['title'],
            content=blog_data['content'],
            meta_description=blog_data['meta_description'],
            keywords=blog_data['keywords'],
            schema_markup=blog_data.get('schema_markup', ''),
            hubspot_properties={
                'category': 'AI Automation',
                'tags': blog_data['keywords'],
                'author': 'Gauntlet AI Team'
            }
        )
        
        socketio.emit('publish_update', {
            'message': f'🚀 Publishing to HubSpot: {blog_post.title}'
        })
        
        # Publish to HubSpot
        success = blog_system.publish_to_hubspot(blog_post)
        
        if success:
            socketio.emit('publish_complete', {
                'message': '✅ Blog published successfully!',
                'success': True
            })
            return jsonify({'success': True, 'message': 'Blog published successfully!'})
        else:
            return jsonify({'error': 'Failed to publish blog'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-pipeline', methods=['POST'])
def run_complete_pipeline():
    """Run the complete blog generation pipeline"""
    global blog_system
    
    if not blog_system:
        return jsonify({'error': 'Please configure API keys first'}), 400
    
    data = request.json
    num_blogs = data.get('num_blogs', 5)
    
    try:
        socketio.emit('pipeline_start', {
            'message': '🚀 Starting complete Gauntlet AI blog generation pipeline...'
        })
        
        # Find latest tweet file
        latest_tweet_file = "tweets/Austen_20250728_162654.xlsx"
        
        # Run pipeline with real-time updates
        socketio.emit('blog_generation_update', {
            'message': '📊 PHASE 1: Analyzing tweets for themes...'
        })
        
        # Phase 1: Theme & Question Mining
        blog_topics = blog_system.analyze_tweets_for_themes(latest_tweet_file)
        csv_path = blog_system.generate_topic_csv(blog_topics)
        
        socketio.emit('blog_generation_update', {
            'message': f'✅ Found {len(blog_topics)} blog topics'
        })
        
        # Phase 2: Blog Generation with real-time updates
        socketio.emit('blog_generation_update', {
            'message': f'✍️ PHASE 2: Generating {num_blogs} blog posts...'
        })
        
        generated_blogs = []
        for i, topic in enumerate(blog_topics[:num_blogs]):
            socketio.emit('blog_generation_update', {
                'message': f'📝 Generating blog {i+1}/{num_blogs}: {topic.canonical_question}'
            })
            
            blog_post = generate_blog_with_updates(topic)
            if blog_post:
                generated_blogs.append(blog_post)
                blog_system._save_blog_locally(blog_post)
        
        # Phase 3: Publishing (if configured)
        socketio.emit('blog_generation_update', {
            'message': f'🚀 PHASE 3: Publishing {len(generated_blogs)} blogs...'
        })
        
        published_count = 0
        for blog_post in generated_blogs:
            if blog_system.publish_to_hubspot(blog_post):
                published_count += 1
        
        # Generate robots.txt
        blog_system.generate_robots_txt()
        
        results = {
            "topics": blog_topics,
            "blogs": generated_blogs,
            "published": published_count,
            "csv_path": csv_path
        }
        
        socketio.emit('pipeline_complete', {
            'message': f'🎉 Pipeline complete! Generated {len(results["blogs"])} blogs',
            'results': {
                'topics_count': len(results['topics']),
                'blogs_generated': len(results['blogs']),
                'blogs_published': results['published'],
                'csv_path': results['csv_path']
            }
        })
        
        return jsonify({
            'success': True,
            'results': {
                'topics_count': len(results['topics']),
                'blogs_generated': len(results['blogs']),
                'blogs_published': results['published'],
                'csv_path': results['csv_path']
            }
        })
        
    except Exception as e:
        socketio.emit('pipeline_error', {'error': str(e)})
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status"""
    global blog_system
    
    # Check tweet files
    tweet_files = [f for f in os.listdir('tweets') if f.endswith('.xlsx')]
    latest_file = "tweets/Austen_20250728_162654.xlsx" if tweet_files else None
    
    # Check generated files
    blog_files = [f for f in os.listdir('.') if f.startswith('blog_') and f.endswith('.html')]
    csv_exists = os.path.exists('gauntlet_blog_topics.csv')
    robots_exists = os.path.exists('robots.txt')
    
    return jsonify({
        'api_keys_configured': blog_system is not None,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'hubspot_configured': bool(os.getenv('HUBSPOT_API_KEY')),
        'tweet_files_count': len(tweet_files),
        'latest_tweet_file': latest_file,
        'generated_blogs': len(blog_files),
        'topics_csv_exists': csv_exists,
        'robots_txt_exists': robots_exists
    })

@app.route('/api/list-blogs')
def list_blogs():
    """List all generated blog files (both HTML and TXT)"""
    try:
        blog_files = []
        for file in os.listdir('.'):
            if file.startswith('blog_') and (file.endswith('.html') or file.endswith('.txt')):
                # Get file modification time
                file_path = os.path.join('.', file)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Extract title from filename
                if file.endswith('.txt'):
                    title = file.replace('blog_', '').replace('.txt', '').replace('_', ' ').title()
                    file_type = 'Text File (GPT-4)'
                else:
                    title = file.replace('blog_', '').replace('.html', '').replace('_', ' ').title()
                    file_type = 'HTML File'
                
                blog_files.append({
                    'filename': file,
                    'title': title,
                    'type': file_type,
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modification time (newest first)
        blog_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'blogs': blog_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get-blog-content')
def get_blog_content():
    """Get content of a specific blog file (HTML or TXT)"""
    try:
        filename = request.args.get('filename')
        if not filename or not filename.startswith('blog_') or not (filename.endswith('.html') or filename.endswith('.txt')):
            return jsonify({
                'success': False,
                'error': 'Invalid filename - must be blog_*.html or blog_*.txt'
            })
        
        file_path = os.path.join('.', filename)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            })
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if filename.endswith('.txt'):
            # For text files, return as-is (already formatted nicely)
            return jsonify({
                'success': True,
                'content': content,
                'type': 'text'
            })
        else:
            # For HTML files, extract text content
            from html import unescape
            import re
            
            # Remove HTML tags and decode entities
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = unescape(text_content)
            
            # Clean up extra whitespace
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content.strip())
            
            return jsonify({
                'success': True,
                'content': text_content,
                'type': 'html'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🎯 Starting Gauntlet AI Blog Management Interface")
    print("📊 Dashboard: http://localhost:5001")
    socketio.run(app, debug=True, port=5001, load_dotenv=False) 