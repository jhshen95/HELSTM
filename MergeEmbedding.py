import numpy as np
import theano
import theano.tensor as T

import lasagne

from lasagne.layers.base import MergeLayer, Layer
from lasagne.layers.input import InputLayer

class MergeEmbeddingLayer(MergeLayer):
	"""
	output: embed_event + T.sum(embed_feature_idx * tanh(feature_trans*(feature_value + embed_feature_b)), axis=2)
	"""

	def __init__(self, embed_event, embed_feature_idx, embed_feature_b, embed_feature_trans, feature_value, **kwargs):
		incomings = [embed_event, embed_feature_idx, embed_feature_b, embed_feature_trans, feature_value]
		super(MergeEmbeddingLayer, self).__init__(incomings, **kwargs)

	def get_output_shape_for(self, input_shapes):
		input_shape = input_shapes[0]
		return input_shape

	def get_output_for(self, inputs, deterministic=False, **kwargs):
		event = inputs[0]#(None, 1000, embed)
		feature_idx = inputs[1]  #(None, 1000, feature_num, embed)
		feature_b = inputs[2]    #(None, 1000, feature_num, 1)
		feature_trans = inputs[3]#(None, 1000, feature_num, 1)
		feature_value = inputs[4]#(None, 1000, feature_num)
		value_up = T.shape_padright(feature_value, 1)#(None, 1000, feature_num, 1)
		bias_value = feature_trans*(value_up + feature_b)
		bias_value_broad = T.addbroadcast(bias_value, 3)#make the last axis broadcastable
		v_idx = T.sum(feature_idx * lasagne.nonlinearities.tanh(bias_value_broad), axis=2)#(None, 1000, embed)
		return v_idx + event

