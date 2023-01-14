#!/usr/bin/env python
# encoding: utf-8
## Module to parse Proquest full-text newspaper files
## Tested with a sample of Ethnic Newswatch files
## Alex Hanna (alex.hanna@gmail.com)

import os
import re
import sys
from datetime import datetime
from nltk.metrics.distance import edit_distance

SEP = "____________________________________________________________"
META = r'([A-Z][A-Za-z- ]*?):'

def parseProquest(filename):
    text = open(filename, 'r').read()

    # Figure out what metadata is being reported
    meta_list = list(set(re.findall('\\n' + META, text))) 

    ## set permanent columns
    header    = ['INTERNAL_ID', 'PUBLICATION', 'DATE', 'TITLE', 'EDITION']

    ## set publication title for null entries
    pub_title = None

    # clean up crud at the beginning of the file
    text = text.replace('\xef\xbb\xbf','') 

    ## Split by Proquest header separator (SEP)
    docs = []
    ids  = []
    for i, d in enumerate(re.split(SEP, text)):
        d = d.strip()
        docs.append(d)
        if re.match(r'Document \d+ of \d+', d):
            ids.append(i)

    # Keep only the commonly occuring metadata
    meta_list = [m for m in meta_list if float(text.count(m)) / len(docs) > .20] 

    articles = []
    skipped  = 0
    ## Begin loop over each article
    for i, f in enumerate(docs):
        if len(f) == 0 or re.match('^Contact us at:', f):
            continue

        meta_dict  = {k : '' for k in header}

        # Split into lines, and clean up the hard returns at the end of each line
        lines = [row.replace('\r\n', '<br/>').strip() for row in f.split('\r\n\r\n') if len(row) > 0]
        
        ## if it's still a big line, split by newlines
        if len(lines) == 1:
            lines = [row for row in f.split('\n\n') if len(row) > 0]

        ## find the meta data
        for line in lines:
            metacheck = re.match('^' + META, line)
            if metacheck and metacheck.group(1) in meta_list:
                meta_dict[metacheck.group(1)] = line.replace(metacheck.group(1) + ': ','')

        ## occasional truncated files
        if 'Title' not in meta_dict:
            skipped += 1
            continue

        if 'Publication date' not in meta_dict:
            if 'Publicationdate' in meta_dict:
                meta_dict['Publication date'] = meta_dict['Publicationdate']
                del meta_dict['Publicationdate']
            else:       
                print(meta_dict)
                sys.exit()

        date = ''
        ## match date to different formats
        if re.match(r'([A-Za-z]{3,4}) (\d{1,2}), (\d{4})$', meta_dict['Publication date']):
            ## Jun 20, 2008 or Sept 04, 2008
            matchobj = re.match(r'([A-Za-z]{3,4}) (\d{1,2}), (\d{4})$', meta_dict['Publication date'])

            month = matchobj.group(1)
            day   = matchobj.group(2)
            year  = matchobj.group(3)

            if len(month) == 4:
                month = month[0:3]

            date = datetime.strptime(" ".join([month, day, year]), "%b %d %Y")
        elif re.match(r'[A-Za-z]{3} \d{4}$', meta_dict['Publication date']):
            ## Jun 2008
            date = datetime.strptime(meta_dict['Publication date'], "%b %Y")
        elif re.match(r'[A-Za-z]{3} \d{4}/[A-Za-z]{3} \d{4}$', meta_dict['Publication date']):
            ## Jun 2008/Jul 2008
            date = datetime.strptime(meta_dict['Publication date'].split('/')[0], "%b %Y")
        elif re.match(r'([A-Za-z]{3})/[A-Za-z]{3} (\d{4})$', meta_dict['Publication date']):
            ## Jun/Jul 2008
            matchobj = re.match(r'([A-Za-z]{3})/[A-Za-z]{3} (\d{4})$', meta_dict['Publication date'])
            date = datetime.strptime("%s %s" % (matchobj.group(1), matchobj.group(2)), "%b %Y")
        elif re.match(r'(Winter|Spring|Summer|Fall) (\d{4})$', meta_dict['Publication date']):
            ## Spring 2007
            matchobj = re.match(r'(Winter|Spring|Summer|Fall) (\d{4})$', meta_dict['Publication date'])
            month = ''
            if matchobj.group(1) == 'Winter':
                month = 'Jan'
            elif matchobj.group(1) == 'Spring':
                month = 'Apr'
            elif matchobj.group(1) == 'Fall':
                month = 'Aug'
            elif matchobj.group(1) == 'Summer':
                month = 'Jun'
            date = datetime.strptime("%s %s" % (month, matchobj.group(2)), "%b %Y")
        elif re.match(r'([A-Za-z]{3}) (\d{1,2})(\-|/)[A-Za-z]{3} \d{1,2}, (\d{4})', meta_dict['Publication date']):
            ## Oct 17-Oct 23, 2007 or Oct 17/Oct 23, 2007
            matchobj = re.match(r'([A-Za-z]{3}) (\d{1,2})(\-|/)[A-Za-z]{3} \d{1,2}, (\d{4})', meta_dict['Publication date'])
            date = datetime.strptime(' '.join([matchobj.group(1), matchobj.group(2), matchobj.group(4)]), '%b %d %Y')
        elif re.match(r'([A-Za-z]{3}) (\d{1,2}), (\d{4})(\-|/)[A-Za-z]{3} \d{1,2}, \d{4}', meta_dict['Publication date']):
            ## Dec 26, 2007-Jan 1, 2008 or Dec 27, 2012/Jan 9, 2013
            matchobj = re.match(r'([A-Za-z]{3}) (\d{1,2}), (\d{4})(\-|/)[A-Za-z]{3} \d{1,2}, \d{4}', meta_dict['Publication date'])
            date = datetime.strptime(' '.join([matchobj.group(1), matchobj.group(2), matchobj.group(3)]), '%b %d %Y')
        elif re.match(r'([A-Za-z]{3}) (\d{1,2})\-\d{1,2}, (\d{4})', meta_dict['Publication date']):
            ## Aug 6-12, 2009
            matchobj = re.match(r'([A-Za-z]{3}) (\d{1,2})\-\d{1,2}, (\d{4})', meta_dict['Publication date'])
            date = datetime.strptime(' '.join([matchobj.group(1), matchobj.group(2), matchobj.group(3)]), '%b %d %Y')
        elif re.match(r'(\d{4})', meta_dict['Publication date']):
            ## 2005
            matchobj = re.match(r'(\d{4})', meta_dict['Publication date'])
            date = datetime.strptime('Jan 1 ' + matchobj.group(1), '%b %d %Y')
        else:
            print("WARNING: Date not valid: %s" % meta_dict['Publication date'])
            continue

        ## store publication title in case it's not in file
        if 'Publication title' in meta_dict:
            pub_title = meta_dict['Publication title']

        ## put everything in the metadata dictionary
        meta_dict['PUBLICATION'] = pub_title
        meta_dict['DATE'] = date.strftime("%Y-%m-%d")
        meta_dict['TITLE'] = meta_dict['Title']
        meta_dict['DOCSOURCE'] = "Proquest (%s)" % filename

        if 'Full text' in meta_dict:
            meta_dict['TEXT'] = meta_dict['Full text']
            meta_dict['TEXT'] = '<br/>'.join(meta_dict['TEXT'].split('\n'))
            del meta_dict['Full text']            
        else:
            skipped += 1
            continue

        if ids:
            meta_dict['INTERNAL_ID'] = "%s_%s_%s" % (pub_title, date, ids[i])
        else:
            meta_dict['INTERNAL_ID'] = "%s_%s_%s" % (pub_title, date, i)

        ## Solr doesn't seem to like this
        if 'Pages' in meta_dict:
            del meta_dict['Pages']

        ## remove spaces
        for field in ['Last updated', 'ProQuest document ID', 'ISSN', 'Publication year', 'Volume']:
            if field in meta_dict:
                meta_dict[field] = meta_dict[field].replace(' ', '')
                meta_dict[field] = meta_dict[field].replace('X', '')
            
        articles.append(meta_dict)

    print("\tAdded %d, Skipped %d." % (len(articles), skipped))
    return articles
