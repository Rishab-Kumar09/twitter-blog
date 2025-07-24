# Twitter Scraper with Playwright

A simple web application that uses Playwright to directly scrape Twitter profiles and save the data to both text files and Excel spreadsheets. Now with **advanced filtering** including keywords and date ranges!

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

4. **NEW!** Set filtering options:
   - **Keywords**: Comma-separated keywords to search for
   - **Start Date**: Only get tweets from this date onwards

5. Click "Start Scraping" and watch the browser work!

## How It Works

- Uses Playwright to directly control a Chrome browser
- Navigates to the Twitter profile
- Extracts tweet data directly from the DOM elements:
  - Tweet text from `[data-testid="tweetText"]`
  - Date from `time` elements
  - Likes from `[data-testid="like"]`
  - Retweets from `[data-testid="retweet"]`
  - Tweet URLs from status links
- **NEW!** Filters tweets by date (from specified date onwards)
- **NEW!** Filters tweets by keywords (case-insensitive)
- Intelligent scrolling (more scrolls when filtering for better results)
- Saves everything to both text and Excel files

## 🔍 Advanced Filtering Features

### 📅 Date Filtering:
- **From Date**: Get only tweets from a specific date onwards
- **Default**: Pre-filled with 7 days ago for convenience
- **Format**: YYYY-MM-DD (e.g., 2025-01-15)
- **Smart Parsing**: Handles timezone differences automatically

### 🔍 Keyword Filtering:
- **Case-insensitive**: Finds "AI", "ai", "Ai"
- **Partial matching**: "tech" matches "technology"
- **Multiple keywords**: Separate with commas
- **Any match**: Tweet included if it contains ANY of the keywords

### 📊 Combined Filtering:
- Use **both** date and keyword filters together
- Example: Tweets containing "AI" from the last week
- More scrolling automatically applied for better results
- Smart stopping when no new tweets are found

### Examples:
- **Keywords only**: `python, coding, programming`
- **Date only**: From `2025-01-01`
- **Combined**: Keywords `AI, machine learning` from `2025-01-15`
- **Recent research**: Keywords `bitcoin, crypto` from `2025-01-20`

## Output Formats

### 📄 Text File (.txt)
- Human-readable format
- Easy to read and share
- Contains all tweet information
- Shows matched keywords and date filters applied
- Clear separation between tweets

### 📈 Excel File (.xlsx)
- Organized in spreadsheet columns:
  - **Tweet #** - Sequential numbering
  - **Username** - @username
  - **Date** - ISO format timestamp
  - **Tweet Text** - Full tweet content
  - **Likes** - Number of likes
  - **Retweets** - Number of retweets
  - **Tweet URL** - Direct link to tweet
  - **🆕 Matched Keywords** - Which keywords were found in the tweet
  - **🆕 Filter Keywords** - What keywords you searched for
  - **🆕 Start Date Filter** - What date filter was applied
  - **Scraped At** - When the data was collected
- Auto-sized columns for easy reading
- Bold headers
- Perfect for data analysis and research

## Features

- **No API keys required** - Direct DOM scraping
- **Visible browser** - Watch the scraping process
- **🆕 Advanced date filtering** - Get tweets from specific time periods
- **🆕 Smart keyword filtering** - Case-insensitive, partial matching
- **🆕 Combined filters** - Use date and keywords together
- **Duplicate detection** - Avoids saving the same tweet twice
- **Intelligent scrolling** - More scrolls when filtering, stops when no new tweets
- **Comprehensive data** - Text, date, likes, retweets, and URLs
- **Dual output formats** - Both text and Excel files
- **Professional formatting** - Clean, organized Excel output
- **Smart file naming** - Includes all applied filters in filename

## File Naming Examples

Files are automatically named with timestamps and filter information:
- **All tweets**: `elonmusk_20250123_143022.xlsx`
- **Keyword filtered**: `elonmusk_keywords_AI-tech_20250123_143022.xlsx`
- **Date filtered**: `elonmusk_from_20250115_20250123_143022.xlsx`
- **Both filters**: `elonmusk_keywords_AI-tech_from_20250115_20250123_143022.xlsx`

## Use Cases

### 📊 Research & Analysis:
- **Trend Analysis**: Track how topics evolve over time
- **Brand Monitoring**: Find mentions of your brand in recent tweets
- **Competitor Research**: Monitor competitor discussions from specific dates
- **Event Analysis**: Get tweets about events from the day they happened

### 📈 Content Strategy:
- **Performance Tracking**: See which content performs best over time
- **Hashtag Research**: Find trending hashtags from specific periods
- **Engagement Analysis**: Compare tweet performance across different dates
- **Content Planning**: Research what works in your industry

### 🔍 Academic Research:
- **Sentiment Analysis**: Track sentiment changes over time
- **Topic Modeling**: Analyze how topics trend across dates
- **Social Media Studies**: Research patterns in social media behavior
- **Event Impact**: Study how events affect social media discussions

### 💼 Business Intelligence:
- **Market Research**: Track industry discussions from key dates
- **Customer Feedback**: Monitor customer sentiment over time
- **Crisis Management**: Track mentions during specific time periods
- **Campaign Analysis**: Measure campaign impact from launch dates

## Notes

- The browser will be visible so you can watch the scraping process
- Date filtering uses the tweet's original posting date
- Keyword filtering is applied after date filtering for efficiency
- When using filters, the scraper automatically scrolls more to find relevant tweets
- Smart stopping prevents infinite scrolling when no new tweets are found
- Files saved with descriptive names including all applied filters
- Excel files include clickable URLs and proper formatting
- Default date is set to 7 days ago for convenience

## Advantages Over AI Approach

- **Much faster** - No AI processing needed
- **More reliable** - Direct DOM access
- **No costs** - No API fees
- **More accurate** - Gets exact data from HTML elements
- **Simpler** - No complex prompt engineering
- **Better data format** - Excel files for easy analysis
- **🆕 Precise filtering** - Exact keyword and date matching
- **🆕 Efficient processing** - Smart filtering order for better performance

## Troubleshooting

If you encounter any issues:
1. Make sure all dependencies are installed correctly (`pip install -r requirements.txt`)
2. Ensure the Twitter profile is public
3. Check your internet connection
4. Try with a different username
5. If no tweets match your filters, try:
   - Broader keywords
   - Earlier start date
   - Removing one filter to test
6. For date issues, ensure format is YYYY-MM-DD 