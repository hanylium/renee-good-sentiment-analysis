"""
Analysis Script - Batch Processing with Groq API
Reads raw_data.csv, classifies each comment using Groq, and saves results to analyzed_data.csv.
Includes error handling with retry logic for rate limits.
"""
import os
import csv
import json
import time
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are a political science researcher. Analyze the following YouTube comment regarding the Renee Good ICE shooting incident in Minneapolis. Classify it into ONE category: JUSTIFIED (supports the ICE agent's actions), EXCESSIVE (criticizes the agent's actions as excessive force), or NEUTRAL (no clear stance). Additionally, identify the dominant frame: MORALITY (ethical/moral arguments), CONFLICT (us vs them, political polarization), or LEGALITY (legal rights, constitutional arguments). Return results in a structured format (JSON).

Return ONLY valid JSON in this exact format:
{"category": "JUSTIFIED|EXCESSIVE|NEUTRAL", "frame": "MORALITY|CONFLICT|LEGALITY", "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""

INPUT_FILE = "raw_data.csv"
OUTPUT_FILE = "analyzed_data.csv"

MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 2
RATE_LIMIT_DELAY = 60

def create_groq_client():
    """Create and return Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ ERROR: GROQ_API_KEY not found in environment variables.")
        return None
    return Groq(api_key=api_key)

def parse_response(response_text):
    """Extract JSON from Groq response, handling markdown code blocks."""
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        response_text = json_match.group(1)
    
    json_match = re.search(r'\{[^{}]*\}', response_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None

def classify_comment(client, comment_body, retries=0):
    """
    Send a comment to Groq for classification.
    Implements retry logic with exponential backoff.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Comment: {comment_body}"}
            ],
            temperature=0.1,
            max_tokens=256
        )
        
        result_text = response.choices[0].message.content
        parsed = parse_response(result_text)
        
        if parsed:
            return {
                "category": parsed.get("category", "NEUTRAL"),
                "frame": parsed.get("frame", "CONFLICT"),
                "confidence": parsed.get("confidence", 0.5),
                "reasoning": parsed.get("reasoning", ""),
                "raw_response": result_text
            }
        else:
            return {
                "category": "NEUTRAL",
                "frame": "CONFLICT",
                "confidence": 0.0,
                "reasoning": "Failed to parse response",
                "raw_response": result_text
            }
            
    except Exception as e:
        error_str = str(e).lower()
        
        if "rate" in error_str or "limit" in error_str or "429" in error_str:
            if retries < MAX_RETRIES:
                wait_time = RATE_LIMIT_DELAY * (retries + 1)
                print(f"   ⏳ Rate limited. Waiting {wait_time}s before retry {retries + 1}/{MAX_RETRIES}...")
                time.sleep(wait_time)
                return classify_comment(client, comment_body, retries + 1)
        
        elif retries < MAX_RETRIES:
            wait_time = INITIAL_RETRY_DELAY * (2 ** retries)
            print(f"   ⚠️ API error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            return classify_comment(client, comment_body, retries + 1)
        
        print(f"   ❌ Failed after {MAX_RETRIES} retries: {e}")
        return {
            "category": "ERROR",
            "frame": "ERROR",
            "confidence": 0.0,
            "reasoning": str(e),
            "raw_response": ""
        }

def load_existing_progress(output_file):
    """Load already processed comment IDs to enable resume functionality."""
    processed_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_ids.add(row.get("comment_id", ""))
    return processed_ids

def analyze_comments():
    """Main function to process all comments."""
    print("="*60)
    print("COMMENT ANALYSIS - Groq Classification Pipeline")
    print("="*60)
    
    client = create_groq_client()
    if not client:
        return
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file '{INPUT_FILE}' not found.")
        print("   Please run collect_data.py first.")
        return
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        comments = list(reader)
    
    print(f"✅ Loaded {len(comments)} comments from {INPUT_FILE}")
    
    processed_ids = load_existing_progress(OUTPUT_FILE)
    if processed_ids:
        print(f"📌 Resuming: {len(processed_ids)} comments already processed")
    
    fieldnames = [
        "comment_id", "body", "source", "bias", "score", "date",
        "video_title", "author", "category", "frame",
        "confidence", "reasoning"
    ]
    
    file_exists = os.path.exists(OUTPUT_FILE) and len(processed_ids) > 0
    mode = "a" if file_exists else "w"
    
    with open(OUTPUT_FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        to_process = [c for c in comments if c.get("comment_id") not in processed_ids]
        total = len(to_process)
        
        print(f"\n🔄 Processing {total} comments...\n")
        
        for i, comment in enumerate(to_process, 1):
            comment_id = comment.get("comment_id", "")
            body = comment.get("body", "")[:1000]
            source = comment.get("source", "")
            bias = comment.get("bias", "UNKNOWN")
            
            print(f"[{i}/{total}] {source} ({bias}) - {body[:50]}...")
            
            result = classify_comment(client, body)
            
            row = {
                "comment_id": comment_id,
                "body": comment.get("body", ""),
                "source": source,
                "bias": bias,
                "score": comment.get("score", 0),
                "date": comment.get("date", ""),
                "video_title": comment.get("video_title", ""),
                "author": comment.get("author", ""),
                "category": result["category"],
                "frame": result["frame"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"]
            }
            
            writer.writerow(row)
            f.flush()
            
            print(f"   → {result['category']} | {result['frame']} | conf: {result['confidence']}")
            
            time.sleep(0.5)
    
    print("\n" + "="*60)
    print(f"✅ Analysis complete! Results saved to {OUTPUT_FILE}")
    print("Next step: Run visualize.py to generate charts")
    print("="*60)

if __name__ == "__main__":
    analyze_comments()
