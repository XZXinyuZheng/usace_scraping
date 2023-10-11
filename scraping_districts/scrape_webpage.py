import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

def get_web_expire_date(soup):
    """
    Get the public notice expiration date
    """
    
    if soup.find("div", "expire") is None:
        web_expire_date = None
    else:
        try:
            web_expire_date = re.search(r'(?<=:\s).+', soup.find_all("div", "expire")[0].get_text()).group()
        except Exception as e:
            web_expire_date  = "ERROR: " + str(e)
    return web_expire_date


def get_web_pdf_url(soup):
    """
    Get the pdf url for the public notice
    """
    
    try:
        pdf_end = soup.findAll('a', {"class": "link"})[2]['href']
        pdf_url = "https://www.mvn.usace.army.mil" + pdf_end
    except Exception as e:
        pdf_url = "ERROR: " + str(e)
    finally:
        return pdf_url

    
# def get_web_special(soup):
#     try:
#         notice_type = soup.find_all("a", {"class":"link"})[2].get_text()
#         if "Special" in notice_type:
#             special_public_notice = "Yes"   
#         else:
#             special_public_notice = "No"
#     except Exception as e:
#         special_public_notice = "ERROR: " + str(e)
#     finally:
#         return special_public_notice

    
def get_web_text(soup):
    """
    Get all web texts
    """
    
    try:
        body = soup.find_all("div", {"itemprop": "articleBody"})[0]
        if body.find("p") is None:
            web_text = body.get_text()
        else:
            web_text = body.get_text().replace(u'\xa0', u'').replace("\n", "")
    except:
        web_text = "Error"
    finally:
        return web_text

    
def get_web_applicant(web_text):
    """
    Get all info in "NAME OF APPLICANT"
    """
    
    if any(w in web_text for w in ["APPLICANT", "Applicant"]):
        try:
            web_applicant_contents = re.search(r'(?<=(APPLICANT|Applicant):)\s*.+(?=(LOCATION|Location))', web_text).group().strip()
        except Exception as e:
            web_applicant_contents = "Error: " + str(e)
    else:
        web_applicant_contents = None
    return web_applicant_contents


def get_web_location(web_text):
    """
    Get all info in "LOCATION OF WORK"
    """
    
    if any(w in web_text for w in ["LOCATION", "Location"]):
        try:
            web_location = re.search(r'(?<=(LOCATION OF WORK|Location of Work):)\s*.+(?=(CHARACTER OF WORK|Character of Work))', web_text).group().strip()
        except Exception as e:
            web_location = "ERROR: " + str(e)
    else:
        web_location = None
    return web_location
        
    
def get_web_character_mitigation(web_text):
    """
    Get all info in "CHRACATER OF WORK"
    """
    
    if any(w in web_text for w in ["MITIGATION", "Mitigation"]):
        if any(w in web_text for w in ["CHARACTER", "Character"]):
            try:
                web_character = re.search(r'(?<=(CHARACTER OF WORK|Character of Work):)\s*.+?(?=(MITIGATION|Mitigation))', web_text).group().strip()
            except Exception as e:
                web_character = "ERROR: " + str(e)
        else:
            web_character = None
        try:
            web_mitigation = re.search(r'(?<=(MITIGATION|Mitigation):)\s*.+', web_text).group().strip()
        except Exception as e:
            web_mitigation = "ERROR: " + str(e)
    else:
        web_mitigation = None
        if any(w in web_text for w in ["CHARACTER", "Character"]):
            try:
                web_character = re.search(r'(?<=(CHARACTER OF WORK|Character of Work):)\s*.+', web_text).group().strip()
            except Exception as e:
                web_character = "ERROR: " + str(e)
        else:
            web_character = None
    return web_character, web_mitigation        


def web_extraction(web_url, update):
    """
    This function consists of all the components above to extract fields from the public notice website.
    
    update can take two values: 1 and 0; 
    1 means running this function for the updating purpose; 
    0 means running this function for the first time to scrape all public notices
    """
    
    req = requests.get(web_url)
    content = req.text
    soup = BeautifulSoup(content, 'html.parser')
    
    # Get pdf urls and expiration date from website only when updating from rss feed
    
    if update == 1:
        # Get the pdf links
        pdf_url = get_web_pdf_url(soup)

        # Get expiration date
        web_expire_date = get_web_expire_date(soup)

    # Extract webpage body
    web_text = get_web_text(soup)

    if web_text != "Error":

        # Get applicant and contractor
        web_applicant = get_web_applicant(web_text)

        # Get location
        web_location = get_web_location(web_text)

        # Get character of work and mitigation if any
        web_character_mitigation = get_web_character_mitigation(web_text)
        
    else:
        # Assign "Error" to all fields inside of website body.
        web_applicant = "ERROR"
        web_location = "ERROR"
        web_character_mitigation = "ERROR", "ERROR"
    
    if update == 1:
        return [pdf_url, web_expire_date, web_applicant, web_location, web_character_mitigation[0], \
                web_character_mitigation[1]]
    else:
        return [web_applicant, web_location, web_character_mitigation[0], \
        web_character_mitigation[1]]