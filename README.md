# HELSTM
This is the model "Heterogeneous Event LSTM"(HELSTM) for the paper "Learning the Joint Representation of Heterogeneous Temporal Events for Clinical Endpoint Prediction"

You can find the paper [here](https://arxiv.org/abs/1803.04837)

task.py shows how we used HELSTM to do end-to-end prediction. Data will be load from "/data/", or you can change data_path in task.py.

We divided all data into three parts: train_data, valid_data and test_datam, and processed data into h5py format, containing "time", "label", "event", "feature_id" and "feature_value". Data sequences should have the same length (by padding 0 in the end) and we set length to 1000 in task.py.

How to use the data generator:
1.put extractor.cpp and dataExt.py under the same directory as the origin mimic data.
2.compile and run extractor.cpp as:
g++ extractor.cpp -o extractor
./extractor
3.run dataExt.py as
python dataExt.py
