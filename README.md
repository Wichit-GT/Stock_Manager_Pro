# 🚀 Stock Manager Pro

<p align="center">
  <b>A comprehensive, lightweight inventory and POS management system for modern businesses.</b><br/>
  Streamline your stock tracking, sales, and reporting with a powerful desktop application built for performance and reliability.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" />
  <img src="https://img.shields.io/badge/database-SQLite-lightgrey.svg" />
  <img src="https://img.shields.io/badge/UI-Tkinter-orange.svg" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" />
  <img src="https://img.shields.io/badge/status-active-success.svg" />
</p>

---

## 📖 Overview
**Stock Manager Pro** is an all-in-one desktop solution designed to simplify retail and warehouse operations. From managing multiple branches to tracking real-time stock movements and processing Point of Sale (POS) transactions, this application provides a robust suite of tools for business owners.

It features a beautiful, themeable interface (Light/Dark mode) and supports multi-language operations (English/Thai), making it accessible for diverse teams.

## ✨ Features
- 🛒 **POS System:** Fast checkout process with barcode support, promotions, and customer loyalty points.
- 📦 **Inventory Management:** Track products with low-stock alerts, category organization, and unit conversions.
- 🔄 **Stock Operations:** Manage Stock-In, Stock-Out, and seamless transfers between different branches.
- 🏪 **Multi-Branch Support:** Monitor inventory levels and sales performance across multiple locations.
- 📊 **Analytics & Reporting:** Built-in charts (via Matplotlib) and PDF/CSV export capabilities for deep business insights.
- 🛡️ **Security & Auditing:** Role-based access (Admin/Staff), encrypted passwords, and detailed audit logs of all actions.
- 🔲 **Barcode Utility:** Generate and print custom Code-128B barcodes directly from the app without external hardware.
- 🎨 **Customization:** Toggle between Light and Dark themes and switch languages on the fly.

## 🖼 Preview
*(Optional: Add screenshots here to showcase the Dashboard, POS, and Inventory views)*

## 🛠 Tech Stack
| Category | Technology |
|----------|-----------|
| **Language** | Python 3.x |
| **GUI Framework** | Tkinter |
| **Database** | SQLite3 |
| **Reporting** | ReportLab (PDF), CSV |
| **Visualization** | Matplotlib |
| **Security** | SHA-256 Hashing |

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/stock-manager-pro.git](https://github.com/your-username/stock-manager-pro.git)
   cd stock-manager-pro
Install dependencies:

Bash
pip install matplotlib reportlab pillow
Note: These are optional but highly recommended for charts, PDF exports, and barcode saving.

Initialize the database:
The application will automatically create stock.db on the first run.

▶️ Usage
Run the main application script:

Bash
python stock_manager.py
Default Credentials:

Username: admin

Password: admin123

📁 Project Structure
Bash
/stock-manager-pro
 ├── stock_manager.py     # Main application logic & UI
 ├── stock.db             # SQLite database (auto-generated)
 ├── backups/             # Automatic and manual DB backups
 └── README.md
⚙️ Configuration
The application stores settings directly in the shop_settings table within the SQLite database. You can configure the following through the in-app System Settings menu:

Language: Thai (default) or English

Theme: Light or Dark mode

Shop Info: Name, Address, and Contact details for receipts

Bank Details: For QR payment generation or display

🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create.

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙌 Acknowledgements
Tkinter for the GUI framework.

SQLite for the lightweight, reliable database engine.

Shields.io for the project badges.
