# 🐦 Twitter Scraper

> Advanced Twitter scraping tool with real-time progress updates, keyword filtering, and Excel export capabilities.

![Twitter Scraper Demo](https://img.shields.io/badge/Status-Ready%20for%20Deployment-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Playwright](https://img.shields.io/badge/Playwright-Latest-orange)
![Flask](https://img.shields.io/badge/Flask-Latest-red)

## ✨ Features

### 🔓 **Full Profile Access**
- Login-based scraping to access thousands of tweets (not just recent ~10)
- Bypasses Twitter's anonymous user limitations
- Access to complete tweet history

### 🔍 **Advanced Filtering**
- **Keyword filtering**: Case-insensitive, comma-separated search terms
- **Date range filtering**: Scrape tweets from specific date onwards
- **Smart matching**: Partial text matching for flexible searches

### 📊 **Dual Export Formats**
- **Text files (.txt)**: Human-readable format with full tweet details
- **Excel files (.xlsx)**: Structured spreadsheet with auto-formatted columns
- **Complete data**: Tweet text, dates, likes, retweets, and direct URLs

### 📺 **Real-Time Progress**
- **Live updates**: See scraping progress in real-time on the web interface
- **Tweet counter**: Track how many tweets have been collected
- **Scroll progress**: Monitor infinite scroll progress
- **Milestone markers**: Highlighted progress every 50 tweets
- **Login guidance**: Step-by-step login assistance

### ⚡ **Smart Technology**
- **Infinite scrolling**: Automatically detects when all tweets are collected
- **Duplicate detection**: Prevents collecting the same tweet multiple times
- **Intelligent stopping**: Stops when no new tweets are found
- **Browser automation**: Uses Playwright for reliable scraping

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Stable internet connection
- 4GB+ RAM (8GB recommended for large profiles)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/twitter-scraper.git
   cd twitter-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 Usage

### Basic Scraping
1. Enter a Twitter username (without @)
2. Click "Start Scraping"
3. Log in to Twitter when prompted
4. Watch real-time progress
5. Download generated files

### Advanced Filtering
- **Keywords**: Enter comma-separated terms (e.g., "AI, technology, startup")
- **Date range**: Set a start date to scrape tweets from
- **Combined filters**: Use both keywords and date filtering together

### Output Files
Files are saved in the `tweets/` directory with descriptive names:
- `username_keywords_ai-tech_from_20240101_20250124_143022.txt`
- `username_keywords_ai-tech_from_20240101_20250124_143022.xlsx`

## 📋 Excel File Structure

| Column | Description |
|--------|-------------|
| Tweet # | Sequential numbering |
| Username | @username of the profile |
| Date | ISO format timestamp |
| Tweet Text | Full tweet content |
| Likes | Number of likes |
| Retweets | Number of retweets |
| Tweet URL | Direct link to tweet |
| Matched Keywords | Which keywords were found |
| Filter Keywords | Search terms used |
| Start Date Filter | Date filter applied |
| Scraped At | When the scraping occurred |

## 🌐 Deployment

### Netlify Deployment (Landing Page)
This project includes a static landing page that can be deployed to Netlify:

1. **Build the static site**
   ```bash
   npm run build
   ```

2. **Deploy to Netlify**
   - Connect your GitHub repository to Netlify
   - Set build command: `npm run build`
   - Set publish directory: `dist`

3. **What gets deployed**
   - Professional landing page
   - Download instructions
   - Feature documentation
   - Setup guide

> **Note**: The full scraping functionality requires local installation due to browser automation requirements.

### Full App Deployment Options
- **Local Network**: Change host to `0.0.0.0` for LAN access
- **VPS + Docker**: Use provided Dockerfile for cloud deployment
- **Heroku/Railway**: Supports Python + Playwright with proper buildpacks

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Configuration

### Environment Variables (Optional)
Create a `.env` file for custom settings:
```env
FLASK_DEBUG=True
FLASK_PORT=5000
MAX_SCROLLS=2000
TWEETS_PER_MILESTONE=50
```

### Customization
- **Scroll limits**: Adjust `scroll_count > 2000` in `app.py`
- **Wait times**: Modify `wait_time` values for different scroll speeds
- **Progress intervals**: Change milestone frequency in progress updates

## 🛠️ Development

### Project Structure
```
Twitter Scraper/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Web interface template
├── static/
│   └── style.css         # Stylesheet
├── requirements.txt      # Python dependencies
├── netlify.toml         # Netlify configuration
├── package.json         # Build scripts
├── index.html           # Static landing page
├── dist/                # Built static site
└── tweets/              # Output directory
```

### Key Technologies
- **Backend**: Flask + Socket.IO for real-time updates
- **Browser Automation**: Playwright for reliable scraping
- **Data Processing**: Pandas for Excel export
- **Frontend**: Vanilla JavaScript + WebSocket
- **Styling**: Modern CSS with gradients and animations

## ⚖️ Legal & Ethical Use

**Important**: This tool is for educational and research purposes only.

### Guidelines
- ✅ Respect Twitter's Terms of Service
- ✅ Only scrape public information
- ✅ Use reasonable rate limits
- ✅ Respect user privacy
- ❌ Don't scrape private/protected accounts
- ❌ Don't use for spam or harassment
- ❌ Don't violate data protection laws

### Disclaimer
Users are responsible for ensuring their use complies with applicable laws and platform terms of service.

## 🎯 Use Cases

- **Research**: Academic studies on social media trends
- **Content Analysis**: Brand mention tracking and sentiment analysis
- **Personal Archiving**: Backup your own tweets
- **Marketing**: Competitor analysis and market research
- **Journalism**: Data gathering for news stories
- **Data Science**: Training datasets for ML projects

## 🐛 Troubleshooting

### Common Issues

**"No tweets found"**
- Ensure you're logged in to Twitter
- Check if the profile is public
- Verify the username is correct

**"Login timeout"**
- Refresh the page and try again
- Clear browser cache
- Check internet connection

**"Browser crashes"**
- Increase system RAM
- Close other applications
- Reduce scroll limits

**"Excel export failed"**
- Check disk space
- Ensure write permissions
- Try smaller datasets first

### Performance Tips
- **Large profiles**: Run during off-peak hours
- **Memory usage**: Close other browser tabs
- **Network**: Use stable, fast internet connection
- **Filtering**: Use specific keywords to reduce dataset size

## 📈 Roadmap

- [ ] **Multi-threading**: Parallel processing for faster scraping
- [ ] **Database support**: PostgreSQL/MongoDB integration
- [ ] **API endpoints**: RESTful API for programmatic access
- [ ] **Scheduling**: Automated periodic scraping
- [ ] **Analytics dashboard**: Built-in data visualization
- [ ] **Export formats**: JSON, CSV, and XML support
- [ ] **User management**: Multi-user support with authentication

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/your-username/twitter-scraper.git
cd twitter-scraper
pip install -r requirements.txt
playwright install chromium
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright Team**: For the excellent browser automation framework
- **Flask Community**: For the lightweight web framework
- **Twitter**: For providing the data platform
- **Open Source Community**: For inspiration and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/twitter-scraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/twitter-scraper/discussions)
- **Email**: your-email@example.com

---

<div align="center">

**⭐ Star this repository if you find it useful!**

Made with ❤️ by [Your Name](https://github.com/your-username)

</div> 