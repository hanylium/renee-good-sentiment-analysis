"""
YouTube Data Collection Script
Collects comments from YouTube videos about the Renee Good ICE shooting.
Uses YouTube Data API v3 to extract comment data from diverse news sources.
"""
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

CHANNEL_CATEGORIES = {
    "local_news": {
        "description": "Local Minneapolis/Minnesota News",
        "channels": ["KARE 11", "WCCO", "FOX 9", "KSTP"],
        "bias": "LOCAL"
    },
    "mainstream": {
        "description": "Mainstream National News",
        "channels": ["ABC News", "CBS News", "NBC News", "Reuters", "Associated Press"],
        "bias": "MAINSTREAM"
    },
    "right_leaning": {
        "description": "Right-Leaning Sources",
        "channels": ["Fox News", "Daily Wire", "Newsmax", "The First"],
        "bias": "RIGHT"
    },
    "left_leaning": {
        "description": "Left-Leaning Sources",
        "channels": ["MSNBC", "The Young Turks", "Democracy Now", "CNN"],
        "bias": "LEFT"
    }
}

SEARCH_QUERIES = [
    "Renee Good ICE",
    "Minneapolis ICE shooting",
    "ICE agent Minneapolis",
    "Renee Good shooting",
]

OUTPUT_FILE = "raw_data.csv"

def create_youtube_client():
    """Create and return YouTube API client."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key or api_key == "your_youtube_api_key":
        print("❌ ERROR: YouTube API key not found.")
        print("   Please add YOUTUBE_API_KEY to your .env file.")
        print("   Get a key at: https://console.cloud.google.com/apis/credentials")
        print("\n   Quick setup:")
        print("   1. Go to Google Cloud Console")
        print("   2. Create a new project (or select existing)")
        print("   3. Enable 'YouTube Data API v3'")
        print("   4. Create credentials → API Key")
        print("   5. Copy the key to your .env file")
        return None
    
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        print("✅ YouTube API client initialized")
        return youtube
    except Exception as e:
        print(f"❌ Failed to initialize YouTube client: {e}")
        return None

def get_channel_bias(channel_title):
    """Determine the political bias category of a channel."""
    channel_lower = channel_title.lower()
    
    for category, info in CHANNEL_CATEGORIES.items():
        for channel_name in info["channels"]:
            if channel_name.lower() in channel_lower or channel_lower in channel_name.lower():
                return info["bias"]
    
    return "UNKNOWN"

def search_videos(youtube, query, max_results=25):
    """Search for videos matching the query."""
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            order="relevance",
            maxResults=max_results,
            publishedAfter="2026-01-01T00:00:00Z"
        )
        response = request.execute()
        
        videos = []
        for item in response.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel_title": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"]
            })
        return videos
    except HttpError as e:
        print(f"   ⚠️ Search error: {e}")
        return []

def get_video_comments(youtube, video_id, max_comments=100):
    """Get comments from a specific video."""
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_comments, 100),
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()
        
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "body": snippet["textDisplay"].replace("\n", " ").replace("\r", " "),
                "author": snippet["authorDisplayName"],
                "likes": snippet.get("likeCount", 0),
                "published_at": snippet["publishedAt"]
            })
            
    except HttpError as e:
        if "commentsDisabled" in str(e):
            pass
        else:
            print(f"   ⚠️ Comment fetch error: {e}")
    
    return comments

def collect_comments(youtube, max_videos_per_query=10, max_comments_per_video=50):
    """
    Collect comments from YouTube videos using search queries.
    Returns a list of comment dictionaries with channel bias tags.
    """
    comments_data = []
    seen_ids = set()
    seen_videos = set()
    
    for query in SEARCH_QUERIES:
        print(f"\n🔍 Searching: '{query}'")
        
        videos = search_videos(youtube, query, max_results=max_videos_per_query)
        print(f"   Found {len(videos)} videos")
        
        for video in videos:
            video_id = video["video_id"]
            if video_id in seen_videos:
                continue
            seen_videos.add(video_id)
            
            channel = video["channel_title"]
            bias = get_channel_bias(channel)
            
            print(f"   📺 {channel} ({bias}): {video['title'][:50]}...")
            
            comments = get_video_comments(youtube, video_id, max_comments=max_comments_per_video)
            
            for comment in comments:
                if comment["comment_id"] in seen_ids:
                    continue
                seen_ids.add(comment["comment_id"])
                
                if len(comment["body"]) < 20:
                    continue
                
                comment_data = {
                    "comment_id": comment["comment_id"],
                    "body": comment["body"],
                    "source": channel,
                    "bias": bias,
                    "score": comment["likes"],
                    "date": comment["published_at"][:10],
                    "video_title": video["title"],
                    "author": comment["author"]
                }
                comments_data.append(comment_data)
            
            print(f"      → {len(comments)} comments collected")
    
    return comments_data

def save_to_csv(comments_data, filename=OUTPUT_FILE):
    """Save collected comments to CSV file."""
    if not comments_data:
        print("❌ No comments to save.")
        return False
    
    fieldnames = ["comment_id", "body", "source", "bias", "score", "date", "video_title", "author"]
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comments_data)
    
    print(f"\n✅ Saved {len(comments_data)} comments to {filename}")
    return True

def main():
    """Main function to run the data collection pipeline."""
    print("="*60)
    print("YOUTUBE DATA COLLECTION - Renee Good ICE Shooting Analysis")
    print("="*60)
    
    youtube = create_youtube_client()
    if not youtube:
        return
    
    print(f"\nSearch queries: {SEARCH_QUERIES}")
    print("\nChannel categories:")
    for cat, info in CHANNEL_CATEGORIES.items():
        print(f"   {info['bias']}: {', '.join(info['channels'][:3])}...")
    
    comments = collect_comments(youtube, max_videos_per_query=50, max_comments_per_video=100)
    
    print(f"\n📊 Collection Summary:")
    print(f"   Total unique comments: {len(comments)}")
    
    bias_counts = {}
    for c in comments:
        b = c["bias"]
        bias_counts[b] = bias_counts.get(b, 0) + 1
    
    for bias, count in sorted(bias_counts.items(), key=lambda x: -x[1]):
        print(f"   {bias}: {count} comments")
    
    save_to_csv(comments)
    
    print("\n" + "="*60)
    print("Data collection complete! Next step: Run analyze.py")
    print("="*60)

if __name__ == "__main__":
    main()
