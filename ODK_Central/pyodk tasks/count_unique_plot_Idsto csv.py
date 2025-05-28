import pandas as pd
import os
from pyodk.client import Client

def fetch_records(form_id):
    """Fetches submission records from the ODK Central server."""
    client = Client()
    project_id = client.config.central.default_project_id
    records = client.submissions.get_table(project_id=project_id, form_id=form_id)['value']
    return records

def analyze_global_stats(df):
    """Prints overall statistics about plot submissions."""
    submitter_names = df['__system.submitterName'].dropna().unique()
    print(f"Unique submitter names: {len(submitter_names)}")
    for name in submitter_names:
        print(name)

    unique_plot_counts = df.groupby('__system.submitterName')['plot_id'].nunique().reset_index()
    print("\nUnique plot counts by submitter:")
    print(unique_plot_counts)

    most_repeated_plot = df['plot_id'].mode()[0]
    most_repeated_count = df['plot_id'].value_counts().max()
    least_repeated_plot = df['plot_id'].value_counts().idxmin()
    least_repeated_count = df['plot_id'].value_counts().min()
    average_repetitions = df['plot_id'].value_counts().mean()
    
    print(f"\nMost repeated plot ID: {most_repeated_plot} ({most_repeated_count} times)")
    print(f"Least repeated plot ID: {least_repeated_plot} ({least_repeated_count} times)")
    print(f"Average number of repetitions of a plot ID: {average_repetitions:.2f}")
    
    return submitter_names

def create_output_directory():
    """Ensures output directory exists and returns its path."""
    output_dir = os.path.join(os.path.dirname(__file__), 'output_files')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def generate_submitter_reports(df, submitter_names, output_file):
    """Generates an Excel file with pivoted plot counts and side-by-side statistics for each submitter."""
    if os.path.exists(output_file):
        os.remove(output_file)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for name in submitter_names:
            submitter_df = df[df['__system.submitterName'] == name]
            plot_counts = submitter_df['plot_id'].value_counts().reset_index()
            plot_counts.columns = ['plot_id', 'submission_count']

            # Pivot-style table
            pivot_df = plot_counts.set_index('plot_id')

            # Stats table
            total_submissions = len(submitter_df)
            unique_plots = len(pivot_df)
            most_frequent_plot = pivot_df['submission_count'].idxmax()
            most_frequent_count = pivot_df['submission_count'].max()
            least_frequent_count = pivot_df['submission_count'].min()
            average_submissions = pivot_df['submission_count'].mean()

            stats_df = pd.DataFrame({
                'Metric': [
                    'Total Submissions',
                    'Unique Plot IDs',
                    'Most Frequent Plot ID',
                    'Most Frequent Count',
                    'Least Frequent Count',
                    'Average Submissions per Plot'
                ],
                'Value': [
                    total_submissions,
                    unique_plots,
                    most_frequent_plot,
                    most_frequent_count,
                    least_frequent_count,
                    round(average_submissions, 2)
                ]
            })

            # Clean Excel sheet name
            sheet_name = name[:31].replace('/', '_').replace('\\', '_')

            # Write to Excel sheet side by side
            pivot_df.reset_index().to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=0, index=False)
            stats_df.to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=3, index=False)

            # Excel formatting
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.set_column('A:B', 22)
            worksheet.set_column('D:E', 28)

def main():
    form_id = 'Image Safari Crop Scout (Phone Approach)'
    print("Fetching records...")
    records = fetch_records(form_id)
    
    print("Normalizing records into a DataFrame...")
    df = pd.json_normalize(records)

    print("Analyzing global statistics...")
    submitter_names = analyze_global_stats(df)

    output_dir = create_output_directory()
    output_file = os.path.join(output_dir, 'submitter_plot_counts.xlsx')

    print(f"Generating Excel reports in {output_file} ...")
    generate_submitter_reports(df, submitter_names, output_file)
    print("Done.")

if __name__ == "__main__":
    main()
# This script fetches submission records from an ODK Central server, analyzes the data to count unique plot IDs per submitter,
# and generates an Excel report with detailed statistics for each submitter.