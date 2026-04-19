import pandas as pd

def read_excel(file):
    df = pd.read_excel(file)

    if df.empty:
        return []

    return df.to_dict(orient="records")