import os
import pandas as pd

base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "SampleData")

for f in os.listdir(data_dir):
    if f.startswith("."): continue
    path = os.path.join(data_dir, f)
    print(f"\n--- {f} ---")
    try:
        if f.endswith(".txt"):
            with open(path, 'r', encoding='latin1') as tf:
                print(tf.read(100)) # First 100 chars
        else:
            # Try reading first few lines to detect headers
            df = pd.read_csv(path, nrows=1)
            print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"Error: {e}")
