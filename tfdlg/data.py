import tensorflow as tf
import numpy as np


class BlockDataset:
    def __init__(self, block_size, batch_size, buffer_size=10000):
        self._block_size = block_size
        self._batch_size = batch_size
        self._buffer_size = buffer_size

    def _gen_iter_ids(self, text_generator, encode_fn):
        def gen():
            for text in text_generator():
                for id_ in np.array(encode_fn(text), dtype=np.int32):
                    yield id_
        return gen

    def from_text_generator(self, generator, encode_fn, shuffle=False):
        """
        Args:
            generator: callable object which returns a generator function.
                The generator functions returns str for each time.
            encode_fn: function which takes str as an input and returns list of integers (i.e. List[int])
        """
        window_length = self._block_size + 1

        dataset = tf.data.Dataset.from_generator(self._gen_iter_ids(generator, encode_fn),
                                                 output_types=tf.int32,
                                                 output_shapes=tf.TensorShape([]))
        dataset = dataset.window(window_length,
                                 shift=self._block_size,
                                 drop_remainder=True)
        dataset = dataset.flat_map(lambda wd: wd.batch(window_length))
        if shuffle:
            dataset = dataset.shuffle(self._buffer_size)
        dataset = dataset.batch(self._batch_size, drop_remainder=True)
        dataset = dataset.map(lambda x: (x[:, :-1], x[:, 1:]))
        dataset = dataset.prefetch(1)

        return dataset

    def from_ids(self, ids, shuffle=False):
        return self.build(ids=ids, shuffle=shuffle)

    def build(self, ids, shuffle=False):
        """
        Args:
            ids (Iterator[np.int32]): Iterator which generates
                a np.int32 value at each time
        """
        window_length = self._block_size+1

        # Example of dataset transformation
        # In the example, {} means dataset, [] means batch
        #
        # Notes:
        # - window makes new dataset consisting of several sub-Dataset
        #
        # Example:
        #   init slice -> {1, 2, 3, 4, 5, 6, 7}
        #   window     -> {{1, 2, 3}, {4, 5, 6}}
        #   map batch  -> {{[1, 2, 3]}, {[4, 5, 6]}}
        #   flat       -> {[1, 2, 3], [4, 5, 6]}
        #   batch      -> {[[1, 2, 3], [4, 5, 6]]}
        dataset = tf.data.Dataset.from_tensor_slices(ids)
        dataset = dataset.window(window_length,
                                 shift=self._block_size,
                                 drop_remainder=True)
        dataset = dataset.flat_map(lambda wd: wd.batch(window_length))
        if shuffle:
            dataset = dataset.shuffle(self._buffer_size)
        dataset = dataset.batch(self._batch_size, drop_remainder=True)
        dataset = dataset.map(lambda x: (x[:, :-1], x[:, 1:]))
        dataset = dataset.prefetch(1)

        return dataset


class LineByLineDataset:
    def __init__(self, max_len, batch_size, buffer_size=10000):
        self._max_len = max_len
        self._batch_size = batch_size
        self._buffer_size = buffer_size

    def _gen_iter_ids(self, text_generator, encode_fn):
        def gen():
            for text in text_generator():
                yield np.array(encode_fn(text)[:self._max_len], dtype=np.int32)
        return gen

    def from_text_generator(self, generator, encode_fn, shuffle=False):
        dataset = tf.data.Dataset.from_generator(self._gen_iter_ids(generator, encode_fn),
                                                 output_types=tf.int32,
                                                 output_shapes=tf.TensorShape([None]))
        if shuffle:
            dataset = dataset.shuffle(self._buffer_size)
        # padded_shapes should be greater than the actual length
        dataset = dataset.padded_batch(batch_size=self._batch_size,
                                       padding_values=0,
                                       padded_shapes=self._max_len,
                                       drop_remainder=True,
                                       )
        dataset = dataset.map(lambda x: (x[:, :-1], x[:, 1:]))
        dataset = dataset.prefetch(1)

        return dataset

    def build(self, ids, shuffle=False):
        """
        Args:
            ids (Iterator[List[np.int32]]): Iterator which generates
                a List[lnp.int32] value at each time
        """
        dataset = tf.data.Dataset.from_generator(lambda: ids, tf.int32)
        if shuffle:
            dataset = dataset.shuffle(self._buffer_size)
        dataset = dataset.padded_batch(batch_size=self._batch_size,
                                       padding_values=0,
                                       padded_shapes=self._max_len,
                                       drop_remainder=True,
                                       )
        dataset = dataset.map(lambda x: (x[:, :-1], x[:, 1:]))
        dataset = dataset.prefetch(1)

        return dataset