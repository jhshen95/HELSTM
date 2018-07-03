from util import connect, date2str, time2str, data_dir
import os
import sys
from datetime import timedelta
from extractor import *

true_test_extractor = ConstantExtractor(True)
exist_test = lambda x: x is not None and x != ''

def get_patients_extractors(data_dir, extractor_map):
    extractors = []
    table = "patients"

    id_extractor = MultiExtractor(names = ['subject_id'])
    dob_time_extractor = TimeExtractor(name = 'dob', converter = date2str)
    dob_type_extractor = FmtExtractor(names = [], fmt = "patients.dob")
    dob_value_extractor = ConstantExtractor("FLAG")
    dob_test = lambda x: x.year >= 1900
    dob_test_extractor = TestExtractor(name = 'dob', test = dob_test)
    dob_extractor = ExtractorInfo(table, os.path.join(data_dir, table + '.dob.tsv'), id_extractor, 
                                dob_time_extractor, dob_type_extractor,
                                dob_value_extractor, dob_test_extractor)
    extractors.append(dob_extractor)

    dod_out_path = os.path.join(data_dir, table + ".dod.tsv")
    dod_type_extractor = FmtExtractor(names = [], fmt = "patients.dod")
    dod_time_extractor = TimeExtractor(name = 'dod', converter = date2str)
    dod_value_extractor = ConstantExtractor("FLAG")
    dod_test = exist_test
    dod_test_extractor = TestExtractor(name = 'dod', test = dod_test)
    dod_extractor = ExtractorInfo(table, dod_out_path, id_extractor,
                                dod_time_extractor, dod_type_extractor,
                                dod_value_extractor, dod_test_extractor)
    extractors.append(dod_extractor)
    extractor_map[table] = extractors
    return table

def get_admissions_extractors(data_dir, extractor_map):
    extractors = []
    table = "admissions"

    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")
    admit_outpath = os.path.join(data_dir, table + ".admittime.tsv")
    admit_time_ext = TimeExtractor(name = 'admittime', converter = time2str)
    admit_type_ext = FmtExtractor(names = [], fmt = "admissions.admit")
    admmit_value_ext = MultiExtractor(names = ['admission_type'])
    admit_test_ext = TestExtractor(name = 'admission_type', test = exist_test)
    admit_extractor = ExtractorInfo(table, admit_outpath, id_extractor,
                                    admit_time_ext, admit_type_ext,
                                    admmit_value_ext, admit_test_ext)
    extractors.append(admit_extractor)

    disch_outpath = os.path.join(data_dir, table + ".dischtime.tsv")
    disch_time_ext = TimeExtractor(name = "dischtime", converter = time2str)
    disch_type_ext = FmtExtractor(names = [], fmt = "admissions.disch")
    disch_value_ext = ConstantExtractor("FLAG")
    disch_test_ext = true_test_extractor
    disch_extractor = ExtractorInfo(table, disch_outpath, id_extractor,
                                    disch_time_ext, disch_type_ext,
                                    disch_value_ext, disch_test_ext)
    extractors.append(disch_extractor)

    death_outpath = os.path.join(data_dir, table + ".deathtime.tsv")
    death_time_ext = TimeExtractor(name = 'deathtime', converter = time2str)
    death_type_ext = FmtExtractor(names = [], fmt = "admissions.death")
    death_value_ext = ConstantExtractor("FLAG")
    death_test_ext = TestExtractor(name = 'deathtime', test = exist_test)
    death_extractor = ExtractorInfo(table, death_outpath, id_extractor,
                                    death_time_ext, death_type_ext,
                                    death_value_ext, death_test_ext)
    extractors.append(death_extractor)

    extractor_map[table] = extractors
    return table

def get_icustays_extractors(data_dir, extractor_map):
    extractors = []
    table = 'icustays'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = "_")

    intime_outpath = os.path.join(data_dir, table + '.tsv')
    intime_time_ext = TimeExtractor(name = 'intime', converter = time2str)
    intime_type_ext = FmtExtractor(names = [], fmt = 'icustays')
    intime_value_ext = MultiExtractor(names = ['outtime'])
    intime_test_ext = TestExtractor(name = 'outtime', test = exist_test)
    intime_extractor = ExtractorInfo(table, intime_outpath, id_extractor,
                                    intime_time_ext, intime_type_ext,
                                    intime_value_ext, intime_test_ext)
    extractors.append(intime_extractor)
    extractor_map[table] = extractors
    return table


# def get_callout_extractors(data_dir, extractor_map):
#   extractors = []
#   table = 'callout'
#   id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")

#   create_outpath = os.path.join(data_dir, table + '.createtime.tsv')
#   create_time_ext = TimeExtractor(name = 'createtime', converter = time2str)
#   create_type_ext = FmtExtractor(names = [], fmt = 'callout.createtime')
#   create_value_ext = ConstantExtractor(1)
#   create_test_ext = true_test_extractor
#   create_extractor = ExtractorInfo(table, create_outpath, id_extractor,
#                                   create_time_ext, create_type_ext,
#                                   create_value_ext, create_test_ext)
#   extractors.append(create_extractor)

#   update_outpath = os.path.join(data_dir, table + ".updatetime.tsv")
#   update_time_ext = TimeExtractor(name = 'updatetime', converter = time2str)
#   update_type_ext = FmtExtractor(names = [], fmt = 'callout.updatetime')
#   update_value_ext = ConstantExtractor(1)
#   update_test_ext = true_test_extractor
#   update_extractor = ExtractorInfo(table, update_outpath, id_extractor,
#                                   update_time_ext, update_type_ext,
#                                   update_value_ext, update_test_ext)
#   extractors.append(update_extractor)

#   ack_outpath = os.path.join(data_dir, table + ".acknowledgetime.tsv")
#   ack_time_ext = TimeExtractor(name = 'acknowledgetime', converter = time2str)
#   ack_type_ext = FmtExtractor(names = [], fmt = 'callout.acknowledge')
#   ack_value_ext = MultiExtractor(names = ['acknowledge_status'])
#   ack_test_ext = TestExtractor(name = 'acknowledgetime', test = exist_test)
#   # ack_test_ext = TestExtractor(name = 'acknowledge')
#   ack_extractor = ExtractorInfo(table, ack_outpath, id_extractor,
#                               ack_time_ext, ack_type_ext, 
#                               ack_value_ext, ack_test_ext)
#   extractors.append(ack_extractor)

#   outcome_outpath = os.path.join(data_dir, table + '.outcome.tsv')
#   outcome_time_ext = TimeExtractor(name = 'outcometime', converter = time2str)
#   outcome_type_ext = FmtExtractor(names = [], fmt = 'callout.outcome')
#   outcome_value_ext = MultiExtractor(names = ['callout_outcome'])
#   outcome_test_ext = true_test_extractor
#   outcome_extractor = ExtractorInfo(table, outcome_outpath, id_extractor,
#                                   outcome_time_ext, outcome_type_ext,
#                                   outcome_value_ext, outcome_test_ext)
#   extractors.append(outcome_extractor)

#   extractor_map[table] = extractors
#   return table


def get_labevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'labevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")

    outpath = os.path.join(data_dir, table + '.tsv')
    time_ext = TimeExtractor(name = 'charttime', converter = time2str)
    type_ext = FmtExtractor(names = ['itemid'], fmt = 'labevents.%s')
    # value unit flag
    # value_ext = MultiExtractor(names = ['value', 'valueuom', 'flag'])
    value_ext = MultiExtractor(names = ['value', 'flag'])
    test_ext = TestExtractor(name = "value", test = exist_test)
    extractor = ExtractorInfo(table, outpath,  id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)    
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_microbiologyevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'microbiologyevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")

    outpath = os.path.join(data_dir, table + '.tsv')
    charttime_ext = TimeExtractor(name = 'charttime', converter = time2str)
    chartdate_ext = TimeExtractor(name = 'chartdate', converter = date2str)
    time_ext = SelectExtractor([charttime_ext, chartdate_ext])
    # specimen organ ab
    type_ext = FmtExtractor(names = ['spec_itemid', 'org_itemid', 'ab_itemid'], fmt = 'microbioevents.%s&%s&%s')
    #  text comp value inter
    value_ext = MultiExtractor(names = ['dilution_text', 'dilution_comparison', 'dilution_value', 'interpretation'])
    test_ext = TestExtractor(name = 'interpretation', test = exist_test)
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_outputevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'outputevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = "_")

    outpath = os.path.join(data_dir, table + '.tsv')
    time_ext = TimeExtractor(name = 'charttime', converter = time2str)
    type_ext = FmtExtractor(names = ['itemid'], fmt = 'outputevents.%s')
    # value_ext = MultiExtractor(names = ['value', 'valueuom'])
    value_ext = MultiExtractor(names = ['value'])
    test_ext = TestExtractor(name = "value", test = exist_test)
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_diagnoses_extractors(data_dir, extractor_map):
    extractors = []
    table = 'diagnoses_icd'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")

    outpath = os.path.join(data_dir, table + ".tsv")
    time_ext = ConstantExtractor(None)
    type_ext = FmtExtractor(names = [], fmt = 'diagnoses_icd')
    value_ext = MultiExtractor(names = ['seq_num', 'icd9_code'])
    test_ext = true_test_extractor
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_prescriptions_extractors(data_dir, extractor_map):
    extractors = []
    table = 'prescriptions'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = "_")

    st_outpath = os.path.join(data_dir, table + '.tsv')
    sttime_ext = TimeExtractor(name = 'startdate', converter = date2str)
    st_type_ext = FmtExtractor(names = [], fmt = 'prescriptions')
    value_ext = MultiExtractor(names = ['enddate', 'formulary_drug_cd'])
    st_test_ext = TestExtractors(names = ['startdate', 'enddate', 'formulary_drug_cd'],
                                 test = exist_test)
    st_extractor = ExtractorInfo(table, st_outpath, id_extractor,
                            sttime_ext, st_type_ext,
                            value_ext, st_test_ext)
    extractors.append(st_extractor)

    extractor_map[table] = extractors
    return table

def get_datetimeevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'datetimeevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = "_")

    outpath = os.path.join(data_dir, table + '.tsv')
    time_ext = TimeExtractor(name = 'charttime', converter = time2str)
    type_ext = FmtExtractor(names = ['itemid'], fmt = 'datetimeevents.%s')
    value_ext = ConstantExtractor("Flag")
    test_ext = TestExtractor(name = 'charttime', test = exist_test)
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_chartevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'chartevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = '_')

    outpath = os.path.join(data_dir, table + ".tsv")
    time_ext = TimeExtractor(name = 'charttime', converter = time2str)
    type_ext = FmtExtractor(names = ['itemid'], fmt = 'chartevents.%s')
    value_ext = MultiExtractor(names = ['value'])
    test_ext = TestExtractor(name = 'value', test = exist_test)
    tables = []
    for i in range(1, 15):
        sub_table = table + "_" + str(i)
        sub_outpath = os.path.join(data_dir, "chartevents_%d.tsv" %(i))
        extractor = ExtractorInfo(sub_table, sub_outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
        extractor_map[sub_table] =  [extractor]
        tables.append(sub_table)

    return tables

def get_proceduresicd_extractors(data_dir, extractor_map):
    extractors = []
    table = 'procedures_icd'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'],  sep = "_")

    outpath = os.path.join(data_dir, table + ".tsv")
    time_ext = ConstantExtractor(None)
    type_ext = FmtExtractor(names = [], fmt = 'procedures_icd')
    value_ext = MultiExtractor(names = ['seq_num', 'icd9_code'])
    test_ext = true_test_extractor
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_procedureevents_extractors(data_dir, extractor_map):
    extractors = []
    table =  "procedureevents_mv"
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = "_")

    st_outpath = os.path.join(data_dir, table + ".tsv")
    st_time_ext = TimeExtractor(name = 'starttime', converter = time2str)
    st_type_ext = FmtExtractor(names = ['itemid'], fmt = 'procedureevents_mv.%s')
    # value_ext = MultiExtractor(names = ['endtime', 'value', 'valueuom'])
    value_ext = MultiExtractor(names = ['endtime', 'value'])
    test_ext = TestExtractors(names = ['endtime', 'value'], test = exist_test)

    st_extractor = ExtractorInfo(table, st_outpath, id_extractor,
                                st_time_ext, st_type_ext,
                                value_ext, test_ext)
    extractors.append(st_extractor)

    extractor_map[table] = extractors
    return table

def get_inputevents_cv_extractors(data_dir, extractor_map):
    extractors = []
    table = 'inputevents_cv'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = '_')

    outpath = os.path.join(data_dir, table + ".tsv")
    time_ext = TimeExtractor(name = 'charttime', converter = time2str)
    type_ext = FmtExtractor(names = ['itemid'], fmt = 'inputevents_cv.%s')
    # value_ext = MultiExtractor(names = ['amount', 'amountuom', 'rate', 'rateuom'])
    value_ext = MultiExtractor(names = ['amount', 'rate'])
    test_ext = TestExtractor(name = 'amount', test = exist_test)
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)

    extractor_map[table] = extractors
    return table

def get_inputevents_mv_extractors(data_dir, extractor_map):
    extractors = []
    table = 'inputevents_mv'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id', 'icustay_id'], sep = '_')

    st_outpath = os.path.join(data_dir, table + ".tsv")
    st_time_ext = TimeExtractor(name = 'starttime', converter = time2str)
    st_type_ext = FmtExtractor(names = ['itemid'], fmt = 'inputevents_mv.%s')
    # value_ext = MultiExtractor(names = ['endtime', 'amount', 'amountuom', 'rate', 'rateuom'])
    value_ext = MultiExtractor(names = ['endtime', 'amount', 'rate'])
    test_ext = TestExtractors(names = ['endtime', 'amount'], test = exist_test)

    st_extractor = ExtractorInfo(table, st_outpath, id_extractor,
                                st_time_ext, st_type_ext,
                                value_ext, test_ext)
    extractors.append(st_extractor)

    extractor_map[table] = extractors;
    return table

def get_cptevents_extractors(data_dir, extractor_map):
    extractors = []
    table = 'cptevents'
    id_extractor = MultiExtractor(names = ['subject_id', 'hadm_id'], sep = "_")

    outpath = os.path.join(data_dir, table + '.tsv')
    time_ext = MultiExtractor(names = ['chartdate'])
    type_ext = FmtExtractor(names = [], fmt = 'cptevents')
    value_ext = MultiExtractor(names = ['cpt_cd', 'ticket_id_seq'])
    test_ext = true_test_extractor
    extractor = ExtractorInfo(table, outpath, id_extractor,
                            time_ext, type_ext,
                            value_ext, test_ext)
    extractors.append(extractor)
    extractor_map[table] = extractors
    return table




if __name__ == '__main__':

    extractor_map = {}
    funcs = [get_patients_extractors, get_admissions_extractors, get_icustays_extractors, 
    get_labevents_extractors, get_microbiologyevents_extractors, get_outputevents_extractors, get_diagnoses_extractors,
    get_prescriptions_extractors, get_datetimeevents_extractors, get_chartevents_extractors, get_proceduresicd_extractors,
    get_procedureevents_extractors, get_inputevents_cv_extractors, get_inputevents_mv_extractors, get_cptevents_extractors]

    # funcs = [get_labevents_extractors]
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    tables = []
    for func in funcs:
        table = func(data_dir, extractor_map)
        if type(table) == list:
            tables.extend(table)
        else:
            tables.append(table)
    for table in tables[:]:
        extract_from_table(table, extractor_map[table], only_test = False, limit = 1000000)

        





