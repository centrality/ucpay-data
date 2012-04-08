import os
import re

# 1. Author or Authors
# 2. Might specify school (Princeton)
# 3. `,` or ` and `
# 4. J. Smith or J Smith
# 5. J. M. Smith or J.M. Smith

def parse_abstracts(FOLDER="hep-th-abs"):
    PARENS1 = re.compile(r"\([^\)\(]*\)")
    dirs = [d for d in os.listdir(FOLDER) if os.path.isdir(os.path.join(FOLDER, d))]
    h = {}
    for directory in dirs:
        abstracts = [a for a in os.listdir(os.path.join(FOLDER, directory))
                       if a.find(".abs") >= 0]
        for abstract in abstracts:
            with file(os.path.join(FOLDER, directory, abstract)) as f:
                text = f.readlines()

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
                aid = int(abstract.split(".")[0],10)
                h[aid] = [a for a in authors if len(a) > 0]
    return h


def dump_authors(hashtb):
    import sqlite3
    conn = sqlite3.connect("authors.db")
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS authors");
    c.execute("CREATE TABLE authors (id INTEGER, author VARCHAR(255))")
    c.execute("CREATE INDEX id_idx ON authors (id)")

    for id, authors in hashtb.items():
        for author in authors:
            c.execute("INSERT INTO authors VALUES (?, ?)", [id, author])

    conn.commit()
    c.close()
    conn.close()



