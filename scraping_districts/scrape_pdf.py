import pandas as pd
from bs4 import BeautifulSoup
import requests
import PyPDF2 as pdf
import io
import re
import nltk



# Read pdf

def pdf_read(pdf_url, district):
    """
    Read pdf
    """
    
    try:
        # Download the PDF content as a bytes object
        pdf_bytes = requests.get(pdf_url).content

        # Create a PyPDF2 PdfFileReader object from the PDF content
        pdf_reader = pdf.PdfReader(io.BytesIO(pdf_bytes))

        # Extract text from all pages except appendix in the PDF file
        pdf_full = []
        for p in range(len(pdf_reader.pages)):
            pdf_p = pdf_reader.pages[p].extract_text().replace("\n", "")
            
            # Remove the footer for public notices from new_orleans District
            if district == "new_orleans" and p != 0:
                pdf_p = re.sub(r'-?' + str(p+1) + '-?', "", pdf_p)
            
            # Remove the header for public notices from Mobile District
            if district == "mobile" and p != 0:
                pdf_header = re.search(r'.*Page \d of \d', pdf_p).group()
                pdf_p = pdf_p.replace(pdf_header, "")
            
            # Remove the footer for public notices from Galveston District
            if district == "galveston" and p != 0:
                try:
                    pdf_header = re.search(r'.*?\s{5,}' + str(p+1), pdf_p).group()
                except:
                    try:
                        pdf_header = re.search(r'.*?#.*?\d{5}.*?\s{2}', pdf_p).group()
                    except Exception as e:
                        pdf_header = "ERROR"
                if "ERROR" not in pdf_header:
                    pdf_p = pdf_p.replace(pdf_header, "")

            pdf_full.append(pdf_p)
            
            # Remove attachments(pictures) to speed up the reading process
            if district in ["new_orleans", "mobile"] and any(w in pdf_p for w in ["Enclosure", "Attachment"]):
                break
            if district == "jacksonville" and "REQUEST FOR PUBLIC HEARING" in pdf_p:
                break

        pdf_text = "".join(pdf_full)
        
    except Exception as e:
        pdf_text = "ERROR: " + str(e)
        
    finally:
        return pdf_text
    
    
    

# Seperate pdf texts into big chuncks:

def get_comment_window(pdf_text, district):
    """
    Get the comment window (days)
    """
    if "days" in pdf_text:
        try:
            if district == "new_orleans":
                comment_window = re.search(r'(?<=close)\s?i?n?[\s\d]*(?=days)', 
                                           pdf_text).group().replace("in", "").strip().replace(" ", "")
            if district == "mobile":
                comment_window = re.search(r'(?<=later than)[\s\d]*(?=days)', 
                                           pdf_text).group().strip().replace(" ", "")
            if district == "jacksonville":
                comment_window = re.search(r'(?<=within)[\s\d]*(?=days)', 
                                           pdf_text).group().strip().replace(" ", "")
            if district == "galveston":
                comment_window = re.search(r'(?<=within)[\s\d]*(?=days)', 
                                           pdf_text).group().strip().replace(" ", "")
        except Exception as e:
            comment_window = "ERROR: " + str(e)
    else:
        comment_window = None
        
    return comment_window




district_dic = {"MVN": "New Orleans District",
               "SWG": "Galveston District",
               "SAM": "Mobile District",
               "SAJ": "Jacksonville District"}

def get_pdf_app_num_dist(pdf_text, district):
    """
    Get permit application # + district code + district Name
    """
    
    try:
        if district == "new_orleans":
            permit_application_number = re.search(r'(Application|Subject).*(?=PUBLIC)', \
                                                  pdf_text).group().replace("#", "").replace(
                                                  ":", "").replace("Number", "").replace(
                                                  "Application", "").replace("Subject", "").strip().replace(
                                                  " ", "")
        if district == "mobile":
            permit_application_number = re.search(r'(?<=NO\.).*(?=JOINT)', \
                                                  pdf_text).group().replace(" ", "")
        if district == "jacksonville":
            permit_application_number = re.search(r'(?<=No\.).*?(?=\()', \
                                      pdf_text).group().replace(" ", "")
        if district == "galveston":
            permit_application_number = re.search(r'(?<=No:).*?(?=Of)', \
                                      pdf_text).group().replace(" ", "")
        district_code = permit_application_number[0:3]
        district_name = district_dic[district_code]
    except Exception as e:
        permit_application_number = "ERROR: " + str(e)
        district_code = "ERROR: cannot get permit application number"
        district_name = "ERROR: cannot get permit application number"
    finally:
        return permit_application_number, district_code, district_name

    
    

def get_pdf_manager(pdf_text, district):
    """
    Get manager name + phone + email
    """
 
    # Manager name
    if district == "new_orleans":
        try:
            manager_name = re.search(r'(?<=Project Manager)[\:a-zA-Z\s\.]*', \
                                         pdf_text).group().replace(":", "").strip()
        except Exception as e:
            manager_name = "ERROR: " + str(e)
    
    ## For Mobile, Jacksonville, and Galveston, first, get the paragraph containing manager information because the information is at the end of the pdf, which may be in duplicated formatting with previous texts.

    try:
        if district == "mobile":
            para_manager = re.search(r'directed to.*(?=Copies|copy)',
                                     pdf_text).group().strip()
        if district == "jacksonville":
            para_manager = re.search(r'QUESTIONS.*?\d{4}\.', pdf_text).group().strip()
        if district  == "galveston":
            para_manager = re.search(r'(?<=submitted to:).*?(?=DISTRICT)', pdf_text).group().strip()
    except Exception as e:
        para_manager = "ERROR: " + str(e)
            

    if district in ("mobile", "jacksonville"):
        if para_manager.find("ERROR") == -1:
            try:
                manager_name = re.search(r'(Attention|project manager\,).*?(?=(\,|or|by))', 
                                         para_manager).group().replace("Attention", "").replace(
                                         "project manager", "").replace(",", "").replace(":", "").strip()
            except Exception as e:
                manager_name = "ERROR: " + str(e)
        else:
            manager_name = "ERROR: fail to get the paragraph containing manager information"

    if district == "galveston":
        if para_manager.find("ERROR") == -1:
            try:
                manager_name = re.search(r'.*Galveston District', para_manager).group().strip()
            except Exception as e:
                manager_name = "ERROR: " + str(e)
            pdf_text = para_manager
        else:
            manager_name = pdf_text = "ERROR: fail to get the paragraph containing manager information" 

    
    # Manager phone number
    try:
        manager_phone = re.search(r'\(?\d{3}\)?-?\s{0,3}-?\d{3}\s?-?\s?\d{4}', 
                                  pdf_text).group().strip().replace(" ", "")
    except Exception as e:
        manager_phone = "ERROR: " + str(e)

    # Manager email address
    try:
        manager_email = re.search(r'[\w\.-]+\s?@us\s?a\s?c\s?e\s?\.army\.m\s?i\s?l',
                                  pdf_text).group().strip().replace(" ", "")
    except Exception as e:
        manager_email = "ERROR: " + str(e)
        
    return manager_name, manager_phone, manager_email




def get_pdf_applicant(pdf_text, district):
    """ 
    Get all info in "NAME OF APPLICANT"
    """
    
    if district == "new_orleans":
        if pdf_text.find("NAME OF APPLICANT") != -1:
            try:
                pdf_applicant_contents = re.search(r'(?<=(APPLICANT|Applicant)).+(?=(LOCATION|Location))',
                                                   pdf_text).group().replace(":", "").replace("  ", " ").strip()

                # Extract applicant and contractor
                if pdf_applicant_contents.find("c/o") != -1:
                    try:
                        applicant = re.search(r'.+?(?=\,* c/o)', pdf_applicant_contents).group().strip()
                    except Exception as e:
                        applicant = "ERROR: " + str(e)
                    try:    
                        contractor = re.search(r'(?<=c/o( |:)).+?(?=(,?\s?Post|,?\s?PO|,?\s?P\.O\.|,?\s*\d|,?\s?[Aa][tT]))', \
                                               pdf_applicant_contents).group().strip()
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
    
    if district == "mobile":
        if pdf_text.find("APPLICANT") != -1:
            try:
                pdf_applicant_contents = re.search(r'APPLICANT.+(?=LOCATION)', 
                                                   pdf_text).group().replace("  ", " ").strip()
            except Exception as e:
                pdf_applicant_contents = "ERROR: " + str(e)
            try:
                applicant = re.search(r'(?<=APPLICANT).+?(?=Attention)', pdf_text).group().replace(":", "").strip()
            except Exception as e:
                applicant = "ERROR: " + str(e)
        else:
            pdf_applicant_contents = applicant = None
        if pdf_text.find("AGENT") != -1:
            try:
                contractor = re.search(r'(?<=AGENT).+?(?=Attention)', pdf_text).group().replace(":", "").strip()
            except Exception as e:
                contractor = "ERROR: " + str(e)
        else:
            contractor = None
            
    if district == "jacksonville":
        if pdf_text.find("APPLICANT") != -1:
            try:
                pdf_applicant_contents = re.search(r'(?<=APPLICANT:)\s*.+?(?=WATER)', 
                                                   pdf_text).group().replace("  ", " ").strip()

                # Extract applicant and contractor                    
                try:
                    applicant = re.search(r'.+?(?=(Post|PO|P\.O\.|\d|c/o|Attn|Attention))', 
                                          pdf_applicant_contents).group().strip()
                except Exception as e:
                    applicant = "ERROR: " + str(e)
                contractor = None

            except Exception as e:
                pdf_applicant_contents = applicant = contractor = "Error: " + str(e)
        else:
            pdf_applicant_contents = applicant = contractor = None
            
        
    if district == "galveston":
        if pdf_text.find("APPLICANT") != -1:
            try:
                pdf_applicant_contents = re.search(r'APPLICANT.+(?=LOCATION)', 
                                                   pdf_text).group().replace("  ", " ").strip()
            except Exception as e:
                pdf_applicant_contents = "ERROR: " + str(e)
            try:
                applicant = re.search(r'(?<=APPLICANT).+?(?=(Post|PO|P\.O\.|\d|c/o|Attn|Attention))',
                                      pdf_text).group().replace(":", "").strip()
            except Exception as e:
                applicant = "ERROR: " + str(e)
        else:
            pdf_applicant_contents = applicant = None
        if pdf_text.find("AGENT") != -1:
            try:
                contractor = re.search(r'(?<=AGENT).+?(?=(Post|PO|P\.O\.|\d|c/o|Attn|Attention|LOCATION))',
                                       pdf_text).group().replace(":", "").strip()
            except Exception as e:
                contractor = "ERROR: " + str(e)
        else:
            contractor = None
            
    return pdf_applicant_contents, applicant, contractor



    
def get_pdf_location(pdf_text, district):
    """
    Get location of work
    """
    
    if pdf_text.find("LOCATION") != -1:
        if district == "new_orleans":
            try:
                pdf_location = re.search(r'((?<=LOCATION OF WORK).*(?=CHARACTER OF WORK))', \
                                         pdf_text).group().replace(":", "").replace("  ", " ").strip()
            except Exception as e:
                pdf_location = "ERROR: " + str(e)
                
        if district  == "mobile":
            try:
                pdf_location = re.search(r'((?<=LOCATION).*(?=(PROJECT|PROPOSED|APPLICANT|WORK)))', \
                                         pdf_text).group().replace(":", "").replace("  ", " ").strip()
            except Exception as e:
                pdf_location = "ERROR: " + str(e)
                
        if district == "jacksonville":
            try:
                pdf_location = re.search(r'(?<=LOCATION).*(?=Directio\s?ns)', \
                                         pdf_text).group().replace(":", "").replace("  ", " ").strip()
            except Exception as e:
                pdf_location = "ERROR: " + str(e)
                
        if district == "galveston":
            try:
                pdf_location = re.search(r'(?<=LOCATION).*(?=LATITUDE|AGENDA)', \
                                         pdf_text).group().replace(":", "").replace("  ", "").strip()
            except Exception as e:
                pdf_location = "ERROR: " + str(e)
                
    else:
        pdf_location = None
    return pdf_location

 
    
    
def get_pdf_character(pdf_text, district):
    """
    Get character of work
    """
    
    if district == "new_orleans":
        if pdf_text.find("CHARACTER OF WORK") != -1:
            try:
                pdf_character = re.search(r'(?<=CHARACTER OF WORK).*?(?=(MITIGATION|The comment\s*p\s*eriod))',
                                          pdf_text).group().replace(":", "").replace("  ", " ").strip()
            except Exception as e:
                pdf_character = "ERROR: " + str(e)
        else:
            pdf_character = None
            
    if district in ("mobile", "jacksonville"):
        if pdf_text.find("WORK") != -1:
            try:
                pdf_character = re.search(
                    r'(PROPOSED WORK|WORK DESCRIPTION|WORK).*?(?=(AVOIDANCE|COASTAL|The applicant has applied))',
                    pdf_text).group()
                pdf_character = pdf_character.replace(":", "").replace("  ", " ").replace(
                    "PROPOSED WORK", "").replace("WORK DESCRIPTION", "").replace("WORK", "").strip()
            except Exception as e:
                pdf_character = "ERROR: " + str(e)
        else:
            pdf_character = None
            
    if district == "galveston":
        if pdf_text.find("PROJECT DESCRIPTION") != -1:
            try:
                pdf_character = re.search(r'(?<=PROJECT DESCRIPTION).*?(?=[A-Z\s]+:)',
                                          pdf_text).group().replace(":", "").replace("  ", "").strip()
            except Exception as e:
                pdf_character = "ERROR: " + str(e)
        else:
            pdf_character = None
            
    return pdf_character




def get_pdf_mitigation(pdf_text, district):
    """
    Get mitigation
    """
    
    if district == "new_orleans":
        if "MITIGATION" in pdf_text:
            try:
                pdf_mitigation = re.search(r'(?<=MITIGATION).*?(?=The comment period)', 
                                           pdf_text).group().replace(":", "").replace("  ", " ").strip()
            except Exception as e:
                pdf_mitigation = "ERROR: " + str(e)
        else:
            pdf_mitigation = None
    
    if district in ["mobile", "jacksonville", "galveston"]:
        if any(w in pdf_text for w in ["AVOIDANCE & MINIMIZATION", 
                                       "AVOIDANCE AND MINIMIZATION",
                                       "COMPENSATORY MITIGATION", 
                                       "MITIGATION"]):
                # pdf_mitigation = re.search(r'(AVOIDANCE|COMPENSATORY|MITIGATION).*?(?=WATER|The applicant will apply|The applicant has applied|CULTURAL)', pdf_text).group().strip()
            try:
                pdf_avio_mini = re.search(r'MINIMIZATION.+?(?=[A-Z\s]+:)', 
                                     pdf_text).group().replace("  ", "").strip()
            except:
                pdf_avio_mini = "ERROR: AVOIDANCE AND MINIMIZATION"
            try:
                pdf_comp_miti = re.search(r'MITIGATION.+?(?=[A-Z\s]+:)', 
                                     pdf_text).group().replace("  ", "").strip()
            except:
                pdf_comp_miti = "ERROR: COMPENSATORY MITIGATION"
            if "ERROR" not in pdf_avio_mini and "ERROR" not in pdf_comp_miti:
                pdf_mitigation = pdf_avio_mini + " " + pdf_comp_miti
            else:
                pdf_mitigation = "ERROR:" + pdf_avio_mini + pdf_comp_miti
        else:
            pdf_mitigation = None
        
    return pdf_mitigation
                



# Extract fields from paragraphs

## From location of work

# def get_pdf_city_county_parish_MVN_SAM(pdf_text):
#     """
#     Get county, city or parish name for New Orleans and Mobile
#     """
    
#     if pdf_text.find("COUNTY") != -1:
#         try:
#             county = re.search(r'[\w\s]+C\s?ounty', pdf_text).group().strip()
#         except Exception as e:
#             county = "ERROR: " + str(e)
#         try:
#             city = re.search(r'[\w\s]+(?=,\s*' + county + ')', pdf_text).group().strip()
#         except Exception as e:
#             city = "ERROR: " + str(e)
#     else:
#         county = None
#         city = None
#     if pdf_text.find("PARISH") != -1:
#         try:
#             parish = re.search(r'((?<=(IN|in)).{1,50}PARISH)', pdf_text).group().strip()
#             #parish = re.search(r'((?<=in).{1,100}(?= Parish))', pdf_text).group().strip()
#         except Exception as e:
#             parish = "ERROR: " + str(e)
#     else:
#         parish = None
            
#     return county, parish, city




def get_pdf_city_county_parish(pdf_location):
    """
    Get county, city, and parish name
    """
    
    loc_sent_list = nltk.sent_tokenize(pdf_location)
    
    county_list = []
    city_list = []
    
    for sent in loc_sent_list:
        if any(x in sent for x in ["Louisiana", "LA", "Alabama", "AL", "Florida", "FL", "Texas", "TX"]):
            if any(w in sent for w in ["County", "C ounty"]):
                try:
                    county = re.search(r'(,|\sin)([\w\s]+C\s?ounty)', sent).group(2).strip()
                except Exception as e:
                    county = "ERROR: " + str(e)
                if "ERROR" not in county:
                    try:
                        city = re.search(r'(in|near)([\w\s]+)(?=,\s*' + county + ')', 
                                         sent).group(2).strip()
                    except Exception as e:
                        city = "ERROR: " + str(e)
                    county = county.replace("in", "").strip()
                    if "ERROR" not in city and len(city) > 25:
                        city = "Might be ERROR: " + city
                else:
                    city = "ERROR: fail to pull county"
            else:
                county = None
                try:
                    city = re.search(
                        r'(entitled|in|near):?([\w\s]+)(?=,?\s?(Louisiana|LA|Alabama|AL|Florida|FL|Texas|TX))', 
                        sent).group(2).strip()
                except Exception as e:
                    city = "ERROR: " + str(e)
                    
            county_list.append(county)
            city_list.append(city)
            
            if "Parish" in sent:
                try:
                    parish = re.search(r'(?<=in).{1,50}Parish', sent).group().strip()
                except Exception as e:
                    parish = "ERROR: " + str(e)
            else:
                parish = None
                    
    return county_list, parish, city_list




def get_pdf_hydrologic(pdf_text):
    """
    Get hydrologic unit code
    """
    if pdf_text.find(r'Hydrologic Unit Code') != -1:
        try:
            hydrologic_unit_code = re.search(r'(?<=Hydrologic Unit Code(:|\s))[\s|\d]*', pdf_text).group().strip().replace(" ", "")
        except Exception as e:
            hydrologic_unit_code = "ERROR: " + str(e)
    else:
        hydrologic_unit_code = None
    return hydrologic_unit_code




def get_lon_lat_MVN_SAM(pdf_location):
    """
    Get longitude and latitude for New Orleans and Mobile districts
    """
    
    if any(w in pdf_location for w in ["Longitude", "long"]):
        try:
            lon = re.findall(r'(?<=[-W])\s*\d{2}\.\d+', pdf_location)
        except Exception as e:
            lon = "ERROR: " + str(e)
        if "ERROR" not in lon:
            lon = [i.strip() for i in lon]
    else:
        lon = None
    if any(w in pdf_location for w in ["Latitude", "lat"]):
        try:
            lat = re.findall(r"(?<=[^-W][^-\d])\d{2}\.\d+", pdf_location)
        except Exception as e:
            lat = "ERROR: " + str(e)
        if "ERROR" not in lat:
            lat = [i.strip() for i in lat]
    else:
        lat = None
        
    return lon, lat




def get_lon_lat_SAJ_SWG(pdf_text):
    """
    Get longitude and latitude for Jacksonville and Galveston
    """
    
    # Longitude
    if "Longitude" in pdf_text:
        try:
            lon = re.findall(r"(?<=Longitude)\s?:?([\s\-\d\.]+)", pdf_text)
        except Exception as e:
            lon = "ERROR: " + str(e)
        if "ERROR" not in lon:
            lon = [i.replace(":", "").strip() for i in lon]
            lon = [i[1:] if i[0] == "0" else i for i in lon]
    else:
        lon = None
    
    # Latitude
    if "Latitude" in pdf_text:
        try:
            lat = re.findall(r"(?<=Latitude)\s?:?([\s\d\.]+)", pdf_text)
        except Exception as e:
            lat = "ERROR: " + str(e)
        if "ERROR" not in lat:
            lat = [i.replace(":", "").strip() for i in lat]
            lat = [i[1:] if i[0] == "0" else i for i in lat]
    else:
        lat = None
    
    # Form coordinate
    # for i in range(0,len(lon))
        
    return lon, lat




## From character of work

def get_pdf_acreage(pdf_character):
    """
    Get impacted acreage
    """
    # Split character of work into sentences
    char_sent_list = nltk.sent_tokenize(pdf_character)
    
    # Create a empty acre output list
    acre_output = []

    # Select sentences containing "impact", "affect", and "loss"
    for i in range(0, len(char_sent_list)):
        if  any(w in char_sent_list[i] for w in ["impact", "affect", "loss"]):
            
            # Break one sentence into pieces with each piece having one subject, one verb, and one object
            # And select piece containing acreage info
            acre_list = re.findall(r'([^,]*.?\d*,?\d*\s?\.?\s?\d*-?\s?acres?.+?\D)(,|\.|\sand)', char_sent_list[i])

            # For each piece, pull acreage number, impacted type, and impacted time length
            def acre_type_term(i):
                # Pull the acreage number r'\d*\s?\.\s?\d*(?=-?\s?acres?\)?)'
                acre = re.search(r'[^A-Za-z]+(?=acres?\)?)', acre_list[i][0]).group()

                # type of impacted areas
                if any(w in acre_list[i][0] for w in ["habitat", "wetland", "we tland", "wetl and", "water", "pond", "marsh", "waterbottom", "water bottom"]):
                    try:
                        acre_type = re.search(
                            r'' + acre + 'acres?\)?(of|to)?(.*?(habitat|we\s?tl\s?and|pond|water\s?bottom|marsh|water))',
                            acre_list[i][0]).group(2).replace("of", "").replace("to", "").strip()
                    except Exception as e:
                        acre_type = "ERROR: " + str(e)
                else:
                    acre_type = None

                # If the impact is permanent or temperary
                if  any(w in acre_list[i][0] for w in ["impact", "affect", "loss", "fill"]) \
                and any(w in acre_list[i][0] for w in ["permanent", "temporar"]):
                    try:
                        acre_term = re.search(r'(permanent[a-z]*\s|temporar[a-z]*\s)', acre_list[i][0]).group().strip()
                    except Exception as e:
                        acre_term = "ERROR: " + str(e)
                else:
                    acre_term = None
                    
                acre = acre.replace(" ", "").replace("-", "").replace(",", "")
                return acre, acre_type, acre_term

            acre_output_part = [acre_type_term(i) for i in range(0, len(acre_list))]
            acre_output = acre_output + acre_output_part
    
    return acre_output




def get_pdf_linear_feet(pdf_character):
    """
    Get impacted linear feet
    """
    
    # Split character of work into sentences
    char_sent_list = nltk.sent_tokenize(pdf_character)
    
    # Create a empty acre output list
    lf_output = []

   # Select sentences containing "impact", "affect", and "loss"
    for i in range(0, len(char_sent_list)):
        if  any(w in char_sent_list[i] for w in ["impact", "affect", "loss"]):
            
            # Break one sentence into pieces with each piece having one subject, one verb, and one object
            # And select piece containing linear feet info
            linear_feet_list = re.findall(r'([^,]*?\d*,?\d*\s?\.?\s?\d*-?\s?linear\sfeet.+?\D)(,|\.|\sand)', char_sent_list[i])
            
            # For each piece, pull linear feet number, impacted type, and impacted time length
            def linear_feet_type_term(i):
                # Pull the linear feet number
                linear_feet = re.search(r'[^A-Za-z]+(?=linear)', linear_feet_list[i][0]).group()

                # What is the type of impacted areas
                if any(w in linear_feet_list[i][0] for w in ["stream"]):
                    try:
                        linear_feet_type = re.search(r'' + linear_feet + '.*(of|to)(.*?(stream))', 
                                                     linear_feet_list[i][0]).group(2).strip()
                    except Exception as e:
                        linear_feet_type = "ERROR: " + str(e)
                else:
                    linear_feet_type = None
                if  any(w in linear_feet_list[i][0] for w in ["impact", "affect", "fill", "loss"]) \
                and any(w in linear_feet_list[i][0] for w in ["permanent", "temporar"]):
                    try:
                        linear_feet_term = re.search(r'(permanent[a-z]*\s|temporar[a-z]*\s)',
                                                     linear_feet_list[i][0]).group().strip()
                    except Exception as e:
                        linear_feet_term = "ERROR: " + str(e)
                else:
                    linear_feet_term = None
                
                linear_feet = linear_feet.replace(" ", "").replace("-", "").replace(",", "")
                return linear_feet, linear_feet_type, linear_feet_term

            lf_output_part = [linear_feet_type_term(i) for i in range(0, len(linear_feet_list))]
            lf_output = lf_output + lf_output_part
    
    return lf_output




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

    
    
    
# FINAL FUNCTION (COMBINED)

def pdf_extraction(pdf_url, district):
    """
    This function consists of all the components above to extract fields from the public notice pdf.
    """
    # print(pdf_url)
    pdf_text = pdf_read(pdf_url, district)
    
    # No PDF reader problem
    if  "ERROR" not in pdf_text:
            
        comment_window = get_comment_window(pdf_text, district)

        pdf_app_num_dist = get_pdf_app_num_dist(pdf_text, district)

        pdf_manager = get_pdf_manager(pdf_text, district)

        pdf_applicant = get_pdf_applicant(pdf_text, district)

        pdf_location = get_pdf_location(pdf_text, district)

        pdf_character = get_pdf_character(pdf_text, district)

        pdf_mitigation = get_pdf_mitigation(pdf_text, district)

        wqc = get_wqc(pdf_text)
        cup = get_coastal_use_permit(pdf_text)
        
        if pdf_location is None:
            hydrologic_unit_code = county = city = parish = None
        elif "ERROR" in pdf_location:
            hydrologic_unit_code = county = city = parish = "ERROR: cannot extract location of work"
        else:
            hydrologic_unit_code = get_pdf_hydrologic(pdf_location)
            county = get_pdf_city_county_parish(pdf_location)[0]
            parish = get_pdf_city_county_parish(pdf_location)[1]
            city = get_pdf_city_county_parish(pdf_location)[2]

        if district in ["new_orleans", "mobile"]:
            if pdf_location is None:
                lon = lat = None
            elif "ERROR" in pdf_location:
                lon = lat = "ERROR: cannot extract location of work"
            else:
                lon = get_lon_lat_MVN_SAM(pdf_location)[0]
                lat = get_lon_lat_MVN_SAM(pdf_location)[1]

        if district in ["jacksonville", "galveston"]:
            lon = get_lon_lat_SAJ_SWG(pdf_text)[0]
            lat = get_lon_lat_SAJ_SWG(pdf_text)[1]

        if pdf_character is None:
            acre_output = lf_output = None
            # acre_dict = {}
            # for i in range(1, 7):
            #     acre_dict["acre{0}".format(i)] = None
            #     acre_dict["acre_type{0}".format(i)] = None
            #     acre_dict["acre_term{0}".format(i)] = None
            # lf_dict = {}
            # for i in range(1, 4):
            #     lf_dict["lf{0}".format(i)] = None
            #     lf_dict["lf_type{0}".format(i)] = None
            #     lf_dict["lf_term{0}".format(i)] = None

        elif "ERROR" in pdf_character:
            acre_output = lf_output = "ERROR: cannot extract character of work " + pdf_character
            # acre_dict = {}
            # for i in range(1, 7):
            #     acre_dict["acre{0}".format(i)] = "ERROR: cannot extract character of work " + pdf_character
            #     acre_dict["acre_type{0}".format(i)] = "ERROR: cannot extract character of work" + pdf_character
            #     acre_dict["acre_term{0}".format(i)] = "ERROR: cannot extract character of work" + pdf_character
            # lf_dict = {}
            # for i in range(1, 4):
            #     lf_dict["lf{0}".format(i)] = "ERROR: cannot extract character of work " + pdf_character
            #     lf_dict["lf_type{0}".format(i)] = "ERROR: cannot extract character of work " + pdf_character
            #     lf_dict["lf_term{0}".format(i)] = "ERROR: cannot extract character of work " + pdf_character

        else:
            acre_output = get_pdf_acreage(pdf_character)
            # acre = get_pdf_acreage(pdf_character)
            # acre_dict = {}
            # for i in range(1, 7):
            #     acre_dict["acre{0}".format(i)] = None
            #     acre_dict["acre_type{0}".format(i)] = None
            #     acre_dict["acre_term{0}".format(i)] = None
            # if len(acre) > 0:
            #     for i in range(0, len(acre)):
            #         acre_dict["acre{0}".format(i+1)] = acre[i][0]
            #         acre_dict["acre_type{0}".format(i+1)] = acre[i][1]
            #         acre_dict["acre_term{0}".format(i+1)] = acre[i][2]
            
            lf_output = get_pdf_linear_feet(pdf_character)
            # lf_dict = {}
            # for i in range(1, 4):
            #     lf_dict["lf{0}".format(i)] = None
            #     lf_dict["lf_type{0}".format(i)] = None
            #     lf_dict["lf_term{0}".format(i)] = None
            # if district == "mobile" or "jacksonville":
            #     lf = get_pdf_linear_feet(pdf_character)
            #     if len(lf) > 0:
            #         for i in range(0, len(lf)):
            #             lf_dict["lf{0}".format(i+1)] = lf[i][0]
            #             lf_dict["lf_type{0}".format(i+1)] = lf[i][1]
            #             lf_dict["lf_term{0}".format(i+1)] = lf[i][2]

        # Special public notice
        if any(w in pdf_text for w in ["Special Public Notice", "SPECIAL"]):
            special = 1
        else:
            if all(item is None for item in [pdf_applicant[0], pdf_location, pdf_character, pdf_mitigation]):
                special = 1
            else:
                special = 0
        
    # else:
    #     special = 1
    #     pdf_app_num_dist = [None]*3
    #     pdf_manager = [None]*3
    #     pdf_applicant = [None]*3
    #     comment_window = pdf_location = pdf_character = pdf_mitigation = county = parish = city = hydrologic_unit_code = lon = lat = wqc = cup = None
    #     acre_dict = {}
    #     for i in range(1, 7):
    #         acre_dict["acre{0}".format(i)] = None
    #         acre_dict["acre_type{0}".format(i)] = None
    #         acre_dict["acre_term{0}".format(i)] = None
    #     lf_dict = {}
    #     for i in range(1, 4):
    #         lf_dict["lf{0}".format(i)] = None
    #         lf_dict["lf_type{0}".format(i)] = None
    #         lf_dict["lf_term{0}".format(i)] = None
     
    # PDF reader problem
    else:
        special = ["ERROR: fail to read pdf " + pdf_text]
        pdf_app_num_dist = ["ERROR: fail to read pdf " + pdf_text]*3
        pdf_manager = ["ERROR: fail to read pdf " + pdf_text]*3
        pdf_applicant = ["ERROR: fail to read pdf " + pdf_text]*3
        comment_window = pdf_location = pdf_character = pdf_mitigation = county = parish = city = hydrologic_unit_code = lon = lat = wqc = cup = "ERROR: fail to read pdf " + pdf_text
        acre_output = lf_output = "ERROR: fail to read pdf " + pdf_text
        # acre_dict = {}
        # for i in range(1, 7):
        #     acre_dict["acre{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        #     acre_dict["acre_type{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        #     acre_dict["acre_term{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        # lf_dict = {}
        # for i in range(1, 4):
        #     lf_dict["lf{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        #     lf_dict["lf_type{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        #     lf_dict["lf_term{0}".format(i)] = "ERROR: fail to read pdf " + pdf_text
        
    return [special, comment_window, pdf_app_num_dist[0], pdf_app_num_dist[1], pdf_app_num_dist[2], \
            pdf_manager[0], pdf_manager[1], pdf_manager[2], pdf_applicant[0], pdf_applicant[1], \
            pdf_applicant[2], pdf_location, pdf_character, pdf_mitigation, \
            county, parish, city, hydrologic_unit_code, lon, lat, wqc, cup, \
            # acre_dict["acre1"], acre_dict["acre_type1"], acre_dict["acre_term1"], \
            # acre_dict["acre2"], acre_dict["acre_type2"], acre_dict["acre_term2"], \
            # acre_dict["acre3"], acre_dict["acre_type3"], acre_dict["acre_term3"], \
            # acre_dict["acre4"], acre_dict["acre_type4"], acre_dict["acre_term4"], \
            # acre_dict["acre5"], acre_dict["acre_type5"], acre_dict["acre_term5"], \
            # acre_dict["acre6"], acre_dict["acre_type6"], acre_dict["acre_term6"], \
            # lf_dict["lf1"], lf_dict["lf_type1"], lf_dict["lf_term1"], \
            # lf_dict["lf2"], lf_dict["lf_type2"], lf_dict["lf_term2"], \
            # lf_dict["lf3"], lf_dict["lf_type3"], lf_dict["lf_term3"], 
            acre_output, lf_output, pdf_text]




def download_pdf_attachment(pdf_url):
    """
    Download PDFs and attachements.
    """
    
    # Download PDFs
    pdf_bytes = requests.get(pdf_url).content
    pdf_name = re.search(r'(?<=public_notices/).*(?=\.pdf)', pdf_url).group()
    open(pdf_name + '.pdf', 'wb').write(pdf_bytes)

    # Extract images in the attachment
    pdf_reader = pdf.PdfReader(io.BytesIO(pdf_bytes))
    for p in range(len(pdf_reader.pages)):
        pdf_page = pdf_reader.pages[p]
        if p != 0 and len(pdf_page.images) != 0:
            open(str(p) + ".png", "wb").write(pdf_page.images[0].data)