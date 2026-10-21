"""Turn the R pull's csv.gz files into parquet, one file per source per season.

Only files the release does not already hold are converted; the workflow uploads what this
prints. Usage: python afl/data/to_parquet.py afl/cache/raw afl/cache
"""
import glob
import os
import sys

import pandas as pd


def main(raw, out):
    made = []
    for f in sorted(glob.glob(os.path.join(raw, '*.csv.gz'))):
        name = os.path.basename(f)[:-len('.csv.gz')]
        dest = os.path.join(out, name + '.parquet')
        if os.path.exists(dest) and os.path.getmtime(dest) >= os.path.getmtime(f):
            continue
        df = pd.read_csv(f, low_memory=False)
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype('string')
        df.to_parquet(dest, index=False)
        made.append(dest)
        print(f'{dest}: {len(df):,} rows, {df.shape[1]} columns')
    with open(os.path.join(out, 'new_files.txt'), 'w') as fh:
        fh.write('\n'.join(made))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
