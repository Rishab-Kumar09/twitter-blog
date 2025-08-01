import os
import re
import asyncio
import time
from datetime import datetime
from dateutil import parser as date_parser
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from playwright.async_api import async_playwright

app = Flask(__name__)
app.config['SECRET_KEY'] = 'twitter_scraper_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

def emit_progress(message, data=None):
    """Emit progress updates to the frontend"""
    socketio.emit('progress_update', {
        'message': message,
        'data': data,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
    print(message)  # Also print to console

def save_tweets_to_files(username, tweets, keywords=None, start_date=None):
    # Create 'tweets' directory if it doesn't exist
    os.makedirs('tweets', exist_ok=True)
    
    # Create filename with timestamp, keywords, and date
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    keyword_suffix = f"_keywords_{'-'.join(keywords)}" if keywords else ""
    date_suffix = f"_from_{start_date.strftime('%Y%m%d')}" if start_date else ""
    txt_filename = f'tweets/{username}{keyword_suffix}{date_suffix}_{timestamp}.txt'
    excel_filename = f'tweets/{username}{keyword_suffix}{date_suffix}_{timestamp}.xlsx'
    
    emit_progress("💾 Saving tweets to files...")
    
    # Save as text file
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Tweets from @{username}\n")
        if keywords:
            f.write(f"Filtered by keywords: {', '.join(keywords)}\n")
        if start_date:
            f.write(f"From date: {start_date.strftime('%Y-%m-%d')}\n")
        f.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total tweets found: {len(tweets)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet #{i}:\n")
            f.write(f"Date: {tweet.get('date', 'N/A')}\n")
            f.write(f"Text: {tweet.get('text', 'N/A')}\n")
            f.write(f"Likes: {tweet.get('likes', '0')}\n")
            f.write(f"Retweets: {tweet.get('retweets', '0')}\n")
            f.write(f"URL: {tweet.get('url', 'N/A')}\n")
            if keywords:
                matched_keywords = [kw for kw in keywords if kw.lower() in tweet.get('text', '').lower()]
                f.write(f"Matched Keywords: {', '.join(matched_keywords)}\n")
            f.write("-" * 80 + "\n\n")
    
    # Save as Excel file
    try:
        emit_progress("📊 Creating Excel file...")
        
        # Prepare data for DataFrame
        excel_data = []
        for i, tweet in enumerate(tweets, 1):
            matched_keywords = []
            if keywords:
                matched_keywords = [kw for kw in keywords if kw.lower() in tweet.get('text', '').lower()]
            
            excel_data.append({
                'Tweet #': i,
                'Username': f"@{username}",
                'Date': tweet.get('date', 'N/A'),
                'Tweet Text': tweet.get('text', 'N/A'),
                'Likes': tweet.get('likes', '0'),
                'Retweets': tweet.get('retweets', '0'),
                'Tweet URL': tweet.get('url', 'N/A'),
                'Matched Keywords': ', '.join(matched_keywords) if matched_keywords else 'N/A',
                'Filter Keywords': ', '.join(keywords) if keywords else 'None',
                'Start Date Filter': start_date.strftime('%Y-%m-%d') if start_date else 'None',
                'Scraped At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(excel_data)
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            sheet_name = f'{username}_tweets'
            if keywords or start_date:
                sheet_name = f'{username}_filtered'
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                # Set column width (with some padding)
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Make headers bold
            from openpyxl.styles import Font
            for cell in worksheet[1]:
                cell.font = Font(bold=True)
        
        emit_progress("✅ Files saved successfully!")
        return txt_filename, excel_filename
        
    except Exception as e:
        emit_progress(f"⚠️ Error creating Excel file: {e}")
        return txt_filename, None

def filter_tweets_by_keywords(tweets, keywords):
    """Filter tweets that contain any of the specified keywords (case-insensitive)"""
    if not keywords:
        return tweets
    
    filtered_tweets = []
    keywords_lower = [kw.lower().strip() for kw in keywords]
    
    emit_progress(f"🔍 Filtering {len(tweets)} tweets for keywords: {', '.join(keywords_lower)}")
    
    for tweet in tweets:
        tweet_text = tweet.get('text', '').lower()
        matches = [kw for kw in keywords_lower if kw in tweet_text]
        if matches:
            filtered_tweets.append(tweet)
    
    emit_progress(f"🎯 Keyword filtering result: {len(filtered_tweets)} tweets matched")
    return filtered_tweets

def filter_tweets_by_date(tweets, start_date):
    """Filter tweets that are from the start_date or later"""
    if not start_date:
        return tweets
    
    filtered_tweets = []
    emit_progress(f"📅 Filtering {len(tweets)} tweets from date: {start_date.strftime('%Y-%m-%d')}")
    
    for tweet in tweets:
        tweet_date_str = tweet.get('date', '')
        if tweet_date_str and tweet_date_str != 'N/A':
            try:
                # Parse the tweet date (ISO format from Twitter)
                tweet_date = date_parser.parse(tweet_date_str)
                # Make start_date timezone-aware if tweet_date is timezone-aware
                if tweet_date.tzinfo and not start_date.tzinfo:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                elif not tweet_date.tzinfo and start_date.tzinfo:
                    tweet_date = tweet_date.replace(tzinfo=timezone.utc)
                
                if tweet_date.date() >= start_date.date():
                    filtered_tweets.append(tweet)
            except Exception as e:
                # If we can't parse the date, include the tweet to be safe
                filtered_tweets.append(tweet)
        else:
            # If no date available, include the tweet
            filtered_tweets.append(tweet)
    
    emit_progress(f"📅 Date filtering result: {len(filtered_tweets)} tweets matched")
    return filtered_tweets

async def scrape_twitter_with_playwright(username, keywords=None, start_date=None):
    """Multi-session scraper with persistent login - login once, use forever!"""
    import tempfile
    import shutil
    import json
    import os
    
    # Create a persistent user data directory for login sessions
    persistent_profile = os.path.join(os.getcwd(), "twitter_login_profile")
    
    all_tweets = []
    seen_urls = set()
    session_count = 0
    max_sessions = float('inf')  # No session limit - continue until start date reached
    tweets_per_session = float('inf')  # No limit - exhaust each session completely
    
    # Parse start date for comparison
    start_date_obj = None
    if start_date:
        try:
            from datetime import datetime
            # Handle both string and datetime object inputs
            if isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                # Already a datetime object
                start_date_obj = start_date
            
            emit_progress(f"📅 Will scrape tweets until: {start_date_obj.strftime('%Y-%m-%d')}")
            emit_progress(f"🔍 Debug: Parsed start date object: {start_date_obj.date()}")
            emit_progress(f"🔍 Debug: Looking for tweets older than {start_date_obj.date()}")
        except Exception as e:
            emit_progress(f"⚠️ Invalid date format ({e}), scraping all available tweets")
    
    emit_progress(f"🎯 Multi-session scraping with PERSISTENT LOGIN!")
    emit_progress(f"💡 You only need to log in ONCE - future sessions will reuse your login!")
    emit_progress(f"📊 Target: Collect all tweets until {start_date_obj.strftime('%Y-%m-%d %H:%M:%S') if start_date_obj else 'profile limit'}")
    emit_progress(f"🏆 GOAL: Scrape until start date reached or profile exhausted!")
    
    # Check if we have a saved login
    if os.path.exists(persistent_profile):
        emit_progress(f"🔓 Found saved login profile - no login required!")
    else:
        emit_progress(f"🆕 First time setup - you'll need to log in once")
        emit_progress(f"💾 Your login will be saved for future use!")
    
    # Continue scraping until we reach the start date or run out of tweets
    reached_start_date = False
    while not reached_start_date:
        session_count += 1
        session_tweets = []
        
        emit_progress(f"🆕 Starting session #{session_count} with persistent login profile...")
        
        async with async_playwright() as p:
            try:
                # Use persistent context that saves login data
                context = await p.chromium.launch_persistent_context(
                    persistent_profile,  # Persistent user data directory
                    headless=False,
                    args=[
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-extensions',
                        '--disable-default-apps',
                        '--disable-sync',
                        '--disable-background-networking',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-features=TranslateUI',
                        '--disable-ipc-flooding-protection',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                page = await context.new_page()
                emit_progress(f"✨ Session #{session_count}: Using persistent browser profile")
                
                # Check if we're already logged in
                await page.goto('https://twitter.com/home')
                await page.wait_for_timeout(3000)
                
                current_url = page.url
                if 'login' in current_url or 'oauth' in current_url:
                    emit_progress(f"🔑 Session #{session_count}: Please log in to Twitter (this will be saved)...")
                    emit_progress(f"💡 After logging in, all future sessions will be automatic!")
                    
                    # Wait for login completion
                    login_timeout = 300  # 5 minutes for login
                    login_wait = 0
                    
                    while login_wait < login_timeout:
                        await page.wait_for_timeout(5000)
                        login_wait += 5
                        current_url = page.url
                        
                        if 'login' not in current_url and 'oauth' not in current_url:
                            emit_progress(f"✅ Session #{session_count}: Login successful and SAVED!")
                            break
                        
                        if login_wait % 30 == 0:  # Every 30 seconds
                            emit_progress(f"⏳ Session #{session_count}: Still waiting for login... ({login_wait}s/{login_timeout}s)")
                    
                    if login_wait >= login_timeout:
                        emit_progress(f"⏰ Session #{session_count}: Login timeout - skipping this session")
                        await context.close()
                        continue
                else:
                    emit_progress(f"🎉 Session #{session_count}: Already logged in - using saved session!")
                
                # Navigate to the user's profile
                profile_url = f'https://twitter.com/{username}'
                
                # Try different profile sections for variety and more comprehensive coverage
                profile_sections = [
                    ('', 'main timeline'),
                    ('/with_replies', 'tweets & replies'), 
                    ('/media', 'media tweets'),
                    ('/likes', 'liked tweets'),  # Sometimes accessible
                ]
                
                # For sessions beyond basic sections, try search-based approach
                if session_count > len(profile_sections):
                    # Use Twitter search to find more tweets from this user
                    search_query = f'from:{username}'
                    
                    # Add date ranges for deeper historical search
                    if session_count > len(profile_sections) + 5:
                        # Try different date ranges for historical tweets
                        import datetime
                        current_year = datetime.datetime.now().year
                        years_back = (session_count - len(profile_sections) - 1) // 2
                        target_year = current_year - years_back
                        
                        search_query += f' since:{target_year}-01-01 until:{target_year}-12-31'
                        section_name = f'search results for @{username} ({target_year})'
                    else:
                        section_name = f'search results for @{username}'
                    
                    profile_url = f'https://twitter.com/search?q={search_query}&src=typed_query&f=live'
                else:
                    # Use different sections for different sessions
                    section_index = (session_count - 1) % len(profile_sections)
                    section_path, section_name = profile_sections[section_index]
                    profile_url += section_path
                
                emit_progress(f"🌐 Session #{session_count}: Navigating to @{username} ({section_name})")
                await page.goto(profile_url)
                await page.wait_for_timeout(5000)
                
                # Check if profile loaded successfully
                if username.lower() not in page.url.lower():
                    emit_progress(f"❌ Session #{session_count}: Failed to load profile")
                    await context.close()
                    continue
                
                emit_progress(f"✅ Session #{session_count}: Profile loaded successfully")
                emit_progress(f"🔄 Session #{session_count}: Starting to collect tweets...")
                
                # Collect tweets for this session - be more aggressive per session
                no_new_tweets_count = 0
                scroll_count = 0
                max_scrolls_per_session = 100  # Increased from 50 to 100 - exhaust each session more
                
                # Progressive empty scroll limit - be very patient within each session
                base_empty_limit = 50  # Increased from 20 to 50
                progressive_empty_limit = base_empty_limit + (100 * (session_count - 1))  # Much more patient
                emit_progress(f"📊 Session #{session_count}: Empty scroll limit = {progressive_empty_limit} (base: {base_empty_limit} + {100 * (session_count - 1)} for depth)")
                emit_progress(f"🎯 Session #{session_count}: Will try up to {max_scrolls_per_session} scrolls to exhaust this session")
                
                while scroll_count < max_scrolls_per_session and no_new_tweets_count < progressive_empty_limit and not reached_start_date:
                    scroll_count += 1
                    tweets_before = len(session_tweets)
                    
                    # Get all tweet elements
                    tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
                    
                    for tweet_element in tweet_elements:
                        try:
                            # Extract tweet URL for duplicate checking
                            link_element = await tweet_element.query_selector('a[href*="/status/"]')
                            if not link_element:
                                continue
                            
                            tweet_url = f"https://twitter.com{await link_element.get_attribute('href')}"
                            
                            # Check for duplicates across ALL sessions
                            if tweet_url in seen_urls:
                                continue
                            
                            seen_urls.add(tweet_url)
                            
                            # Extract tweet data
                            text_element = await tweet_element.query_selector('[data-testid="tweetText"]')
                            tweet_text = await text_element.inner_text() if text_element else "No text content"
                            
                            # Extract date
                            time_element = await tweet_element.query_selector('time')
                            tweet_date = await time_element.get_attribute('datetime') if time_element else None
                            
                            # Check if we've reached the start date
                            if start_date_obj:
                                if tweet_date:
                                    try:
                                        from datetime import datetime
                                        import dateutil.parser
                                        
                                        # Parse Twitter's datetime format (handles various formats)
                                        tweet_date_obj = dateutil.parser.parse(tweet_date)
                                        
                                        # Debug: Show tweet dates every 10 tweets for better monitoring
                                        if len(session_tweets) % 10 == 0:
                                            emit_progress(f"🔍 Tweet #{len(session_tweets)}: {tweet_date_obj.date()} vs target {start_date_obj.date()}")
                                        
                                        # Stop if tweet is older than (before) the start date
                                        if tweet_date_obj.date() < start_date_obj.date():
                                            emit_progress(f"📅 STOPPING: Tweet from {tweet_date_obj.date()} is before target {start_date_obj.date()}")
                                            reached_start_date = True
                                            break  # Stop processing more tweets in this batch
                                    except Exception as e:
                                        # Debug: Show parsing errors more frequently
                                        if len(session_tweets) % 10 == 0:
                                            emit_progress(f"⚠️ Date parsing error: '{tweet_date}' -> {e}")
                                        pass  # Continue if date parsing fails
                                else:
                                    # Debug: Show when tweets have no date
                                    if len(session_tweets) % 10 == 0:
                                        emit_progress(f"⚠️ Tweet #{len(session_tweets)} has no date attribute")
                            
                            # Extract engagement metrics
                            like_element = await tweet_element.query_selector('[data-testid="like"] span')
                            likes = await like_element.inner_text() if like_element else "0"
                            
                            retweet_element = await tweet_element.query_selector('[data-testid="retweet"] span')
                            retweets = await retweet_element.inner_text() if retweet_element else "0"
                            
                            tweet_data = {
                                'text': tweet_text,
                                'date': tweet_date,
                                'url': tweet_url,
                                'likes': likes,
                                'retweets': retweets,
                                'session': session_count
                            }
                            
                            session_tweets.append(tweet_data)
                            
                        except Exception as e:
                            continue
                    
                    # Check if we broke out due to reaching start date
                    if reached_start_date:
                        emit_progress(f"🔄 Breaking out of tweet processing - start date reached!")
                        break
                    
                    new_tweets = len(session_tweets) - tweets_before
                    if new_tweets > 0:
                        emit_progress(f"📊 Session #{session_count}: Scroll {scroll_count} - Found {new_tweets} tweets (total: {len(session_tweets)})")
                        no_new_tweets_count = 0
                    else:
                        no_new_tweets_count += 1
                        emit_progress(f"📊 Session #{session_count}: Scroll {scroll_count} - No new tweets ({no_new_tweets_count}/{progressive_empty_limit})")
                        
                        # Show patience message for deeper sessions
                        if session_count > 1 and no_new_tweets_count % 10 == 0:
                            emit_progress(f"�� Session #{session_count}: Being extra patient for deeper tweets... ({no_new_tweets_count}/{progressive_empty_limit})")
                    
                    # Scroll down
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    
                    # Progressive wait time - longer waits for deeper sessions
                    base_wait = 3000
                    progressive_wait = base_wait + (1000 * min(session_count - 1, 5))  # Cap at 8 seconds
                    await page.wait_for_timeout(progressive_wait)
                    
                    # No per-session limit - exhaust each session completely
                    # Continue until we hit the empty scroll limit or max scrolls
                
                emit_progress(f"✅ Session #{session_count} complete: {len(session_tweets)} tweets collected")
                all_tweets.extend(session_tweets)
                emit_progress(f"📈 Total tweets so far: {len(all_tweets)}")
                
                # Check if we reached the start date
                if reached_start_date:
                    emit_progress(f"🏆 SUCCESS: Reached start date {start_date}! Scraping complete.")
                    break
                
                # Milestone celebrations
                if len(all_tweets) >= 500 and len(all_tweets) < 600:
                    emit_progress(f"🎉 Milestone: 500+ tweets collected!")
                elif len(all_tweets) >= 1000 and len(all_tweets) < 1100:
                    emit_progress(f"🚀 Milestone: 1,000+ tweets collected!")
                elif len(all_tweets) >= 1500 and len(all_tweets) < 1600:
                    emit_progress(f"🔥 Milestone: 1,500+ tweets collected!")
                elif len(all_tweets) >= 2000 and len(all_tweets) < 2100:
                    emit_progress(f"🎯 Milestone: 2,000+ tweets collected!")
                
                await context.close()
                
                # Break if we got very few tweets (might indicate end of profile)
                if len(session_tweets) < 5:
                    emit_progress(f"⚠️ Very few tweets in session #{session_count} - trying recovery strategies...")
                    
                    # Don't give up immediately - Twitter might just be slow
                    if session_count <= 10:
                        emit_progress(f"🔄 Early session with few tweets - continuing with next strategy...")
                        continue
                    else:
                        emit_progress(f"🛑 Multiple sessions with few tweets - likely reached profile limits")
                        break
                
                # Wait between sessions to avoid rate limiting
                if session_count < max_sessions:
                    # Progressive wait time + human behavior simulation
                    base_wait = 5 * session_count  # Progressive: 5s, 10s, 15s, 20s...
                    
                    emit_progress(f"🤖 Simulating human behavior between sessions...")
                    emit_progress(f"⏱️ Taking a {base_wait}s break + browsing other sites...")
                    
                    # Human behavior simulation - browse other websites
                    await simulate_human_browsing(p, session_count)
                    
                    # Additional wait time
                    await asyncio.sleep(base_wait)
                
            except Exception as e:
                emit_progress(f"❌ Session #{session_count} error: {e}")
                try:
                    await context.close()
                except:
                    pass
                continue
    
    emit_progress(f"🎯 Multi-session scraping complete!")
    emit_progress(f"📊 Total sessions: {session_count}")
    emit_progress(f"📈 Total unique tweets collected: {len(all_tweets)}")
    emit_progress(f"💾 Login profile saved for future use!")
    
    # Provide insights about the scraping results
    if reached_start_date:
        emit_progress(f"🏆 SUCCESS: Reached start date {start_date}! All tweets until that date collected.")
    elif start_date:
        emit_progress(f"")
        emit_progress(f"🔍 ANALYSIS: Collected {len(all_tweets)} tweets but didn't reach start date {start_date}:")
        emit_progress(f"   • Twitter limits timeline access to ~3,200 recent tweets per profile")
        emit_progress(f"   • Rate limiting kicks in after intensive scrolling")
        emit_progress(f"   • Profile may not have tweets going back to {start_date}")
        emit_progress(f"")
        emit_progress(f"💡 TO GET MORE HISTORICAL TWEETS, try these strategies:")
        emit_progress(f"   • Run scraper multiple times with breaks (Twitter resets limits)")
        emit_progress(f"   • Try different keywords/hashtags this user commonly uses")
        emit_progress(f"   • Use Twitter's advanced search with specific date ranges")
        emit_progress(f"   • Check if user has more content in replies/media sections")
    else:
        emit_progress(f"🏆 SUCCESS: Collected all available tweets from profile!")
    
    return all_tweets

async def simulate_human_browsing(playwright_instance, session_count):
    """Simulate human browsing behavior to avoid detection"""
    
    # List of popular websites to visit
    browsing_sites = [
        ('https://www.youtube.com', 'YouTube', 8),
        ('https://www.google.com', 'Google', 5),
        ('https://www.reddit.com', 'Reddit', 7),
        ('https://news.ycombinator.com', 'Hacker News', 6),
        ('https://www.github.com', 'GitHub', 5),
        ('https://www.stackoverflow.com', 'Stack Overflow', 6),
        ('https://www.wikipedia.org', 'Wikipedia', 7),
        ('https://www.medium.com', 'Medium', 6),
    ]
    
    # Select 2-3 sites to visit based on session count
    sites_to_visit = browsing_sites[(session_count - 1) % len(browsing_sites):(session_count - 1) % len(browsing_sites) + 2]
    
    try:
        # Create a temporary browser for human simulation
        browser = await playwright_instance.chromium.launch(headless=True)  # Hidden for speed
        context = await browser.new_context()
        page = await context.new_page()
        
        for site_url, site_name, browse_time in sites_to_visit:
            try:
                emit_progress(f"🌐 Browsing {site_name} for {browse_time}s (human simulation)...")
                await page.goto(site_url, timeout=10000)
                await page.wait_for_timeout(1000)  # Wait for page load
                
                # Simulate human scrolling
                for _ in range(3):
                    await page.evaluate('window.scrollBy(0, Math.random() * 500 + 200)')
                    await page.wait_for_timeout(browse_time * 1000 // 3)  # Divide time across scrolls
                
                emit_progress(f"✅ Finished browsing {site_name}")
                
            except Exception as e:
                emit_progress(f"⚠️ Error browsing {site_name}: {str(e)[:50]}... (continuing)")
                continue
        
        await browser.close()
        emit_progress(f"🎭 Human simulation complete - ready for next Twitter session!")
        
    except Exception as e:
        emit_progress(f"⚠️ Human simulation error: {str(e)[:50]}... (continuing anyway)")
        try:
            await browser.close()
        except:
            pass

async def scrape_twitter(username, keywords=None, start_date=None):
    try:
        emit_progress(f"🚀 Starting multi-session scrape for @{username}")
        if keywords:
            emit_progress(f"🔍 Keywords: {keywords}")
        if start_date:
            emit_progress(f"📅 Start date: {start_date.strftime('%Y-%m-%d')}")
            
        tweets = await scrape_twitter_with_playwright(username, keywords, start_date)
        
        if not tweets:
            message_parts = []
            if keywords:
                message_parts.append(f"containing keywords: {', '.join(keywords)}")
            if start_date:
                message_parts.append(f"from {start_date.strftime('%Y-%m-%d')}")
            
            if message_parts:
                return False, f"No tweets found {' and '.join(message_parts)}"
            else:
                return False, "No tweets were found. The profile might be private or doesn't exist."
        
        # Apply filters to the collected tweets
        original_count = len(tweets)
        emit_progress(f"🎯 Applying filters to {original_count} collected tweets...")
        
        # Filter tweets by date first (more efficient)
        if start_date:
            tweets = filter_tweets_by_date(tweets, start_date)
        
        # Then filter by keywords
        if keywords:
            tweets = filter_tweets_by_keywords(tweets, keywords)
        
        emit_progress(f"🎯 Final result: {len(tweets)} tweets after filtering (started with {original_count})")
        
        # Save tweets to both text and Excel files
        txt_file, excel_file = save_tweets_to_files(username, tweets, keywords, start_date)
        
        # Build success message
        message_parts = []
        if keywords:
            message_parts.append(f"containing keywords: {', '.join(keywords)}")
        if start_date:
            message_parts.append(f"from {start_date.strftime('%Y-%m-%d')}")
        
        filter_info = f" {' and '.join(message_parts)}" if message_parts else ""
        
        if excel_file:
            return True, f"Successfully scraped {len(tweets)} tweets from @{username}{filter_info}. Saved to {txt_file} and {excel_file}"
        else:
            return True, f"Successfully scraped {len(tweets)} tweets from @{username}{filter_info}. Saved to {txt_file} (Excel export failed)"
    except Exception as e:
        emit_progress(f"❌ Error: {str(e)}")
        return False, f"Error scraping Twitter: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
async def scrape():
    data = request.get_json()
    username = data.get('username')
    keywords_input = data.get('keywords', '').strip()
    start_date_input = data.get('startDate', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'})
    
    # Process keywords
    keywords = None
    if keywords_input:
        keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    
    # Process start date
    start_date = None
    if start_date_input:
        try:
            start_date = datetime.strptime(start_date_input, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Please use YYYY-MM-DD'})
    
    try:
        emit_progress(f"🚀 Starting scrape for @{username}")
        if keywords:
            emit_progress(f"🔍 Keywords: {keywords}")
        if start_date:
            emit_progress(f"📅 Start date: {start_date.strftime('%Y-%m-%d')}")
            
        tweets = await scrape_twitter_with_playwright(username, keywords, start_date)
        
        if not tweets:
            message_parts = []
            if keywords:
                message_parts.append(f"containing keywords: {', '.join(keywords)}")
            if start_date:
                message_parts.append(f"from {start_date.strftime('%Y-%m-%d')}")
            
            if message_parts:
                return jsonify({'status': 'error', 'message': f"No tweets found {' and '.join(message_parts)}"})
            else:
                return jsonify({'status': 'error', 'message': "No tweets were found. The profile might be private or doesn't exist."})
        
        # Save tweets to both text and Excel files
        txt_file, excel_file = save_tweets_to_files(username, tweets, keywords, start_date)
        
        # Build success message
        message_parts = []
        if keywords:
            message_parts.append(f"containing keywords: {', '.join(keywords)}")
        if start_date:
            message_parts.append(f"from {start_date.strftime('%Y-%m-%d')}")
        
        filter_info = f" {' and '.join(message_parts)}" if message_parts else ""
        
        if excel_file:
            return jsonify({'status': 'success', 'message': f"Successfully scraped {len(tweets)} tweets from @{username}{filter_info}. Saved to {txt_file} and {excel_file}"})
        else:
            return jsonify({'status': 'success', 'message': f"Successfully scraped {len(tweets)} tweets from @{username}{filter_info}. Saved to {txt_file} (Excel export failed)"})
    except Exception as e:
        emit_progress(f"❌ Error during scraping: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

def scrape_twitter_profile(username, keywords, start_date, progress_callback=None):
    """
    Export function for unified app to use Twitter scraping functionality
    """
    global emit_progress
    
    # Override emit_progress if callback provided
    if progress_callback:
        original_emit = emit_progress
        emit_progress = progress_callback
    
    try:
        # Parse inputs
        keywords_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else None
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            except:
                pass
        
        # Run the scraping
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tweets = loop.run_until_complete(scrape_twitter_with_playwright(username, keywords_list, start_date_obj))
        loop.close()
        
        if not tweets:
            return {'success': False, 'message': 'No tweets found', 'tweet_count': 0}
        
        # Save tweets
        txt_file, excel_file = save_tweets_to_files(username, tweets, keywords_list, start_date_obj)
        
        return {
            'success': True, 
            'message': f'Successfully scraped {len(tweets)} tweets',
            'tweet_count': len(tweets),
            'txt_file': txt_file,
            'excel_file': excel_file
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e), 'tweet_count': 0}
    finally:
        # Restore original emit_progress
        if progress_callback:
            emit_progress = original_emit

if __name__ == '__main__':
    socketio.run(app, debug=True, port=3000, load_dotenv=False) 