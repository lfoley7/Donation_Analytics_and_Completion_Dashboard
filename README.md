# Donation Analytics and Completion Dashboard

## GitHub Pages Website

The project is available on GitHub Pages at the following link: [Donation Analytics and Completion Dashboard](https://lfoley7.github.io/Donation_Analytics_and_Completion_Dashboard/)

## Tech Stack

This project was built using:

- **Python** 3.12.2
- **Flask**
- **SQLite**
- **Plotly**
- **Numpy**
- **Pandas**
- **Bootstrap** 5.3.0
- **Jinja2**
- **Flask**
- **HTML**
- **CSS**
- **jQuery**
- **FontAwesome** 6.0.0
- **Google Fonts**

## Run the Code!

- 1. **Clone the Repository**:
   ```bash
   git clone https://github.com/lfoley7/Donation_Analytics_and_Completion_Dashboard.git
   cd Donation_Analytics_and_Completion_Dashboard
   ```

## Project Requirements Completed

- **Subqueries**: Subqueries were used in SQL queries to extract specific data and to create more complex queries and refined results
- **Built-in Functions**: Several built-in SQL functions -- such as `SUM()`, `COUNT()`, `ROUND()`, and `TRIM()` -- were used to process and clean data
- **Display Metrics**: The dashboard displays metrics related to the completion percentage of donations, including average completion percentage, time between key events, and most popular cancellation reasons

## Errors Encountered

- **Partner Status Issue**:
  The project requirements mention a `partner_status` field that needed to be set to "completed." I was unable to find this field in the SQL tabels, and I believe that this field was confused with the "hauler status" field. The code assumes that this was meant to be `hauler_status`, which tracks the completion of hauler tasks.
  
- **Hauler Name Sorting Issue**:
  Two of the hauling companies had a leading space before their names, causing sorting issues. This was resolved by applying the `TRIM()` function in SQL to remove the leading spaces.

- **Future Data Handling**:
  The dataset included future data for scheduled pickups, which haven't been fulfilled and were skewing the results. The code now cuts off data processing at August 28th, 2024, so future data does not interfere with the analysis.

## Additional Opportunities

In addition to fulfilling the basic project requirements, this dashboard includes several additional features:

- **Time Between Key Events**: The dashboard calculates and displays the average time taken between key events
  
- **Cancellation Reasons**: The most popular cancellation reason is displayed
  
- **Trend Analysis**: Users can apply trendline analyses (e.g., linear, quadratic, cubic, moving average) to the completion percentage data to better understand trends over time
  
- **Customizable Dashboard**: The dashboard allows users to filter the data by date range, hauler, and location
