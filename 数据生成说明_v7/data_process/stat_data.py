import glob
import os
import extractor
from util import data_dir, parse_time, stat_dir, time2str, result_dir
import re
import math


class Stat:
    pattern = re.compile(r'\[(?P<rtype>[\w\.&]+)] statistics: (?P<count>\d+) entries')


    def __init__(self, rtype):
        self.rtype = rtype
        self.stat = {}
        self.value_stat = None
        self.row = 0


    def nentry(self):
        return len(self.stat)

    def nrow(self):
        return self.row

    def get_value_stat(self):
        return self.value_stat

    def add_whole_entry(self, entry):
        self.stat[entry.ID] = entry

    
    def add_entry(self, ID, time, value = None):
        if not ID in self.stat:
            self.stat[ID] = StatEntry(ID)
        self.stat[ID].add_time(time)
        if value is not None:
            parts = value.split("|&|")
            self.add_value(ID, parts)

    def add_value(self, ID, parts):
            if self.value_stat is None:
                nvalue = len(parts)
                self.value_stat = [0] * nvalue
            self.row += 1
            assert len(parts) == len(self.value_stat)

            for i in range(len(parts)):
                if parts[i] != "":
                    self.value_stat[i] += 1

    def write_to_local(self, outf):
        outf.write('[%s] statistics: %d entries\n' %(self.rtype, len(self.stat)))
        for ID in sorted(self.stat.keys()):
            outf.write(self.stat[ID].to_line())
            outf.write("\n")

    def get_mean(self, valuef):
        tot = 0.0
        nentry = 0
        for entry in self.stat.values():
            value = valuef(entry)
            if value > 0:
                tot += value
                nentry += 1
        mean = 0
        if nentry > 0:
            mean = round(tot / nentry, 4)
        return (nentry, mean)

    def get_var(self, valuef):
        nentry, mean = self.get_mean(valuef)
        tot = 0
        for entry in self.stat.values():
            value = valuef(entry)
            if value > 0:
                tot += (value - mean) * (value - mean)
        var = 0.0
        if nentry > 0:
            var = round(math.sqrt(tot / nentry), 4)
        return (nentry, var)

    def calc_rate(self):
        for entry in self.stat.values():
            entry.calc_rate()

    @staticmethod
    def load_from_file(filename):
        stats = {}
        rtype = None
        for line in file(filename, 'r'):

            line = line.rstrip()
            if line.startswith("["):
                res = Stat.pattern.match(line)
                rtype = res.group('rtype')
                cnt = res.group("count")
                stats[rtype] = Stat(rtype)
                stat = stats[rtype]
            else:
                entry = StatEntry.load_from_line(line)
                stat.add_whole_entry(entry)
        return stats



class StatEntry:
    fmt = '%s\t%d\t%s\t%s'

    def __init__(self, ID, cnt = 0, st = None, ed = None):
        self.ID = ID
        self.st = st
        self.ed = ed
        self.cnt = cnt

    def add_time(self, time):
        if self.st is None:
            self.st = time
            self.ed = time
        elif time is not None:
            self.st = min(self.st, time)
            self.ed = max(self.ed, time)
        self.cnt += 1


    def to_line(self):
        return StatEntry.fmt %(self.ID, self.cnt, self.st, self.ed)

    def calc_rate(self):
        self.rate = 0
        if self.st is not None:
            nhour = (self.ed - self.st).total_seconds()/3600.00
            if nhour > 0:
                self.rate = self.cnt / nhour

    @staticmethod
    def load_from_line(line):
        parts = line.rstrip().split("\t")
        ID = int(parts[0])
        cnt = int(parts[1])
        st = parts[2]
        ed = parts[3]
        if st != "None":
            st_time = parse_time(st)
        else:
            st_time = None
        if ed != "None":
            ed_time = parse_time(ed)
        else:
            ed_time = None
        entry = StatEntry(ID, cnt, st_time, ed_time)
        return entry


def get_patientid(IDs_str):
    IDs = IDs_str.split("_")
    return int(IDs[0])

def get_id(IDs_str):
    IDs = IDs_str.split("_")
    return int(IDs[0])

    # if len(IDs) >= 2:
    #   if IDs[1] == "":
    #       return None
    #   return int(IDs[1])
    # else:
    #   return int(IDs[0])

def process(filename, outfilename, value_stats):
    stats = {}
    print 'process [%s]' %(os.path.basename(filename))
    cnt = 0
    for line in file(filename, 'r'):
        cnt += 1
        if cnt % 100000 == 0:
            print "\t %d lines" %cnt
        parts = extractor.parse_line(line)

        ID = get_id(parts[0])
        if ID is None:
            continue

        rtype = parts[2]
        if not rtype in stats:
            stats[rtype] = Stat(rtype)
        stat = stats[rtype]

        time = parse_time(parts[1])
        stat.add_entry(ID, time, parts[3].strip())

        values = parts[3].split("|&|")
        if len(values) >= 1:
            time = parse_time(values[0])
            if time is not None:
                stat.add_entry(ID, time)
    if outfilename is not None:
        outf = file(outfilename, 'w')
        for rtype in sorted(stats.keys()):
            stats[rtype].write_to_local(outf)
        outf.close()

    if not value_stats is None:
        for rtype in stats.keys():
            stat = stats[rtype]
            total = stat.nrow()
            value_cnts = stat.get_value_stat()
            for i in range(len(value_cnts)):
                key = rtype + "#" +  str(i)
                rate = round(value_cnts[i] / (total + 0.0), 3)
                value = (rate, value_cnts[i])
                value_stats[key] = value

def count_table_event(filepath):
    print "count event from [%s]" %os.path.basename(filepath)
    event_cnt = {}
    for line in file(filepath):
        parts = extractor.parse_line(line)
        pid = int(parts[0].split("_")[0])
        if not pid in event_cnt:
            event_cnt[pid] = 0
        event_cnt[pid] += 1
    return event_cnt

def count_event(filepaths, outpath):
    patients = set()
    table_names = []
    table_cnt = {}
    for filepath in filepaths:
        event_cnt = count_table_event(filepath)
        name = os.path.basename(filepath)[:-4]
        table_cnt[name] = event_cnt
        table_names.append(name)
        for pid in event_cnt:
            patients.add(pid)

    outf = file(outpath, 'w')
    table_names = sorted(table_names)
    out = ["pid"]
    out.extend(table_names)
    outf.write("\t".join(out) + "\n")
    for pid in sorted(patients):
        out = [pid] 
        for table_name in table_names:
            cnt = table_cnt[table_name].get(pid, 0)
            out.append(cnt)
        out = map(str, out)
        outf.write("\t".join(out) + "\n")
    outf.close()


def write_value_stat(value_stats, outpath):
    outf = file(outpath, 'w')
    for key in sorted(value_stats.keys(), reverse = True, key = lambda x:value_stats[x][0]):
        outf.write("%-35s %5f %d\n" %(key, value_stats[key][0], value_stats[key][1]))
    outf.close()

class SimpleStat:
    def __init__(self):
        self.pid_event_cnt = {}
        self.nb_event = 0
        self.rtype_set = set()

    def add_pid(self, pid):
        if not pid in self.pid_event_cnt:
            self.pid_event_cnt[pid] = 0
            
    
    def add_data(self, line):
        self.nb_event += 1
        parts = extractor.parse_line(line)
        pid = get_id(parts[0])
        rtype = parts[2]
        self.add_pid(pid)
        self.rtype_set.add(rtype)
        self.pid_event_cnt[pid] += 1

    def print_info(self):
        out_format = """
        # of patients = {0}
        # of events = {1}
        Avg # of events per patient = {2}
        Max # of events per patient = {3}
        Min # of events per patient = {4}
        # of unique events = {5}
        """
        nb_patients = len(self.pid_event_cnt)
        nb_events = self.nb_event
        ave_events = round((nb_events + 0.0) / nb_patients, 4)
        max_events = reduce(max, self.pid_event_cnt.values())
        min_events = reduce(min, self.pid_event_cnt.values())
        nb_event_type = len(self.rtype_set)
        print out_format.format(
            nb_patients,
            nb_events,
            ave_events,
            max_events,
            min_events,
            nb_event_type
        )
        



def gather_statistics(filepath, stat):
    print "gather info from %s" %filepath
    for line in file(filepath):
        stat.add_data(line)
        



if __name__ == '__main__':
    # process('data/chartevents_8.tsv', 'stat/test.stat')

    # stat data
    if not os.path.exists(stat_dir):
        os.mkdir(stat_dir)
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)
    value_stats = {}
    for filename in glob.glob(data_dir + "/*tsv"):
        stat_filename = os.path.join(stat_dir, os.path.basename(filename))
        process(filename, stat_filename, value_stats)
    if value_stats and len(value_stats) > 0:
        write_value_stat(value_stats, os.path.join(result_dir, 'value_coverage_stat.tsv'))


    # filepaths = glob.glob(data_dir + "/*tsv")
    # count_event(filepaths, os.path.join(result_dir, 'event_cnt.tsv'))

    # print statistics
    # stat = SimpleStat()
    # for filename in glob.glob(data_dir + "/*tsv"):
    #     gather_statistics(filename, stat)
    # stat.print_info()
