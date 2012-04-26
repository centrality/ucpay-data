from collections import namedtuple
import os
import re
import time
import dateutil
import dateutil.tz
import dateutil.parser
import eventlet
from eventlet.green import os as eos

# 1. Author or Authors
# 2. Might specify school (Princeton)
# 3. `,` or ` and `
# 4. J. Smith or J Smith
# 5. J. M. Smith or J.M. Smith
PARENS1 = re.compile(r"\([^\)\(]*\)")

Paper = namedtuple('Paper', ['arxiv_id', 'authors', 'publisher', 'date'])
    


def get_abstracts(FOLDER="hep-th-abs"):
    dirs = [d for d in os.listdir(FOLDER) if os.path.isdir(os.path.join(FOLDER, d))]
    filenames = []
    for directory in dirs:
        abstracts = [a for a in os.listdir(os.path.join(FOLDER, directory))
                       if a.find(".abs") >= 0 and a.find(".sw") < 0]
        for abstract in abstracts:
            filenames.append((FOLDER, directory, abstract))
    return filenames


def parse_abstracts2(abstract, text):
    paper = None
    try:
        authors = parse_authors(text)
        publisher = parse_publisher(text)
        date = parse_date(text)
        arxiv_id = int(abstract.replace(r'.abs','').strip(), 10)
        paper = Paper(arxiv_id=arxiv_id, authors=authors,
                      publisher=publisher, date=date)
    except:
        print text
        raise
    return paper

def parse_authors(text):
    # might be have multiline authors
    # in that case, we want to read until we reach a new block
    # which doesn't start with "  "
    authors = [l for l in text if l.find("Author") == 0][0]
    authors_idx = text.index(authors)
    authors_idx += 1
    while text[authors_idx].find("  ") == 0:
        authors = authors + text[authors_idx]
        authors_idx += 1
    authors = authors.replace("\n", " ")

    # remove nested parenthesis
    authors = PARENS1.sub("", authors)
    authors = PARENS1.sub("", authors)
    authors = PARENS1.sub("", authors)

    # remove "Authors:" or "Authors" tag
    authors = authors.split(":")[1]
    # "kijun and mike" -> "kijun, mike"
    authors = authors.replace(" and ", ",")
    authors = [a.strip() for a in authors.split(",")]
    return [a for a in authors if len(a) > 0]


def parse_date(text):
    """
    Date: Wed, 18 MAR 92 15:22 N   (6kb)
    """
    date_str = [l for l in text if l.find("Date") == 0][0]
    date_str = PARENS1.sub("", date_str)
    date_parts = [p for p in date_str.strip().split(' ')[1:] if p.strip() != ""]
    for i in xrange(-len(date_parts),0):
        try:
            date = dateutil.parser.parse(' '.join(date_parts[0:-i]))
            tz = date_parts[-1]
            tzinfo = dateutil.tz.gettz(date_parts[-1])
            return date.replace(tzinfo=tzinfo)
        except:
            pass
    print "couldn't parse "
    print date_parts


def parse_publisher(text):
    publine = [l for l in text if l.find("Journal-ref") == 0]
    # might not have a publisher
    if len(publine) == 0:
        return
    publine = publine[0][13:]
    first_integer = re.search(r'[^a-zA-Z\s\.]', publine)
    if first_integer:
        return publine[0:first_integer.start()].strip()
    return publine


#Paper = namedtuple('Paper', ['arxiv_id', 'authors', 'publisher', 'date'])


def dump_papers(papers):
    with open('paper_dump.txt', 'w') as f:
        f.write('')
        for paper in papers:
            f.write(' ')


def fetch_txt(nameparts):
    with file(os.path.join(*nameparts)) as f:
        return nameparts[2], f.readlines()

def name_to_key(name):
    parts = re.sub(r"\."," ", re.sub(r"[^a-zA-Z\.\s]", "", name)).split(" ")
    if len(parts) > 1:
        try:
            last = parts[-1]
            first_l = parts[0][0]
            key = "%s_%s" % (first_l.upper(), last.upper())
            return key
        except:
            print parts
    return name

def run(f):
    pool = eventlet.GreenPool()
    filenames = get_abstracts()
    unparsed = []
    f.write("arxiv_id\tauthors\tauthor_keys\tpublisher\tdate\ttimestamp\n")
    for abstract, text in pool.imap(fetch_txt, filenames):
        try:
            p = parse_abstracts2(abstract, text)
            author_keys = [name_to_key(name) for name in p.authors]
            f.write("%s\t%s\t%s\t%s\t%s\t%d\n" % (
                p.arxiv_id,
                "|".join(p.authors),
                "|".join(author_keys),
                p.publisher,
                p.date.isoformat(),
                time.mktime(p.date.timetuple())
            ))
        except:
            unparsed.append(abstract)
    f.flush()
    return unparsed


