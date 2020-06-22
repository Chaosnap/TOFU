import h5py
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(description='FOOBAR')
parser.add_argument('-f', '--file', type=str, help='path to ttest hdf', required=True)
namespace = parser.parse_args()


with h5py.File(namespace.file, 'r') as f:
    foo = list(f.keys())[2]
    bar = list(f[foo].keys())[0]
    a = np.array(f[foo][bar])

a = np.abs(a)


plt.axhline(y=+4.5, color='r', linestyle='-')

# key loading
plt.axvline(x=26406, color='g', linestyle='-')
plt.axvline(x=28906, color='g', linestyle='-')

# tag
plt.axvline(x=175468, color='g', linestyle='-')
plt.axvline(x=176718, color='g', linestyle='-')

plt.xlabel("messpunkt")
plt.ylabel("t wert")
plt.plot(a)
plt.show()
