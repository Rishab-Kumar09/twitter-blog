import asyncio
from flask import Flask, render_template, request, jsonify
from playwright.async_api import async_playwright
import os
from datetime import datetime
import re
import time
import pandas as pd

app = Flask(__name__)

def save_tweets_to_files(username, tweets):
    # Create 'tweets' directory if it doesn't exist
    os.makedirs('tweets', exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    txt_filename = f'tweets/{username}_{timestamp}.txt'
    excel_filename = f'tweets/{username}_{timestamp}.xlsx'
    
    # Save as text file
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Tweets from @{username}\n")
        f.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet #{i}:\n")
            f.write(f"Date: {tweet.get('date', 'N/A')}\n")
            f.write(f"Text: {tweet.get('text', 'N/A')}\n")
            f.write(f"Likes: {tweet.get('likes', '0')}\n")
            f.write(f"Retweets: {tweet.get('retweets', '0')}\n")
            f.write(f"URL: {tweet.get('url', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")
    
    # Save as Excel file
    try:
        # Prepare data for DataFrame
        excel_data = []
        for i, tweet in enumerate(tweets, 1):
            excel_data.append({
                'Tweet #': i,
                'Username': f"@{username}",
                'Date': tweet.get('date', 'N/A'),
                'Tweet Text': tweet.get('text', 'N/A'),
                'Likes': tweet.get('likes', '0'),
                'Retweets': tweet.get('retweets', '0'),
                'Tweet URL': tweet.get('url', 'N/A'),
                'Scraped At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(excel_data)
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'{username}_tweets', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[f'{username}_tweets']
            
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

async def scrape_twitter_with_playwright(username):
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
            
            # Scroll and collect tweets
            for scroll in range(3):  # Scroll 3 times to get more tweets
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
                
                # Scroll down to load more tweets
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(2000)  # Wait for new tweets to load
            
            await browser.close()
            return tweets
            
        except Exception as e:
            await browser.close()
            raise e

async def scrape_twitter(username):
    try:
        tweets = await scrape_twitter_with_playwright(username)
        
        if not tweets:
            return False, "No tweets were found. The profile might be private or doesn't exist."
        
        # Save tweets to both text and Excel files
        txt_file, excel_file = save_tweets_to_files(username, tweets)
        
        if excel_file:
            return True, f"Successfully scraped {len(tweets)} tweets from @{username}. Saved to {txt_file} and {excel_file}"
        else:
            return True, f"Successfully scraped {len(tweets)} tweets from @{username}. Saved to {txt_file} (Excel export failed)"
    except Exception as e:
        return False, f"Error scraping Twitter: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
async def scrape():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'})
    
    success, message = await scrape_twitter(username)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    app.run(debug=True, load_dotenv=False) 