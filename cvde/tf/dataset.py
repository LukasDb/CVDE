import tensorflow as tf # type: ignore

import sys
from abc import abstractmethod, ABC
from pathlib import Path
import pickle
import numpy as np
import multiprocessing as mp
import tqdm
import psutil

import cvde


class Dataset(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._current_idx = 0

    def __iter__(self) -> "Dataset":
        return self

    @abstractmethod
    def visualize_example(self, example) -> None:
        """Specify how to visualize on (not batched) example from the dataset
        Use streamlit to visualize the example

        Args:
            example (as returned by this Dataset): Python object yielded by this Dataset

        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __getitem__(self, idx: int) -> dict:
        pass

    def __next__(self):
        try:
            data = self[self._current_idx]
        except IndexError:
            raise StopIteration
        self._current_idx += 1
        return data

    def cache(self, preprocess_folder: Path):
        """Iterates through the dataset and saves it to a tfrecord file in the specified folder.
        This requires the dataset to return dictionaries of tensors."""
        if not preprocess_folder.exists():
            preprocess_folder.mkdir(parents=True)

        one_datapoint = self[0]
        # get size in bytes of one datapoint
        size_one_datapoint = sum(
            [sys.getsizeof(tf.io.serialize_tensor(val).numpy()) for val in one_datapoint.values()]
        )
        # shard every 500MB (compression leads to ~2x smaller files)
        shard_every_n_datapoints = max(
            1, int(1000e6 / size_one_datapoint)
        )  # at least one example per shard
        shard_every_n_datapoints = min(
            len(self), shard_every_n_datapoints
        )  # make sure we don't shard more than the dataset size

        # split range into chunks of shard_every_n_datapoints
        starts = np.array_split(np.arange(len(self)), len(self) // shard_every_n_datapoints)
        starts = [start[0] for start in starts]
        stops = [x - 1 for x in starts[1:]]
        stops.append(len(self))  # add last stop

        jobs = [(start, stop, preprocess_folder) for start, stop in zip(starts, stops)]

        try:
            mp.set_start_method("spawn")
        except RuntimeError:
            pass

        n_workers = min(psutil.cpu_count(logical=False), 16)
        n_workers = min(n_workers, len(jobs))
        job_queue: mp.Queue = mp.Queue(maxsize=n_workers)

        workers = [mp.Process(target=self.process, args=(job_queue,)) for _ in range(n_workers)]

        for worker in tqdm.tqdm(workers, desc="Starting workers", ascii=False):
            worker.start()

        with tqdm.tqdm(total=len(self), desc="Caching", smoothing=0, ascii=False) as bar:
            for job in jobs:
                job_queue.put(job)
                bar.update(job[1] - job[0])

        for _ in range(n_workers):
            job_queue.put(None)

        for worker in workers:
            worker.join()

    def process(self, process_queue: mp.Queue):
        """get queue stop when receive None, otherwise run _cache_index_range"""
        while True:
            job = process_queue.get()
            if job is None:
                break
            self._cache_index_range(*job)

    def _cache_index_range(
        self, start, stop, preprocess_folder: Path  # shard_every_n_datapoints: int
    ):
        options = tf.io.TFRecordOptions(compression_type="ZLIB")
        writer = tf.io.TFRecordWriter(
            str((preprocess_folder / f"preprocessed_{start:04}.tfrecord").resolve()),
            options=options,
        )
        dtype_dict = None
        for i in range(start, stop):
            data = self[i]
            if not isinstance(data, dict):
                raise ValueError("Dataset must return dictionaries of tensors to be cached")

            dtype_dict = {name: val.dtype for name, val in data.items()}

            serialized_features = {
                name: tf.train.Feature(
                    bytes_list=tf.train.BytesList(value=[tf.io.serialize_tensor(val).numpy()])  # type: ignore
                )  # type: ignore
                for name, val in data.items()
            }
            example_proto = tf.train.Example(
                features=tf.train.Features(feature=serialized_features)  # type: ignore
            )
            example = example_proto.SerializeToString()  # type: ignore

            writer.write(example)

        writer.close()

        assert dtype_dict is not None

        # only the first worker writes the dtypes
        if start == 0:
            with (preprocess_folder / "dtypes_preprocessed.bin").open("wb") as F:
                pickle.dump(dtype_dict, F)

    def from_cache(self, preprocess_folder: Path) -> tf.data.Dataset:
        """returns tf.Dataset from tfrecord files (only preprocessed)"""

        try:
            with (preprocess_folder / "dtypes_preprocessed.bin").open("rb") as F:
                dtype_dict = pickle.load(F)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find dtypes_preprocessed.bin in {preprocess_folder}. "
                "Please run .cache() first."
            )

        output_names = list(dtype_dict.keys())

        feature_description = {name: tf.io.FixedLenFeature([], tf.string) for name in output_names}

        def get_data_as_dict(data):
            return {
                name: tf.io.parse_tensor(data[name], dtype_dict[name]) for name in output_names
            }

        def parse_tfrecord(example_proto):
            return tf.io.parse_single_example(example_proto, feature_description)

        # chunked tfrecords
        files = tf.io.matching_files(str(preprocess_folder / "preprocessed_*.tfrecord"))

        shards = tf.data.Dataset.from_tensor_slices(files)
        tf_ds = shards.interleave(
            lambda x: tf.data.TFRecordDataset(x, compression_type="ZLIB"),
            deterministic=True,
            num_parallel_calls=tf.data.AUTOTUNE,
        )

        return tf_ds.map(parse_tfrecord, num_parallel_calls=tf.data.AUTOTUNE).map(
            get_data_as_dict, num_parallel_calls=tf.data.AUTOTUNE
        )
        # .map(
        #     get_data_as_tuple, num_parallel_calls=tf.data.AUTOTUNE
        # )
