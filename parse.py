import requests
import sys
import re
import json
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Read in command line arguments.
file_path = sys.argv[1]
out_path = sys.argv[2]
list_path = sys.argv[3]
# Open a new file to write output to
lines = open(file_path, 'r').read().splitlines()
# Match DOIs in Frontiers URLs.
fdoix = re.compile('10[.][0-9]{4,}[/][f][a-z]{3,}[.][0-9]{3,}[.][0-9]{4,}')
# Match non-standard formatting of journal title in Frontiers site titles.
fjtx = re.compile('\s\|\s.*')
# Match PMID in PubMed URLs.
pmidx = re.compile('\/pubmed\/[0-9]+')
pmtx = re.compile('\/pubmed\/\?term\=[0-9]+')
# Set the base URL for the Entrez summary API.
pmapi_base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=xml&rettype=abstract&id='
# Match DOI in JOCN URLs.
jocnx = re.compile('10\.1162\/jocn\_a\_[0-9]{3,}')

# Scrape input file for URLs
url_list = []
for line in lines:
    # NTS: Consider changing this to a more flexible regex-based search.
    if line.startswith('http'):
        url_list.append(line)
n_urls = len(url_list)
with open(list_path, 'w') as f:
    for item in url_list:
        f.write(item + '\n')
f.close()
print "Found %s URLs." % n_urls

# Loop through URLs
item_tups = []
error_tups = []

# Loop through URLs.
for idx, url in enumerate(url_list):
    print "Processing URL %s of %s." % (idx, n_urls)

    journal = 'other'
    source = 'other'
    
    # If the URL obviously points to a PDF file, note this and move to the next URL.
    if url.endswith('.pdf'):
        print "%s is a PDF." % url
        item_tups.append(('PDF document', 'unknown', 'unknown', 'unknown', url))
        continue
    
    # Attempt to process the URL.
    
    # First, try to identify the source and clean up the URL.
    try:
        # Check if source is Frontiers.
        if 'frontiersin.org' in url:
            source = 'frontiers'
            # Try to scrape the DOI from original URL.
            doi_res = fdoix.search(url)
            # If a DOI was found, generate a clean URL for this item.
            if doi_res:
                fdoi = doi_res.group()
                url = '/'.join(['http://journal.frontiersin.org/article', fdoi, 'full'])
            else:
                pass

        # Check if source is Pubmed.
        if 'ncbi.nlm.nih.gov' and '/pubmed/' in url:
            source = 'pubmed'
            # Try to scrape the PMID from original URL.
            pmid_res = pmidx.search(url)
            pmtx_res = pmtx.search(url)
            # If a PMID was found, generate a clean URL for this item.
            if pmid_res:
                pmid = re.sub(r'\/pubmed\/', '', pmid_res.group())
                url = '/'.join(['http://www.ncbi.nlm.nih.gov/pubmed', pmid])
            elif pmtx_res:
                pmid = re.sub(r'\/pubmed\/\?term\=', '', pmtx_res.group())
                url = '/'.join(['http://www.ncbi.nlm.nih.gov/pubmed', pmid])
            else:
                pass
        


    else:
        try:
            # Attempt to identify article source, and if possible, generate a clean URL.

            
            
                       
            # Check if source is JOCN
            elif 'mitpressjournals.org' and 'jocn' in url:
                source = 'jocn'

            # Parse Pubmed articles
            if source == 'pubmed':
                pmapi_url = ''.join([pmapi_base, pmid])
                try:
                    esummary = requests.get(pmapi_url, timeout=15).text
                except requests.exceptions.RequestException as e:
                    print "Error loading summary info for PMID %s." % pmid
                    item_tups.append(('Unable to load Entrez for PMID %s.' % pmid, url))
                    pass
                else:
                    tree = ET.fromstring(str(esummary.encode('utf-8')))
                    title = tree[0][6].text
                    item_tups.append((title, url))

            # Parse JOCN articles
            elif source == 'jocn':
                doi = jocnx.search(url).group()
                crapi_url = ''.join(['http://api.crossref.org/works/', doi])
                try:
                    refsum = requests.get(crapi_url, timeout=15).text
                except requests.exceptions.RequestException as e:
                    print "Error loading Crossref summary for DOI %s." % doi
                    item_tups.append(('Unable to load CrossRef summary for DOI %s.' % doi, url))
                    pass
                else:
                    refj = json.loads(refsum)
                    title = str(refj.get('message').get('title')[0])
                    item_tups.append((title, url))

            else:
                try:
                    response = BeautifulSoup(requests.get(url, timeout=15).text)       
                except requests.exceptions.RequestException as e:
                    print "Error loading %s." % url
                    pass
                else:
                    site_title = str(response.title.text.encode("utf-8")).strip()
                    if source == 'frontiers':
                        pstrip = re.sub(r'Frontiers\s\|\s', '', site_title)
                        site_title = re.sub(r'\s\|\sFrontiers\sin.*', '', pstrip)
                        fjt_res = fjtx.search(site_title)
                        if fjt_res:
                            suffx = fjt_res.group()
                            if 'Frontiers Research Topic' not in suffx:
                                site_title = re.sub(r'\s\|\s.*', '', site_title)
                    item_tups.append((site_title, url))
        except:
            print "Error processing %s!" % url
            item_tups.append(('Unknown Error', url))
            pass
item_df = pd.DataFrame.from_records(item_tups, columns=['title', 'article_type', 'citations', 'doi', 'url'])
item_df.to_csv(out_path, index=None)



class article

attributes URL, doi, pmid, title, citation, article_type, source
