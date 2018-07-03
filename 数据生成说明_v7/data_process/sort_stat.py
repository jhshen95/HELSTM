import re
pattern = re.compile(r"\s{2,}")
outf = file('result/sorted_stat.tsv', 'w')
stats = []
for line in file('result/stat.tsv'):
    if line.startswith('****') or line.strip() == "":
        continue
    else:
        nentry  = int(pattern.split(line)[1])
        stats.append((nentry, line))

stats.sort(key = lambda x:x[0], reverse = True)
for nentry, line in stats:
    outf.write(line)
outf.close()


