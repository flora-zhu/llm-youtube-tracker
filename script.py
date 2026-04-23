import requests
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from config import YOUTUBE_API_KEY, GROQ_API_KEY
import json
import time


# --- CHANNELS TO TRACK ---
CHANNELS = [
    "UCNJ1Ymd5yFuUPtn21xtRbbw",  # Yannic Kilcher
    "UChpleBmo18P08aKCIgti38g",  # Matt Wolfe
    "UCsBjURrPoezykLs9EqgamOA",  # Fireship
    "UCqcbQf6yw5KzRoDDcZ_wBSw",  # Wes Roth
]

CHANNEL_NAMES = {
    "UCNJ1Ymd5yFuUPtn21xtRbbw": "Yannic Kilcher",
    "UChpleBmo18P08aKCIgti38g": "Matt Wolfe",
    "UCsBjURrPoezykLs9EqgamOA": "Fireship",
    "UCqcbQf6yw5KzRoDDcZ_wBSw": "Wes Roth",
}

# --- STEP 1: GET RECENT VIDEOS ---
def get_recent_videos(channel_id, max_results=3):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=max_results,
        order="date",
        type="video"
    )
    response = request.execute()
    videos = []
    for item in response["items"]:
        videos.append({
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "date": item["snippet"]["publishedAt"][:10],
            "channel": CHANNEL_NAMES[channel_id]
        })
    return videos

# --- STEP 2: GET TRANSCRIPT ---
def get_transcript(video_id):
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        full_text = " ".join([t.text for t in transcript])
        return " ".join(full_text.split()[:800])
    except Exception:
        return None
    
# --- STEP 3: SUMMARIZE WITH AI ---
def summarize(transcript, title):
    if not transcript:
        return "No transcript available", "N/A"
    
    prompt = f"""Analyze this YouTube video about AI/LLMs.
Title: {title}
Transcript excerpt: {transcript}

You MUST respond with ONLY a JSON object, no other text, no backticks, no explanation.
Example format: {{"topics": "RAG, agents, fine-tuning", "summary": "Two sentence summary here."}}

topics: comma-separated list of LLM/AI topics covered
summary: exactly 2 sentences about the creator's main points"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    
    content = response.json()["choices"][0]["message"]["content"].strip()
    # Aggressively strip any markdown formatting
    content = content.replace("```json", "").replace("```", "").strip()
    # Find the JSON object even if there's junk around it
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end != 0:
        content = content[start:end]
    
    try:
        parsed = json.loads(content)
        return parsed.get("summary", "N/A"), parsed.get("topics", "N/A")
    except Exception as e:
        print(f"  Parse error: {e} | Raw: {content[:100]}")
        return "N/A", "N/A"
    
# --- STEP 4: BUILD HTML ---
def build_html(rows):
    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
            <td>{r['channel']}</td>
            <td><a href="https://youtube.com/watch?v={r['id']}" target="_blank">{r['title']}</a></td>
            <td>{r['date']}</td>
            <td>{r['topics']}</td>
            <td>{r['summary']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>LLM YouTube Tracker</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 30px; background: #f9f9f9; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; background: white; }}
        th {{ background: #4a4a8a; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; vertical-align: top; }}
        tr:hover {{ background: #f1f1ff; }}
        a {{ color: #4a4a8a; }}
        .updated {{ color: #888; font-size: 0.85em; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>LLM YouTube Landscape Tracker</h1>
    <p class="updated">Last updated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <table>
        <tr>
            <th>Channel</th>
            <th>Video</th>
            <th>Date</th>
            <th>Topics</th>
            <th>Summary</th>
        </tr>
        {rows_html}
    </table>
</body>
</html>"""

# --- CHECK IF VIDEO IS TOPICAL ---
def is_llm_related(title):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": f"Is this YouTube video title related to AI, LLMs, machine learning, or technology? When in doubt, say YES. Reply with only YES or NO.\n\nTitle: {title}"}]
        }
    )
    answer = response.json()["choices"][0]["message"]["content"].strip().upper()
    return "YES" in answer

# --- MAIN ---
all_rows = []

for channel_id in CHANNELS:
    print(f"Fetching videos for {CHANNEL_NAMES[channel_id]}...")
    videos = get_recent_videos(channel_id)
    for video in videos:
        print(f"  Checking: {video['title']}")
        if not is_llm_related(video["title"]):
            print(f"  Skipping (not LLM related)")
            time.sleep(5)
            continue
        print(f"  Processing: {video['title']}")
        transcript = get_transcript(video["id"])
        summary, topics = summarize(transcript, video["title"])
        time.sleep(30)
        all_rows.append({**video, "summary": summary, "topics": topics})

html = build_html(all_rows)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("\nDone! Open index.html in your browser.")

import subprocess
subprocess.run(["git", "add", "index.html"], shell=True)
subprocess.run(["git", "commit", "-m", "update dashboard"], shell=True)
subprocess.run(["git", "push"], shell=True)