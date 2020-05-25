import numpy as np
import logging


def valueExtract(self):

    # create a logger
    logger = logging.getLogger('analyze')
    if (logger.hasHandlers()):
        logger.handlers.clear()
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)

    logger.info("extracting value (key)")

    value_signal_numeric_id = 6776
    value_signal_time_from = 679334500000
    value_signal_time___to = 679350500000

    value_signal_list = []
    value_signal_list_unshared = []

    if value_signal_numeric_id not in self.numeric_ids_under_inspection_set:
        raise synthesizeException("signal %s is not in the loaded pickle" % value_signal_numeric_id)

    # extract key updates
    for update in self.updates:
        if update[0] >= value_signal_time_from and update[0] <= value_signal_time___to and update[1] == value_signal_numeric_id:
            foo = update[2]
            value_signal_list.append(bytearray(int("0b" + foo, 2).to_bytes(4, 'big')))
    assert(len(value_signal_list) == 16)

    # unshare
    for i in range(0, 8):
        x = value_signal_list[i * 2]
        y = value_signal_list[i * 2 + 1]
        assert(len(x) == len(y))
        unshared = bytes(x ^ y for (x, y) in zip(x, y))
        value_signal_list_unshared.append(unshared)

    # flatten
    value = [item for sub in value_signal_list_unshared for item in sub]

    assert(len(value) == 32)
    value = np.array([value], dtype=np.uint8)

    return value


def valueExtractIndex(self):
    # create a logger
    logger = logging.getLogger('analyze')
    if (logger.hasHandlers()):
        logger.handlers.clear()
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)

    logger.info("extracting value (key) i.e. index: %d" % (self.index))
    return np.array([self.index], dtype=np.uint8)
