from util import connect, date2str, time2str, data_dir
import os
import sys
from datetime import timedelta
import datetime

fmt = "%-25s %-25s %-40s %s\n"

def parse_line(line):
    line = line.rstrip()
    ret = []
    ret.append(line[0:26])
    ret.append(line[26:26+26])
    ret.append(line[52:52+41])
    ret.append(line[93:])
    ret = [item.rstrip() for item in ret]
    return ret



class Extractor:
    def extract(self, row):
        pass


class MultiExtractor(Extractor):
    def __init__(self, names, sep = '|&|'):
        self.names = names
        self.sep = sep

    def extract(self, row):
        values = [row[name] for name in self.names]
        for i in range(len(values)):
            if values[i] is None:
                values[i] = ""
        values = map(str, values)
        return self.sep.join(values)


class ConstantExtractor(Extractor):
    def __init__(self, constant):
        self.constant = constant

    def extract(self, row):
        return self.constant


class TimeExtractor(Extractor):
    def __init__(self, name, converter):
        self.name = name
        self.converter = converter

    def extract(self, row):
        value = row[self.name]
        return self.converter(value)


class TestExtractor(Extractor):
    def __init__(self, name, test):
        self.name = name
        self.test = test

    def extract(self, row):
        return self.test(row[self.name])
class TestExtractors(Extractor):
    def __init__(self, names, test):
        self.tests = []
        for name in names:
            self.tests.append(TestExtractor(name, test))

    def extract(self, row):
        ret = True
        for test in self.tests:
            ret = ret and test.extract(row) 
        return ret 

class FmtExtractor(Extractor):
    def __init__(self, names, fmt):
        self.names = names
        self.fmt = fmt

    def extract(self, row):
        values = tuple([row[name] for name in self.names])
        return self.fmt % values

class SelectExtractor(Extractor):
    def __init__(self, sub_extractors):
        self.sub_extractors = sub_extractors

    def extract(self, row):
        for ext in self.sub_extractors:
            try:
                value = ext.extract(row)
            except Exception, e:
                pass
            else:
                return value
        return None



class ExtractorInfo:
    def __init__(self, table, outpath, id_extractor, time_extractor, 
                type_extractor = None, value_extractor = ConstantExtractor(1), 
                test_extractor = ConstantExtractor(True)):
        self.table = table
        self.outpath = outpath
        self.id_extractor = id_extractor
        self.time_extractor = time_extractor
        self.type_extractor = type_extractor
        self.value_extractor = value_extractor
        self.test_extractor = test_extractor

    def open(self):
        self.outf = file(self.outpath, 'w')

    def extract(self, row):
        global fmt
        if self.test_extractor.extract(row):
            ID = self.id_extractor.extract(row)
            time = self.time_extractor.extract(row)
            dtype = self.type_extractor.extract(row)
            value = self.value_extractor.extract(row)
            out = (ID, time, dtype, value)
            self.outf.write(fmt % out)

    def close(self):
        self.outf.close()


def extract_from_table(table, extractors, only_test = False, limit = 100000):
    print "query from [%s]" %table
    db = connect()
    offset = 0
    for extractor in extractors:
        extractor.open()
    while True:
        query = "select * from %s order by row_id limit %d offset %d" %(table, limit, offset)
        print '\t%s' %query
        res = db.query(query)
        cnt = 0
        for row in res.dictresult():
            cnt += 1
            for extractor in extractors:
                extractor.extract(row)

        ntuples = res.ntuples()
        offset += limit
        if ntuples < limit or only_test:
            break
    for extractor in extractors:
        extractor.close()



if __name__ == '__main__':
    extractor_map = {}
    get_patients_extractors(data_dir, extractor_map)
    get_admissions_extractors(data_dir, extractor_map)
    extract_from_table('patients', extractors)