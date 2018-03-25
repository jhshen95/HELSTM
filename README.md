# HELSTM
This is the model "Heterogeneous Event LSTM"(HELSTM) for the paper "Learning the Joint Representation of Heterogeneous Temporal Events for Clinical Endpoint Prediction"

You can find the paper [here](https://arxiv.org/abs/1803.04837)

task.py shows how we used HELSTM to do end-to-end prediction. Data will be load from "/data/", or you can change data_path in task.py.

We divided all data into three parts: train_data, valid_data and test_datam, and processed data into h5py format, containing "time", "label", "event", "feature_id" and "feature_value". Data sequences should have the same length (by padding 0 in the end) and we set length to 1000 in task.py.
