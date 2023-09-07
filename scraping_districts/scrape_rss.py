import pandas as pd
import feedparser
import requests

# URL of the New Orleans RSS feed to scrape
rss_url = "https://www.mvn.usace.army.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=4&Site=417&isdashboardselected=0&max=3000"

def rss_update(rss_url):
    """
    Scrape the rss feed of one district website to get updated public notices
    """
    # Parse the RSS feed using feedparser
    rss_parsed = feedparser.parse(rss_url)

    # Create a df to save everything into
    rss_df = pd.DataFrame(rss_parsed.entries)

    # Clean the df for New Orleans
    rss_df = rss_df[["title", "link", "summary", "published"]].rename(
        columns = {"title": "web_title", "link": "web_link", "summary": "web_summary", "published": "published_date"}, 
        copy = False)