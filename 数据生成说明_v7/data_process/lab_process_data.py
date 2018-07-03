import h5py
import numpy as np
import time

seq_len = 200

def time_to_stamp(time_string, start, time_format='%Y-%m-%d %H:%M:%S'):
	if (time_string==""):
		return -10800.
	return time.mktime(time.strptime(time_string, time_format)) - start

def load_data(path, start, end):
	f = h5py.File(path)
	labels = f['label'][start:end]
	events = f['event'][start:end]
	times = f['time'][start:end]
	features = f['feature'][start:end]

	time_shift = []
	for id in xrange(times.shape[0]):
		event_time = times[id]
		event_shift = []
		start_time = time_to_stamp(event_time[0], 0.)
		for i in xrange(event_time.shape[0]):
			event_shift.append(time_to_stamp(event_time[i], start_time)/10800.)
		time_shift.append(event_shift)
	times = np.asarray(time_shift, dtype='float32')

	chosen_event = []
	chosen_time = []
	chosen_label = []
	chosen_feature_id = []
	chosen_feature_value = []
	tic = time.time()
	for id in xrange(labels.shape[0]):
		this_label = labels[id]
		this_event = events[id]
		this_feature_id = features[id][:,(0,2,4)]
		this_feature_value = features[id][:,(1,3,5)]
		this_time = times[id]

		chosen = this_label[(this_label[:,0]==34)+(this_label[:,0]==35)]#choose id 34 or 35
		for tmp in chosen:
			this_start = int(tmp[-1])
			this_end = int(tmp[-2])
			if this_end<=this_start+10:#ignore seq whose len<10
				continue
			if this_end>this_start+seq_len:#cut max seq len to seq_len
				this_start = this_end-seq_len
			pad_num = seq_len-this_end+this_start
			chosen_event.append(
				np.pad(this_event[this_start+1:this_end+1], ((0,pad_num),), 'constant'))
			chosen_time.append(
				np.pad(this_time[this_start+1:this_end+1], ((0,pad_num),), 'constant'))
			chosen_feature_id.append(
				np.pad(this_feature_id[this_start+1:this_end+1], ((0,pad_num),(0,0)), 'constant'))
			chosen_feature_value.append(
				np.pad(this_feature_value[this_start+1:this_end+1], ((0,pad_num),(0,0)), 'constant'))
			chosen_label.append(tmp[2])#use 0/1 as label

	chosen_event = np.asarray(chosen_event, dtype='int16')
	chosen_time = np.asarray(chosen_time, dtype='float32')
	chosen_feature_id = np.asarray(chosen_feature_id, dtype='int16')
	chosen_feature_value = np.asarray(chosen_feature_value, dtype='float32')
	chosen_label = np.asarray(chosen_label, dtype='float32')
	f.close()
	return chosen_event, chosen_time, chosen_feature_id, chosen_feature_value, chosen_label

def load_data_all(name, start, end):
	path = '../Data/Lab.h5'
	f = h5py.File('../Data/{}.h5'.format(name), 'w')
	events, times, feature_id, feature_value, labels = load_data(path, start, end)
	f['events'] = events
	f['times'] = times
	f['feature_id'] = feature_id
	f['feature_value'] = feature_value
	f['labels'] = labels
	f.close()

load_data_all('test', 0, 9112)
load_data_all('train', 9112, 41006)
load_data_all('valid', 41006, 45563)
