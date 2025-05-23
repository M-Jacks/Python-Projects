import os
import pandas as pd
import pygsheets
from pyodk.client import Client
from dotenv import load_dotenv
from typing import List

def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    return os.getenv("SHEETNAME")


def initialize_odk_client() -> Client:
    """Initialize and return an ODK client."""
    return Client()


def fetch_and_process_data(client: Client, allowed_submitters: List[str]) -> pd.DataFrame:
    """Fetch data from ODK, filter it, and return a processed pivot DataFrame."""
    data = client.submissions.get_table(form_id='Image Safari Crop Scout (Phone Approach)')
    records = data['value']
    df = pd.json_normalize(records)

    df['submitter'] = df['__system.submitterName'].fillna('unknown')
    df = df[df['submitter'].isin(allowed_submitters)]

    df['photo_count'] = df['photos.photoQuantity'].fillna(0).astype(int)
    df['duration'] = df['photos.photoSessionDuration'].fillna(0).astype(int)

    grouped = df.groupby(['today', 'submitter'])[['photo_count', 'duration']].sum().reset_index()
    pivot_counts = grouped.pivot(index='today', columns='submitter', values='photo_count').fillna(0).astype(int)
    pivot_duration = grouped.pivot(index='today', columns='submitter', values='duration').fillna(0).astype(int)

    pivot_duration = pivot_duration.applymap(format_seconds_to_hhmmss)
    pivot_counts.columns = [f'{col}_count' for col in pivot_counts.columns]
    pivot_duration.columns = [f'{col}_duration' for col in pivot_duration.columns]

    pivot_combined = pd.concat([pivot_counts, pivot_duration], axis=1)
    pivot_combined = pivot_combined.reindex(sorted(pivot_combined.columns), axis=1)

    # Sort by date (index) in descending order
    return pivot_combined.sort_index(ascending=False)


def format_seconds_to_hhmmss(seconds: int) -> str:
    """Convert seconds to hh:mm:ss format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f'{hours}:{minutes:02}:{secs:02}'


def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Save the DataFrame to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path)
    print(f"Pivoted photo summary with durations saved to: {output_path}")


def update_google_sheet(df: pd.DataFrame, sheet_name: str, service_file: str) -> None:
    """Update the Google Sheet with the given DataFrame."""
    gc = pygsheets.authorize(service_file=service_file)
    spreadsheet = gc.open(sheet_name)
    worksheet = spreadsheet.worksheet_by_title('Summary')
    worksheet.set_dataframe(df.reset_index(), (2, 1))
    print("Google Sheets updated with the pivoted photo summary.")


def main() -> str:
    sheet_name = load_environment()
    service_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    output_file = os.path.join(os.path.dirname(__file__), 'output_files', 'pivoted_photo_summary5.csv')
    sheet_url = os.getenv("SHEET_URL")

    allowed_submitters = os.getenv('ALLOWED_SUBMITTERS_LIST', '')
    allowed_submitters = [s.strip() for s in allowed_submitters.split(',') if s.strip()]

    print(f"📋 Working on sheet: {sheet_name}")

    # Process data
    client = initialize_odk_client()
    pivot_combined = fetch_and_process_data(client, allowed_submitters)

    print(pivot_combined)

    # Save and upload
    save_to_csv(pivot_combined, output_file)
    update_google_sheet(pivot_combined, sheet_name, service_file)

    # Create email
    summary_lines = ["📸 Total Image Count Summary:\n"]
    for col in pivot_combined.columns:
        if col.endswith('_count'):
            name = col.replace('_count', '')
            total = pivot_combined[col].sum()
            summary_lines.append(f"• {name}: {total} images")

    summary_text = "\n".join(summary_lines)
    return (
            # f"{summary_text}\n\n✅ Summary updated and saved at {output_file}"
            f"{summary_text}\n\n✅ Summary updated and saved at:🔗 {sheet_url}"
            )

# if __name__ == "__main__":
#     main()
