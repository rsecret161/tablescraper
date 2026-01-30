import os


def save_to_file(df, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv' or ext == '':
        df.to_csv(path, index=False)
    elif ext in ('.xls', '.xlsx'):
        df.to_excel(path, index=False, engine='openpyxl')
    elif ext == '.json':
        df.to_json(path, orient='records', lines=False)
    else:
        # Unknown extension: fallback to CSV but keep provided path
        df.to_csv(path, index=False)
