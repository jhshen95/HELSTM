from util import *
import datetime

class Admission:
    def __init__(self):
        self.cnt = 0
        self.admit_type = None
        self.disch = None
        self.admit = None
        self.death = False

    def add_disch(self, disch):
        if self.disch == None:
            self.disch = disch
        else:
            self.disch = max(self.disch, disch)
        self.cnt += 1

    def add_admit(self, admit, admit_type):
        if self.admit is None:
            self.admit = admit
            self.admit_type = admit_type
        elif self.admit > admit:
            self.admit = admit
            self.admit_type = admit_type

    def add_death(self, death):
        self.death = True

    def range(self):
        return (self.disch - self.admit).days

    def __str__(self):
        out = map(str, [self.admit, self.disch, self.cnt, self.death, self.admit_type])
        return "\t".join(out)

    @staticmethod
    def load_from_line(line):
        admission = Admission()
        parts = line.strip().split("\t")
        admission.cnt = int(parts[2])
        admission.admit = parse_time(parts[0])
        admission.disch = parse_time(parts[1])
        admission.death = False if parts[3] == "False" else True
        admission.admit_type = parts[-1]
        return admission

def load_admission():
    ad_map = {}
    for line in file(static_data_dir + "/admission.tsv"):
        parts = line.strip().split("\t")
        pid = int(parts[0])
        adm = Admission.load_from_line("\t".join(parts[1:]))
        ad_map[pid] = adm
    return ad_map

class SingleAdmission:
    def __init__(self, pid, admit_time, disch_time, admit_type):
        self.pid = pid
        self.admit_time = admit_time
        self.disch_time = disch_time
        self.admit_type = admit_type

    def __str__(self):
        out = map(str, [self.pid, self.admit_time, self.disch_time, self.admit_type])
        return "\t".join(out)
    
    @staticmethod
    def load_from_line(line):
        parts = line.strip().split("\t")
        pid = int(parts[0])
        admit_time = parse_time(parts[1])
        disch_time = parse_time(parts[2])
        admit_type = parts[3]
        admission = SingleAdmission(pid, admit_time, disch_time, admit_type)
        return admission

def get_d_icd_diagnoses():
    diag_icd_map = {}
    db = connect()
    table = 'd_icd_diagnoses'
    query = 'select * from %s' %table
    res = db.query(query)
    for row in res.dictresult():
        code = row['icd9_code']
        value = (row['short_title'], row['long_title'])
        diag_icd_map[code] = value

    return diag_icd_map

def get_d_labitems():
    d_labitem_map = {}
    db = connect()
    table = "d_labitems"
    query = "select * from %s" %table
    res = db.query(query)
    for row in res.dictresult():
        code = row['itemid']
        value = row['label'] + " | " + row['fluid']
        d_labitem_map[code] = value
    return d_labitem_map

def get_d_items():
    d_item_map = {}
    db = connect()
    table = "d_items"
    query = "select * from %s" %table
    res = db.query(query)
    for row in res.dictresult():
        code = row['itemid']
        value = row['label']
        d_item_map[code] = value
    return d_item_map

def get_single_admission():
    admission_map = {}
    db = connect()
    table = "admissions"
    query = "select * from %s" %table
    res = db.query(query)
    cnt = 0
    for row in res.dictresult():
        cnt += 1
        if cnt % 1000 == 0:
            print cnt
        hid = row['hadm_id']
        pid = row['subject_id']
        admit_time = row['admittime']
        disch_time = row['dischtime']
        admit_type = row['admission_type']
        admission_map[hid] = SingleAdmission(pid, admit_time, disch_time, admit_type)

    return admission_map


def write_map(data, filepath):
    outf = file(filepath, 'w')
    keys = data.keys()
    try:
        keys = map(int, keys)
    except Exception, e:
        pass
    for key in sorted(keys):
        outf.write('\t'.join(map(str, [key, data[key]])) + '\n')
    outf.close()

def write_map_value(data, filepath):
    outf = file(filepath, "w")
    keys = data.keys()
    for key in sorted(keys):
        outf.write(str(data[key]) + "\n")
    outf.close()

def get_admission_map(admit_path, disch_path, death_path):
    admission_map = {}
    id2event_value = load_id2event_value()
    for line in file(disch_path):
        parts = line.strip().split("\t")
        pid = int(parts[1])
        time = parse_time(parts[3])
        assert time is not None
        if not pid in admission_map:
            admission_map[pid] = Admission()
        admission_map[pid].add_disch(time)
    for line in file(admit_path):
        parts = line.strip().split("\t")
        pid = int(parts[1])
        admit_type = id2event_value[int(parts[0])].split(".")[-1]
        time = parse_time(parts[3])
        assert time is not None
        admission_map[pid].add_admit(time, admit_type)

    for line in file(death_path):
        parts = line.strip().split("\t")
        pid = int(parts[1])
        time = parse_time(parts[3])
        assert time is not None
        admission_map[pid].add_death(time)

    return admission_map




if __name__ == '__main__':
    if not os.path.exists(static_data_dir):
        os.mkdir(static_data_dir)
    # diagnose code map
    # diag_icd_map = get_d_icd_diagnoses()
    # write_map(diag_icd_map, os.path.join(static_data_dir, 'diag_ICD9.tsv'))

    # item code map
    item_map = get_d_items()
    write_map(get_d_items(), os.path.join(static_data_dir, 'item_code.tsv'))

    # labitem code map
    labitem_map = get_d_labitems()
    write_map(labitem_map, os.path.join(static_data_dir, "labitem_code.tsv"))

    # gather admission from database
    # admission_map = get_single_admission()
    # write_map(admission_map, os.path.join(static_data_dir, "single_admission.tsv"))
    

    # admission map
    # admit_path = os.path.join(event_dir, "admissions.admittime.tsv")
    # disch_path = os.path.join(event_dir, 'admissions.dischtime.tsv')
    # death_path = os.path.join(event_dir, "admissions.deathtime.tsv")
    # admission_map = get_admission_map(admit_path, disch_path, death_path)
    # write_map(admission_map, os.path.join(static_data_dir, "admission.tsv"))
