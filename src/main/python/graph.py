import numpy as np
import pandas as pd
import tensorflow as tf


def _outputToDF(node, nparray):
    return pd.DataFrame(nparray, columns=node.output_names)


class Graph:
    def __init__(self, nodes, edges):
        self._nodes = nodes.copy()
        self._edges = edges
        self._sess = tf.keras.backend.get_session()

    def group_train(self, train_x, train_s, aggregator, epochs=100):
        indices = {node: {name: i for i, name in enumerate(train_x[node]["states"].columns.values)} for node in train_x}
        predict_s = aggregator.aggregate({node: node.output_tensor() for node in self._nodes}, train_s.shape[0], indices)
        loss = tf.losses.mean_squared_error(tf.constant(train_s.to_numpy()), predict_s)
        optimizer = tf.train.GradientDescentOptimizer(0.01)
        train = optimizer.minimize(loss)
        last_percent = 0
        for i in range(epochs):
            _, loss_val = self._sess.run((train, loss), feed_dict={
                node.input_tensor(): self._prepare_node_input(train_x, node) for node in self._nodes
            })
            if int(i * 100.0 / epochs) > last_percent:
                last_percent = int(i * 100.0 / epochs)
                print("{} %, loss {}".format(last_percent, loss_val))

    def group_test(self, test_x, test_s, aggregator):
        indices = {node: {name: i for i, name in enumerate(test_x[node]["states"].columns.values)} for node in test_x}
        predict_s = aggregator.aggregate({node: node.output_tensor() for node in self._nodes}, test_s.shape[0], indices)
        loss = tf.losses.mean_squared_error(tf.constant(test_s.to_numpy()), predict_s)
        loss_val = self._sess.run(loss, feed_dict={
            node.input_tensor(): self._prepare_node_input(test_x, node) for node in self._nodes
        })
        return loss_val

    def learn_input(self, train_s, aggregator, epochs=100):
        def equal_predictions(extended_model):
            for node in extended_model:
                for i in range(len(node._model.get_weights())):
                    if not np.array_equal(node._model.get_weights()[i], extended_model[node].get_weights()[i]):
                        return False
                random_input = np.random.normal(size=(100, node.input_size()))
                output1 = node._model.predict(random_input)
                self._sess.run(tf.assign(extended_model[node].input, random_input, validate_shape=False))
                output2 = self._sess.run(extended_model[node].output)
                if not np.array_equal(np.round(output1, 4), np.round(output2, 4)):
                    return False
            return True

        n_samples = train_s.shape[0]
        extended_model = {node: node.extended_model(n_samples) for node in self._nodes}
        input_vars = {node: extended_model[node].input for node in self._nodes}
        assert equal_predictions(extended_model)

        indices = {node: {name: i for i, name in enumerate(node.output_names)} for node in self._nodes}
        predict_s = aggregator.aggregate({node: extended_model[node].output for node in self._nodes}, n_samples, indices)
        loss = tf.losses.mean_squared_error(tf.constant(train_s.to_numpy()), predict_s)
        train = tf.train.GradientDescentOptimizer(0.01).minimize(loss)

        for node in self._nodes:
            self._sess.run(tf.assign(input_vars[node], np.random.normal(size=(n_samples, node.input_size())), validate_shape=False))
            # print(node, self._sess.run(input_vars[node]))
        last_percent = 0
        for i in range(epochs):
            _, l = self._sess.run([train, loss])
            if int(i * 100.0 / epochs) > last_percent:
                last_percent = int(i * 100.0 / epochs)
                print("{} %, loss {}".format(last_percent, l))
        return {node: pd.DataFrame(self._sess.run(input_vars[node]), columns=node.input_names) for node in self._nodes}

    def solo_train(self, node, train_x, train_agent_y, batch_size=32, epochs=10):
        train_agent_y.columns = node.output_names
        node.train(self._prepare_node_input(train_x, node), train_agent_y.to_numpy(), batch_size, epochs)

    def solo_test(self, node, test_x, test_agent_y):
        test_agent_y.columns = node.output_names
        return node.test(self._prepare_node_input(test_x, node), test_agent_y.to_numpy())

    def _prepare_node_input(self, data, node):
        result = data[node]["constants"]
        for in_node in self._edges[node]:
            result = pd.concat([result, data[in_node]["states"]], axis=1)
        result = result.reindex(columns=node.input_names)
        # todo: remove nan columns
        return result.to_numpy()

    def predict(self, data, time=1):
        for _ in range(time):
            data = {node: {
                "constants": data[node]["constants"],
                "states": _outputToDF(node, node.predict(self._prepare_node_input(data, node)))
            } for node in data}
        return data

    def predict_over_time(self, data_vec, time):
        data = {node: {
            "constants": pd.DataFrame(columns=data_vec[node]["constants"].columns, dtype=np.float32),
            "states": pd.DataFrame(columns=data_vec[node]["states"].columns, dtype=np.float32)
        } for node in data_vec}
        for _ in range(time):
            data_vec = self.predict(data_vec)
            data = {node: {
                "constants": data[node]["constants"].append(data_vec[node]["constants"], ignore_index=True),
                "states": data[node]["states"].append(data_vec[node]["states"], ignore_index=True)
            } for node in data}
        return data

    def cor(self, p1, p2, data_vec, samples=1000):
        data = {node: data_vec[node].repeat(samples).reshape(samples, len(data_vec[node])) for node in self._nodes}
        data[p1.node] = np.random.normal(size=samples)

        new_data = self.predict(data)

        vec1, vec2 = data[:, p1.input_index], new_data[:, p2.output_index]
        return np.cov([vec1, vec2])[0, 1] / np.sqrt(vec1.var(ddof=1) * vec2.var(ddof=1))

    def inter_node_derivative(self, p1, p2, ds_dy1, globals_position, data):
        dy1_dp1 = p1.node.derivative(data[p1.node])[:, p1.input_index].reshape(-1, 1)
        new_data = self.predict(data)
        ind = globals_position[p2.node]
        dp2_ds = p2.node.derivative(new_data[p2.node])[p2.output_index, ind:].reshape(1, -1)
        return dp2_ds.dot(ds_dy1).dot(dy1_dp1)
