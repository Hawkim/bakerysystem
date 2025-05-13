import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QLineEdit,
                            QTableWidget, QTableWidgetItem, QMessageBox,
                            QTabWidget, QSpinBox, QDoubleSpinBox, QGridLayout,
                            QScrollArea, QFrame, QFileDialog, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QTextDocument

import base64
from contextlib import contextmanager


import uuid
from PyQt6.QtWidgets import QMessageBox

AUTHORIZED_ID = "841b77f4b67b"  # Your authorized machine ID

def get_machine_id():
    return f"{uuid.getnode():012x}"

def enforce_license():
    if get_machine_id() != AUTHORIZED_ID:
        QMessageBox.critical(None, "Unauthorized", "This copy is not licensed for this machine.")
        sys.exit()


class DatabaseManager:
    """Centralized database management"""
    def __init__(self, db_name='bakery.db'):
        self.db_name = db_name
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    image_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER,
                    quantity INTEGER,
                    total_price REAL,
                    sale_date DATETIME,
                    FOREIGN KEY (item_id) REFERENCES items (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_invoice_count (
                    date TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()

class EditItemDialog(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Item")
        self.setModal(True)
        self.item_data = item_data
        self.image_path = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name field
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(self.item_data[1])
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Price field
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(0, 1000)
        self.price_edit.setPrefix("$")
        self.price_edit.setValue(self.item_data[2])
        price_layout.addWidget(self.price_edit)
        layout.addLayout(price_layout)
        
        # Image section
        image_layout = QHBoxLayout()
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(50, 50)
        self.image_preview.setStyleSheet("border: 1px solid #ccc;")
        
        if self.item_data[3]:
            try:
                image_data = base64.b64decode(self.item_data[3])
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                self.image_preview.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
            except:
                pass
        
        select_image_btn = QPushButton("Change Image")
        select_image_btn.clicked.connect(self.select_image)
        
        image_layout.addWidget(self.image_preview)
        image_layout.addWidget(select_image_btn)
        layout.addLayout(image_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            self.image_preview.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
    
    def get_updated_data(self):
        image_data = self.item_data[3]  # Keep existing image by default
        if self.image_path:
            with open(self.image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        return {
            'name': self.name_edit.text(),
            'price': self.price_edit.value(),
            'image_data': image_data
        }

class BakeryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_sale_items = []
        self.last_clear_time = datetime.now()
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("Bakery Management System")
        self.setGeometry(100, 100, 1200, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        self._create_sales_tab(tabs)
        self._create_reports_tab(tabs)
        self._create_inventory_tab(tabs)
    
    def _create_inventory_tab(self, tabs):
        inventory_tab = QWidget()
        layout = QVBoxLayout(inventory_tab)
        
        # Add item section
        add_section = QWidget()
        add_layout = QHBoxLayout(add_section)
        
        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("Item Name")
        self.item_price = QDoubleSpinBox()
        self.item_price.setRange(0, 1000)
        self.item_price.setPrefix("$")
        
        self._setup_image_upload(add_layout)
        
        add_btn = QPushButton("Add Item")
        add_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 1px solid #2e7d32;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
            }
        """)
        add_btn.clicked.connect(self._add_item)
        
        add_layout.addWidget(QLabel("Name:"))
        add_layout.addWidget(self.item_name)
        add_layout.addWidget(QLabel("Price:"))
        add_layout.addWidget(self.item_price)
        add_layout.addWidget(add_btn)
        
        layout.addWidget(add_section)
        
        self._setup_inventory_buttons(layout)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["ID", "Name", "Price", "Image", "Actions"])
        layout.addWidget(self.items_table)
        
        tabs.addTab(inventory_tab, "Inventory")
        self._load_items()
    
    def _setup_image_upload(self, layout):
        self.image_path = None
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(50, 50)
        self.image_preview.setStyleSheet("border: 1px solid #ccc;")
        
        select_image_btn = QPushButton("Select Image")
        select_image_btn.clicked.connect(self._select_image)
        
        layout.addWidget(select_image_btn)
        layout.addWidget(self.image_preview)
    
    def _setup_inventory_buttons(self, layout):
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #f5f5f5;
                color: #424242;
                border: 1px solid #9e9e9e;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #eeeeee;
            }
        """)
        refresh_btn.clicked.connect(self._load_items)
        button_layout.addWidget(refresh_btn)
        layout.addLayout(button_layout)
    
    def _select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(file_name)
            self.image_preview.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
    
    def _add_item(self):
        name = self.item_name.text()
        price = self.item_price.value()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter an item name")
            return
        
        try:
            image_data = None
            if self.image_path:
                with open(self.image_path, 'rb') as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO items (name, price, image_data) VALUES (?, ?, ?)',
                              (name, price, image_data))
                conn.commit()
            
            self._load_items()
            self._load_item_buttons()
            self.item_name.clear()
            self.item_price.setValue(0)
            self.image_path = None
            self.image_preview.clear()
            self.image_preview.setStyleSheet("border: 1px solid #ccc;")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add item: {str(e)}")
    
    def _load_items(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM items')
                items = cursor.fetchall()
            
            self.items_table.setRowCount(len(items))
            for i, item in enumerate(items):
                self._populate_item_row(i, item)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load items: {str(e)}")
    
    def _populate_item_row(self, row, item):
        self.items_table.setItem(row, 0, QTableWidgetItem(str(item[0])))
        self.items_table.setItem(row, 1, QTableWidgetItem(item[1]))
        self.items_table.setItem(row, 2, QTableWidgetItem(f"${item[2]:.2f}"))
        
        if item[3]:
            try:
                image_data = base64.b64decode(item[3])
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                image_label = QLabel()
                image_label.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
                self.items_table.setCellWidget(row, 3, image_label)
            except Exception:
                self.items_table.setItem(row, 3, QTableWidgetItem("No Image"))
        else:
            self.items_table.setItem(row, 3, QTableWidgetItem("No Image"))
        
        self._add_row_buttons(row, item[0])
    
    def _add_row_buttons(self, row, item_id):
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda checked, r=row: self._edit_item(r))
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda checked, r=row: self._delete_item(r))
        buttons_layout.addWidget(delete_btn)
        
        self.items_table.setCellWidget(row, 4, buttons_widget)
    
    def _edit_item(self, row):
        try:
            item_id = int(self.items_table.item(row, 0).text())
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
                item_data = cursor.fetchone()
            
            if not item_data:
                raise Exception("Item not found")
            
            dialog = EditItemDialog(self, item_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_updated_data()
                
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE items 
                        SET name = ?, price = ?, image_data = ?
                        WHERE id = ?
                    ''', (updated_data['name'], updated_data['price'], 
                          updated_data['image_data'], item_id))
                    conn.commit()
                
                self._load_items()
                self._load_item_buttons()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to edit item: {str(e)}")
    
    def _delete_item(self, row):
        try:
            item_id = int(self.items_table.item(row, 0).text())
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
                conn.commit()
            
            self._load_items()
            self._load_item_buttons()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete item: {str(e)}")

    def _create_sales_tab(self, tabs):
        sales_tab = QWidget()
        layout = QVBoxLayout(sales_tab)
        
        sales_layout = QHBoxLayout()
        
        # Left side - Item buttons
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        buttons_widget = QWidget()
        self.buttons_layout = QGridLayout(buttons_widget)
        self.buttons_layout.setSpacing(2)
        self.buttons_layout.setContentsMargins(2, 2, 2, 2)
        
        scroll.setWidget(buttons_widget)
        left_layout.addWidget(scroll)
        
        # Right side - Current sale
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.current_sale_table = QTableWidget()
        self.current_sale_table.setColumnCount(5)
        self.current_sale_table.setHorizontalHeaderLabels(["Item", "Quantity", "Price", "Total", "Actions"])
        self.current_sale_table.setColumnWidth(0, 100)
        self.current_sale_table.setColumnWidth(1, 80)
        self.current_sale_table.setColumnWidth(2, 80)
        self.current_sale_table.setColumnWidth(3, 80)
        self.current_sale_table.setColumnWidth(4, 60)
        right_layout.addWidget(self.current_sale_table)
        
        # Total and buttons section
        total_section = QWidget()
        total_layout = QHBoxLayout(total_section)
        
        total_labels = QWidget()
        total_labels_layout = QVBoxLayout(total_labels)
        total_labels_layout.setSpacing(2)
        
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.total_lbp_label = QLabel("Total: LBP 0")
        self.total_lbp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e7d32;")
        
        total_labels_layout.addWidget(self.total_label)
        total_labels_layout.addWidget(self.total_lbp_label)
        
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(10)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px;
                background-color: #ffebee;
                color: #d32f2f;
                border: 1px solid #d32f2f;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        clear_all_btn.clicked.connect(self._clear_sale)
        
        make_sale_btn = QPushButton("Make Sale")
        make_sale_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px;
                background-color: #e8f5e9;
                color: #2e7d32;
                border: 1px solid #2e7d32;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
            }
        """)
        make_sale_btn.clicked.connect(self._make_sale)
        
        buttons_layout.addWidget(clear_all_btn)
        buttons_layout.addWidget(make_sale_btn)
        
        total_layout.addWidget(total_labels)
        total_layout.addWidget(buttons_container)
        
        right_layout.addWidget(total_section)
        
        sales_layout.addWidget(left_panel, 2)
        sales_layout.addWidget(right_panel, 1)
        
        layout.addLayout(sales_layout)
        
        tabs.addTab(sales_tab, "Sales")
        self._load_item_buttons()

    def _handle_delete_row(self, row):
        """More reliable row deletion handler"""
        if 0 <= row < self.current_sale_table.rowCount():
            self.current_sale_table.removeRow(row)
            # Reset the row count to ensure proper cleanup
            remaining_rows = self.current_sale_table.rowCount()
            self.current_sale_table.setRowCount(remaining_rows)
            self._update_total()
    
    
    def _load_item_buttons(self):
        for i in reversed(range(self.buttons_layout.count())): 
            self.buttons_layout.itemAt(i).widget().setParent(None)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, price, image_data FROM items')
            items = cursor.fetchall()
        
        button_width = 120
        button_height = 100
        
        row = 0
        col = 0
        for item in items:
            container = QWidget()
            container.setFixedSize(button_width, button_height + 40)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(2)
            container_layout.setContentsMargins(2, 2, 2, 2)
            
            btn = QPushButton()
            btn.setFixedSize(button_width - 4, button_height - 4)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 2px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            
            if item[3]:
                try:
                    image_data = base64.b64decode(item[3])
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                    scaled_pixmap = pixmap.scaled(
                        button_width - 8,
                        button_height - 8,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    btn.setIcon(QIcon(scaled_pixmap))
                    btn.setIconSize(scaled_pixmap.size())
                except:
                    pass
            
            name_label = QLabel(item[1])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("font-size: 11px; font-weight: bold;")
            name_label.setWordWrap(True)
            
            price_label = QLabel(f"${item[2]:.2f}")
            price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_label.setStyleSheet("font-size: 10px; color: #666;")
            
            container_layout.addWidget(btn)
            container_layout.addWidget(name_label)
            container_layout.addWidget(price_label)
            
            btn.clicked.connect(lambda checked, item_id=item[0], name=item[1], price=item[2]: 
                              self._add_to_sale(item_id, name, price))
            
            self.buttons_layout.addWidget(container, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def _add_to_sale(self, item_id, name, price):
        for i in range(self.current_sale_table.rowCount()):
            if self.current_sale_table.item(i, 0).text() == name:
                current_qty = int(self.current_sale_table.item(i, 1).text())
                new_qty = current_qty + 1
                self.current_sale_table.setItem(i, 1, QTableWidgetItem(str(new_qty)))
                self.current_sale_table.setItem(i, 3, QTableWidgetItem(f"${price * new_qty:.2f}"))
                self._update_total()
                return
        
        row = self.current_sale_table.rowCount()
        self.current_sale_table.insertRow(row)
        
        self.current_sale_table.setItem(row, 0, QTableWidgetItem(name))
        self.current_sale_table.setItem(row, 1, QTableWidgetItem("1"))
        self.current_sale_table.setItem(row, 2, QTableWidgetItem(f"${price:.2f}"))
        self.current_sale_table.setItem(row, 3, QTableWidgetItem(f"${price:.2f}"))
        
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                color: #d32f2f;
                font-size: 16px;
                font-weight: bold;
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #ffebee;
                border-radius: 3px;
            }
        """)
        delete_btn.clicked.connect(lambda: self._remove_from_sale(row))
        
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(delete_btn)
        
        self.current_sale_table.setCellWidget(row, 4, button_widget)
        self._update_total()
    
    def _update_total(self):
        total = 0
        for row in range(self.current_sale_table.rowCount()):
            total += float(self.current_sale_table.item(row, 3).text().replace("$", ""))
        self.total_label.setText(f"Total: ${total:.2f}")
        self.total_lbp_label.setText(f"Total: LBP {int(total * 90000):,}")
    
    def _make_sale(self):
        if self.current_sale_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No items in current sale")
            return

        try:
            invoice_number = self._get_next_invoice_number()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")

                for row in range(self.current_sale_table.rowCount()):
                    item_name = self.current_sale_table.item(row, 0).text()
                    quantity = int(self.current_sale_table.item(row, 1).text())
                    total_price = float(self.current_sale_table.item(row, 3).text().replace("$", ""))

                    cursor.execute('SELECT id FROM items WHERE name = ?', (item_name,))
                    item = cursor.fetchone()

                    if not item:
                        raise Exception(f"Item {item_name} not found")

                    cursor.execute('''
                        INSERT INTO sales (item_id, quantity, total_price, sale_date)
                        VALUES (?, ?, ?, ?)
                    ''', (item[0], quantity, total_price, datetime.now()))

                cursor.execute("COMMIT")

            self._show_receipt(invoice_number)
            self.current_sale_table.setRowCount(0)
            self._update_total()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def _show_receipt(self, invoice_number):
        receipt = f"=== BAKERY RECEIPT ===\n\nInvoice #: INV-{invoice_number:04d}\n"
        receipt += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        html = f"""
        <h2>Bakery Receipt</h2>
        <p><strong>Invoice #:</strong> INV-{invoice_number:04d}<br>
        <strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr><ul>
        """

        total = 0
        for row in range(self.current_sale_table.rowCount()):
            item = self.current_sale_table.item(row, 0).text()
            qty = self.current_sale_table.item(row, 1).text()
            price = self.current_sale_table.item(row, 2).text()
            total_item = self.current_sale_table.item(row, 3).text()
            total += float(total_item.replace("$", ""))

            receipt += f"{item}\n  {qty} x {price} = {total_item}\n"
            html += f"<li>{item} - {qty} x {price} = {total_item}</li>"

        receipt += f"\nTotal: ${total:.2f}\nTotal: LBP {int(total * 90000):,}\nThank you for your purchase!"
        html += f"</ul><hr><p><strong>Total:</strong> ${total:.2f}<br><strong>Total (LBP):</strong> {int(total * 90000):,}</p>"

        dialog = QDialog(self)
        dialog.setWindowTitle("Receipt")
        layout = QVBoxLayout(dialog)

        label = QLabel()
        label.setText(receipt.replace("\n", "<br>"))
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)

        print_btn = QPushButton("Print Invoice")
        print_btn.clicked.connect(lambda: self._print_html_invoice(html))
        layout.addWidget(print_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
    
    def _show_report_dialog(self, title, html):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(html)
        label.setWordWrap(True)
        layout.addWidget(label)

        print_btn = QPushButton("Print Report")
        print_btn.clicked.connect(lambda: self._print_html_invoice(html))
        layout.addWidget(print_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    
    def _remove_from_sale(self, row):
        try:
            if self.current_sale_table.rowCount() > 0:
                self.current_sale_table.removeRow(row)
                # Force immediate update of the table
                self.current_sale_table.setRowCount(self.current_sale_table.rowCount())
                self._update_total()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to remove item: {str(e)}")

    def _clear_sale(self):
        if self.current_sale_table.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                "Clear Sale",
                "Are you sure you want to clear the current sale?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_sale_table.setRowCount(0)
                self._update_total()

    def _get_next_invoice_number(self):
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear out any old entries (older than 30 days)
                cursor.execute("DELETE FROM daily_invoice_count WHERE date < date('now', '-30 days')")
                
                # Get or create today's count
                cursor.execute('SELECT count FROM daily_invoice_count WHERE date = ?', (today,))
                result = cursor.fetchone()
                
                if result:
                    count = result[0] + 1
                    cursor.execute('UPDATE daily_invoice_count SET count = ? WHERE date = ?', 
                                 (count, today))
                else:
                    count = 1
                    cursor.execute('INSERT INTO daily_invoice_count (date, count) VALUES (?, ?)', 
                                 (today, count))
                
                conn.commit()
                return count
                
        except Exception as e:
            print(f"Error getting invoice number: {e}")
            return 1  # Fallback

    def _create_reports_tab(self, tabs):
        reports_tab = QWidget()
        layout = QVBoxLayout(reports_tab)
        
        reports_layout = QHBoxLayout()
        
        # Left side - Report buttons
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        daily_btn = QPushButton("Generate Daily Report")
        monthly_btn = QPushButton("Generate Monthly Report")
        view_history_btn = QPushButton("View Invoice History")
        clear_invoices_btn = QPushButton("Clear Invoices")
        
        clear_invoices_btn.setStyleSheet("""
            QPushButton {
                padding: 5px;
                background-color: #ffebee;
                color: #d32f2f;
                border: 1px solid #d32f2f;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        
        daily_btn.clicked.connect(self._generate_daily_report)
        monthly_btn.clicked.connect(self._generate_monthly_report)
        view_history_btn.clicked.connect(self._show_invoice_history)
        clear_invoices_btn.clicked.connect(self._clear_invoice_history)
        
        left_layout.addWidget(daily_btn)
        left_layout.addWidget(monthly_btn)
        left_layout.addWidget(view_history_btn)
        left_layout.addWidget(clear_invoices_btn)
        
        # Right side - Invoice history table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Search Invoice:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter invoice number (e.g., INV-0001)")
        self.search_input.textChanged.connect(self._filter_invoices)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        right_layout.addLayout(search_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Items Count", "Total", "Details"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSortingEnabled(True)
        self.history_table.horizontalHeader().sectionClicked.connect(self._sort_table)
        
        right_layout.addWidget(self.history_table)
        
        reports_layout.addWidget(left_panel, 1)
        reports_layout.addWidget(right_panel, 3)
        
        layout.addLayout(reports_layout)
        
        tabs.addTab(reports_tab, "Reports")
        self._load_invoice_history()
    
    def _load_invoice_history(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        MIN(s.id) as sale_id,
                        s.sale_date,
                        COUNT(DISTINCT s.item_id) as unique_items,
                        SUM(s.quantity) as total_quantity,
                        SUM(s.total_price) as total_price
                    FROM sales s
                    WHERE s.sale_date > ?
                    GROUP BY strftime('%Y-%m-%d %H:%M:%S', s.sale_date)
                    ORDER BY s.sale_date DESC
                ''', (self.last_clear_time,))
                sales = cursor.fetchall()
            
            self.history_table.setSortingEnabled(False)
            self.history_table.setRowCount(len(sales))
            
            # Get today's count once at the beginning
            today = datetime.now().strftime('%Y-%m-%d')
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT count FROM daily_invoice_count WHERE date = ?', (today,))
                result = cursor.fetchone()
                base_count = result[0] if result else 0
            
            for i, sale in enumerate(sales):
                # Use the base count plus the reverse index to maintain order
                invoice_num = f"INV-{(base_count - i):04d}"
                self.history_table.setItem(i, 0, QTableWidgetItem(invoice_num))
                
                date = datetime.strptime(sale[1], '%Y-%m-%d %H:%M:%S.%f')
                self.history_table.setItem(i, 1, QTableWidgetItem(date.strftime('%Y-%m-%d %H:%M')))
                
                self.history_table.setItem(i, 2, QTableWidgetItem(str(sale[3])))
                self.history_table.setItem(i, 3, QTableWidgetItem(f"${sale[4]:.2f}"))
                
                view_btn = QPushButton("View Details")
                view_btn.setStyleSheet("""
                    QPushButton {
                        padding: 3px;
                        background-color: #e3f2fd;
                        border: 1px solid #2196f3;
                        border-radius: 3px;
                        color: #1976d2;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #bbdefb;
                    }
                """)
                view_btn.clicked.connect(lambda checked, sale_date=sale[1]: self._show_invoice_details(sale_date))
                self.history_table.setCellWidget(i, 4, view_btn)
            
            self.history_table.setSortingEnabled(True)
            self.history_table.setColumnWidth(0, 120)
            self.history_table.setColumnWidth(1, 150)
            self.history_table.setColumnWidth(2, 100)
            self.history_table.setColumnWidth(3, 100)
            self.history_table.setColumnWidth(4, 90)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load invoice history: {str(e)}")

    def _print_html_invoice(self, html):
        document = QTextDocument()
        document.setHtml(html)

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            document.print(printer)

    def _show_invoice_details(self, sale_date):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        s.sale_date,
                        i.name,
                        s.quantity,
                        s.total_price
                    FROM sales s
                    JOIN items i ON s.item_id = i.id
                    WHERE strftime('%Y-%m-%d %H:%M:%S', s.sale_date) = strftime('%Y-%m-%d %H:%M:%S', ?)
                    ORDER BY s.id
                ''', (sale_date,))
                items = cursor.fetchall()
            
            if not items:
                return

            # Prepare invoice text
            sale_time = datetime.strptime(items[0][0], '%Y-%m-%d %H:%M:%S.%f')
            html = f"""
            <h2>Invoice Details</h2>
            <p><strong>Date:</strong> {sale_time.strftime('%Y-%m-%d %H:%M')}</p>
            <hr>
            <ul>
            """
            total = 0
            for item in items:
                qty = item[2]
                unit_price = item[3] / qty
                html += f"<li>{item[1]} - {qty} x ${unit_price:.2f} = ${item[3]:.2f}</li>"
                total += item[3]
            
            html += f"""
            </ul>
            <hr>
            <p><strong>Total:</strong> ${total:.2f}</p>
            <p><strong>Total (LBP):</strong> {int(total * 90000):,}</p>
            """

            # Show in a dialog with Print option
            dialog = QDialog(self)
            dialog.setWindowTitle("Invoice Details")
            layout = QVBoxLayout(dialog)

            label = QLabel()
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(html)
            label.setWordWrap(True)
            layout.addWidget(label)

            print_btn = QPushButton("Print Invoice")
            print_btn.clicked.connect(lambda: self._print_html_invoice(html))
            layout.addWidget(print_btn)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to show invoice details: {str(e)}")

    
    def _show_invoice_history(self):
        self._load_invoice_history()

    def _sort_table(self, column):
        current_order = self.history_table.horizontalHeader().sortIndicatorOrder()
        
        if column == 0:
            rows_data = []
            for row in range(self.history_table.rowCount()):
                date_item = self.history_table.item(row, 1)
                if date_item:
                    date = datetime.strptime(date_item.text(), '%Y-%m-%d %H:%M')
                    rows_data.append((row, date))
            
            rows_data.sort(key=lambda x: x[1], reverse=(current_order == Qt.SortOrder.AscendingOrder))
            
            for new_row, (old_row, _) in enumerate(rows_data):
                self.history_table.insertRow(new_row)
                for col in range(self.history_table.columnCount()):
                    if col == 4:
                        continue
                    item = self.history_table.item(old_row + 1, col)
                    if item:
                        self.history_table.setItem(new_row, col, QTableWidgetItem(item.text()))
                
                button = self.history_table.cellWidget(old_row + 1, 4)
                if button:
                    self.history_table.setCellWidget(new_row, 4, button)
                
                self.history_table.removeRow(old_row + 1)
        elif column == 3:
            rows_data = []
            for row in range(self.history_table.rowCount()):
                total_item = self.history_table.item(row, 3)
                if total_item:
                    price = float(total_item.text().replace('$', ''))
                    rows_data.append((row, price))
            
            rows_data.sort(key=lambda x: x[1], reverse=(current_order == Qt.SortOrder.AscendingOrder))
            
            for new_row, (old_row, _) in enumerate(rows_data):
                self.history_table.insertRow(new_row)
                for col in range(self.history_table.columnCount()):
                    if col == 4:
                        continue
                    item = self.history_table.item(old_row + 1, col)
                    if item:
                        self.history_table.setItem(new_row, col, QTableWidgetItem(item.text()))
                
                button = self.history_table.cellWidget(old_row + 1, 4)
                if button:
                    self.history_table.setCellWidget(new_row, 4, button)
                
                self.history_table.removeRow(old_row + 1)
        else:
            self.history_table.sortItems(column, Qt.SortOrder.AscendingOrder if current_order == Qt.SortOrder.DescendingOrder else Qt.SortOrder.DescendingOrder)

    def _filter_invoices(self):
        search_text = self.search_input.text().strip().upper()
        
        if not search_text:
            for row in range(self.history_table.rowCount()):
                self.history_table.setRowHidden(row, False)
            return
        
        for row in range(self.history_table.rowCount()):
            invoice_item = self.history_table.item(row, 0)
            if invoice_item and search_text in invoice_item.text().upper():
                self.history_table.setRowHidden(row, False)
            else:
                self.history_table.setRowHidden(row, True)

    def _clear_invoice_history(self):
        reply = QMessageBox.question(
            self,
            "Clear Invoice History",
            "Are you sure you want to clear the invoice history view? This will not affect the actual sales data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_table.setRowCount(0)
            self.search_input.clear()
            self.last_clear_time = datetime.now()

    def _generate_daily_report(self):
        today = datetime.now().date()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.name, SUM(s.quantity) as total_quantity, SUM(s.total_price) as total_sales
                    FROM sales s
                    JOIN items i ON s.item_id = i.id
                    WHERE DATE(s.sale_date) = DATE(?)
                    GROUP BY i.name
                ''', (today,))
                sales = cursor.fetchall()

            if not sales:
                QMessageBox.information(self, "Daily Report", "No sales recorded for today")
                return

            report_text = f"<h2>Daily Sales Report - {today}</h2><hr><ul>"
            total_sales = 0

            for item in sales:
                report_text += f"<li>{item[0]}: {item[1]} units - ${item[2]:.2f}</li>"
                total_sales += item[2]

            report_text += f"</ul><hr><p><strong>Total Sales:</strong> ${total_sales:.2f}<br>"
            report_text += f"<strong>Total Sales (LBP):</strong> {int(total_sales * 90000):,}</p>"

            self._show_report_dialog("Daily Report", report_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate daily report: {str(e)}")

    def _generate_monthly_report(self):
        today = datetime.now()
        first_day = today.replace(day=1)

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.name, SUM(s.quantity) as total_quantity, SUM(s.total_price) as total_sales
                    FROM sales s
                    JOIN items i ON s.item_id = i.id
                    WHERE DATE(s.sale_date) >= DATE(?)
                    GROUP BY i.name
                ''', (first_day,))
                sales = cursor.fetchall()

            if not sales:
                QMessageBox.information(self, "Monthly Report", "No sales recorded for this month")
                return

            report_text = f"<h2>Monthly Sales Report - {today.strftime('%B %Y')}</h2><hr><ul>"
            total_sales = 0

            for item in sales:
                report_text += f"<li>{item[0]}: {item[1]} units - ${item[2]:.2f}</li>"
                total_sales += item[2]

            report_text += f"</ul><hr><p><strong>Total Sales:</strong> ${total_sales:.2f}<br>"
            report_text += f"<strong>Total Sales (LBP):</strong> {int(total_sales * 90000):,}</p>"

            self._show_report_dialog("Monthly Report", report_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate monthly report: {str(e)}")

if __name__ == '__main__':
    enforce_license() 
    app = QApplication(sys.argv)
    window = BakeryApp()
    window.show()
    sys.exit(app.exec())
