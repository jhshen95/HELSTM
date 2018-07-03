from util import *
import os
import json
import re

class ValueCount:
    def __init__(self, ratio, number = 0):
        self.ratio = ratio
        self.number = number

    @staticmethod
    def load_from_str(part):
        l = part.split("/")
        number = int(l[0])
        ratio = float(l[1])
        return ValueCount(ratio, number)

    def __cmp__(self, other):
        return cmp(self.ratio, other.ratio)

class FeatureValueCount:
    '''
        parts:type nentry time% num% null% txt% ntxt_type
    '''
    main_type_threshold = ValueCount(0.95)
    max_text_kinds = 40
    small_coverage = "small coverage"
    def __init__(self, parts):
        time_cnt = ValueCount.load_from_str(parts[2])
        num_cnt = ValueCount.load_from_str(parts[3])
        null_cnt = ValueCount.load_from_str(parts[4])
        txt_cnt = ValueCount.load_from_str(parts[5])
        self.cnts = {
        "time":time_cnt,
        "number":num_cnt,
        "null":null_cnt,
        "text":txt_cnt,
        }
        self.feature = parts[0]
        self.ntxt_type = int(parts[6])

    def check_valid(self):
        main_type = self.main_type()
        coverage = self.get_count(main_type)
        if coverage < FeatureValueCount.main_type_threshold:
            print "**** coverage:%f" %coverage.ratio
            return False
        if main_type == "text" and self.ntxt_type > FeatureValueCount.max_text_kinds:
            print "**** text #types:%d" %self.ntxt_type
            return False
        return True

    def main_type(self):
        main_name = None
        max_value = ValueCount(0.0)
        for name in self.cnts:
            value = self.cnts[name]
            if value > max_value:
                max_value = value
                main_name = name
        return main_name

    def get_count(self, name):
        return self.cnts[name]



def load_value_type_text(filepath):
    text_map = {}
    for line in file(filepath):
        parts = line.strip().split('\t')
        feature = parts[0]
        texts = json.loads(parts[2])
        text_map[feature] = texts
    return text_map

def load_value_type_stat(filepath):
    value_type_map = {}
    space_spliter = re.compile(r"\s+")
    for line in file(filepath):
        line = line.strip()
        if line.startswith("****"):
            continue
        parts = space_spliter.split(line)
        value_cnt = FeatureValueCount(parts)
        value_type_map[value_cnt.feature] = value_cnt
    return value_type_map

class TypeFeature():
    def __init__(self, rtype, nentry):
        self.rtype = rtype
        self.nentry = nentry
        self.features = []

    def add_feature(self, value_feature):
        self.features.append(value_feature)

    def to_string(self):
        self.features.sort()
        out = []
        out.append(self.rtype + "#" + str(self.nentry))
        for feature in self.features:
            out.append("\t"+feature.to_string())
        return "\n".join(out)

    @staticmethod
    def load_from_str(string):
        parts = string.split("\n")
        rtype, nentry = parts[0].split("#")
        type_feature = TypeFeature(rtype, int(nentry))
        for part in parts[1:]:
            type_feature.features.append(ValueFeature.load_from_str(part.lstrip("\t")))
        return type_feature


class ValueFeature:
    def __init__(self, order, main_type, f_value_cnt = None):
        self.order = order
        self.main_type = main_type
        if f_value_cnt is not None:
            self.coverage = f_value_cnt.get_count(main_type).ratio
            self.ndim = 1
            if self.main_type == "text":
                self.ndim = f_value_cnt.ntxt_type


    def to_string(self):
        out = [self.order, self.main_type, self.coverage, self.ndim]
        out = map(str, out)
        return " ".join(out)

    @staticmethod
    def load_from_str(string):
        parts = string.split(" ")
        # print string
        order = int(parts[0])
        main_type = parts[1]
        value_f = ValueFeature(order, main_type)
        value_f.coverage = float(parts[2])
        value_f.ndim = int(parts[3])
        return value_f

    def __cmp__(self, other):
        return cmp(self.order, other.order)

def gen_type_feature(rtype, nentry, value_stat_map, text_map):
    Flag = True
    i = 0 
    type_feature = TypeFeature(rtype, nentry)
    while True:
        order = i
        i += 1
        feature_name = rtype + "#" + str(order)
        if feature_name in value_stat_map:
            value_stat = value_stat_map[feature_name]
            if value_stat.check_valid():
                value_feature = ValueFeature(order, value_stat.main_type(), value_stat)
                type_feature.add_feature(value_feature)
            else:
                if rtype.startswith("inputevents_mv") and order == 2:
                    continue
                if rtype.startswith("inputevents_cv") and order == 1:
                    continue
                return None
        else:
            break
    return type_feature



def select_feature(stat_file, limit, text_map, value_stat_map):
    black_regs = load_reg(os.path.join(config_dir, 'blacklist.reg'))
    features = []
    rtypes = []
    space_spliter = re.compile(r"\s+")
    nfeature = 0
    dim = 0
    event_dim = 0
    for idx, line in enumerate(file(stat_file)):
        if idx >= limit:
            continue
        parts = space_spliter.split(line.strip())
        rtype = parts[0]
        in_black = False
        for reg in black_regs:
            if reg.match(rtype):
                in_black = True
        if in_black:
            continue

        nentry = int(parts[1])
        type_feature = gen_type_feature(rtype, nentry, value_stat_map, text_map)
        if type_feature is not None:
            features.append(type_feature)
            t_event_dim = 1
            cc = 0
            for value_feature in type_feature.features:
                if value_feature.main_type != "text":
                    dim += value_feature.ndim
                    # print value_feature.ndim
                if value_feature.ndim > 1:
                    cc += 1
                t_event_dim *= value_feature.ndim
            if cc >= 2:
                print "**********",  rtype
            event_dim += t_event_dim
    print "feature dim =", dim
    print "event dim =", event_dim
    print "nfeature =", len(features)

    return features

def write_features(features, filepath):
    outf = file(filepath, 'w')

    for feature in features:
        outf.write(feature.to_string() + "\n")
        # main_type = feature.main_type
        # out = [feature.name, feature.f_coverage, main_type]
        # if main_type in error_main_types:
        #     main_name, max_ratio = feature.f_value_cnt.max_ratio()
        #     out.append(main_name)
        #     out.append(max_ratio)
        # else:
        #     value_cnt = feature.f_value_cnt.get_count(main_type)
        #     out.append('%d/%f' %(value_cnt.number, value_cnt.ratio))
        #     if main_type == "text":
        #         out.append(feature.f_value_cnt.ntxt_type)
        # out = map(str, out)
        # outf.write("\t".join(out) + "\n")
    outf.close()
    


if __name__ == '__main__':
    text_map = load_value_type_text(os.path.join(result_dir, "value_type_text.tsv"))
    value_stat_map = load_value_type_stat(os.path.join(result_dir, "value_type_stat.tsv"))
    stat_file = os.path.join(result_dir, "sorted_stat.tsv")
    feature_limit = 1000
    features = select_feature(stat_file, feature_limit, text_map, value_stat_map)
    write_features(features, os.path.join(result_dir, "selected_features.tsv"))

    




