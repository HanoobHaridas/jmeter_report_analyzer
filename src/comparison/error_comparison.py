import pandas as pd
import logging

logger = logging.getLogger(__name__)

def compare_errors(df1, df2):
    """Compare error statistics between two reports."""
    if df1 is None or df2 is None or df1.empty or df2.empty:
        logger.warning("One or both DataFrames are empty or None")
        return pd.DataFrame()

    comparison_data = []
    
    # Get unique endpoints and errors from both reports
    endpoints = set(df1['Endpoint'].unique()) | set(df2['Endpoint'].unique())
    
    for endpoint in sorted(endpoints):
        try:
            errors1 = df1[df1['Endpoint'] == endpoint] if endpoint in df1['Endpoint'].values else pd.DataFrame()
            errors2 = df2[df2['Endpoint'] == endpoint] if endpoint in df2['Endpoint'].values else pd.DataFrame()
            
            # Get unique error descriptions
            error_descriptions = set(errors1['Error'].unique()) | set(errors2['Error'].unique())
            
            for error in sorted(error_descriptions):
                try:
                    # Get error counts
                    count1 = errors1[errors1['Error'] == error]['Count'].iloc[0] if not errors1.empty and error in errors1['Error'].values else 0
                    count2 = errors2[errors2['Error'] == error]['Count'].iloc[0] if not errors2.empty and error in errors2['Error'].values else 0
                    
                    # Get total samples for percentage calculation
                    total1 = errors1['Total'].iloc[0] if not errors1.empty and 'Total' in errors1.columns else 0
                    total2 = errors2['Total'].iloc[0] if not errors2.empty and 'Total' in errors2.columns else 0
                    
                    # Calculate error percentages
                    pct1 = (count1 / total1 * 100) if total1 > 0 else 0
                    pct2 = (count2 / total2 * 100) if total2 > 0 else 0
                    
                    # Calculate difference in error counts and percentages
                    count_diff = count2 - count1
                    pct_diff = pct2 - pct1
                    
                    comparison_data.append({
                        'Endpoint': endpoint,
                        'Error Description': error,
                        'Report 1 Count': count1,
                        'Report 1 %': pct1,
                        'Report 2 Count': count2,
                        'Report 2 %': pct2,
                        'Count Difference': count_diff,
                        '% Difference': pct_diff
                    })
                except Exception as e:
                    logger.error(f"Error processing error {error} for endpoint {endpoint}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error processing endpoint {endpoint}: {str(e)}")
            continue
    
    if not comparison_data:
        logger.warning("No comparison data generated")
        return pd.DataFrame()
    
    # Create DataFrame and format numeric columns
    comparison_df = pd.DataFrame(comparison_data)
    
    # Format numeric columns
    numeric_cols = ['Report 1 %', 'Report 2 %', '% Difference']
    for col in numeric_cols:
        if col in comparison_df.columns:
            comparison_df[col] = comparison_df[col].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)
    
    return comparison_df 