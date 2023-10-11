import pandas as pd
from bs4 import BeautifulSoup
import requests
import PyPDF2 as pdf
import io
import re

district_dic = {"MVN": "New Orleans District",
               "SWG": "Galveston District",
               "SAM": "Mobile District",
               "SAJ": "Jacksonville District"}

# Seperate pdf texts into big chuncks:


def get_pdf_app_num_dist(pdf_text, district):
    """
    Get permit application # + district code + district Name
    """
    
    try:
        if district == "new_orleans":
            permit_application_number = re.search(r'(?<=Application).*(?=PUBLIC)', \
                                                  pdf_text).group().replace("#", "").replace(":", "").strip()
        elif district == "mobile":
            permit_application_number = re.search(r'(?<=NO\.).*(?=JOINT)', \
                                                  pdf_text).group().strip().replace(" ", "")
        district_code = permit_application_number[0:3]
        district_name = district_dic[district_code]
    except Exception as e:
        permit_application_number = "ERROR: " + str(e)
        district_code = "ERROR: cannot get permit application number"
        district_name = "ERROR: cannot get permit application number"
    finally:
        return permit_application_number, district_code, district_name


def get_pdf_manager(pdf_text):
    """
    Get manager name + phone + email
    """
    
    try:
        manager_name = re.search(r'(?<=Project Manager)[\:a-zA-Z\s\.]*', pdf_text).group().replace(":", "").strip()
    except Exception as e:
        manager_name = "ERROR: " + str(e)
    try:
        manager_phone = re.search(r'\(\d{3}\)\s{1,3}\d{3}\s?-?\s?\d{4}', pdf_text).group().strip()
    except Exception as e:
        manager_phone = "ERROR: " + str(e)
    try:
        manager_email = re.search(r'[\w\.-]+@us\s?a\s?c\s?e\s?\.army\.m\s?i\s?l', pdf_text).group().strip()
    except Exception as e:
        manager_email = "ERROR: " + str(e)
    return manager_name, manager_phone, manager_email


def get_pdf_applicant(pdf_text):
    """ 
    Get all info in "NAME OF APPLICANT"
    """
    
    if pdf_text.find("NAME OF APPLICANT") != -1:
        try:
            pdf_applicant_contents = re.search(r'(?<=(APPLICANT|Applicant):)\s*.+(?=(LOCATION|Location))', pdf_text).group().strip()
            
            # Extract applicant and contractor
            if pdf_applicant_contents.find("c/o") != -1:
                try:
                    applicant = re.search(r'.+?(?=\,* c/o)', pdf_applicant_contents).group().strip()
                except Exception as e:
                    applicant = "ERROR: " + str(e)
                try:    
                    contractor = re.search(r'(?<=c/o( |:)).+?(?=(,?\s?Post|,?\s?PO|,?\s?P\.O\.|,?\s*\d|,?\s?[Aa][tT]))', pdf_applicant_contents).group().strip()
                except Exception as e:
                    contractor = "ERROR: " + str(e)
            else:
                contractor = None
                try:
                    applicant = re.search(r'.+?(?=(,?\s?Post|,?\s?PO|,?\s?P\.O\.|,?\s?\d|,?\s?[Aa][tT]))', pdf_applicant_contents).group().strip()
                except Exception as e:
                    applicant = "ERROR: " + str(e)
                    
        except Exception as e:
            pdf_applicant_contents = applicant = contractor = "Error: " + str(e)
    else:
        pdf_applicant_contents = applicant = contractor = None
        
    return pdf_applicant_contents, applicant, contractor

    
def get_pdf_location(pdf_text):
    """
    Get location of work
    """
    
    if pdf_text.find("LOCATION OF WORK") != -1:
        try:
            pdf_location = re.search(r'((?<=LOCATION OF WORK).*(?=CHARACTER OF WORK))', pdf_text).group().replace(":", "").strip()
        except Exception as e:
            pdf_location = "ERROR: " + str(e)
    else:
        pdf_location = None
    return pdf_location

 
def get_pdf_character(pdf_text):
    """
    Get character of work
    """
    
    if pdf_text.find("CHARACTER OF WORK") != -1:
        try:
            pdf_character = re.search(r'((?<=CHARACTER OF WORK).*(?=(MITIGATION|The comment period)))', pdf_text).group().replace(":", "").strip()
        except Exception as e:
            pdf_character = "ERROR: " + str(e)
    else:
        pdf_character = None
    return pdf_character


# Extract fields from paragraphs

## From location of work

def get_pdf_county_parish(pdf_text):
    """
    Get county or parish name
    """
    
    if pdf_text.find("County") != -1:
        try:
            county = re.search(r'((?<=, ).*County)', pdf_text).group().strip()
        except Exception as e:
            county = "ERROR: " + str(e)
    else:
        county = None
    if pdf_text.find("Parish") != -1:
        try:
            parish = re.search(r'((?<=in ).{1,100}(?= Parish))', pdf_text).group().strip()
        except Exception as e:
            parish = "ERROR: " + str(e)
    else:
        parish = None
    return county, parish


def get_pdf_hydrologic(pdf_text):
    """
    Get hydrologic unit code
    """
    if pdf_text.find(r'Hydrologic Unit Code') != -1:
        try:
            hydrologic_unit_code = re.search(r'(?<=Hydrologic Unit Code(:|\s))[\s|\d]*', pdf_text).group().strip()
        except Exception as e:
            hydrologic_unit_code = "ERROR: " + str(e)
    else:
        hydrologic_unit_code = None
    return hydrologic_unit_code


def get_lon_lat(pdf_text):
    """
    Get longitude and latitude
    """
    
    if any(w in pdf_text for w in ["Longitude", "long"]):
        try:
            lon = re.findall(r'(?<=[-W])\s*\d{2}\.\d+', pdf_text)
        except Exception as e:
            lon = "ERROR: " + str(e)
    else:
        lon = None
    if any(w in pdf_text for w in ["Latitude", "lat"]):
        try:
            lat = re.findall(r"(?<=[^-W][^-\d])\d{2}\.\d+", pdf_text)
        except Exception as e:
            lat = "ERROR: " + str(e)
    else:
        lat = None
    return lon, lat


## From character of work

def get_pdf_acreage(pdf_text):
    """
    Get impacted acreage
    """
    
    if all(w in pdf_text for w in ["acre", "impact"]):
        try:
            acreage = re.findall(r'(\d*\.\d*-?\s?(?=acres of))', pdf_text)
            acreage = [a.strip() for a in acreage]
            # wetland_type = re.search(r'(?<=acres of).+? wetlands', pdf_text).group().strip()
        except Exception as e:
            acreage = "ERROR: " + str(e)
            # wetland_type = "ERROR: " + str(e)
    else:
        acreage = None
        # wetland_type = None
    return acreage


# Others

def get_wqc(pdf_text):
    """
    Get the Water Quality Certificant
    """
    
    if pdf_text.find("WQC") != -1:
        try:
            wqc = re.search(r'(?<=WQC)[\d\s\:]*-[\s\d]*', pdf_text).group().strip().replace(" ", "")
        except Exception as e:
            wqc = "ERROR: " + str(e)
    else:
        wqc = None
    return wqc


def get_coastal_use_permit(pdf_text):
    """
    Get the coastal use permit numbers
    """
    
    if pdf_text.find("Natural Resource’s Coastal Resources Program") != -1:
        try:
            coastal_use_permit_list = re.findall(r'P\d{8}', pdf_text)
            coastal_use_permit = ", ".join(coastal_use_permit_list)
        except Exception as e:
            coastal_use_permit = "ERROR: " + str(e)
    else:
        coastal_use_permit = None
    return coastal_use_permit


# Read pdf

def pdf_read(pdf_url):
    """
    Read pdf into python
    """
    
    try:
        # Download the PDF content as a bytes object
        pdf_bytes = requests.get(pdf_url).content

        # Create a PyPDF2 PdfFileReader object from the PDF content
        pdf_reader = pdf.PdfReader(io.BytesIO(pdf_bytes))

        # Extract text from all pages except appendix in the PDF file
        pdf_full = []
        for p in range(len(pdf_reader.pages)):
            pdf_p = pdf_reader.pages[p].extract_text()
            pdf_full.append(pdf_p)
            if "Enclosure" in pdf_p:
                break

        pdf_text = "".join(pdf_full).replace("\n", "")
        
    except Exception as e:
        pdf_text = "ERROR: " + str(e)
    finally:
        return pdf_text

    
# FINAL FUNCTION (COMBINED)

def pdf_extraction(pdf_url):
    """
    This function consists of all the components above to extract fields from the public notice pdf.
    """
    
    pdf_text = pdf_read(pdf_url)
    
    # standardized public notice
    if  pdf_text.find("ERROR") == -1:

        pdf_app_num_dist = get_pdf_app_num_dist(pdf_text)

        pdf_manager = get_pdf_manager(pdf_text)
        
        pdf_applicant = get_pdf_applicant(pdf_text)

        pdf_location = get_pdf_location(pdf_text)

        if pdf_location is None:
            county = parish = hydrologic_unit_code = lon = lat = None
        elif "ERROR" in pdf_location:
            county = parish = hydrologic_unit_code = lon = lat = "ERROR: cannot extract location of work"
        else:
            county = get_pdf_county_parish(pdf_location)[0]
            parish = get_pdf_county_parish(pdf_location)[1]
            hydrologic_unit_code = get_pdf_hydrologic(pdf_location)
            lon = get_lon_lat(pdf_location)[0]
            lat = get_lon_lat(pdf_location)[1]

        pdf_character = get_pdf_character(pdf_text)

        if pdf_character is None:
            acreage = None
        elif "ERROR" in pdf_character:
            acreage = "ERROR: cannot extract character of work"
        else:
            acreage = get_pdf_acreage(pdf_character)
        
        wqc = get_wqc(pdf_text)
        
        cup = get_coastal_use_permit(pdf_text)
    
    # Special public notice
    else:
        pdf_app_num_dist = ["ERROR: fail to read pdf " + pdf_text]*3
        pdf_manager = ["ERROR: fail to read pdf " + pdf_text]*3
        pdf_applicant = ["ERROR: fail to read pdf " + pdf_text]*3
        pdf_location = pdf_character = county = parish = hydrologic_unit_code = lon = lat = acreage = wqc = cup = "ERROR: fail to read pdf " + pdf_text
        
    return [pdf_app_num_dist[0], pdf_app_num_dist[1], pdf_app_num_dist[2], pdf_manager[0], pdf_manager[1], \
            pdf_manager[2], pdf_applicant[0], pdf_applicant[1], pdf_applicant[2], pdf_location, pdf_character,\
            county, parish, hydrologic_unit_code, lon, lat, acreage, wqc, cup]