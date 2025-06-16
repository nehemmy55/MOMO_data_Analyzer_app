import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)

CORS(app)
DATABASE = 'transactions.db'

def get_db_connection():
    """Creating database connection that returns rows as dictionaries."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def _build_filter_clause(args):
    """Helper function to build the WHERE clause and params for filtering."""
   
    where_clause = " WHERE 1=1"
    params = []


    transaction_type = args.get('type')
    start_date = args.get('start_date')
    end_date = args.get('end_date')

    
    if transaction_type:
        where_clause += " AND transaction_type = ?"
        params.append(transaction_type)

    if start_date:
        where_clause += " AND date >= ?"
        params.append(f"{start_date} 00:00:00")

    if end_date:

        where_clause += " AND date <= ?"
        params.append(f"{end_date} 23:59:59")
        
    return where_clause, params

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Fetch all transactions with optional filtering."""
    try:
        where_clause, params = _build_filter_clause(request.args)
        
        query = f"SELECT * FROM transactions {where_clause} ORDER BY date DESC"
        
        conn = get_db_connection()
        transactions = conn.execute(query, params).fetchall()
        conn.close()
        
        
        transactions_list = [dict(row) for row in transactions]
        
        return jsonify({
            'success': True,
            'count': len(transactions_list),
            'transactions': transactions_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary statistics, apply the same filters as transactions."""
    try:
        where_clause, params = _build_filter_clause(request.args)
        conn = get_db_connection()
        
       
        total_stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(AVG(amount), 0) as avg_amount
            FROM transactions
            {where_clause}
        """
        total_stats = conn.execute(total_stats_query, params).fetchone()
        
       
        type_stats_query = f"""
            SELECT 
                transaction_type,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM transactions
            {where_clause}
            GROUP BY transaction_type
            ORDER BY total_amount DESC
        """
        type_stats = [dict(row) for row in conn.execute(type_stats_query, params).fetchall()]
        
       
        monthly_stats_query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM transactions
            {where_clause}
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month ASC
        """
        monthly_stats = [dict(row) for row in conn.execute(monthly_stats_query, params).fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_transactions': total_stats['total_count'],
                'total_amount': total_stats['total_amount'],
                'average_amount': total_stats['avg_amount'],
                'by_type': type_stats,
                'by_month': monthly_stats
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions/types', methods=['GET'])
def get_transaction_types():
    """Get a unique list of all transaction types from the database."""
    try:
        conn = get_db_connection()
        types = conn.execute("SELECT DISTINCT transaction_type FROM transactions WHERE transaction_type IS NOT NULL ORDER BY transaction_type").fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'types': [t['transaction_type'] for t in types]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

