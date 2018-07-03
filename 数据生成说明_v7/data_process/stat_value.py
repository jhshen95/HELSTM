from util import *
import glob
import os
import extractor
import json

class ValueStat:
    header = "***** type nentry time% num% null% txt% ntxt_type"
    fmt = "%-3s %-8s %-7s%-7s%-7s%-7s%-7s"
    def __init__(self, order):
        self.order = order
        self.nnum = 0
        self.ntime = 0
        self.nentry = 0
        self.ntxt = 0
        self.nnull = 0
        self.ntype_txt = set()

    def add(self, value):
        value = value.strip()
        self.nentry += 1
        if value == "":
            self.nnull += 1
            self.ntxt += 1
        elif is_time(value):
            self.ntime += 1
        elif is_number(value):
            self.nnum += 1
        else:
            self.ntxt += 1
        self.ntype_txt.add(value.lower())

    def __str__(self):
        self.nentry += 0.0
        out = ["%-3d" %self.order]
        out.append("%-8d" %self.nentry)
        counts = [self.ntime, self.nnum, self.nnull, self.ntxt]
        for count in counts:
            out.append("%5d/%-.3f" %(count, round(count/self.nentry, 3)))
        out.append("%-7d" %len(self.ntype_txt))
        return " ".join(out)

        # out = [self.order, self.nentry, round(self.ntime/self.nentry, 3),
        #       round(self.nnum/self.nentry, 3), round(self.nnull/self.nentry,3),
        #       round(self.ntxt/self.nentry, 3), len(self.ntype_txt)]
        # out = map(str, out)
        # return ValueStat.fmt % tuple(out)


class TypeValueStat:
    def __init__(self, rtype):
        self.nvalue = -1
        self.rtype = rtype
        self.value_stats = []

    def add(self, values):
        if self.nvalue == -1:
            self.nvalue = len(values)
            for i in range(self.nvalue):
                self.value_stats.append(ValueStat(i))
        assert self.nvalue == len(values)
        for i in range(self.nvalue):
            self.value_stats[i].add(values[i])

    def to_string(self):
        ret = []
        for value_stat in self.value_stats:
            ret.append("%15s" %self.rtype + "#" + str(value_stat))
        return ret


class FileValueStat:
    def __init__(self, filename):
        self.filename = filename
        self.type_stats = {}

    def add(self, rtype, values):
        if not rtype in self.type_stats:
            self.type_stats[rtype] = TypeValueStat(rtype)
        self.type_stats[rtype].add(values)



def stat_value_types(filepath, outf, txt_outf = None):
    value_sep = "|&|"
    filename = ".".join(os.path.basename(filepath).split(".")[:-1])
    print filename
    file_stat = FileValueStat(filename)
    for line in file(filepath):
        parts = extractor.parse_line(line)
        rtype = parts[2]
        values = parts[3].split(value_sep)
        file_stat.add(rtype, values)
    outf.write("***** %s start *****\n" %filename)
    for rtype in sorted(file_stat.type_stats.keys()):
        for out_str in file_stat.type_stats[rtype].to_string():
            outf.write(out_str + "\n")
    outf.write("***** %s end   *****\n" %filename)

    if txt_outf is not None:
        for rtype in sorted(file_stat.type_stats.keys()):
            type_stat = file_stat.type_stats[rtype]
            for value_stat in type_stat.value_stats:
                if len(value_stat.ntype_txt) > 0:
                    name = type_stat.rtype + "#" + str(value_stat.order)
                    text = json.dumps([text for text in value_stat.ntype_txt])
                    txt_outf.write(name + '\t' + str(len(value_stat.ntype_txt)) + '\t' + text + "\n")





if __name__ == '__main__':
    outf = file(os.path.join(result_dir, "value_type_stat.tsv"), 'w')
    txt_outf = file(os.path.join(result_dir, "value_type_text.tsv"), 'w')
    outf.write(ValueStat.header+"\n")
    for filepath in glob.glob('data/' + "*.tsv"):
        stat_value_types(filepath, outf, txt_outf)
    outf.close()
    txt_outf.close()