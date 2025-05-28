import os
import pandas as pd
import pygsheets
from pyodk.client import Client
from dotenv import load_dotenv
from typing import List, Tuple
from datetime import datetime

def load_environment():
    load_dotenv()
    return os.getenv("SHEETNAME")

def initialize_odk_client() -> Client:
    return Client()

def format_seconds_to_hhmmss(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f'{hours}:{minutes:02}:{secs:02}'

def calculate_weekly_average(df: pd.DataFrame) -> pd.DataFrame:
    df['week_start'] = df['today'].dt.to_period('W-SUN').apply(lambda r: r.start_time)
    weekly_avg = df.groupby(['week_start', 'submitter'])['photo_count'].mean().reset_index()
    return weekly_avg.pivot(index='week_start', columns='submitter', values='photo_count').fillna(0).round(2)

def calculate_weekly_total(df: pd.DataFrame) -> pd.DataFrame:
    df['week_start'] = df['today'].dt.to_period('W-SUN').apply(lambda r: r.start_time)
    weekly_total = df.groupby(['week_start', 'submitter'])['photo_count'].sum().reset_index()
    return weekly_total.pivot(index='week_start', columns='submitter', values='photo_count').fillna(0).astype(int)

def calculate_submitter_totals(pivot_df: pd.DataFrame) -> pd.DataFrame:
    counts = pivot_df[[col for col in pivot_df.columns if col.endswith('_count')]].sum()
    submitter_totals = counts.to_frame(name='Total')
    submitter_totals.index = [i.replace('_count', '') for i in submitter_totals.index]
    return submitter_totals.T

def fetch_and_process_data(client: Client, allowed_submitters: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
    records = data['value']
    df = pd.json_normalize(records)

    df['submitter'] = df['__system.submitterName'].fillna('unknown')
    df = df[df['submitter'].isin(allowed_submitters)]

    df['photo_count'] = df['photos.photoQuantity'].fillna(0).astype(int)
    df['duration'] = df['photos.photoSessionDuration'].fillna(0).astype(int)
    df['today'] = pd.to_datetime(df['today'])

    grouped = df.groupby(['today', 'submitter'])[['photo_count', 'duration']].sum().reset_index()
    pivot_counts = grouped.pivot(index='today', columns='submitter', values='photo_count').fillna(0).astype(int)
    pivot_duration = grouped.pivot(index='today', columns='submitter', values='duration').fillna(0).astype(int)

    pivot_duration = pivot_duration.applymap(format_seconds_to_hhmmss)
    pivot_counts.columns = [f'{col}_count' for col in pivot_counts.columns]
    pivot_duration.columns = [f'{col}_duration' for col in pivot_duration.columns]

    pivot_combined = pd.concat([pivot_counts, pivot_duration], axis=1)
    pivot_combined = pivot_combined.reindex(sorted(pivot_combined.columns), axis=1)

    weekly_avg = calculate_weekly_average(grouped)
    weekly_total = calculate_weekly_total(grouped)
    submitter_totals = calculate_submitter_totals(pivot_combined)

    return pivot_combined.sort_index(ascending=False), weekly_avg, weekly_total, submitter_totals

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path)
    print(f"Pivoted photo summary with durations saved to: {output_path}")

def update_google_sheet(df: pd.DataFrame, sheet_name: str, service_file: str,
                        weekly_avg: pd.DataFrame, weekly_total: pd.DataFrame,
                        totals: pd.DataFrame) -> None:
    gc = pygsheets.authorize(service_file=service_file)
    spreadsheet = gc.open(sheet_name)
    worksheet = spreadsheet.worksheet_by_title('Summary')

    worksheet.clear(start='A1')

    worksheet.update_value('A1', '📅 Daily Photo Summary')
    worksheet.set_dataframe(df.reset_index(), start='A2')

    worksheet.update_value('L1', '📊 Weekly Averages Table')
    worksheet.set_dataframe(weekly_avg.reset_index(), start='L2')

    worksheet.update_value('H1', '🧮 Weekly Totals Table')
    worksheet.set_dataframe(weekly_total.reset_index(), start='H2')

    worksheet.update_value('P1', '🔢 Totals Summary per Center')
    worksheet.set_dataframe(totals.reset_index(), start='P2')

    print("✅ Google Sheets updated with all pivot tables and summaries.")



def main() -> str:
    sheet_name = load_environment()
    service_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    output_file = os.path.join(os.path.dirname(__file__), 'output_files', 'pivoted_photo_summary5.csv')
    sheet_url = os.getenv("SHEET_URL")

    allowed_submitters = os.getenv('ALLOWED_SUBMITTERS_LIST', '')
    allowed_submitters = [s.strip() for s in allowed_submitters.split(',') if s.strip()]

    print(f"📋 Working on sheet: {sheet_name}")

    client = initialize_odk_client()
    pivot_combined, weekly_avg, weekly_total, submitter_totals = fetch_and_process_data(client, allowed_submitters)

    print(pivot_combined)
    save_to_csv(pivot_combined, output_file)
    update_google_sheet(pivot_combined, sheet_name, service_file, weekly_avg, weekly_total, submitter_totals)

    summary_lines = ["📸 Total Image Count Summary:\n"]
    for col in pivot_combined.columns:
        if col.endswith('_count'):
            name = col.replace('_count', '')
            total = pivot_combined[col].sum()
            summary_lines.append(f"• {name}: {total} images")

    latest_week_start = weekly_total.index.max()
    latest_week_dates = pd.date_range(start=latest_week_start, periods=7, freq='D')
    recent_daily_counts = pivot_combined.loc[pivot_combined.index.isin(latest_week_dates)]

    summary_lines.append("\n📅 This week's Daily Photo Counts:")
    for date, row in recent_daily_counts.iterrows():
        day_counts = [f"{col.replace('_count', '')}: {row[col]}" for col in recent_daily_counts.columns if col.endswith('_count')]
        summary_lines.append(f"• {date.strftime('%Y-%m-%d')}: {', '.join(day_counts)}")

    summary_text = "\n".join(summary_lines)
    return f"{summary_text}\n\n✅ Summary updated and saved at:🔗 {sheet_url}"


# if __name__ == "__main__":
#     main()
