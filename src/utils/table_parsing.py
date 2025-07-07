import pandas as pd
from bs4 import BeautifulSoup
import tempfile
import os
import logging
import json
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
REPORT_TABLES = {
    'endpoint_stats': 'Endpoint-wise Stats',
    'aggregate_summary': 'Aggregate Metrics Summary',
    'errors': 'Errors'
}

# Define the column mapping at module level for reuse
COLUMN_MAPPING = {
    'Label': 'Label',
    'sampleCount': '#Samples',
    'errorCount': 'FAIL',
    'errorPct': 'Error %',
    'meanResTime': 'Average',
    'minResTime': 'Min',
    'maxResTime': 'Max',
    'medianResTime': 'Median',
    'pct1ResTime': '90th pct',
    'pct2ResTime': '95th pct',
    'pct3ResTime': '99th pct',
    'throughput': 'Transactions/s',
    'receivedKBytesPerSec': 'Received',
    'sentKBytesPerSec': 'Sent'
}

# Define the column order to match HTML report
COLUMN_ORDER = [
    'Label',
    '#Samples',
    'FAIL',
    'Error %',
    'Average',
    'Min',
    'Max',
    'Median',
    '90th pct',
    '95th pct',
    '99th pct',
    'Transactions/s',
    'Received',
    'Sent'
]

def extract_js_variable(js_content, var_name):
    """Extract a JavaScript variable value."""
    pattern = rf'var\s+{var_name}\s*=\s*({{\s*.*?\n}})\s*;'
    match = re.search(pattern, js_content, re.DOTALL)
    if match:
        return match.group(1)
    return None

def clean_json_string(json_str):
    """Clean up JavaScript object to make it valid JSON."""
    # Remove trailing commas
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Fix unquoted property names
    json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
    
    # Fix single quotes to double quotes
    json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
    json_str = re.sub(r':\s*\'([^\']*)\'', r':"\1"', json_str)
    
    # Fix JavaScript undefined to null
    json_str = re.sub(r':\s*undefined\b', ':null', json_str)
    
    # Handle special characters in strings
    json_str = re.sub(r'\\([^"])', r'\\\\\1', json_str)
    
    # Handle boolean values
    json_str = re.sub(r':\s*true\b', ':true', json_str)
    json_str = re.sub(r':\s*false\b', ':false', json_str)
    
    return json_str

def extract_table_data(js_content, table_id):
    """Extract table data from JavaScript content."""
    # For statistics table, look for the createTable call with the data
    if table_id == 'statisticsTable':
        pattern = r'createTable\(\$\("#statisticsTable"\),\s*({.*?}),\s*function'
        match = re.search(pattern, js_content, re.DOTALL)
        if not match:
            # Try alternative pattern
            pattern = r'createTable\(\$("#statisticsTable"\),\s*({.*?}),\s*function'
            match = re.search(pattern, js_content, re.DOTALL)
    else:
        # For other tables, use similar patterns
        pattern = rf'createTable\(\$\("#{table_id}"\),\s*({{\s*.*?}}),\s*function'
        match = re.search(pattern, js_content, re.DOTALL)
        if not match:
            pattern = rf'createTable\(\$("#{table_id}"\),\s*({{\s*.*?}}),\s*function'
            match = re.search(pattern, js_content, re.DOTALL)
    
    if not match:
        logger.debug(f"No match found for table {table_id}")
        return None
    
    try:
        data_str = match.group(1)
        # Clean up the JavaScript object
        data_str = clean_json_string(data_str)
        data = json.loads(data_str)
        return data
    except Exception as e:
        logger.error(f"Error extracting data for {table_id}: {str(e)}")
        return None

def extract_js_data(js_content):
    """Extract data from JavaScript content."""
    tables_data = {}
    
    # Map of table IDs to our internal names
    table_mappings = {
        'statisticsTable': 'endpoint_stats',
        'errorsTable': 'errors',
        'apdexTable': 'aggregate_summary'
    }
    
    for table_id, internal_name in table_mappings.items():
        try:
            data = extract_table_data(js_content, table_id)
            if data:
                tables_data[internal_name] = data
                logger.debug(f"Successfully extracted data for {table_id}")
        except Exception as e:
            logger.error(f"Error processing {table_id}: {str(e)}")
    
    return tables_data

def parse_statistics_table(html_content):
    """Parse the statistics table from HTML content."""
    soup = BeautifulSoup(html_content, 'lxml')
    stats_table = None
    
    # Look for the statistics table
    tables = soup.find_all('table')
    for table in tables:
        # Check if this is the statistics table by looking for the header row
        headers = table.find_all('th')
        header_texts = [h.get_text(strip=True) for h in headers]
        
        if 'Label' in header_texts and '#Samples' in header_texts:
            stats_table = table
            break
    
    if not stats_table:
        return None
        
    # Extract data from statistics.json
    js_content = None
    with open(os.path.join(os.path.dirname(html_content), 'content', 'js', 'dashboard.js'), 'r') as f:
        js_content = f.read()
    
    if js_content:
        stats_data = extract_table_data(js_content, 'statisticsTable')
        if stats_data and 'items' in stats_data:
            rows = []
            for item in stats_data['items']:
                row = {}
                for old_col, new_col in COLUMN_MAPPING.items():
                    if old_col in item:
                        row[new_col] = item[old_col]
                rows.append(row)
            
            # Create DataFrame with the new column order
            columns = list(COLUMN_MAPPING.values())
            df = pd.DataFrame(rows, columns=columns)
            
            # Round numeric columns to 2 decimal places
            numeric_cols = ['Error %', 'Average', 'Min', 'Max', 'Median', '90th pct', '95th pct', '99th pct', 
                          'Transactions/s', 'Received', 'Sent']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: round(float(x), 2) if pd.notnull(x) else x)
            
            # Keep sample counts as integers
            if '#Samples' in df.columns:
                df['#Samples'] = df['#Samples'].astype(int)
            if 'FAIL' in df.columns:
                df['FAIL'] = df['FAIL'].astype(int)
            
            return df
    
    return None

def create_aggregate_from_statistics(stats_df):
    """Create aggregate metrics summary from statistics total row."""
    if stats_df is None or stats_df.empty:
        logger.debug("Statistics DataFrame is None or empty")
        return None
    
    logger.debug(f"Columns in stats_df: {stats_df.columns.tolist()}")
    logger.debug(f"Unique values in Label column: {stats_df['Label'].unique().tolist() if 'Label' in stats_df.columns else 'No Label column'}")
    
    # First try to find the Total row
    total_row = None
    if 'Label' in stats_df.columns:
        total_rows = stats_df[stats_df['Label'] == 'Total']
        if not total_rows.empty:
            total_row = total_rows.iloc[0]
        else:
            # Try case-insensitive match
            total_rows = stats_df[stats_df['Label'].str.lower() == 'total']
            if not total_rows.empty:
                total_row = total_rows.iloc[0]
    
    # If no Total row found, try to find overall data
    if total_row is None and 'overall' in stats_df.columns:
        total_row = stats_df.iloc[0]  # Use first row if it contains overall data
    
    if total_row is None:
        logger.debug("No Total row found in statistics")
        return None
    
    logger.debug(f"Found total row: {total_row.to_dict()}")
    
    try:
        # Create aggregate metrics dataframe
        metrics = {
            'Metric': [
                'Average Response Time (ms)',
                'Median Response Time (ms)',
                'Min Response Time (ms)',
                'Max Response Time (ms)',
                'Throughput (req/sec)',
                'Error %',
                '90th Percentile (ms)',
                '95th Percentile (ms)',
                '99th Percentile (ms)'
            ],
            'Value': [
                round(float(total_row.get('meanResTime', 0)), 2),
                round(float(total_row.get('medianResTime', total_row.get('Median', 0))), 2),
                round(float(total_row.get('minResTime', 0)), 2),
                round(float(total_row.get('maxResTime', 0)), 2),
                round(float(total_row.get('throughput', 0)), 2),
                round(float(total_row.get('errorPct', 0)), 2),
                round(float(total_row.get('pct1ResTime', 0)), 2),  # 90th percentile
                round(float(total_row.get('pct2ResTime', 0)), 2),  # 95th percentile
                round(float(total_row.get('pct3ResTime', 0)), 2)   # 99th percentile
            ]
        }
        
        return pd.DataFrame(metrics)
    except Exception as e:
        logger.error(f"Error creating aggregate metrics: {str(e)}")
        logger.debug(f"Total row data types: {total_row.dtypes.to_dict()}")
        return None

def calculate_total_statistics(stats_data):
    """Calculate total statistics from all endpoints."""
    # Initialize counters
    total_samples = 0
    total_errors = 0
    total_response_time = 0
    min_response_time = float('inf')
    max_response_time = 0
    total_bytes = 0
    total_sent_bytes = 0
    all_response_times = []
    
    # Aggregate data from all endpoints
    for label, data in stats_data.items():
        if label.lower() != 'total':  # Skip if there's already a Total entry
            samples = int(data.get('sampleCount', 0))
            total_samples += samples
            total_errors += int(data.get('errorCount', 0))
            
            # Response times
            mean_time = float(data.get('meanResTime', 0))
            total_response_time += mean_time * samples
            min_response_time = min(min_response_time, float(data.get('minResTime', float('inf'))))
            max_response_time = max(max_response_time, float(data.get('maxResTime', 0)))
            
            # Collect all response times for percentile calculation
            if 'rawResponses' in data:
                all_response_times.extend(data['rawResponses'])
            
            # Bytes
            total_bytes += float(data.get('receivedBytes', 0))
            total_sent_bytes += float(data.get('sentBytes', 0))
    
    # Calculate aggregates
    if total_samples > 0:
        avg_response_time = round(total_response_time / total_samples, 2)
        error_percent = round((total_errors / total_samples) * 100, 2)
        throughput = round(total_samples / (max_response_time / 1000), 2)  # Convert max time to seconds
        
        # Calculate percentiles
        if all_response_times:
            all_response_times.sort()
            idx_90 = int(len(all_response_times) * 0.9)
            idx_95 = int(len(all_response_times) * 0.95)
            idx_99 = int(len(all_response_times) * 0.99)
            pct_90 = round(all_response_times[idx_90], 2)
            pct_95 = round(all_response_times[idx_95], 2)
            pct_99 = round(all_response_times[idx_99], 2)
        else:
            # If no raw responses, estimate from the endpoints
            pct_90 = round(max(float(data.get('pct1ResTime', 0)) for data in stats_data.values()), 2)
            pct_95 = round(max(float(data.get('pct2ResTime', 0)) for data in stats_data.values()), 2)
            pct_99 = round(max(float(data.get('pct3ResTime', 0)) for data in stats_data.values()), 2)
        
        return {
            'sampleCount': total_samples,
            'errorCount': total_errors,
            'errorPct': error_percent,
            'meanResTime': avg_response_time,
            'minResTime': round(min_response_time if min_response_time != float('inf') else 0, 2),
            'maxResTime': round(max_response_time, 2),
            'pct1ResTime': pct_90,
            'pct2ResTime': pct_95,
            'pct3ResTime': pct_99,
            'throughput': throughput,
            'receivedBytes': round(total_bytes, 2),
            'sentBytes': round(total_sent_bytes, 2)
        }
    return None

def is_http_endpoint(label):
    """Check if the label is an HTTP endpoint."""
    return label.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'PATCH '))

def sort_endpoints(df):
    """Sort endpoints with Total first, then non-HTTP endpoints, then HTTP endpoints."""
    if 'Label' not in df.columns:
        return df
        
    # Create a sorting key
    def get_sort_key(label):
        if label == 'Total':
            return (0, label)
        elif is_http_endpoint(label):
            return (2, label)
        else:
            return (1, label)
    
    # Sort the DataFrame
    df['sort_key'] = df['Label'].apply(get_sort_key)
    df = df.sort_values('sort_key')
    df = df.drop('sort_key', axis=1)
    return df

def extract_error_info(js_content):
    """Extract error information from dashboard.js."""
    # Look for the error table data
    pattern = r'createTable\(\$\("#errorsTable"\),\s*({.*?}),\s*function'
    match = re.search(pattern, js_content, re.DOTALL)
    if match:
        try:
            error_data = json.loads(clean_json_string(match.group(1)))
            return error_data.get('items', [])
        except Exception as e:
            logger.error(f"Error parsing error table data: {str(e)}")
    return []

def create_errors_table(stats_data):
    """Create errors table from statistics data."""
    error_rows = []
    
    # Try to find the dashboard.js file to get error information
    dashboard_js_path = None
    if '__file__' in stats_data:
        # If we have the file path of statistics.json
        stats_path = stats_data['__file__']
        dashboard_js_path = os.path.join(os.path.dirname(os.path.dirname(stats_path)), 'content', 'js', 'dashboard.js')
    else:
        # Try to find it in common locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'content', 'js', 'dashboard.js'),
            os.path.join(os.getcwd(), 'temp_jmeter_reports', 'persistent', 'content', 'js', 'dashboard.js')
        ]
        for path in possible_paths:
            if os.path.exists(path):
                dashboard_js_path = path
                break
    
    # Get error information from dashboard.js (specifically the Top 5 Errors table)
    error_info = {}
    if dashboard_js_path and os.path.exists(dashboard_js_path):
        try:
            with open(dashboard_js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
                # Extract Top 5 Errors table data
                error_pattern = r'createTable\(\$\("#top5ErrorsBySamplerTable"\),\s*({.*?}),\s*function'
                match = re.search(error_pattern, js_content, re.DOTALL)
                if match:
                    error_data_str = match.group(1)
                    error_data = json.loads(clean_json_string(error_data_str))
                    logger.debug(f"Extracted top5ErrorsBySamplerTable data: {json.dumps(error_data, indent=2)}")
                    # Extract error information from items
                    # The structure is: item['data'] = [Label, #Samples, #Errors, Error1, #Err1, Error2, #Err2, ...]
                    for item in error_data.get('items', []):
                        if isinstance(item.get('data'), list) and len(item['data']) >= 5:
                            label = item['data'][0]
                            errors_count = int(item['data'][2])
                            if errors_count > 0:
                                # Get the primary error (assuming the first listed is most relevant)
                                error_text = item['data'][3]
                                error_info[label] = error_text
                                logger.debug(f"Found error for label '{label}': '{error_text}'")
                            else:
                                logger.debug(f"No errors reported for label '{label}' in top5 table.")
                        else:
                            logger.debug(f"Skipping item due to unexpected data format: {item.get('data')}")
                else:
                    logger.warning("Could not find top5ErrorsBySamplerTable data in dashboard.js")
        except Exception as e:
            logger.error(f"Error reading error information from dashboard.js: {str(e)}", exc_info=True)
    
    # Create the error table using extracted info
    for label, data in stats_data.items():
        # Skip total row and non-HTTP endpoints for errors
        if label.lower() != 'total' and is_http_endpoint(label):
            error_count = int(data.get('errorCount', 0))
            if error_count > 0:
                # Get error text from the extracted error_info dictionary
                error_text = error_info.get(label, 'Unknown Error') 
                if error_text == "": # Handle cases where dashboard.js might have empty error string
                    error_text = "Unknown Error"
                
                error_row = {
                    'Endpoint': label,
                    'Request #': int(data.get('sampleCount', 0)),
                    'Error #': error_count,
                    'Error': error_text,
                    'Error %': round(float(data.get('errorPct', 0)), 2)
                }
                error_rows.append(error_row)
            elif label in error_info:
                 logger.debug(f"Label '{label}' found in error_info but stats_data shows 0 errors.")

    if not error_rows and len(error_info) > 0:
         logger.warning("Extracted error info from dashboard.js, but no corresponding error rows created. Check label matching.")

    if error_rows:
        return pd.DataFrame(error_rows)
    return None

def parse_jmeter_tables(report_path):
    """Parse JMeter report tables from the statistics.json file."""
    tables = {key: None for key in REPORT_TABLES.keys()}
    
    try:
        # Check if the input is directly a statistics.json file
        if report_path.endswith('statistics.json'):
            statistics_json_path = report_path
        else:
            # If not, look for statistics.json in the report directory
            report_dir = os.path.dirname(report_path)
            statistics_json_path = os.path.join(report_dir, 'statistics.json')
        
        if os.path.exists(statistics_json_path):
            logger.debug(f"Processing statistics.json at {statistics_json_path}")
            with open(statistics_json_path, 'r', encoding='utf-8') as f:
                stats_data = json.load(f)
            
            # Calculate total statistics if not present
            if 'Total' not in stats_data:
                total_stats = calculate_total_statistics(stats_data)
                if total_stats:
                    stats_data['Total'] = total_stats
            
            # Convert statistics data to DataFrame for endpoint stats
            stats_rows = []
            for label, data in stats_data.items():
                row = {}
                # Map the data to our expected columns
                for old_col, new_col in COLUMN_MAPPING.items():
                    if old_col == 'Label':
                        row[new_col] = label
                    elif old_col in data:
                        value = data[old_col]
                        # Handle numeric values
                        if isinstance(value, (int, float)):
                            if old_col in ['sampleCount', 'errorCount']:
                                row[new_col] = int(value)
                            else:
                                row[new_col] = round(float(value), 2)
                        else:
                            row[new_col] = value
                stats_rows.append(row)
            
            if stats_rows:
                # Create DataFrame with the correct column order
                stats_df = pd.DataFrame(stats_rows)
                stats_df = stats_df[COLUMN_ORDER]  # Reorder columns
                
                # Sort endpoints appropriately
                stats_df = sort_endpoints(stats_df)
                tables['endpoint_stats'] = stats_df
                logger.debug(f"Successfully parsed statistics with shape {stats_df.shape}")
                
                # Create aggregate metrics from Total statistics
                total_stats = stats_data.get('Total')
                if total_stats:
                    metrics = {
                        'Metric': [
                            'Average Response Time (ms)',
                            'Median Response Time (ms)',
                            'Min Response Time (ms)',
                            'Max Response Time (ms)',
                            'Throughput (req/sec)',
                            'Error %',
                            '90th Percentile (ms)',
                            '95th Percentile (ms)',
                            '99th Percentile (ms)'
                        ],
                        'Value': [
                            round(float(total_stats.get('meanResTime', 0)), 2),
                            round(float(total_stats.get('medianResTime', total_stats.get('Median', 0))), 2),
                            round(float(total_stats.get('minResTime', 0)), 2),
                            round(float(total_stats.get('maxResTime', 0)), 2),
                            round(float(total_stats.get('throughput', 0)), 2),
                            round(float(total_stats.get('errorPct', 0)), 2),
                            round(float(total_stats.get('pct1ResTime', 0)), 2),
                            round(float(total_stats.get('pct2ResTime', 0)), 2),
                            round(float(total_stats.get('pct3ResTime', 0)), 2)
                        ]
                    }
                    tables['aggregate_summary'] = pd.DataFrame(metrics)
                    logger.debug("Successfully created aggregate metrics")
                
                # Create errors table
                tables['errors'] = create_errors_table(stats_data)
                if tables['errors'] is not None:
                    logger.debug("Successfully created errors table")
                else:
                    logger.debug("No errors found in the statistics")
            else:
                logger.warning("No data found in statistics.json")
        else:
            logger.error(f"Statistics file not found at {statistics_json_path}")
        
        return tables
    except Exception as e:
        logger.error(f"Error in parse_jmeter_tables: {str(e)}", exc_info=True)
        raise 