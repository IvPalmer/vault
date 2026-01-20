from DataLoader import DataLoader
import pandas as pd

dl = DataLoader()
df = dl.load_all()

# Filter for Checking Account and large negative amounts in Jan
mask = (df['account'] == 'Checking') & (df['amount'] < -1000)
large_outflows = df[mask]

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)

print(large_outflows[['date', 'description', 'amount']].head(20))
