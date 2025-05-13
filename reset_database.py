import sqlite3
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

class DatabaseResetter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bakery Database Reset Tool")
        self.setGeometry(100, 100, 400, 200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add warning label
        warning_label = QLabel(
            "WARNING: This tool will delete ALL data from the bakery database.\n\n"
            "This includes:\n"
            "- All items in inventory\n"
            "- All sales history\n"
            "- All invoice numbers\n\n"
            "This action cannot be undone!"
        )
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)
        
        # Add reset button
        reset_btn = QPushButton("Reset Database")
        reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #ffebee;
                color: #d32f2f;
                border: 1px solid #d32f2f;
                border-radius: 4px;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        reset_btn.clicked.connect(self.reset_database)
        layout.addWidget(reset_btn)
        
        # Add status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def reset_database(self):
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you absolutely sure you want to reset the database?\n\n"
            "This will delete ALL data and cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('bakery.db')
                cursor = conn.cursor()
                
                # Drop all tables
                cursor.execute('DROP TABLE IF EXISTS sales')
                cursor.execute('DROP TABLE IF EXISTS items')
                cursor.execute('DROP TABLE IF EXISTS daily_invoice_count')
                
                # Recreate tables
                cursor.execute('''
                    CREATE TABLE items (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        image_data TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE sales (
                        id INTEGER PRIMARY KEY,
                        item_id INTEGER,
                        quantity INTEGER,
                        total_price REAL,
                        sale_date DATETIME,
                        FOREIGN KEY (item_id) REFERENCES items (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE daily_invoice_count (
                        date TEXT PRIMARY KEY,
                        count INTEGER DEFAULT 0
                    )
                ''')
                
                conn.commit()
                conn.close()
                
                self.status_label.setText("Database has been reset successfully!")
                self.status_label.setStyleSheet("color: #2e7d32; font-size: 12px;")
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
                if conn:
                    conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DatabaseResetter()
    window.show()
    sys.exit(app.exec()) 