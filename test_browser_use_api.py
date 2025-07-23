import os
from browser_use.llm import ChatOpenAI

print("=== Browser-Use API Key Test ===")

# Check environment variable
api_key = os.environ.get('OPENAI_API_KEY')
print(f"1. Environment variable: {api_key[:20] if api_key else 'NOT FOUND'}...")

if api_key:
    try:
        # Create ChatOpenAI exactly like in our app
        llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0.7
        )
        print("2. ✅ ChatOpenAI client created successfully")
        
        # Let's see what attributes it has
        print(f"3. ChatOpenAI type: {type(llm)}")
        print(f"4. ChatOpenAI attributes: {dir(llm)}")
        
        # Try to make a simple call like browser-use would
        try:
            # This is how browser-use might call the LLM
            response = llm.generate("Say hello in one word")
            print(f"5. ✅ LLM call successful: {response}")
        except Exception as e:
            print(f"5. ❌ LLM call failed: {e}")
            
    except Exception as e:
        print(f"2. ❌ ChatOpenAI creation failed: {e}")
else:
    print("2. ❌ No API key found")

# Also check if there are any other environment variables browser-use might need
print("\n=== Environment Check ===")
for key in os.environ:
    if 'OPENAI' in key or 'API' in key:
        print(f"{key}: {os.environ[key][:20]}..." if len(os.environ[key]) > 20 else f"{key}: {os.environ[key]}") 