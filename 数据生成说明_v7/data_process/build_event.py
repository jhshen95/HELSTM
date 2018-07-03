from util import *
from select_feature import load_value_type_text, TypeFeature
from extractor import parse_line
import glob
import itertools

class Feature():
    def __init__(self, index, value):
        self.index = index
        self.value = value

    def __cmp__(self, other):
        return cmp(self.index, other.index)

    def __str__(self):
        return str(self.index) + ":" + str(self.value)

    @staticmethod
    def parse_features(string):
        features = []
        string = string.strip()
        if string == "":
            return []
        for pair in string.split(" "):
            index, value = pair.split(":")
            features.append(Feature(int(index), float(value)))
        return features


class FeatureExtractor():
    def __init__(self, feature_index, value_index):
        self.feature_index = feature_index
        self.value_index = value_index


class TimeFeatureExtractor(FeatureExtractor):
    nerror = 0
    def extract(self, time, values, base):
        value = values[self.value_index]
        value = parse_time(value)
        if value is None:
            return None
        else:
            duration = (value - time).total_seconds()/3600.0
            if duration < 0:
                TimeFeatureExtractor.nerror += 1
                return None
            return Feature(base + self.feature_index, duration)


class NumberFeatureExtractor(FeatureExtractor):
    def extract(self, time, values, base):
        value = values[self.value_index]
        value = parse_number(value)
        if value is None:
            return None
        else:
            return Feature(base + self.feature_index, value)

class Event():
    def __init__(self, event_idx, features, pid, time):
        self.index = event_idx
        self.features = features
        self.pid = pid
        self.time = time

    def is_valid(self):
        for feature in self.features:
            if feature is None:
                return False
        return True

    def __cmp__(self, other):
        ret = cmp(self.time, other.time)
        if ret != 0:
            return ret
        else:
            return cmp(self.index, other.index)

    def __str__(self):
        out = [self.index, self.pid, " ".join(map(str, self.features)), self.time]
        out = map(str, out)
        return "\t".join(out)



    @staticmethod
    def load_from_line(line):
        parts = line.strip().split('\t')
        index = int(parts[0])
        pid = int(parts[1])
        features = Feature.parse_features(parts[2])
        time = parse_time(parts[3])
        return Event(index, features, pid, time)


class EventBuilder():
    sep = "|&|"
    def __init__(self, type_feature, text_map):
        self.type_feature = type_feature
        self.event_builder_init(text_map)
        self.value_builder_init(text_map)

    def builder_des(self):
        des_list = []
        for event_fac in reversed(self.feature_texts):
            if len(event_fac) > 0:
                des_list.append(event_fac)
        if len(des_list) == 0:
            return [""]
        else:
            return [x for x in itertools.product(*des_list)]
          


    def event_builder_init(self, text_map):
        self.event_factor = []
        self.feature_texts = []
        self.orders = []
        self.event_dim = 1
        for feature in self.type_feature.features:
            order = feature.order
            self.orders.append(order)
            value_feature_name = self.type_feature.rtype + "#" + str(order)
            if feature.main_type == "text":
                text = sorted(text_map[value_feature_name])
                self.event_factor.append(self.event_dim)
                self.event_dim *= len(text)
                self.feature_texts.append(text)
            else:
                self.event_factor.append(0)
                self.feature_texts.append([])

    def value_builder_init(self, text_map):
        self.feature_dim = 0
        self.extractors = []
        for value_feature in self.type_feature.features:
            if value_feature.main_type == "time":
                self.extractors.append(TimeFeatureExtractor(self.feature_dim, value_feature.order))
                self.feature_dim += 1
            elif value_feature.main_type == "number":
                self.extractors.append(NumberFeatureExtractor(self.feature_dim, value_feature.order))
                self.feature_dim += 1

    def set_event_base(self, event_base):
        self.event_base = event_base 
        return self.event_base + self.event_dim

    def set_feature_base(self, feature_base):
        self.feature_base = feature_base
        return self.feature_base + self.feature_dim

    def build_event(self, time, values):
        values = [values[order] for order in self.orders]
        event = 0
        for i in range(len(values)):
            if self.event_factor[i] > 0:
                value = values[i]
                idx = self.feature_texts[i].index(value.strip().lower())
                event = event + idx * self.event_factor[i]
        return event + self.event_base

    def build_features(self, time, values):
        features = []
        for extractor in self.extractors:
            features.append(extractor.extract(time, values, self.feature_base))
        return features

    def build(self, row):
        parts = parse_line(row)
        pid = int(parts[0].split("_")[0])
        time = parse_time(parts[1])
        values = parts[3].split(EventBuilder.sep)
        event_idx = self.build_event(time, values)
        features = self.build_features(time, values)
        event = Event(event_idx, features, pid, time)
        if event.is_valid():
            return event
        else:
            return None

def load_type_features(filepath):
    s = ""
    type_features = []
    for line in file(filepath):
        if line.startswith("\t"):
            s = s + line
        else:
            if s != "":
                s = s.rstrip('\n')
                type_features.append(TypeFeature.load_from_str(s))
            s = line
    if s != "":
        s = s.rstrip('\n')
        type_features.append(TypeFeature.load_from_str(s))
    return type_features

def gen_builders(type_features, text_map, build_des_file, feature_des_file):
    '''
    event: event 0 is padding, event 1 is intervel 
    feature: feature 0 is during time feature
    '''
    builders = {}
    event_dim = 2
    feature_dim = 1
    f = file(build_des_file, 'w')
    fea_f = file(feature_des_file, 'w')
    for type_feature in type_features:
        builder = EventBuilder(type_feature, text_map)
        l = event_dim
        event_dim = builder.set_event_base(event_dim)
        r = event_dim
        event_des = builder.builder_des()
        for i in range(l, r):
            f.write("%d %s %s\n" %(i, type_feature.rtype, "\t".join(event_des[i - l])))
        l = feature_dim
        feature_dim = builder.set_feature_base(feature_dim)
        r = feature_dim 
        if r > l:
            fea_f.write("%s\t%s\n" %(type_feature.rtype, "\t".join(map(str, range(l,r)))))
        builders[type_feature.rtype] = builder
    f.close()
    fea_f.close()
    print "event_dim =", event_dim
    print "feature_dim =", feature_dim
    return builders

def build_event(filepath, builders):
    name = ".".join(os.path.basename(filepath).split(".")[:-1])
    print "build event =", name
    outf = file(os.path.join(event_dir, name + ".tsv"), 'w')
    for line in file(filepath):
        line = line.strip()
        parts = parse_line(line)
        rtype = parts[2]
        if rtype in builders:
            event = builders[rtype].build(line)
            if event is not None:
                outf.write(str(event)+"\n")
    outf.close()

def print_event(builders, filepath):
    f = file(filepath, 'w')
    builders = sorted(builders.values(), key = lambda x:x.event_base)
    for builder in builders:
        st = builder.event_base
        ed = builder.event_base + builder.event_dim - 1
        f.write(str(st) + "-" + str(ed) + '\t')
        f.write(builder.type_feature.rtype)
        f.write("\n")
    f.close()


if __name__ == '__main__':
    text_map = load_value_type_text(os.path.join(result_dir, "value_type_text.tsv"))
    type_features = load_type_features(os.path.join(result_dir, 'selected_features.tsv'))
    event_des_file = os.path.join(result_dir, "event_des_text.tsv")
    feature_des_file = os.path.join(result_dir, "feature_des.tsv")
    builders = gen_builders(type_features, text_map, event_des_file, feature_des_file)
    if not os.path.exists(event_dir):
        os.mkdir(event_dir)
    for filepath in glob.glob(data_dir + "/*tsv"):
        name = os.path.basename(filepath)
        # if name in ["labevents.tsv", "datetimeevents.tsv"]:
        # if filepath.find("labevents") == -1:
        #     continue
        build_event(filepath, builders)
    print "#TimeDuration < 0 error =", TimeFeatureExtractor.nerror

    # print_event(builders, "static_data/event_des.txt")
    # print builders['labevents.51294'].feature_texts
