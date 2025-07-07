import pandas as pd
import logging

logger = logging.getLogger(__name__)

def compare_endpoint_stats(dfs, report_names):
    """Compare endpoint statistics between N reports in a side-by-side format."""
    if not dfs or not report_names or len(dfs) != len(report_names):
        logger.warning("Mismatch in number of dataframes and report names or empty input.")
        return pd.DataFrame()
    if any(df is None or df.empty for df in dfs):
        logger.warning("One or more DataFrames are empty or None")
        return pd.DataFrame()

    # Get unique labels from all reports, preserving order from the first, then others
    labels = list(dfs[0]['Label'].unique())
    for df in dfs[1:]:
        labels += [l for l in df['Label'].unique() if l not in labels]

    # Define metrics to compare with their display names and order
    metrics = [
        ('#Samples', '#Samples'),
        ('Average', 'Average Response Time (ms)'),
        ('Error %', 'Error %'),
        ('Transactions/s', 'Throughput (req/sec)'),
        ('Median', 'Median Response Time (ms)'),
        ('90th pct', '90th Percentile (ms)'),
        ('95th pct', '95th Percentile (ms)'),
        ('99th pct', '99th Percentile (ms)')
    ]

    rows = []
    for label in labels:
        row = {'Endpoint': label}
        for metric_key, metric_display in metrics:
            for df, name in zip(dfs, report_names):
                col = f"{metric_display} ({name})"
                val = None
                if label in df['Label'].values:
                    v = df[df['Label'] == label][metric_key].iloc[0] if metric_key in df.columns else None
                    if metric_key == '#Samples':
                        val = f"{int(v)}" if v is not None else ""
                    else:
                        val = f"{float(v):.2f}" if v is not None else ""
                else:
                    val = ""
                row[col] = val
        rows.append(row)

    return pd.DataFrame(rows) 