# Imports
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime

# Flask setup
app = Flask(__name__)

def get_states_and_haulers():
    conn = sqlite3.connect('resupply_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT pickup_address_state FROM donations WHERE pickup_address_state IS NOT NULL ORDER BY pickup_address_state;")
    states = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT assigned_hauler_id, TRIM(assigned_hauler_name) AS hauler_name FROM donations WHERE assigned_hauler_name IS NOT NULL ORDER BY hauler_name;")
    haulers = cursor.fetchall()
    conn.close()
    return states, haulers

# Set the fixed start date
def get_first_date():
    return '2023-08-30'

# Main function - using Flask
@app.route('/', methods=['GET', 'POST'])
def index():
    DATA_START_DATE = '2023-08-30'
    DATA_END_DATE = '2024-08-28'

    start_date = request.form.get('start_date') or DATA_START_DATE
    end_date = request.form.get('end_date') or DATA_END_DATE
    hauler = request.form.get('hauler')
    location = request.form.get('location')
    trendline = request.form.get('trendline') or 'none'
    moving_average_window = request.form.get('moving_average_window') or '3'
    states, haulers = get_states_and_haulers()

    conn = sqlite3.connect('resupply_data.db')
    cursor = conn.cursor()

    # Base query to compare card data to
    fixed_query = '''
        SELECT
            ROUND(AVG(completion_percentage), 2) AS avg_completion_percentage
        FROM (
            SELECT
                donation_date,
                COUNT(*) AS total_donations,
                SUM(CASE WHEN hauler_status = 'completed' THEN 1 ELSE 0 END) AS completed_donations,
                (SUM(CASE WHEN hauler_status = 'completed' THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS completion_percentage
            FROM
                donations
            WHERE
                donation_date BETWEEN ? AND ?
            GROUP BY donation_date
        )
    '''
    cursor.execute(fixed_query, [DATA_START_DATE, DATA_END_DATE])
    all_time_avg_completion_percentage = cursor.fetchone()[0]

    # Dynamic querying based on initial parameters
    query = '''
        SELECT
            donation_date,
            COUNT(*) AS total_donations,
            SUM(CASE WHEN hauler_status = 'completed' THEN 1 ELSE 0 END) AS completed_donations,
            ROUND(
                (SUM(CASE WHEN hauler_status = 'completed' THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                2
            ) AS completion_percentage
        FROM
            donations
        WHERE
            donation_date BETWEEN ? AND ?
    '''
    params = [start_date, end_date]

    if hauler:
        query += " AND assigned_hauler_name = ?"
        params.append(hauler)
    if location:
        query += " AND pickup_address_state = ?"
        params.append(location)

    query += " GROUP BY donation_date ORDER BY donation_date;"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()

    # No data condition - user chose state and hauler that don't match
    if not rows: 
        return render_template(
            'index.html',
            graph_html='',
            states=states,
            haulers=haulers,
            start_date=start_date,
            end_date=end_date,
            hauler=hauler,
            location=location,
            trendline=trendline,
            moving_average_window=moving_average_window,
            average_completion_percentage="N/A",
            completion_percentage_color="black",
            difference_text="",
            average_time_between_events="N/A",
            popular_cancellation_reason="N/A",
            total_donations="N/A",
            total_completed_donations="N/A",
            alert_message="No data was found within the specified parameters."
        )

    df = pd.DataFrame(rows, columns=["donation_date", "total_donations", "completed_donations", "completion_percentage"])
    df['donation_date'] = pd.to_datetime(df['donation_date']).dt.date
    average_completion_percentage = df['completion_percentage'].mean() if not df.empty else 0
    total_donations = df['total_donations'].sum()
    total_completed_donations = df['completed_donations'].sum()
    total_donations_formatted = f"{total_donations:,}"
    total_completed_donations_formatted = f"{total_completed_donations:,}"
    difference_percentage = round(average_completion_percentage - all_time_avg_completion_percentage, 2)

    if difference_percentage > 0:
        completion_percentage_color = 'rgb(36, 141, 40)'
        difference_text = f"({difference_percentage}% above average)"
    elif difference_percentage < 0:
        completion_percentage_color = 'rgb(223, 32, 27)'
        difference_text = f"({abs(difference_percentage)}% below average)"
    else:
        completion_percentage_color = 'rgb(120, 120, 120)'
        difference_text = "(equal to average)"

    # Most popular cancellation reason
    cursor.execute('''
        SELECT cancellation_reason, COUNT(*) AS count
        FROM donations
        WHERE donation_date BETWEEN ? AND ? AND cancellation_reason IS NOT NULL
        GROUP BY cancellation_reason
        ORDER BY count DESC
        LIMIT 1
    ''', params[:2])
    popular_cancellation_reason = cursor.fetchone()
    popular_cancellation_reason = popular_cancellation_reason[0] if popular_cancellation_reason else 'None'

    # Avg time between key events
    cursor.execute('''
        SELECT AVG(julianday(partner_complete.event_timestamp) - julianday(partner_accept.event_timestamp)) AS avg_time_days
        FROM events partner_accept
        JOIN events partner_complete ON partner_accept.donation_id = partner_complete.donation_id
        WHERE partner_accept.event_type = 'partner_accept'
        AND partner_complete.event_type = 'partner_complete'
        AND partner_accept.event_timestamp BETWEEN ? AND ?
    ''', params[:2])
    average_time_between_events = cursor.fetchone()[0]
    average_time_between_events = round(average_time_between_events, 2) if average_time_between_events else 'N/A'
    conn.close()

    # Plotting
    fig = px.scatter(df, x="donation_date", y="completion_percentage", 
                     labels={'donation_date': 'Date', 'completion_percentage': 'Completion Percentage (%)'}, 
                     title='Completion Percentage Over Time')

    fig.update_traces(mode='lines+markers', line=dict(color="rgb(13, 96, 172)"), marker=dict(color="rgb(13, 96, 172)"))

    # Trendlines
    if trendline == 'linear':
        z = np.polyfit(df["donation_date"].map(datetime.toordinal), df["completion_percentage"], 1)
        p = np.poly1d(z)
        df['trend'] = p(df["donation_date"].map(datetime.toordinal))
        fig.add_trace(go.Scatter(x=df["donation_date"], y=df['trend'], mode='lines', name='Linear Trendline', line=dict(color="rgb(223, 32, 27)")))
    elif trendline == 'quadratic':
        z = np.polyfit(df["donation_date"].map(datetime.toordinal), df["completion_percentage"], 2)
        p = np.poly1d(z)
        df['trend'] = p(df["donation_date"].map(datetime.toordinal))
        fig.add_trace(go.Scatter(x=df["donation_date"], y=df['trend'], mode='lines', name='Quadratic Trendline', line=dict(color="rgb(223, 32, 27)")))
    elif trendline == 'cubic':
        z = np.polyfit(df["donation_date"].map(datetime.toordinal), df["completion_percentage"], 3)
        p = np.poly1d(z)
        df['trend'] = p(df["donation_date"].map(datetime.toordinal))
        fig.add_trace(go.Scatter(x=df["donation_date"], y=df['trend'], mode='lines', name='Cubic Trendline', line=dict(color="rgb(223, 32, 27)")))
    elif trendline == 'moving_average':
        window = int(moving_average_window)
        df['trend'] = df["completion_percentage"].rolling(window=window).mean()
        fig.add_trace(go.Scatter(x=df["donation_date"], y=df['trend'], mode='lines', name=f'Moving Average (Window {window})', line=dict(color="rgb(223, 32, 27)")))

    # Figure to plot
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Completion Percentage (%)',
        yaxis=dict(
            tickformat=".2f",
            title_standoff=20
        ),
        xaxis=dict(range=[df['donation_date'].min(), df['donation_date'].max()]),
        template='plotly_white',
        margin=dict(l=70, r=30, t=40, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            family="Poppins, sans-serif",
            size=12,
            color="black"
        ),
        title={
            'text': 'Completion Percentage Over Time',
            'y':.98,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 18
            }
        },
        showlegend=False
    )

    graph_html = pio.to_html(fig, full_html=False)
    graph_html = f'''
        <div style="border: 1px solid rgb(218, 218, 218); border-radius: 0.375rem; border-radius-sm: 0.25rem; bs-border-radius-lg: 0.5rem; bs-border-radius-xl: 1rem; bs-border-radius-xxl: 2rem; padding: 1rem;">
            {graph_html}
        </div>
    '''

    # Interface with HTML
    return render_template(
        'index.html',
        graph_html=graph_html,
        states=states,
        haulers=haulers,
        start_date=start_date,
        end_date=end_date,
        hauler=hauler,
        location=location,
        trendline=trendline,
        moving_average_window=moving_average_window,
        average_completion_percentage=round(average_completion_percentage, 2) if average_completion_percentage is not None else "N/A",
        completion_percentage_color=completion_percentage_color,
        difference_text=difference_text,
        average_time_between_events=average_time_between_events,
        popular_cancellation_reason=popular_cancellation_reason,
        total_donations=total_donations_formatted,
        total_completed_donations=total_completed_donations_formatted,
        alert_message=None
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))