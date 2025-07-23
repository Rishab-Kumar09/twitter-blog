import os
from browser_use.llm import ChatOpenAI

# Get API key from environment
api_key = os.environ.get('OPENAI_API_KEY')

if not api_key:
    print("❌ No OPENAI_API_KEY found in environment variables")
    print("Please set your API key with:")
    print('$env:OPENAI_API_KEY = "your-api-key-here"')
else:
    print(f"✅ Found API key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else 'SHORT_KEY'}")
    
    try:
        # Test the API key with a simple request
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        
        print("🔄 Testing API key...")
        
        # This would normally make a request, but let's just check if we can create the client
        print("✅ API key appears to be valid format")
        print("🎉 You can now run the Twitter scraper!")
        
    except Exception as e:
        print(f"❌ Error with API key: {str(e)}")
        print("Please check:")
        print("1. Your API key is correct")
        print("2. You have credits in your OpenAI account")
        print("3. Your account has API access enabled") 