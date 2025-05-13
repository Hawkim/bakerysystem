# Bakery Management System

A simple desktop application for managing a small bakery's inventory, sales, and reports.

## Features

- Inventory Management
  - Add new items with name, price, and quantity
  - Remove items from inventory
  - View current inventory status

- Sales Management
  - Record sales transactions
  - View sales history
  - Automatic inventory updates

- Reporting
  - Generate daily sales reports
  - Generate monthly sales reports
  - View total sales and quantities sold

## Setup

1. Make sure you have Python 3.8 or higher installed on your system.

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python bakery_app.py
   ```

## Usage

### Inventory Management
- Use the "Inventory" tab to add new items
- Enter the item name, price, and initial quantity
- Click "Add Item" to add the item to inventory
- Use the "Delete" button to remove items

### Sales
- Use the "Sales" tab to record sales
- Enter the item name and quantity
- Click "Record Sale" to process the sale
- The inventory will be automatically updated

### Reports
- Use the "Reports" tab to generate reports
- Click "Generate Daily Report" for today's sales
- Click "Generate Monthly Report" for the current month's sales

## Data Storage

The application uses SQLite database (`bakery.db`) to store all data locally. The database file will be created automatically when you first run the application. 