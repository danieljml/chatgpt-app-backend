RECORDS_PER_SUB_CSV = 25


def split_list_in_chunks(items, limit):
    return [items[i : i + limit] for i in range(0, len(items), limit)]


def split_csv(original_csv):
    header, *records = original_csv.split('\n')
    record_blocks = split_list_in_chunks(records, RECORDS_PER_SUB_CSV)
    splitted_csvs = [[header] + record for record in record_blocks]
    return ['\n'.join(csv) for csv in splitted_csvs]
