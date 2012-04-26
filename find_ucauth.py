d = {}

with open('raw/authors.txt') as f:
   for l in f.readlines():
       d[l.strip()] = True

print d

with open('raw/arxiv_hep_2003_abstract.txt') as f:
    with open('out.txt', 'w') as f2:
        for l in f.readlines():
            try:
                names = l.strip().split('\t')[2].split('|')
                names = [name for name in names if name in d]
                f2.write('%s\n' % ','.join(names))
            except:
                pass
        f2.flush()
