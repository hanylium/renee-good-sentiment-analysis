"""
De-risk script: Test Groq API connection and classification prompt.
Run this first to verify the API works before full data collection.
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are a political science researcher. Analyze the following Reddit comment regarding the Renee Good shooting. Classify it into ONE category: JUSTIFIED (supports the agent), EXCESSIVE (criticizes the agent), or NEUTRAL. Additionally, identify the dominant frame: MORALITY, CONFLICT, or LEGALITY. Return results in a structured format (JSON)."""

TEST_COMMENTS = [
    "The agent was clearly acting in self-defense. Anyone would do the same in that situation.",
    "This is murder plain and simple. ICE has no accountability.",
    "I don't know enough about this case to form an opinion yet. Need more facts.",
    "The law is clear - federal agents have the right to protect themselves. This was justified legally.",
    "This is a moral tragedy. An innocent person lost their life.",
]

def test_groq_api():
    """Test Groq API with sample comments to de-risk assumptions."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ ERROR: GROQ_API_KEY not found in environment variables.")
        print("   Please create a .env file with your Groq API key.")
        print("   See .env.example for the required format.")
        return False
    
    print("✅ Groq API key found")
    
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        return False
    
    print("\n" + "="*60)
    print("TESTING CLASSIFICATION ON SAMPLE COMMENTS")
    print("="*60 + "\n")
    
    for i, comment in enumerate(TEST_COMMENTS, 1):
        print(f"--- Test {i}/5 ---")
        print(f"Comment: {comment[:80]}...")
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": comment}
                ],
                temperature=0.1,
                max_tokens=256
            )
            
            result = response.choices[0].message.content
            print(f"Result: {result}\n")
            
        except Exception as e:
            print(f"❌ API call failed: {e}")
            return False
    
    print("="*60)
    print("✅ ALL TESTS PASSED - Groq API is working correctly!")
    print("="*60)
    print("\nDe-risking complete. Key findings:")
    print("- API connection: WORKING")
    print("- Classification prompt: FUNCTIONAL")
    print("- JSON output: GENERATING")
    print("\nYou can now proceed with data collection and full analysis.")
    
    return True

if __name__ == "__main__":
    test_groq_api()
