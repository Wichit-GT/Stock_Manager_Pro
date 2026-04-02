# 📦 Stock Manager Pro
 
> A comprehensive, offline-first desktop inventory management and Point-of-Sale (POS) system built with Python and Tkinter — designed for small-to-medium retail businesses and multi-branch operations.
 
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-orange)]()
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen)]()
[![SQLite](https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
 
---
 
## 📖 Description
 
**Stock Manager Pro (SMP)** is a fully self-contained desktop application that combines inventory management, point-of-sale, purchase ordering, customer relationship management, and multi-branch stock control into a single executable Python application.
 
It is built for **retail shop owners, warehouse managers, and small business operators** who need a reliable, offline solution without cloud subscriptions or internet dependency. All data is stored locally in a SQLite database, making it fast, portable, and privacy-preserving.
 
**Problem it solves:** Most affordable POS/inventory tools are either cloud-dependent, require monthly fees, or lack Thai-language support. SMP delivers a full-featured business management suite that works entirely offline, supports bilingual (Thai/English) interfaces, and requires no external server infrastructure.
 
---
 
## ✨ Features
 
- **Role-based Authentication** — Secure login with `admin` and `staff` roles. Passwords are hashed with SHA-256. Session-aware UI adapts to user permissions.
- **Interactive Dashboard** — Real-time KPI cards showing today's sales, monthly revenue, estimated profit, bill count, inventory value, low-stock alerts, and top-5 best-selling products.
- **Full Inventory Management** — Add, edit, delete, and search products with support for multiple price tiers (retail, wholesale, member), dual-unit definitions (e.g., piece vs. box), minimum stock thresholds, and category tagging.
- **Category Management** — Create and manage product categories with cascading updates across linked products.
- **Stock Movements** — Dedicated Stock In and Stock Out flows with transaction logging, user attribution, branch tracking, and historical audit trail.
- **Point-of-Sale (POS)** — A full sales terminal with cart management, promotion/discount code application, multiple payment types (cash, transfer, credit), customer linkage, loyalty points earning, and receipt generation.
- **Sales History & Void/Refund** — Browse past transactions, void sales, and process itemised refunds with refund document tracking.
- **Shift Management** — Open/close cashier shifts with opening/closing cash declaration, shift-level sales summaries, and notes.
- **Customer Management** — Customer profiles with purchase history, loyalty points, credit limit, and outstanding credit/debt tracking.
- **Promotions Engine** — Create percentage or fixed-amount discount codes with usage limits, date ranges, and minimum purchase thresholds.
- **Purchase Orders (PO)** — Draft, approve, and receive supplier purchase orders with per-item quantity tracking and supplier management.
- **Multi-Branch Support** — Manage multiple store branches, maintain per-branch stock levels, and perform inter-branch stock transfers.
- **Barcode Generator** — Render Code-128B barcodes natively in-app (no external library required), save as PNG, and batch-print to PDF via ReportLab.
- **Charts & Analytics** — Matplotlib-powered bar and line charts for sales trends and inventory insights, embedded directly in the application.
- **CSV Import/Export** — Bulk-import products from CSV files and export the full product catalogue to CSV.
- **Stock Count** — Create physical stock count sessions, compare system quantities against counted quantities, and review discrepancies.
- **PDF Reports** — Export stock reports and barcode sheets as formatted A4 PDF documents using ReportLab.
- **Light & Dark Themes** — Toggle between light and dark UI themes; preference persisted across sessions.
- **Bilingual UI** — Full Thai and English interface switching, persisted in application settings.
- **Audit Log** — All significant system actions are recorded to an audit log table for accountability.
- **Shop Settings** — Configure shop name, address, tax ID, and bank/payment details used on receipts.
 
---
 
## 🖥️ Demo / Preview
 
**Login Screen**
```
┌─────────────────────────────┐
│  📦  Stock Manager Pro      │
│  กรุณาเข้าสู่ระบบ          │
│                             │
│  👤 Username: [admin      ] │
│  🔒 Password: [••••••••• ] │
│                             │
│  [   เข้าสู่ระบบ →        ] │
│  Default: admin / admin123  │
└─────────────────────────────┘
```
 
**Dashboard KPI Cards (runtime)**
```
📊 ยอดขาย
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
│ 🛒 วันนี้   │ │ 📅 เดือนนี้ │ │ 💹 กำไร     │ │🧾 บิล   │ │👥 ลูกค้า│
│  ฿12,450    │ │  ฿184,200   │ │  ฿52,310    │ │   38 ใบ │ │  210 คน │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────┘ └──────────┘
 
📦 คลังสินค้า
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ สินค้าทั้งหมด│ │ มูลค่าคลัง  │ │ ⚠️ ใกล้หมด  │ │ 🚫 หมดสต็อก │
│   320 รายการ │ │ ฿2,140,000  │ │   12 รายการ │ │   3 รายการ  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```
 
---
 
## 🛠️ Tech Stack
 
| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| GUI Framework | Tkinter + ttk (stdlib) |
| Database | SQLite 3 (stdlib, via `sqlite3`) |
| Charts | Matplotlib 3.x (TkAgg backend) |
| PDF Generation | ReportLab 4.x |
| Barcode Export | Pillow 12.x (PNG save) |
| QR Code | qrcode 8.x |
| Numeric | NumPy 2.x |
| Packaging | pip / venv |
 
---
 
## 📁 Project Structure
 
```
stock-manager-pro/
│
├── stock_manager.py       # Single-file application entry point (~5,800 lines)
├── requirements.txt       # Python package dependencies
├── stock.db               # SQLite database (auto-created on first run)
├── README.md
│
└── (optional exports)
    ├── products_YYYYMMDD.csv
    ├── barcodes_YYYYMMDD.pdf
    └── stock_report.pdf
```
 
> **Note:** The application is intentionally structured as a single-file desktop script for maximum portability. The SQLite database (`stock.db`) is created automatically in the same directory as `stock_manager.py` on first launch.
 
---
 
## ⚙️ Installation
 
### Requirements
 
- Python **3.9** or higher
- `pip` package manager
- A display environment (not headless) — required by Tkinter
 
### Steps
 
```bash
# 1. Clone the repository
git clone https://github.com/your-username/stock-manager-pro.git
cd stock-manager-pro
 
# 2. (Recommended) Create and activate a virtual environment
python -m venv venv
 
# Windows
venv\Scripts\activate
 
# macOS / Linux
source venv/bin/activate
 
# 3. Install dependencies
pip install -r requirements.txt
```
 
### Linux — Tkinter note
 
On Debian/Ubuntu-based systems, Tkinter may not be bundled with Python:
 
```bash
sudo apt-get install python3-tk
```
 
---
 
## 🚀 Usage
 
```bash
python stock_manager.py
```
 
The application will:
1. Auto-create `stock.db` in the same directory (if it does not exist)
2. Seed the default `admin` account and the headquarters branch
3. Display a low-stock startup alert if any products are below their minimum threshold
4. Open the login window
 
### Default Credentials
 
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator |
 
> **Security:** Change the default admin password immediately after first login via the System Settings page.
 
### Navigation
 
After login, the main window (1440×880) is divided into:
 
| Sidebar Section | Sub-tabs |
|---|---|
| 📦 คลังสินค้า (Inventory) | Dashboard, Products, Categories, Barcode, Charts, CSV Import, Stock Count |
| 🔄 เคลื่อนไหวสต็อก (Stock Movements) | Stock In, Stock Out, Transaction History |
| 🛒 การขาย (Sales) | POS Terminal, Sales History, Shift, Customers, Credit/Debt, Promotions |
| 📋 จัดซื้อ (Purchase) | Purchase Orders, Suppliers |
| 🏪 สาขา (Branch) | Branch Management, Stock Transfer |
| ⚙️ ระบบ (System) | Shop Settings |
 
---
 
## 🔧 Configuration
 
All configuration is stored in the `shop_settings` table within `stock.db` and can be managed from the **System Settings** screen inside the application. No external `.env` file is required.
 
Key configurable settings:
 
| Setting Key | Description |
|---|---|
| `app_lang` | Interface language (`th` or `en`) |
| `app_theme` | UI theme (`light` or `dark`) |
| `shop_name` | Store name printed on receipts |
| `shop_address` | Store address |
| `shop_tax_id` | Tax identification number |
| `bank_name` | Bank name for transfer payment info |
| `bank_account` | Bank account number |
 
---
 
## 🗄️ Database Schema
 
The application uses a single SQLite file (`stock.db`) with the following core tables:
 
| Table | Purpose |
|---|---|
| `users` | User accounts, roles, branch assignments |
| `branches` | Store/branch definitions |
| `products` | Product catalogue with multi-tier pricing |
| `categories` | Product categories |
| `transactions` | All stock movement records |
| `sales` | Sales headers (receipts) |
| `sale_items` | Line items per sale |
| `purchase_orders` | Supplier PO headers |
| `po_items` | PO line items |
| `suppliers` | Supplier directory |
| `customers` | Customer profiles with loyalty points |
| `promotions` | Discount/promotion code definitions |
| `shifts` | Cashier shift records |
| `stock_transfers` | Inter-branch stock transfer records |
| `branch_stock` | Per-branch stock levels |
| `stock_counts` | Physical stock count sessions |
| `stock_count_items` | Count session line items with discrepancies |
| `refunds` | Refund/return headers |
| `refund_items` | Refund line items |
| `customer_credit` | Customer credit/debt ledger |
| `audit_log` | System action audit trail |
| `shop_settings` | Key-value application settings |
 
---
 
## 📤 Exports
 
The application supports the following export formats:
 
| Export | Format | Location |
|---|---|---|
| Product catalogue | `.csv` | User-selected path |
| Barcode sheet (batch) | `.pdf` (A4, 2-column) | User-selected path |
| Stock report | `.pdf` (A4) | User-selected path |
| Single barcode | `.png` | User-selected path |
 
---
 
## 🧪 Testing
 
This project currently ships without an automated test suite. To validate core functionality manually:
 
```bash
# Run the application and verify:
# 1. Login with admin / admin123
# 2. Add a product via Inventory > Products
# 3. Perform a stock-in movement
# 4. Complete a POS sale
# 5. Check the Dashboard KPIs update
 
# (Optional) Inspect the SQLite database directly
sqlite3 stock.db ".tables"
sqlite3 stock.db "SELECT * FROM users;"
```
 
To add automated tests in the future, the recommended approach is:
 
```bash
pip install pytest
pytest tests/
```
 
---
 
## 🚢 Deployment
 
### Standalone Executable (Windows)
 
Package the application as a single `.exe` using PyInstaller:
 
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "StockManagerPro" stock_manager.py
```
 
The compiled executable will be in the `dist/` folder. The `stock.db` database will be created alongside the executable on first run.
 
### Portable Distribution
 
For a portable setup (e.g., USB drive deployment):
 
```
StockManagerPro/
├── StockManagerPro.exe   # (or stock_manager.py for script mode)
├── stock.db              # Carries over between machines
└── README.md
```
 
### Production Notes
 
- Back up `stock.db` regularly — all business data resides in this single file.
- For multi-user environments on the same machine, use the built-in user roles (`admin` / `staff`) rather than running multiple instances.
- True concurrent multi-user access is not supported (SQLite limitation); for multi-terminal POS setups, consider migrating to a PostgreSQL backend.
 
---
 
## 🔒 Security Notes
 
- **Password hashing:** All passwords are stored as SHA-256 hashes. Plain-text passwords are never persisted to disk.
- **Default credentials:** The default `admin / admin123` account is seeded on first run. **Change this password immediately in production.**
- **Local database:** `stock.db` contains all business data, including customer records and financial transactions. Restrict file-system access to authorised users only.
- **No network exposure:** The application is fully offline. There are no open ports, no API endpoints, and no outbound network calls.
- **Audit log:** All sensitive operations (stock adjustments, sales voids, user actions) are recorded in the `audit_log` table with timestamp and user attribution.
 
---
 
## 🤝 Contributing
 
Contributions are welcome. Please follow the workflow below:
 
```bash
# 1. Fork the repository on GitHub
 
# 2. Create a feature branch
git checkout -b feature/your-feature-name
 
# 3. Make your changes and commit
git add .
git commit -m "feat: describe your change clearly"
 
# 4. Push to your fork
git push origin feature/your-feature-name
 
# 5. Open a Pull Request against the main branch
```
 
### Guidelines
 
- Keep the application single-file if adding UI frames; extract utility modules only when necessary.
- Thai-language string literals in the UI are intentional — maintain bilingual support for all new user-facing text by updating the `_STRINGS` dictionary.
- Do not introduce dependencies that require a C compiler or non-standard system libraries without strong justification.
- Match the existing code style (PEP 8, 4-space indent, descriptive Thai/English comments).
 
---
 
## 📄 License
 
This project is licensed under the **MIT License**.
 
```
MIT License
 
Copyright (c) 2025 Stock Manager Pro Contributors
 
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```
 
---
 
*Built with ❤️ for Thai retail businesses. Contributions, bug reports, and feature requests are welcome via GitHub Issues.*
