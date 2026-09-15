"""
এই মডিউল YouTube Data API v3 ব্যবহার করে বর্তমানে ট্রেন্ডিং ভিডিওগুলোর
তথ্য নিয়ে আসে (টাইটেল, চ্যানেল, ভিউ, ট্যাগ ইত্যাদি)।

YouTube Data API কী ফ্রিতে Google Cloud Console থেকে নেওয়া যায়:
https://console.cloud.google.com/apis/library/youtube.googleapis.com
"""
import logging
from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)


def get_trending_videos(max_results: int = 15, region_code: str | None = None) -> list[dict]:
    """
    YouTube-এ বর্তমানে সবচেয়ে জনপ্রিয় (mostPopular) ভিডিওগুলোর লিস্ট রিটার্ন করে।
    প্রতিটা আইটেমে থাকবে: title, channel, views, tags, category_id, url
    """
    if not config.YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY সেট করা নেই, YouTube trending স্কিপ করা হচ্ছে।")
        return []

    region_code = region_code or config.YOUTUBE_REGION_CODE

    try:
        youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region_code,
            maxResults=max_results,
        )
        response = request.execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("YouTube API কল করতে সমস্যা হয়েছে: %s", exc)
        return []

    videos = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        videos.append(
            {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "views": int(stats.get("viewCount", 0)),
                "tags": snippet.get("tags", [])[:10],
                "category_id": snippet.get("categoryId", ""),
                "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
            }
        )

    # ভিউ অনুযায়ী সাজানো (বেশি ভিউ আগে)
    videos.sort(key=lambda v: v["views"], reverse=True)
    return videos


def search_videos_by_keyword(keyword: str, max_results: int = 10) -> list[dict]:
    """নির্দিষ্ট কোনো বিষয় নিয়ে সাম্প্রতিক জনপ্রিয় ভিডিও খুঁজে বের করে।"""
    if not config.YOUTUBE_API_KEY:
        return []

    try:
        youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        search_request = youtube.search().list(
            part="snippet",
            q=keyword,
            type="video",
            order="viewCount",
            maxResults=max_results,
        )
        response = search_request.execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("YouTube keyword search-এ সমস্যা: %s", exc)
        return []

    results = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        results.append(
            {
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
    return results
