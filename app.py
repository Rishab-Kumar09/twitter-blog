import asyncio
from flask import Flask, render_template, request, jsonify
from playwright.async_api import async_playwright
import os
from datetime import datetime, timezone
import re
import time
import pandas as pd
from dateutil import parser

app = Flask(__name__)

def save_tweets_to_files(username, tweets, keywords=None, start_date=None):
    # Create 'tweets' directory if it doesn't exist
    os.makedirs('tweets', exist_ok=True)
    
    # Create filename with timestamp, keywords, and date
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    keyword_suffix = f"_keywords_{'-'.join(keywords)}" if keywords else ""
    date_suffix = f"_from_{start_date.strftime('%Y%m%d')}" if start_date else ""
    txt_filename = f'tweets/{username}{keyword_suffix}{date_suffix}_{timestamp}.txt'
    excel_filename = f'tweets/{username}{keyword_suffix}{date_suffix}_{timestamp}.xlsx'
    
    # Save as text file
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Tweets from @{username}\n")
        if keywords:
            f.write(f"Filtered by keywords: {', '.join(keywords)}\n")
        if start_date:
            f.write(f"From date: {start_date.strftime('%Y-%m-%d')}\n")
        f.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
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
        
        return txt_filename, excel_filename
        
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return txt_filename, None

def filter_tweets_by_keywords(tweets, keywords):
    """Filter tweets that contain any of the specified keywords (case-insensitive)"""
    if not keywords:
        return tweets
    
    filtered_tweets = []
    keywords_lower = [kw.lower().strip() for kw in keywords]
    
    for tweet in tweets:
        tweet_text = tweet.get('text', '').lower()
        if any(keyword in tweet_text for keyword in keywords_lower):
            filtered_tweets.append(tweet)
    
    return filtered_tweets

def filter_tweets_by_date(tweets, start_date):
    """Filter tweets that are from the start_date or later"""
    if not start_date:
        return tweets
    
    filtered_tweets = []
    
    for tweet in tweets:
        tweet_date_str = tweet.get('date', '')
        if tweet_date_str and tweet_date_str != 'N/A':
            try:
                # Parse the tweet date (ISO format from Twitter)
                tweet_date = parser.parse(tweet_date_str)
                # Make start_date timezone-aware if tweet_date is timezone-aware
                if tweet_date.tzinfo and not start_date.tzinfo:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                elif not tweet_date.tzinfo and start_date.tzinfo:
                    tweet_date = tweet_date.replace(tzinfo=timezone.utc)
                
                if tweet_date.date() >= start_date.date():
                    filtered_tweets.append(tweet)
            except Exception as e:
                print(f"Error parsing date {tweet_date_str}: {e}")
                # If we can't parse the date, include the tweet to be safe
                filtered_tweets.append(tweet)
        else:
            # If no date available, include the tweet
            filtered_tweets.append(tweet)
    
    return filtered_tweets

async def scrape_twitter_with_playwright(username, keywords=None, start_date=None):
    async with async_playwright() as p:
        # Launch browser (visible)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Go to Twitter profile
            await page.goto(f'https://twitter.com/{username}')
            
            # Wait for tweets to load
            await page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            tweets = []
            no_new_tweets_count = 0
            
            # Scroll and collect tweets (more scrolls if filtering)
            scroll_count = 8 if (keywords or start_date) else 3
            for scroll in range(scroll_count):
                tweets_before = len(tweets)
                
                # Get all tweet containers
                tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
                
                for tweet_element in tweet_elements:
                    try:
                        # Extract tweet text
                        text_element = await tweet_element.query_selector('[data-testid="tweetText"]')
                        tweet_text = await text_element.inner_text() if text_element else "No text found"
                        
                        # Extract date/time
                        time_element = await tweet_element.query_selector('time')
                        tweet_date = await time_element.get_attribute('datetime') if time_element else "N/A"
                        
                        # Extract likes
                        like_element = await tweet_element.query_selector('[data-testid="like"]')
                        likes = "0"
                        if like_element:
                            like_text = await like_element.inner_text()
                            likes = re.search(r'\d+', like_text).group() if re.search(r'\d+', like_text) else "0"
                        
                        # Extract retweets
                        retweet_element = await tweet_element.query_selector('[data-testid="retweet"]')
                        retweets = "0"
                        if retweet_element:
                            retweet_text = await retweet_element.inner_text()
                            retweets = re.search(r'\d+', retweet_text).group() if re.search(r'\d+', retweet_text) else "0"
                        
                        # Get tweet URL
                        link_element = await tweet_element.query_selector('a[href*="/status/"]')
                        tweet_url = f"https://twitter.com{await link_element.get_attribute('href')}" if link_element else "N/A"
                        
                        # Only add if we haven't seen this tweet before
                        tweet_data = {
                            'text': tweet_text,
                            'date': tweet_date,
                            'likes': likes,
                            'retweets': retweets,
                            'url': tweet_url
                        }
                        
                        # Check for duplicates
                        if not any(existing['url'] == tweet_data['url'] for existing in tweets):
                            tweets.append(tweet_data)
                            
                    except Exception as e:
                        print(f"Error extracting tweet: {e}")
                        continue
                
                # Check if we got new tweets
                tweets_after = len(tweets)
                if tweets_after == tweets_before:
                    no_new_tweets_count += 1
                    if no_new_tweets_count >= 2:  # Stop if no new tweets for 2 consecutive scrolls
                        print("No new tweets found, stopping...")
                        break
                else:
                    no_new_tweets_count = 0
                
                # Scroll down to load more tweets
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(3000)  # Wait longer for new tweets to load
            
            await browser.close()
            
            # Filter tweets by date first (more efficient)
            if start_date:
                tweets = filter_tweets_by_date(tweets, start_date)
            
            # Then filter by keywords
            if keywords:
                tweets = filter_tweets_by_keywords(tweets, keywords)
            
            return tweets
            
        except Exception as e:
            await browser.close()
            raise e

async def scrape_twitter(username, keywords=None, start_date=None):
    try:
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
        return False, f"Error scraping Twitter: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
async def scrape():
    data = request.get_json()
    username = data.get('username')
    keywords_input = data.get('keywords', '').strip()
    start_date_input = data.get('start_date', '').strip()
    
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
    
    success, message = await scrape_twitter(username, keywords, start_date)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    app.run(debug=True, load_dotenv=False) 