#!/usr/bin/env python3
"""
Gauntlet AI Automated Blog Generator
====================================

This system:
1. Analyzes Austin's Twitter data for Gauntlet AI-related themes
2. Extracts frequently asked questions and topics
3. Generates SEO/GEO-optimized blog posts (350-500 words)
4. Prepares content for HubSpot CMS publishing

Based on PRD requirements for 20 blogs/week targeting AI engineers and executives.
"""

import pandas as pd
import re
import json
from collections import Counter, defaultdict
from datetime import datetime
import openai
import os
from typing import List, Dict, Tuple, Optional

class GauntletBlogGenerator:
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the blog generator with OpenAI API key."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Gauntlet AI-specific keywords and themes
        self.gauntlet_keywords = [
            'gauntlet', 'gauntlet ai', 'ai-first development', 'ai engineer', 
            'ai training', 'coding bootcamp', 'software engineer', 'ai development',
            'legacy code', 'enterprise', 'fortran', 'cobol', 'assembly',
            'ai agents', 'claude', 'gpt', 'llm', 'machine learning'
        ]
        
        # SEO/GEO optimization prompts
        self.seo_prompt = """
        You are an SEO expert writing for Gauntlet AI. Create content that:
        - Targets AI engineers and executives
        - Uses semantic keywords naturally
        - Includes FAQ-style sections for featured snippets
        - Optimizes for "People Also Ask" sections
        - Uses clear H2 headers for topic clustering
        """
        
        self.geo_prompt = """
        You are optimizing for Generative Engine Optimization (GEO). Create content that:
        - Provides direct, quotable answers to common questions
        - Uses structured data-friendly formats
        - Includes specific examples and use cases
        - Answers questions in a conversational, authoritative tone
        - Optimizes for LLM training data inclusion
        """

    def load_tweet_data(self, file_path: str) -> List[Dict]:
        """Load and parse tweet data from text file."""
        tweets = []
        current_tweet = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by tweet separators
            tweet_blocks = content.split('Tweet #')[1:]  # Skip header
            
            for block in tweet_blocks:
                lines = block.strip().split('\n')
                tweet = {}
                
                for line in lines:
                    if line.startswith('Date:'):
                        tweet['date'] = line.replace('Date:', '').strip()
                    elif line.startswith('Text:'):
                        tweet['text'] = line.replace('Text:', '').strip()
                    elif line.startswith('Likes:'):
                        tweet['likes'] = line.replace('Likes:', '').strip()
                    elif line.startswith('URL:'):
                        tweet['url'] = line.replace('URL:', '').strip()
                
                if tweet.get('text'):
                    tweets.append(tweet)
            
            print(f"✅ Loaded {len(tweets)} tweets from {file_path}")
            return tweets
            
        except Exception as e:
            print(f"❌ Error loading tweets: {e}")
            return []

    def extract_gauntlet_themes(self, tweets: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract Gauntlet AI-related themes and topics from tweets."""
        themes = defaultdict(list)
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            
            # Check for Gauntlet AI mentions
            if any(keyword in text for keyword in self.gauntlet_keywords):
                # Categorize by theme
                if 'gauntlet' in text and ('training' in text or 'bootcamp' in text or 'program' in text):
                    themes['Training Program'].append(tweet)
                elif 'legacy' in text or 'enterprise' in text or any(lang in text for lang in ['fortran', 'cobol', 'assembly']):
                    themes['Legacy Code & Enterprise'].append(tweet)
                elif 'ai-first' in text or 'ai engineer' in text:
                    themes['AI-First Development'].append(tweet)
                elif 'job' in text or 'career' in text or '$' in text:
                    themes['Career & Salary'].append(tweet)
                elif 'agent' in text or 'claude' in text or 'gpt' in text:
                    themes['AI Tools & Agents'].append(tweet)
                else:
                    themes['General AI Development'].append(tweet)
        
        # Sort themes by tweet count
        sorted_themes = dict(sorted(themes.items(), key=lambda x: len(x[1]), reverse=True))
        
        print(f"🎯 Extracted {len(sorted_themes)} Gauntlet AI themes:")
        for theme, tweet_list in sorted_themes.items():
            print(f"   • {theme}: {len(tweet_list)} tweets")
        
        return sorted_themes

    def generate_blog_topics(self, themes: Dict[str, List[Dict]], target_count: int = 20) -> List[Dict]:
        """Generate blog topics from extracted themes."""
        blog_topics = []
        
        # Pre-defined high-value topics for Gauntlet AI
        priority_topics = [
            {
                'title': 'Why AI-First Development is the Future of Software Engineering',
                'theme': 'AI-First Development',
                'keywords': ['ai-first development', 'software engineering', 'ai engineer'],
                'target_audience': 'AI Engineers',
                'priority': 1
            },
            {
                'title': 'How Gauntlet AI Transforms Legacy Enterprise Code with AI',
                'theme': 'Legacy Code & Enterprise',
                'keywords': ['legacy code', 'enterprise', 'ai transformation'],
                'target_audience': 'Executives',
                'priority': 1
            },
            {
                'title': 'From Bootcamp to $200k: The Gauntlet AI Success Story',
                'theme': 'Career & Salary',
                'keywords': ['ai bootcamp', 'career change', 'ai jobs'],
                'target_audience': 'Career Changers',
                'priority': 1
            },
            {
                'title': 'Working with COBOL and Fortran: How AI Handles Legacy Languages',
                'theme': 'Legacy Code & Enterprise',
                'keywords': ['cobol', 'fortran', 'legacy programming'],
                'target_audience': 'Enterprise Developers',
                'priority': 2
            },
            {
                'title': 'AI Agents in Production: Lessons from Gauntlet AI',
                'theme': 'AI Tools & Agents',
                'keywords': ['ai agents', 'production ai', 'claude'],
                'target_audience': 'AI Engineers',
                'priority': 2
            }
        ]
        
        # Add priority topics
        blog_topics.extend(priority_topics)
        
        # Generate additional topics from tweet themes
        for theme, tweet_list in themes.items():
            if len(blog_topics) >= target_count:
                break
                
            # Extract common questions/topics from tweets
            common_phrases = self._extract_common_phrases(tweet_list)
            
            for phrase in common_phrases[:3]:  # Top 3 per theme
                if len(blog_topics) >= target_count:
                    break
                    
                topic = {
                    'title': f'Understanding {phrase} in AI Development',
                    'theme': theme,
                    'keywords': [phrase.lower(), 'ai development'],
                    'target_audience': 'AI Engineers',
                    'priority': 3,
                    'source_tweets': len(tweet_list)
                }
                blog_topics.append(topic)
        
        print(f"📝 Generated {len(blog_topics)} blog topics")
        return blog_topics[:target_count]

    def _extract_common_phrases(self, tweets: List[Dict]) -> List[str]:
        """Extract common phrases from tweet text."""
        all_text = ' '.join([tweet.get('text', '') for tweet in tweets])
        
        # Simple phrase extraction (can be enhanced with NLP)
        phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', all_text)
        phrase_counts = Counter(phrases)
        
        return [phrase for phrase, count in phrase_counts.most_common(10) if count > 1]

    def generate_blog_post(self, topic: Dict, knowledge_base: str = "") -> Dict:
        """Generate a complete blog post for the given topic."""
        
        # Create comprehensive prompt
        prompt = f"""
        {self.seo_prompt}
        {self.geo_prompt}
        
        Write a 400-450 word blog post for Gauntlet AI about: "{topic['title']}"
        
        Target audience: {topic['target_audience']}
        Keywords to include naturally: {', '.join(topic['keywords'])}
        Theme: {topic['theme']}
        
        Knowledge base context:
        {knowledge_base}
        
        Structure:
        1. Compelling H1 title
        2. Brief intro (50 words max)
        3. 2-3 H2 sections with practical insights
        4. FAQ section (2-3 questions)
        5. Conclusion with CTA
        
        Requirements:
        - Write in an authoritative, helpful tone
        - Include specific examples
        - Optimize for featured snippets
        - Make it quotable for LLMs
        - Focus on Gauntlet AI's expertise
        """
        
        try:
            if self.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7
                )
                content = response.choices[0].message.content
            else:
                # Mock content for testing
                content = self._generate_mock_blog_post(topic)
            
            # Generate meta data
            meta_title = topic['title'][:60]  # SEO limit
            meta_description = f"Learn about {topic['theme'].lower()} at Gauntlet AI. Expert insights for {topic['target_audience'].lower()}."[:155]
            slug = re.sub(r'[^a-z0-9]+', '-', topic['title'].lower())[:20]
            
            blog_post = {
                'title': topic['title'],
                'content': content,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'slug': slug,
                'keywords': topic['keywords'],
                'theme': topic['theme'],
                'target_audience': topic['target_audience'],
                'created_date': datetime.now().isoformat(),
                'word_count': len(content.split()),
                'schema_type': 'Article',  # Will add FAQ schema if FAQ section detected
                'hubspot_ready': True
            }
            
            # Add FAQ schema if FAQ section detected
            if 'FAQ' in content or '?' in content:
                blog_post['schema_type'] = 'FAQPage'
            
            print(f"✅ Generated blog post: {topic['title']} ({blog_post['word_count']} words)")
            return blog_post
            
        except Exception as e:
            print(f"❌ Error generating blog post: {e}")
            return {}

    def _generate_mock_blog_post(self, topic: Dict) -> str:
        """Generate mock blog post for testing when OpenAI API is not available."""
        return f"""
# {topic['title']}

The landscape of AI development is rapidly evolving, and {topic['theme'].lower()} represents a critical area where Gauntlet AI is leading innovation.

## Understanding the Challenge

At Gauntlet AI, we've seen firsthand how {topic['keywords'][0]} impacts modern software development. Our approach combines practical experience with cutting-edge AI techniques.

## The Gauntlet AI Approach

Our methodology focuses on:
- Practical implementation strategies
- Real-world case studies from our training program
- Industry-tested best practices

## Frequently Asked Questions

**Q: How does this apply to enterprise environments?**
A: Gauntlet AI's approach is specifically designed for enterprise-scale challenges, as demonstrated in our recent work with legacy systems.

**Q: What makes this different from traditional approaches?**
A: Our AI-first methodology leverages the latest advances in machine learning while maintaining practical applicability.

## Conclusion

{topic['theme']} continues to be a defining factor in AI development success. At Gauntlet AI, we're committed to training the next generation of AI-first engineers.

Ready to learn more? [Apply to Gauntlet AI](http://apply.gauntletai.com) and join our community of AI-first developers.
        """.strip()

    def save_blog_posts(self, blog_posts: List[Dict], output_dir: str = "generated_blogs"):
        """Save generated blog posts to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save individual blog posts
        for i, post in enumerate(blog_posts, 1):
            filename = f"{output_dir}/blog_{i:02d}_{post['slug']}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"title: {post['title']}\n")
                f.write(f"meta_title: {post['meta_title']}\n")
                f.write(f"meta_description: {post['meta_description']}\n")
                f.write(f"slug: {post['slug']}\n")
                f.write(f"keywords: {', '.join(post['keywords'])}\n")
                f.write(f"theme: {post['theme']}\n")
                f.write(f"target_audience: {post['target_audience']}\n")
                f.write(f"schema_type: {post['schema_type']}\n")
                f.write(f"created_date: {post['created_date']}\n")
                f.write(f"word_count: {post['word_count']}\n")
                f.write(f"---\n\n")
                f.write(post['content'])
        
        # Save summary report
        summary_file = f"{output_dir}/blog_generation_report.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generation_date': datetime.now().isoformat(),
                'total_posts': len(blog_posts),
                'themes': list(set([post['theme'] for post in blog_posts])),
                'target_audiences': list(set([post['target_audience'] for post in blog_posts])),
                'average_word_count': sum([post['word_count'] for post in blog_posts]) / len(blog_posts),
                'posts': blog_posts
            }, f, indent=2)
        
        print(f"💾 Saved {len(blog_posts)} blog posts to {output_dir}/")
        print(f"📊 Generation report saved to {summary_file}")

def main():
    """Main execution function."""
    print("🚀 Gauntlet AI Blog Generator Starting...")
    
    # Initialize generator
    generator = GauntletBlogGenerator()
    
    # Load latest tweet data
    tweet_file = "tweets/Austen_from_20250721_20250728_134227.txt"
    tweets = generator.load_tweet_data(tweet_file)
    
    if not tweets:
        print("❌ No tweet data loaded. Please check the file path.")
        return
    
    # Extract Gauntlet AI themes
    themes = generator.extract_gauntlet_themes(tweets)
    
    # Generate blog topics
    topics = generator.generate_blog_topics(themes, target_count=20)
    
    # Generate blog posts
    blog_posts = []
    for i, topic in enumerate(topics, 1):
        print(f"📝 Generating blog post {i}/{len(topics)}: {topic['title']}")
        post = generator.generate_blog_post(topic)
        if post:
            blog_posts.append(post)
    
    # Save results
    generator.save_blog_posts(blog_posts)
    
    print(f"✅ Blog generation complete! Generated {len(blog_posts)} posts")
    print(f"🎯 Ready for HubSpot CMS publishing")

if __name__ == "__main__":
    main() 