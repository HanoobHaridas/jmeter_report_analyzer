import pandas as pd
import logging

logger = logging.getLogger(__name__)

def compare_aggregate_stats(dfs, report_names):
    """Compare aggregate statistics between N reports in a side-by-side format and custom order."""
    if len(dfs) == 0 or not report_names or len(dfs) != len(report_names):
        logger.warning("Mismatch in number of dataframes and report names or empty input.")
        return pd.DataFrame()
    if any(df is None or df.empty for df in dfs):
        logger.warning("One or more DataFrames are empty or None")
        return pd.DataFrame()

    # Custom metric order
    metric_order = [
        'Average Response Time (ms)',
        'Error %',
        'Throughput (req/sec)',
        'Min Response Time (ms)',
        'Max Response Time (ms)',
        'Median Response Time (ms)',
        '90th Percentile (ms)',
        '95th Percentile (ms)',
        '99th Percentile (ms)'
    ]

    # Build a lookup for each report's metrics
    metric_maps = []
    for df in dfs:
        m = {row['Metric']: row['Value'] for _, row in df.iterrows()}
        metric_maps.append(m)

    rows = []
    for metric in metric_order:
        row = {'Metric': metric}
        for m, name in zip(metric_maps, report_names):
            val = m.get(metric, None)
            row[name] = f"{float(val):.2f}" if val is not None else ""
        rows.append(row)

    return pd.DataFrame(rows) 