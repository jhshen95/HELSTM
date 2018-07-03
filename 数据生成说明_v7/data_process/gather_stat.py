from util import stat_dir, result_dir
import os
import glob
from stat_data import Stat

def handle(filename, outf):
    base = os.path.basename(filename)
    print base
    get_cnt = lambda x:x.cnt
    get_rate = lambda x:x.rate
    stats = Stat.load_from_file(filename)
    outf.write("***** %s start *****\n" %base)
    for rtype in sorted(stats.keys()):
        out = []
        stat = stats[rtype]
        nentry = stat.nentry()
        out.append(nentry)
        out.append(stat.get_mean(get_cnt))
        out.append(stat.get_var(get_cnt))
        stat.calc_rate()
        out.append(stat.get_mean(get_rate))
        out.append(stat.get_var(get_rate))
        out = ['%-20s' %str(item) for item in out]
        out.insert(0, '%-40s' %rtype)
        outf.write("".join(out) + "\n")
    outf.write("***** %s end   *****\n\n" %base)


if __name__ == '__main__':
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)
    outf = file(os.path.join(result_dir, 'stat.tsv'), 'w')
    for filename in glob.glob(stat_dir + "/*.tsv"):
        handle(filename, outf)
    outf.close()
