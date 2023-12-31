### Overview

This project scrapes public notices in PDFs from the US Army Corps Engineers website and extracts fields from unstructured PDFs into a tabular table, building a data pipeline for a dashboard managed by Atlas Public Policy to analyze the impact of oil and gas projects on wetlands

This project is under development. This repo only includes my individual work, but the actual project is a collaborative effort held in a private repo that will be public once it is done.

### Structure of the Repo

#### scraping_districts

__Output samples__
* galveston_subset.csv
* jacksonville_subset.csv
* mobile_subset.csv
* new_orleans_subset.csv

__Notebooks__
* notebook_galveston.ipynb
* notebook_jacksonville.ipynb
* notebook_mobile.ipynb
* notebook_new_orleans.ipynb

__Functions__
* scrape_pdf.py
* scrape_rss.py
* scrape_webpage.py
* weblist.py

#### archived
* __rss_feed_scrap_replicate.ipynb__: The testing script for New Orleans. The work will move to scraping_districts going forward.
  * __Instruction for running the notebook__: The error messages and scraping results will be automatically recorded in a Google Sheet for troubleshooting, so running the codes will open up a credential page for users to log in. Please log in and authorize the connection. A token file will be automatically generated when running the codes and enable users to reaccess Google Sheets without logging in.
  * __Google sheet__:https://docs.google.com/spreadsheets/d/1VYcmSCuvBMiRRpUusuulIcS4kjkXrTuFZLfKOV_IxkE/edit#gid=0. Google sheet has 5000-character limitation for each cell, so will export output directly in .csv. Please let me know if you have any problems accessing the sheet. (email: xz531@georgetown.edu)
* new_orleans.csv： The output of rss_feed_scrap_replicate.ipynb for field validation.

#### env: dependencies

### Scraping Dictionary

https://docs.google.com/spreadsheets/d/1oNhgk1LZELt5UWMzuQPn84Qz53IMLesxEEY4H4b_eno/edit#gid=0