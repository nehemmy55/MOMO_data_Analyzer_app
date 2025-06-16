# MOMO_data_Analyzer_app
# MTN MoMo Transaction Dashboard

the full-stack application for analyzing and visualizing MTN Mobile Money transactions from SMS data.


## Features

- Process raw SMS XML data into structured transactions
- Filter transactions by type, date range, and amount
- Visualize transaction patterns with interactive charts
- View detailed transaction information
- Responsive design works on desktop and mobile

## Prerequisites

- Python 3.8+
- Node.js 14+
- SQLite3
- Modern web browser

## Installation

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/nehemmy55/MOMO_data_Analyzer_app.git
   cd momo-dashboard

2. create Python virtual environment with this bash code in your terminal:
   python -m venv venv
   source venv\Scripts\activate

3. Installing  Python dependencies:
   pip install -r requirements.txt

4. Run the data processing script:
   python data_processing.py --> this will process that modified_sms_v2.xml and then categorize transaction and load them to database by creating database called transactions.db but also uncategorized data will be sent to unprocessed_sms.log

5. Run the Flask API as Start the Backend Server
     python api.py

6.  Open the Dashboard by runing index.html in your browser
    The server will start at http://localhost:5000

