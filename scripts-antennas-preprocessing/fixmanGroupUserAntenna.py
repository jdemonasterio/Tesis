from __future__ import division
from __future__ import print_function

import pandas
import numpy

import sys

def main():
    input_file = sys.argv[1]
    passes = int(sys.argv[2])

    for group in range(passes):
        table = pandas.read_csv(
            input_file,
            engine = 'c',
            chunksize = 1000000,
            sep = ' ',
            header = None,
            names = ['user_id', 0, 1, 2, 3, 'antenna'],
            usecols = ['user_id', 'antenna']
        )

        subgroup = pandas.DataFrame()
        for chunk in table:
            chunk = chunk[chunk % passes == group]
            subgroup = subgroup.append(chunk)

        grouped = subgroup.groupby(['user_id', 'antenna'])['antenna'].agg({'count': numpy.size})
        grouped.to_csv(sys.argv[3], index = True, header = group == 0, append = True)

if __name__ == '__main__':
    main()
