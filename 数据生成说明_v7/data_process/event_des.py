from util import *
import json

def load_event_des_pattern():
    event_des = {}
    labevents_items = load_items(os.path.join(static_data_dir, 'labitem_code.tsv'))
    d_items = load_items(os.path.join(static_data_dir, 'item_code.tsv'))
    rtype = None
    for line in file(os.path.join(result_dir, "selected_features.tsv"), 'r'):
        line = line.rstrip()
        if line.startswith("\t"):
            line = line.lstrip('\t')
            p = line.split(" ")
            feature_type = p[1]
            if feature_type == "text":
                event_des[rtype]['feature'].append("text")
            else:
                event_des[rtype]['feature'].append('feature')
        else:
            rtype = line.split("#")[0]
            p = rtype.split(".")
            table = p[0]
            des = table
            if len(p) > 1:
                item_id = p[1]
                if is_number(p[1]):
                    if table == "labevents":
                        des = labevents_items[int(item_id)]
                    else:
                        des = d_items[int(item_id)]
            event_des[rtype] = {"des":des, "feature":[]}
    return event_des
            

def column_name_map():
    return {
        "admissions.admit": ["admission_type"],
        "admissions.disch": ["FLAG"],
        "admissions.death": ["FLAG"],
        "icustays": ["outtime"],
        "labevents": ["value", "flag"],
        "chartevents": ['value'],
        'inputevents_cv': ['amount', 'rate'],
        "inputevents_mv": ['endtime', 'amount', 'rate'],
        "outputevents": ['value'],
        "procedureevents_mv": ['endtime', 'value'],
        "datetimeevents": ['Flag']

    }

def get_event_text_map():
    ret = {}
    for line in file(os.path.join(result_dir, "event_des_text.tsv")):
        parts = line.strip("\n").split(" ")
        event_id = int(parts[0])
        event_type = parts[1]
        value = " ".join(parts[2:]).split("\t")
        ret[event_id] = value
    return ret

def get_id2rtype():
    ret = {}
    for line in file(os.path.join(result_dir, "event_des_text.tsv")):
        parts = line.strip("\n").split(" ")
        event_id = int(parts[0])
        event_type = parts[1]
        value = " ".join(parts[2:]).split("\t")
        ret[event_id] = event_type
    return ret

def load_event_featureidx_map():
    ret ={}
    for line in file(os.path.join(result_dir, 'feature_des.tsv')):
        parts = line.strip().split('\t')
        rtype = parts[0]
        ret[rtype] = []
        for feature_idx in parts[1:]:
            ret[rtype].append(int(feature_idx))
    return ret
            
def get_feature(feature, idx):
    return feature[idx]

class EventDescription:
    def __init__(self):
        self.column_map = column_name_map()
        self.event_text_map = get_event_text_map()
        self.event_des_pattern = load_event_des_pattern()
        self.id2rtype = get_id2rtype()
        self.event_featureidx_map = load_event_featureidx_map()

    def get_name(self, rtype):
        if rtype in self.column_map:
            return self.column_map[rtype]
        table = rtype.split('.')[0]
        return self.column_map[table]

    def reverse_text_feature_name(self, names, feature_types):
        f_names = []
        text_names = []
        for name, f_type in zip(names, feature_types):
            if f_type == "text":
                text_names.append(name)
            else:
                f_names.append(name)
        text_names.reverse()
        t_idx = 0
        f_idx = 0
        new_names = []
        for f_type in feature_types:
            if f_type == "text":
                new_names.append(text_names[t_idx])
                t_idx += 1
            else:
                new_names.append(f_names[f_idx])
                f_idx += 1
        return new_names

    def get_des(self, event_id, feature_pair):
        text_features = self.event_text_map[event_id]
        rtype = self.id2rtype[event_id]
        names = self.get_name(rtype)
        
        num_feature_idx = self.event_featureidx_map.get(rtype, [])
        pattern = self.event_des_pattern[rtype]
        names = self.reverse_text_feature_name(names, pattern['feature'])
        text_idx = 0
        num_idx = 0
        features = []
        ret = ["event = " + pattern['des'], '{']
        for feature_type in pattern['feature']:
            if feature_type == "text":
                features.append(text_features[text_idx])
                text_idx += 1
            else:
                idx = num_feature_idx[num_idx]
                num_idx += 1
                features.append(get_feature(feature_pair, idx))
        for idx, feature in enumerate(features):
            name = names[idx]
            ret.append(name + " = " + str(feature))
        ret.append('}')
        return ret 
            
def write_feature_info(out_path):
    event_des = EventDescription()
    outf = file(out_path, 'w')

    for event_id in range(2, max(event_des.id2rtype.keys()) + 1):
        rtype = event_des.id2rtype[event_id]

        names = event_des.get_name(rtype)
        
        obj = {
            "event_id": event_id,
            "rtype": rtype,
            'text_feature': [],
            "feature": [],
        }

        num_feature_idx = event_des.event_featureidx_map.get(rtype, [])
        pattern = event_des.event_des_pattern[rtype]
        names = event_des.reverse_text_feature_name(names, pattern['feature'])
        text_features = event_des.event_text_map[event_id]
        text_idx = 0
        num_idx = 0
        for name, feature_type in zip(names, pattern['feature']):
            if feature_type == 'text':
                value = text_features[text_idx]
                text_idx += 1
                obj['text_feature'].append("%s=%s" %(name, value))
            else:
                index = num_feature_idx[num_idx]
                num_idx += 1
                obj['feature'].append("%s at %d" %(name, index))\

        outf.write('%s\n' %(json.dumps(obj)) )

    outf.close()



        



if __name__ == "__main__":
    write_feature_info(os.path.join(result_dir, 'feature_info.tsv'))
    # event_des = EventDescription()
    # feas = np.zeros(649)
    # feas[233] = 50
    # feas[234] = 30
    # print "\n".join(event_des.get_des(1726, feas))

