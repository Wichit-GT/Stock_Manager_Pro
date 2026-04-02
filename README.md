# 📦 Stock Manager Pro

![Python](https://img.shields.io/badge/Python-3.x-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-green)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> A complete Inventory & POS (Point of Sale) system built with Python and Tkinter. Designed for small to medium businesses to manage products, sales, stock, and customers in one place.

---

## ✨ Features

### 🧾 Point of Sale (POS)
- Real-time billing system
- Supports discounts and cash payments
- Automatically records sales and items

### 📦 Inventory Management
- Add / Edit / Delete products
- Supports multiple pricing levels
- Automatic stock deduction

### 📊 Dashboard
- Daily / Monthly sales overview
- Profit tracking
- Top-selling products
- Low stock alerts

### 📥📤 Stock Control
- Stock In (Receive products)
- Stock Out (Dispatch products)
- Full transaction history tracking

### 🏭 Supplier & Purchase Orders
- Manage suppliers
- Create and track purchase orders
- Order status management

### 👥 Customer System
- Store customer data
- Loyalty points system
- Credit balance support

### 🔄 Multi-Branch Support
- Manage multiple branches
- Transfer stock between branches

### 🔐 Authentication System
- Secure login system
- Password hashing (SHA-256)
- Role-based access (Admin / Staff)

### 🧾 Reports & Export
- Export data to CSV
- Export reports to PDF (optional)
- Sales charts (matplotlib)

### 🏷️ Barcode System
- Generate Code128 barcodes
- Export as PNG / PDF

---

## 🖥️ Screenshots

```
/docs/screenshots/dashboard.png
/docs/screenshots/pos.png
/docs/screenshots/products.png
```

---

## 🏗️ Tech Stack

| Layer        | Technology |
|-------------|-----------|
| Language     | Python 3  |
| GUI          | Tkinter   |
| Database     | SQLite3   |
| Charts       | matplotlib|
| PDF Export   | reportlab |
| Image        | Pillow    |

---

## 📁 Project Structure

```
.
├── stock_manager.py   # Main application
├── stock.db           # SQLite database (auto-generated)
└── README.md
```

---

## ⚙️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-username/stock-manager-pro.git
cd stock-manager-pro
```

### 2. Install Dependencies (Optional)
```bash
pip install matplotlib reportlab pillow
```

---

## ▶️ Usage

```bash
python stock_manager.py
```

---

## 🔐 Default Credentials

| Username | Password  |
|----------|----------|
| admin    | admin123 |

> ⚠️ Please change the default password after first login.

---

## 🗄️ Database Schema (Overview)

Main tables:

- users
- products
- categories
- suppliers
- sales
- sale_items
- purchase_orders
- transactions
- customers
- promotions
- refunds
- branches
- stock_transfers
- shifts

---

## 🌐 Internationalization

Supported languages:
- Thai (default)
- English

Example:
```python
T("product_name")
```

---

## 🎨 Theme Support

- Light Mode
- Dark Mode

```python
set_theme("dark")
```

---

## 🔒 Security

- Passwords are hashed using SHA-256
- No plaintext password storage

---

## 🚀 Roadmap

- [ ] MySQL / PostgreSQL support
- [ ] REST API backend
- [ ] Web version (React / Vue)
- [ ] Cloud sync
- [ ] AI-based inventory forecasting

---

## 🤝 Contributing

Pull requests are welcome!  
For major changes, please open an issue first.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Developed by Your Name

---

## ⭐ Support

If you like this project:
- ⭐ Star this repository
- 🍴 Fork and use it
- 🐛 Report bugs or request features
