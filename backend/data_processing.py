import xml.etree.ElementTree as ET
import re
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(filename='unprocessed_sms.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def parse_amount(amount_str):
    """Extract numeric amount from string (e.g., '5000 RWF' -> 5000)"""
    match = re.search(r'(\d+)', amount_str)
    return int(match.group(1)) if match else None

def parse_date(date_str):
    """Convert date string to standard format (YYYY-MM-DD HH:MM:SS)"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def categorize_sms(body):
    """Categorize SMS based on content"""
    body = body.lower()
    if 'received' in body:
        return 'Incoming Money'
    elif 'payment' in body and 'airtime' in body:
        return 'Airtime Bill Payment'
    elif 'payment' in body:
        return 'Payments to Code Holders'
    elif 'withdrawn' in body:
        return 'Withdrawals from Agents'
    elif 'purchased' in body and ('internet' in body or 'bundle' in body):
        return 'Internet Bundle Purchase'
    elif 'transfer' in body and 'bank' in body:
        return 'Bank Transfer'
    elif 'deposit' in body and 'bank' in body:
        return 'Bank Deposit'
    elif 'transfer' in body:
        return 'Transfer to Mobile Number'
    elif 'cash power' in body:
        return 'Cash Power Bill Payment'
    else:
        return 'Unknown'

def process_sms(xml_file):
    """Process SMS data from XML file"""
    if not os.path.exists(xml_file):
        logging.error(f"XML file not found: {xml_file}")
        raise FileNotFoundError(f"XML file not found: {xml_file}")

    transactions = []
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Failed to parse XML file: {e}")
        raise

    for sms in root.findall('sms'):
        body_elem = sms.find('body')
        if body_elem is None or body_elem.text is None:
            logging.info(f"Unprocessed SMS: Missing or empty body")
            continue
        body = body_elem.text.strip()

        category = categorize_sms(body)

        # Extract fields using regex
        tx_id = re.search(r'(?:TxId|Transaction ID): *(\d+)', body, re.IGNORECASE)
        amount = re.search(r'(\d+ RWF)', body, re.IGNORECASE)
        date = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', body)
        sender = re.search(r'from ([A-Za-z\s]+)(?:\.|\s|$)', body, re.IGNORECASE)
        recipient = re.search(r'to ([A-Za-z\s]+)(?:\.|\s|$)', body, re.IGNORECASE)
        agent = re.search(r'agent: ([A-Za-z\s]+)(?:\.|\s|$)', body, re.IGNORECASE)
        phone = re.search(r'\((\d+)\)', body)  # Extract phone numbers like (250123456789)

        # Clean and validate data
        tx_data = {
            'tx_id': tx_id.group(1) if tx_id else None,
            'category': category,
            'amount': parse_amount(amount.group(1)) if amount else None,
            'date': parse_date(date.group(1)) if date else None,
            'sender': sender.group(1).strip() if sender else None,
            'recipient': recipient.group(1).strip() if recipient else None,
            'agent': agent.group(1).strip() if agent else None,
            'phone': phone.group(1) if phone else None
        }

        if tx_data['tx_id'] and tx_data['amount'] and tx_data['date']:
            transactions.append(tx_data)
        else:
            logging.info(f"Unprocessed SMS: {body} | Reason: Missing tx_id, amount, or date")

    return transactions

if __name__ == "__main__":
    xml_file = 'modified_sms_v2.xml'
    try:
        transactions = process_sms(xml_file)
        print(f"Processed {len(transactions)} transactions")
    except Exception as e:
        print(f"Error processing XML file: {e}")