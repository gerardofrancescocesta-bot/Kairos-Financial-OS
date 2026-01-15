
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def predict_future_nw(history_df, months_ahead=[6, 12, 24]):
    """
    Performs Linear Regression on Net Worth history.
    Returns a dictionary: {month_offset: predicted_value}
    """
    if history_df.empty or len(history_df) < 2:
        return {m: None for m in months_ahead}, 0
    
    # Prepare data
    # We convert dates to ordinal numbers for regression
    try:
        df = history_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['ordinal'] = df['date'].map(datetime.toordinal)
        x = df['ordinal'].values
        y = df['net_worth'].values
        
        # Fit Line (y = mx + c)
        slope, intercept = np.polyfit(x, y, 1)
        
        predictions = {}
        last_date = df['date'].max()
        
        for m in months_ahead:
            future_date = last_date + pd.DateOffset(months=m)
            future_ordinal = future_date.toordinal()
            pred = slope * future_ordinal + intercept
            predictions[m] = pred
            
        return predictions, slope # Return slope to know daily growth rate
    except Exception as e:
        print(f"Forecast Error: {e}")
        return {m: None for m in months_ahead}, 0

def calculate_time_to_target(current_nw, monthly_saving, target=1000000, growth_rate_annual=0.0):
    """
    Calculates months to reach target.
    If growth_rate is 0, assumes linear accumulation.
    """
    if current_nw >= target:
        return 0
    
    if monthly_saving <= 0:
        return float('inf') # Never reach if we don't save or burn cash
    
    # Simple calculation: (Target - Current) / Monthly
    # Ignoring compound interest on assets for this specific 'Velocity' metric unless specified.
    # User said "based on current savings rate". Let's assume linear for simplicity (Cashflow adds to NW).
    
    needed = target - current_nw
    months = needed / monthly_saving
    return months

def analyze_trajectory(history_df):
    """
    Returns a system status message based on the trend.
    """
    if history_df.empty or len(history_df) < 2:
        return "INSUFFICIENT DATA FOR TRAJECTORY ANALYSIS."
    
    # Check simple diff
    first = history_df.iloc[0]['net_worth']
    last = history_df.iloc[-1]['net_worth']
    
    if last > first:
        return "POSITIVE TRAJECTORY. ASCENDING."
    elif last < first:
        return "NEGATIVE TRAJECTORY. DESCENDING."
    else:
        return "TRAJECTORY FLAT. STAGNATION DETECTED."
