import re
import sqlite3
import logging
from datetime import datetime
import xml.etree.ElementTree as ET

logging.basicConfig(filename='unprocessed_sms.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

DB_FILE = 'transactions.db'
XML_FILE = 'modified_sms_v2.xml'

""" Define transaction categories and their regex patterns """
TRANSACTION_TYPES = {
    "Incoming Money": r'received (\d+[,.]?\d*) RWF from',
    "Payments to Code Holders": r'payment of (\d+[,.]?\d*) RWF to [A-Za-z ]+ \d+',
    "Transfers to Mobile Numbers": r'(\d+[,.]?\d*) RWF transferred to [A-Za-z ]+ \([0-9]+\)',
    "Bank Deposits": r'bank deposit of (\d+[,.]?\d*) RWF',
    "Airtime Bill Payments": r'payment of (\d+[,.]?\d*) RWF to Airtime',
    "Cash Power Bill Payments": r'payment of (\d+[,.]?\d*) RWF to Cash Power',
    "Transactions Initiated by Third Parties": r'transaction of (\d+[,.]?\d*) RWF by [A-Za-z ]+',
    "Withdrawals from Agents": r'withdrawn (\d+[,.]?\d*) RWF',
    "Bank Transfers": r'External Transaction Id',
    "Internet and Voice Bundle Purchases": r'purchased an internet bundle'
}


SCHEMA = '''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    transaction_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    receiver TEXT,
    sender TEXT,
    phone_number TEXT,
    agent TEXT,
    code TEXT,
    date TEXT NOT NULL,
    message TEXT,
    raw_body TEXT
);
'''

def parse_amount(text):
    """Extracting amount from SMS text and change them to integer"""
    match = re.search(r'(\d+[,.]?\d*)\s*RWF', text)
    if match:
        return int(match.group(1).replace(',', ''))
    return None

def parse_date(text):
    """Extract date from SMS text and then change formats"""
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
        r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    return datetime.strptime(match.group(1), '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        return datetime.strptime(match.group(1), '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def parse_transaction_id(text):
    """Extracting transaction ID from SMS text"""
    patterns = [
        r'Transaction ID: (\d+)',
        r'TxId: (\d+)',
        r'Id: (\d+)',
        r'Financial Transaction Id: (\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def categorize_transaction(body):
    """use regex pattern to categorize transaction"""
    body_lower = body.lower()
    for category, pattern in TRANSACTION_TYPES.items():
        if re.search(pattern, body_lower, re.IGNORECASE):
            return category
    return None

def extract_transaction_details(body, category):
    """Extract transaction detail based on categories """
    details = {
        'transaction_type': category,
        'amount': parse_amount(body),
        'date': parse_date(body),
        'transaction_id': parse_transaction_id(body),
        'message': body,
        'raw_body': body
    }
    
    
    if category == "Incoming Money":
        match = re.search(r'from ([A-Za-z ]+)', body, re.IGNORECASE)
        if match:
            details['sender'] = match.group(1).strip()
            
    elif category in ["Payments to Code Holders", "Transfers to Mobile Numbers", 
                     "Airtime Bill Payments", "Cash Power Bill Payments"]:
        match = re.search(r'to ([A-Za-z ]+)', body, re.IGNORECASE)
        if match:
            details['receiver'] = match.group(1).strip()
            
    elif category == "Withdrawals from Agents":
        match = re.search(r'agent: ([A-Za-z ]+)', body, re.IGNORECASE)
        if match:
            details['agent'] = match.group(1).strip()
            
    elif category == "Transactions Initiated by Third Parties":
        match = re.search(r'by ([A-Za-z ]+)', body, re.IGNORECASE)
        if match:
            details['sender'] = match.group(1).strip()
    
    phone_match = re.search(r'\((\d+)\)', body)
    if phone_match:
        details['phone_number'] = phone_match.group(1)
        
    return details

def init_database():
    """start database with schema"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    conn.commit()
    conn.close()

def store_transaction(transaction):
    """Store all transaction in database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO transactions (
                transaction_id, transaction_type, amount, receiver, sender,
                phone_number, agent, code, date, message, raw_body
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction.get('transaction_id'),
            transaction.get('transaction_type'),
            transaction.get('amount'),
            transaction.get('receiver'),
            transaction.get('sender'),
            transaction.get('phone_number'),
            transaction.get('agent'),
            transaction.get('code'),
            transaction.get('date'),
            transaction.get('message'),
            transaction.get('raw_body')
        ))
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing transaction: {e}\nMessage: {transaction.get('raw_body')}")
    finally:
        conn.close()

def process_sms_file():
    """Process XML file and then extract transactions"""
    init_database()
    
    try:
        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    except Exception as e:
        logging.error(f"Error parsing XML file: {e}")
        return
    
    for sms in root.findall('sms'):
        body = sms.attrib.get('body', '')
        category = categorize_transaction(body)
        
        if not category:
            logging.info(f"Uncategorized message: {body}")
            continue
            
        transaction = extract_transaction_details(body, category)
        
        if not transaction.get('amount'):
            logging.info(f"Message with missing amount: {body}")
            continue
            
        store_transaction(transaction)

def main():
    print("Starting SMS processing...")
    process_sms_file()
    print("Processing complete. Check unprocessed_sms.log for any unprocessed messages.")

if __name__ == '__main__':
    main()