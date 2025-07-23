import os
import openai
from openai import OpenAI

print("=== API Key Debug ===")

# Test 1: Check environment variable
api_key = os.environ.get('OPENAI_API_KEY')
print(f"1. Environment variable: {api_key[:20] if api_key else 'NOT FOUND'}...")

# Test 2: Try direct OpenAI client
if api_key:
    try:
        client = OpenAI(api_key=api_key)
        print("2. OpenAI client created successfully")
        
        # Test 3: Make a simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print("3. ✅ API call successful!")
        print(f"   Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"3. ❌ API call failed: {e}")
        
        # Check common issues
        if "401" in str(e):
            print("   → This is an authentication error")
            print("   → Your API key is invalid or expired")
        elif "insufficient_quota" in str(e):
            print("   → You don't have enough credits")
        elif "billing" in str(e):
            print("   → Billing issue - check your payment method")
            
else:
    print("2. ❌ No API key found")

print("\n=== Next Steps ===")
print("1. Get a valid API key from: https://platform.openai.com/api-keys")
print("2. Check billing: https://platform.openai.com/account/billing")
print("3. Set it with: $env:OPENAI_API_KEY = 'your-key-here'") 