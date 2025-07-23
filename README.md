# Twitter Scraper with Playwright

A simple web application that uses Playwright to directly scrape Twitter profiles and save the data to both text files and Excel spreadsheets.

## Setup Instructions

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install the browser:
```bash
playwright install chromium
```

3. That's it! No API keys or credentials needed.

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and go to `http://localhost:5000`

3. Enter a Twitter username (without @)

4. Click "Start Scraping" and watch the browser work!

## How It Works

- Uses Playwright to directly control a Chrome browser
- Navigates to the Twitter profile
- Extracts tweet data directly from the DOM elements:
  - Tweet text from `[data-testid="tweetText"]`
  - Date from `time` elements
  - Likes from `[data-testid="like"]`
  - Retweets from `[data-testid="retweet"]`
  - Tweet URLs from status links
- Scrolls to load more tweets
- Saves everything to both text and Excel files

## Output Formats

### 📄 Text File (.txt)
- Human-readable format
- Easy to read and share
- Contains all tweet information

### 📈 Excel File (.xlsx)
- Organized in spreadsheet columns:
  - **Tweet #** - Sequential numbering
  - **Username** - @username
  - **Date** - ISO format timestamp
  - **Tweet Text** - Full tweet content
  - **Likes** - Number of likes
  - **Retweets** - Number of retweets
  - **Tweet URL** - Direct link to tweet
  - **Scraped At** - When the data was collected
- Auto-sized columns for easy reading
- Bold headers
- Perfect for data analysis

## Features

- **No API keys required** - Direct DOM scraping
- **Visible browser** - Watch the scraping process
- **Duplicate detection** - Avoids saving the same tweet twice
- **Comprehensive data** - Text, date, likes, retweets, and URLs
- **Dual output formats** - Both text and Excel files
- **Professional formatting** - Clean, organized Excel output

## Notes

- The browser will be visible so you can watch the scraping process
- Collects tweets by scrolling through the profile
- Works with public Twitter profiles
- Files saved in the `tweets/` folder with timestamp
- Excel files include clickable URLs and proper formatting

## Advantages Over AI Approach

- **Much faster** - No AI processing needed
- **More reliable** - Direct DOM access
- **No costs** - No API fees
- **More accurate** - Gets exact data from HTML elements
- **Simpler** - No complex prompt engineering
- **Better data format** - Excel files for easy analysis

## Troubleshooting

If you encounter any issues:
1. Make sure Playwright and pandas are installed correctly
2. Ensure the Twitter profile is public
3. Check your internet connection
4. Try with a different username 