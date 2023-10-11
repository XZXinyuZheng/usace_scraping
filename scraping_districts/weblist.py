import pandas as pd
import numpy as np
import feedparser
from bs4 import BeautifulSoup
import requests
import PyPDF2 as pdf
import re

def get_item(soup, item_i, district):
    """
    Extract each items in each page of district website
    """
    item = soup.find_all("div", class_="desc")[item_i]
    web_url = item.find("a", class_="title").get("href")
    web_title = item.find("a", class_="title").get_text()
    publish_date = item.time.get("datetime")
    try:
        expire_date = item.find("p", class_="standout").get_text().replace("Expiration date: ", "")
    except Exception as e:
        expire_date = None
        #print(page_p, item_i, str(e))
    try:
        pdf_end = item.find("div", class_="attachment").a.get("href")
        if district == "jacksonville":
            pdf_url = pdf_end
        else:
            pdf_url = "https://www.sam.usace.army.mil/" + pdf_end
    except Exception as e:
        pdf_url = None
        #print(page_p, item_i, str(e))
    return [web_url, web_title, publish_date, expire_date, pdf_url]


def get_page(url, page_p, district):
    """
    Scrape the main public notice website by page
    """
    main_url = url + "?page=" + str(page_p)
    content = requests.get(main_url).text
    soup = BeautifulSoup(content, 'html.parser')
    item_num = len(soup.find_all("div", class_="desc"))
    
    # Scrape all the public notices item in one district website page
    web_singlepage_df = pd.DataFrame([get_item(soup, i, district) for i in range(0, item_num)], 
                                 columns = ["web_link", "web_title", "published_date", "web_expire_date", "pdf_url"])
    return web_singlepage_df

        
def get_web_list(url, district):
    """
    Scrape the list of public notice webpages for one district USACE website.
    """
    # Check how many pages there are in the website
    check_content = requests.get(url).text
    check_soup = BeautifulSoup(check_content, 'html.parser')
    page_num = int(check_soup.find_all("a", class_="page-link")[-1].string)
    
    # Get a list of public notice pages of all pages
    web_allpage_list = [get_page(url, p, district) for p in range(1, page_num + 1)]
    
    # Convert the list to a dataframe
    web_df = pd.concat(web_allpage_list, axis = 0, ignore_index = True)
        
    return web_df