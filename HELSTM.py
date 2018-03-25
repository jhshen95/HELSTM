import numpy as np
import theano
import theano.tensor as T 
import lasagne
from lasagne import nonlinearities
from lasagne import init
from lasagne.layers.base import MergeLayer, Layer
from lasagne.layers.recurrent import Gate 

class HELSTMGate(object):
    def __init__(self, 
                Period=init.Uniform((10, 100)),
                Shift=init.Uniform((0.,1000.)),
                On_End=init.Constant(0.05),
                Event_W=init.GlorotUniform(),
                Event_b=init.Constant(0.),
                out_W=init.GlorotUniform(),
                out_b=init.Constant(0.)):

        self.Period = Period
        self.Shift = Shift
        self.On_End = On_End
        self.Event_W = Event_W
        self.Event_b = Event_b
        self.out_W = out_W
        self.out_b = out_b

class HELSTMLayer(MergeLayer):
    def __init__(self, incoming, time_input, event_input,
                num_units, num_attention, model='HELSTM',#model options: LSTM, PLSTM or HELSTM
                mask_input=None,
                ingate=Gate(),
                forgetgate=Gate(),
                cell=Gate(W_cell=None, nonlinearity=nonlinearities.tanh),
                timegate=HELSTMGate(),
                nonlinearity=nonlinearities.tanh,
                cell_init=init.Constant(0.),
                hid_init=init.Constant(0.),
                outgate=Gate(),
                backwards=False,
                learn_init=False,
                peepholes=True,
                grad_clipping=0,
                bn=False,
                only_return_final=False,
                off_alpha=1e-3,
                **kwargs):
        incomings = [incoming, time_input, event_input]
        self.time_incoming_idx = 1
        self.event_incoming_idx = 2
        self.mask_incoming_index = -2
        self.hid_init_incoming_index = -2
        self.cell_init_incoming_index = -2

        if mask_input is not None:
            incomings.append(mask_input)
            self.mask_incoming_index = len(incomings)-1
        if isinstance(hid_init, Layer):
            incomings.append(hid_init)
            self.hid_init_incoming_index = len(incomings)-1
        if isinstance(cell_init, Layer):
            incomings.append(cell_init)
            self.cell_init_incoming_index = len(incomings)-1

        super(HELSTMLayer, self).__init__(incomings, **kwargs)

        self.nonlinearity = nonlinearity
        self.learn_init=learn_init
        self.num_units = num_units
        self.num_attention = num_attention
        self.peepholes = peepholes
        self.grad_clipping = grad_clipping
        self.backwards = backwards
        self.off_alpha = off_alpha
        self.only_return_final = only_return_final
        self.model = model
        if self.model == 'LSTM':
            print 'using LSTM'
        elif self.model == 'PLSTM':
            print 'using PLSTM'
        else:
            assert self.model=='HELSTM'
            print 'using HELSTM'

        input_shape = self.input_shapes[0]
        num_inputs = np.prod(input_shape[2:])

        def add_gate_params(gate, gate_name):
            return (self.add_param(gate.W_in, (num_inputs, num_units),
                                   name="W_in_to_{}".format(gate_name)),
                    self.add_param(gate.W_hid, (num_units, num_units),
                                   name="W_hid_to_{}".format(gate_name)),
                    self.add_param(gate.b, (num_units,),
                                   name="b_{}".format(gate_name),
                                   regularizable=False),
                    gate.nonlinearity)

        # Add in parameters from the supplied Gate instances
        (self.W_in_to_ingate, self.W_hid_to_ingate, self.b_ingate,
         self.nonlinearity_ingate) = add_gate_params(ingate, 'ingate')

        (self.W_in_to_forgetgate, self.W_hid_to_forgetgate, self.b_forgetgate,
         self.nonlinearity_forgetgate) = add_gate_params(forgetgate,
                                                         'forgetgate')

        (self.W_in_to_cell, self.W_hid_to_cell, self.b_cell,
         self.nonlinearity_cell) = add_gate_params(cell, 'cell')

        (self.W_in_to_outgate, self.W_hid_to_outgate, self.b_outgate,
         self.nonlinearity_outgate) = add_gate_params(outgate, 'outgate')

        # If peephole (cell to gate) connections were enabled, initialize
        # peephole connections.  These are elementwise products with the cell
        # state, so they are represented as vectors.
        if self.peepholes:
            self.W_cell_to_ingate = self.add_param(
                ingate.W_cell, (num_units, ), name="W_cell_to_ingate")

            self.W_cell_to_forgetgate = self.add_param(
                forgetgate.W_cell, (num_units, ), name="W_cell_to_forgetgate")

            self.W_cell_to_outgate = self.add_param(
                outgate.W_cell, (num_units, ), name="W_cell_to_outgate")

        # Setup initial values for the cell and the hidden units
        if isinstance(cell_init, Layer):
            self.cell_init = cell_init
        else:
            self.cell_init = self.add_param(
                cell_init, (1, num_units), name="cell_init",
                trainable=learn_init, regularizable=False)

        if isinstance(hid_init, Layer):
            self.hid_init = hid_init
        else:
            self.hid_init = self.add_param(
                hid_init, (1, self.num_units), name="hid_init",
                trainable=learn_init, regularizable=False)

        if bn:
            self.bn = lasagne.layers.BatchNormLayer(input_shape, axes=(0,1))  # create BN layer for correct input shape
            self.params.update(self.bn.params)  # make BN params your params
        else:
            self.bn = False

        def add_timegate_params(gate, gate_name, attention=False):
            params = [self.add_param(gate.Period, (num_units, ),
                                      name="Period_{}".format(gate_name)),
                       self.add_param(gate.Shift, (num_units, ),
                                         name="Shift_{}".format(gate_name)),
                       self.add_param(gate.On_End, (num_units, ),
                                         name="On_End_{}".format(gate_name))]
            if attention:
                params += [self.add_param(gate.Event_W, (num_inputs, num_attention),
                                          name="Event_W_{}".format(gate_name)),
                           self.add_param(gate.Event_b, (num_attention, ),
                                             name="Event_b_{}".format(gate_name)),
                           self.add_param(gate.out_W, (num_attention, num_units),
                                             name="out_b_{}".format(gate_name)),
                           self.add_param(gate.out_b, (num_units, ),
                                             name="out_b_{}".format(gate_name))]
            return params

        if model!='LSTM':
            if model=='PLSTM':
                (self.period_timegate, self.shift_timegate, self.on_end_timegate) = add_timegate_params(timegate, 'timegate')
            else:
                assert model == 'HELSTM'
                (self.period_timegate, self.shift_timegate, self.on_end_timegate, 
                 self.event_w_timegate, self.event_b_timegate, self.out_w_timegate, self.out_b_timegate) = add_timegate_params(timegate, 'timegate', attention=True)

    def get_gate_params(self):
        gates = [self.period_timegate, self.shift_timegate, self.on_end_timegate]
        if self.model=="PLSTM":
            return gates
        else:
            assert self.model=="HELSTM"
            gates = gates + [self.event_w_timegate, self.event_b_timegate, self.out_w_timegate, self.out_b_timegate]
            return gates

    def get_output_shape_for(self, input_shapes):
        input_shape = input_shapes[0]
        if self.only_return_final:
            return input_shape[0], self.num_units
        else:
            return input_shape[0], input_shape[1], self.num_units

    def get_output_for(self, inputs, deterministic=False, **kwargs):
        input = inputs[0]
        time_input = inputs[self.time_incoming_idx]
        event_input = inputs[self.event_incoming_idx]

        mask = None
        hid_init = None
        cell_init = None
        if self.mask_incoming_index > 0:
            mask = inputs[self.mask_incoming_index]
        if self.hid_init_incoming_index > 0:
            hid_init = inputs[self.hid_init_incoming_index]
        if self.cell_init_incoming_index > 0:
            cell_init = inputs[self.cell_init_incoming_index]

        if self.bn:
            input = self.bn.get_output_for(input)

        input = input.dimshuffle(1, 0, 2)
        time_input = time_input.dimshuffle(1, 0)

        seq_len, num_batch, _ = input.shape

        # Stack input weight matrices into a (num_inputs, 4*num_units)
        # matrix, which speeds up computation
        W_in_stacked = T.concatenate(
            [self.W_in_to_ingate, self.W_in_to_forgetgate,
             self.W_in_to_cell, self.W_in_to_outgate], axis=1)

        # Same for hidden weight matrices
        W_hid_stacked = T.concatenate(
            [self.W_hid_to_ingate, self.W_hid_to_forgetgate,
             self.W_hid_to_cell, self.W_hid_to_outgate], axis=1)

        # Stack biases into a (4*num_units) vector
        b_stacked = T.concatenate(
            [self.b_ingate, self.b_forgetgate,
             self.b_cell, self.b_outgate], axis=0)

        input = T.dot(input, W_in_stacked) + b_stacked

        # PHASED LSTM: If test time, off-phase means really shut.
        if deterministic:
            print('Using true off for testing.')
            off_slope = 0.0
        else:
            print('Using {} for off_slope.'.format(self.off_alpha))
            off_slope = self.off_alpha

        if self.model != 'LSTM':
            # PHASED LSTM: Pregenerate broadcast vars.
            #   Same neuron in different batches has same shift and period.  Also,
            #   precalculate the middle (on_mid) and end (on_end) of the open-phase
            #   ramp.
            shift_broadcast = self.shift_timegate.dimshuffle(['x',0])
            period_broadcast = T.abs_(self.period_timegate.dimshuffle(['x',0]))
            on_mid_broadcast = T.abs_(self.on_end_timegate.dimshuffle(['x',0])) * 0.5 * period_broadcast
            on_end_broadcast = T.abs_(self.on_end_timegate.dimshuffle(['x',0])) * period_broadcast

        if self.model == 'HELSTM':
            event_W = self.event_w_timegate
            event_b = T.shape_padleft(self.event_b_timegate, 2)
            out_W = self.out_w_timegate
            out_b = T.shape_padleft(self.out_b_timegate, 2)
            hid_attention = nonlinearities.leaky_rectify(T.dot(event_input, event_W) + event_b)
            out_attention = nonlinearities.sigmoid(T.dot(hid_attention, out_W) + out_b)
            out_attention = out_attention.dimshuffle(1, 0, 2)

        def slice_w(x, n):
            return x[:, n*self.num_units:(n+1)*self.num_units]

        def step(input_n, cell_previous, hid_previous, *args):
            gates = input_n + T.dot(hid_previous, W_hid_stacked)

            # Clip gradients
            if self.grad_clipping:
                gates = theano.gradient.grad_clip(
                    gates, -self.grad_clipping, self.grad_clipping)

            # Extract the pre-activation gate values
            ingate = slice_w(gates, 0)
            forgetgate = slice_w(gates, 1)
            cell_input = slice_w(gates, 2)
            outgate = slice_w(gates, 3)

            if self.peepholes:
                # Compute peephole connections
                ingate += cell_previous*self.W_cell_to_ingate
                forgetgate += cell_previous*self.W_cell_to_forgetgate

            # Apply nonlinearities
            ingate = self.nonlinearity_ingate(ingate)
            forgetgate = self.nonlinearity_forgetgate(forgetgate)
            cell_input = self.nonlinearity_cell(cell_input)                

            # Mix in new stuff
            cell = forgetgate*cell_previous + ingate*cell_input

            if self.peepholes:
                outgate += cell*self.W_cell_to_outgate
            outgate = self.nonlinearity_outgate(outgate)     
            
            # Compute new hidden unit activation
            hid = outgate*self.nonlinearity(cell)
            return [cell, hid]      
            
        # PHASED LSTM: The actual calculation of the time gate
        def calc_time_gate(time_input_n):
            # Broadcast the time across all units
            t_broadcast = time_input_n.dimshuffle([0,'x'])
            # Get the time within the period
            in_cycle_time = T.mod(t_broadcast + shift_broadcast, period_broadcast)
            # Find the phase
            is_up_phase = T.le(in_cycle_time, on_mid_broadcast)
            is_down_phase = T.gt(in_cycle_time, on_mid_broadcast)*T.le(in_cycle_time, on_end_broadcast)

            # Set the mask
            sleep_wake_mask = T.switch(is_up_phase, in_cycle_time/on_mid_broadcast,
                                T.switch(is_down_phase,
                                    (on_end_broadcast-in_cycle_time)/on_mid_broadcast,
                                        off_slope*(in_cycle_time/period_broadcast)))

            return sleep_wake_mask

        #HELSTM: Mask the updates based on the time phase and event attention
        def step_masked(input_n, time_input_n, event_input_n, mask_n, cell_previous, hid_previous, *args):
            cell, hid = step(input_n, cell_previous, hid_previous, *args)

            if self.model != 'LSTM':
                # Get time gate openness
                sleep_wake_mask = calc_time_gate(time_input_n)

                if self.model == 'HELSTM':
                      sleep_wake_mask = event_input_n*sleep_wake_mask

                # Sleep if off, otherwise stay a bit on
                cell = sleep_wake_mask*cell + (1.-sleep_wake_mask)*cell_previous
                hid = sleep_wake_mask*hid + (1.-sleep_wake_mask)*hid_previous

            #Skip over any input with mask 0 by copying the previous
            #hidden state; proceed normally for any input with mask 1.
            cell = T.switch(mask_n, cell, cell_previous)
            hid = T.switch(mask_n, hid, hid_previous)

            return [cell, hid]

        if mask is not None:
            # mask is given as (batch_size, seq_len). Because scan iterates
            # over first dimension, we dimshuffle to (seq_len, batch_size) and
            # add a broadcastable dimension
            mask = mask.dimshuffle(1, 0, 'x')
        else:
            mask = T.ones_like(time_input).dimshuffle(0,1,'x')

        if self.model != 'HELSTM':
            out_attention = event_input#if not using HELSTM, out_attention is of no use but still need to assign a value to complete sequences
        sequences = [input, time_input, out_attention, mask]
        step_fun = step_masked

        ones = T.ones((num_batch, 1))
        if not isinstance(self.cell_init, Layer):
            # Dot against a 1s vector to repeat to shape (num_batch, num_units)
            cell_init = T.dot(ones, self.cell_init)

        if not isinstance(self.hid_init, Layer):
            # Dot against a 1s vector to repeat to shape (num_batch, num_units)
            hid_init = T.dot(ones, self.hid_init)

        # Scan op iterates over first dimension of input and repeatedly
        # applies the step function
        cell_out, hid_out = theano.scan(
            fn=step_fun,
            sequences=sequences,
            outputs_info=[cell_init, hid_init],
            go_backwards=self.backwards)[0]

        # When it is requested that we only return the final sequence step,
        # we need to slice it out immediately after scan is applied
        if self.only_return_final:
            hid_out = hid_out[-1]
        else:
            # dimshuffle back to (n_batch, n_time_steps, n_features))
            hid_out = hid_out.dimshuffle(1, 0, 2)

            # if scan is backward reverse the output
            if self.backwards:
                hid_out = hid_out[:, ::-1]

        return hid_out
