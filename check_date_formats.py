from echr_extractor import get_echr

df = get_echr(start_date='2000-01-01', end_date='2000-12-31', batch_size=500, timeout=120)

print(f'Total records: {len(df)}')
print(f'\nReferencedate samples:')

ref_dates = df['referencedate'].dropna().unique()[:10]
for date in ref_dates:
    print(f'  {repr(date)} (type: {type(date).__name__})')

print(f'\nTotal non-null referencedate: {df["referencedate"].notna().sum()}')
print(f'Total null referencedate: {df["referencedate"].isna().sum()}')

# Check judgementdate too
print(f'\nJudgementdate samples:')
judge_dates = df['judgementdate'].dropna().unique()[:10]
for date in judge_dates:
    print(f'  {repr(date)} (type: {type(date).__name__})')

print(f'\nTotal non-null judgementdate: {df["judgementdate"].notna().sum()}')
