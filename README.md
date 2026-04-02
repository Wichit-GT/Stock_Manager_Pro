# 📦 Stock Manager Pro
 
> A fully offline, production-ready desktop inventory management and Point-of-Sale (POS) system for small-to-medium retail businesses — built with Python and Tkinter, with zero cloud dependency.
 
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?logo=githubactions&logoColor=white)]()
[![Production](https://img.shields.io/badge/Production-v1.0.0-blue)]()
[![Development](https://img.shields.io/badge/Development-v1.1.0--beta-orange)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![SQLite](https://img.shields.io/badge/Database-SQLite3-blue?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
 
---
 
## 🚀 Production Deployment
 
### Status: **Stable — Production Ready**
### Version: `v1.0.0` — Branch: `main`
 
The `v1.0.0` release is a fully self-contained, standalone desktop application. It ships as a single Python script (`stock_manager.py`) with an auto-initialising SQLite database. No server, no internet connection, and no external configuration is required beyond installing Python dependencies.
 
### Production Features Available in `v1.0.0`
 
| Module | Features |
|---|---|
| **Authentication** | Role-based login (`admin` / `staff`), SHA-256 password hashing, session-aware UI |
| **Dashboard** | Real-time KPI cards: daily/monthly sales, profit, invoice count, inventory value, top-5 sellers, low-stock alerts |
| **Inventory** | Full product CRUD with multi-tier pricing (retail, wholesale, member), dual-unit support, category management |
| **Stock Movements** | Stock In / Stock Out with full transaction history, user attribution, branch tracking |
| **POS Terminal** | Cart-based sales with keyboard shortcuts (F12, F5, F2, Del), cash/transfer/card payments, change calculation, PromptPay QR code generation |
| **Sales History** | Date-range filter, sale void, itemised refunds, CSV and PDF export |
| **Shift Management** | Open/close cashier shifts with opening cash declaration, shift-level sales summary |
| **Customers** | Customer profiles, loyalty points (1pt/฿10), total spend tracking, credit/debt ledger |
| **Promotions** | Discount codes (percentage or fixed), usage limits, date range, minimum purchase enforcement |
| **Purchase Orders** | Draft → Approve → Receive workflow with automatic stock update on receipt |
| **Suppliers** | Supplier directory linked to purchase orders |
| **Multi-Branch** | Branch management, per-branch stock levels, inter-branch stock transfers |
| **Barcode** | Code-128B barcode generation (no external library required), PNG export, batch PDF printing |
| **Charts** | Matplotlib-powered sales trend and inventory analytics embedded in-app |
| **CSV Import/Export** | Bulk product import from CSV, full catalogue export |
| **Stock Count** | Physical stock count sessions with system-vs-counted discrepancy tracking |
| **Reports** | A4 PDF stock reports and receipt PDFs via ReportLab |
| **Themes** | Light and dark UI themes, persisted across sessions |
| **Bilingual UI** | Thai / English interface toggle, persisted in app settings |
| **Audit Log** | All significant user actions recorded with timestamp and user attribution |
| **Shop Settings** | Store name, address, tax ID, bank/PromptPay account configuration |
 
### Production Packaging (Standalone Executable)
 
```bash
# Install PyInstaller
pip install pyinstaller
 
# Build a single-file Windows executable
pyinstaller --onefile --windowed --name "StockManagerPro" stock_manager.py
 
# macOS / Linux
pyinstaller --onefile --name "StockManagerPro" stock_manager.py
 
# The distributable binary is produced at:
# dist/StockManagerPro.exe  (Windows)
# dist/StockManagerPro      (macOS / Linux)
```
 
### Production Deployment Package
 
After build, the distributable structure is:
 
```
dist/
│── StockManagerPro.exe     # Self-contained executable (~20–30 MB)
                            # stock.db is auto-created beside the .exe on first run
```
 
**What is shipped:**
- The compiled executable with all Python dependencies bundled
- No Python interpreter required on the target machine
 
**What is excluded from the distribution package:**
- Source code (`stock_manager.py`)
- `requirements.txt`
- Tests and development tooling (`pylint`, `black`, etc.)
- Raw `stock.db` — a fresh database is created on first launch at the executable's location
 
### Portable USB Deployment
 
For environments where installation is not possible:
 
```
StockManagerPro_Portable/
│── StockManagerPro.exe     # Executable
│── stock.db                # Copy from existing deployment to migrate all data
│── README.md
```
 
> **Data migration:** Copy `stock.db` from the old machine to carry over all products, sales history, and customer data instantly.
 
---
 
## 🚧 Development Version
 
### Status: **In Progress**
### Version: `v1.1.0-beta` — Branch: `develop`
 
The `develop` branch targets `v1.1.0-beta` and focuses on extended reporting, UX improvements, hardware integrations, and infrastructure hardening based on feedback from `v1.0.0` deployments.
 
### Features In Progress (`v1.1.0-beta`)
 
- **Automated test suite** — Unit and integration tests using `pytest` for database logic, transaction flows, and POS checkout
- **Receipt printer support** — ESC/POS thermal printer integration for direct hardware receipt printing
- **Advanced sales analytics** — Profit margin breakdowns per category, hourly sales heatmaps
- **Customer loyalty tiers** — Bronze / Silver / Gold tiers with automatic upgrade based on spend
- **Barcode scanner input** — USB/serial barcode scanner support for POS product lookup and stock-in flows
- **User management UI** — In-app admin panel to create, edit, and deactivate user accounts without direct database access
- **Scheduled low-stock notifications** — Configurable background polling with system tray alerts
- **Multi-language expansion** — Additional locale support beyond Thai/English
- **Database backup utility** — One-click `stock.db` backup with timestamped archive
 
### Known Issues / TODO in `develop`
 
| Issue | Severity | Status |
|---|---|---|
| SQLite does not support concurrent multi-user writes | Medium | Architectural — documented limitation; PostgreSQL migration planned for v2.0 |
| `postscript → PNG` barcode export may fail on some Linux configurations | Low | Fallback message displayed; Pillow rasterisation path under investigation |
| Dark mode entry widget backgrounds inconsistent on macOS | Low | Under investigation |
| No automated test coverage for POS checkout flow | High | Blocked by test suite milestone |
| `price_wholesale` / `price_member` added via `ALTER TABLE` — absent in fresh schema DDL | Medium | Schema migration cleanup in progress |
 
---
 
## 📖 Description
 
**Stock Manager Pro (SMP)** is a fully offline desktop application that combines inventory management, point-of-sale, purchase ordering, customer relationship management, and multi-branch stock control into a single portable Python program.
 
It targets **Thai retail shop owners, warehouse managers, and small business operators** who need a reliable, private, offline business management tool without recurring cloud subscription costs. All data lives in a local SQLite file — no network, no server, no ongoing fees.
 
**Problem it solves:** Most accessible POS and inventory tools are either cloud-dependent, require monthly licensing, or lack first-class Thai-language support. SMP delivers a production-grade business management suite that works fully offline, natively supports both Thai and English interfaces, and can be packaged into a single executable for zero-friction deployment on any Windows, macOS, or Linux machine.
 
---
 
## ✨ Features
 
### ✅ Production Features (`v1.0.0` — `main`)
 
- **Secure Role-Based Authentication** — Admin and staff roles with SHA-256 hashed passwords and session-aware navigation
- **Live Dashboard KPIs** — Today's sales, monthly revenue, estimated profit, bill count, top-5 best-sellers, low-stock and out-of-stock alerts — all refreshed on navigation
- **Multi-Tier Product Pricing** — Retail, wholesale, and member prices per product; dual-unit definitions (e.g., piece and box)
- **POS Cart Terminal** — Keyboard-driven sales flow, real-time change calculation, quick-fill cash buttons (฿20 / ฿50 / ฿100 / ฿500 / ฿1,000)
- **PromptPay QR Code Generation** — Auto-generates Thai PromptPay-compatible QR codes for bank transfer payments at checkout, including account and amount pre-fill
- **Promotion Engine** — Percentage and fixed-amount discount codes with usage limits, validity dates, and minimum purchase requirements
- **Purchase Order Workflow** — Draft → Approve → Receive with automatic stock increment and transaction logging on receipt
- **Inter-Branch Stock Transfers** — Move inventory between branches with a full transfer history log
- **Physical Stock Count** — Create count sessions, record actual quantities, and surface discrepancies against system records
- **Code-128B Barcode Generator** — Pure-Tkinter rendering with no external barcode library; individual PNG export and batch A4 PDF printing
- **Audit Trail** — Every stock movement, sale, void, and PO action is recorded with user and timestamp
- **Light / Dark Theme** — Full UI theming switchable from System Settings, persisted to database
- **Bilingual Interface** — Thai and English UI modes, switchable at runtime and persisted across sessions
 
### 🚧 Upcoming Features (`v1.1.0-beta` — `develop`)
 
- Automated `pytest` test suite for all core business logic
- ESC/POS thermal receipt printer support
- USB barcode scanner integration for POS and stock-in workflows
- In-app user account management panel (admin only)
- Customer loyalty tier system (Bronze / Silver / Gold) with automatic promotion
- Scheduled low-stock background alerts with system tray notifications
- One-click database backup utility with timestamped archives
 
---
 
## 🛠️ Tech Stack
 
| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.9+ |
| GUI Framework | Tkinter + ttk | stdlib |
| Database | SQLite 3 | stdlib |
| Charts | Matplotlib (TkAgg backend) | 3.10.x |
| PDF Export | ReportLab | 4.4.x |
| Image / Barcode PNG | Pillow | 12.1.x |
| QR Code | qrcode | 8.2 |
| Numeric | NumPy | 2.4.x |
| Packaging *(dev/optional)* | PyInstaller | latest |
| Linting *(dev/optional)* | pylint, black | optional |
 
> **Graceful degradation:** Matplotlib and ReportLab are optional at runtime. The application starts and functions fully without them; chart views and PDF export features display an error prompt until the libraries are installed.
 
---
 
## 📁 Project Structure
 
### Full Project (Development)
 
```
stock-manager-pro/
│
├── stock_manager.py          # Single-file application (~5,800 lines)
├── requirements.txt          # Pinned production dependencies
├── README.md
│
├── tests/                    # [v1.1.0-beta] Automated test suite (planned)
│   ├── test_db.py
│   ├── test_pos.py
│   └── test_reports.py
│
├── docs/                     # Additional documentation
│   └── schema.md             # Full database schema reference
│
└── dist/                     # PyInstaller output (git-ignored)
    └── StockManagerPro.exe
```
 
### Deployment Package (Production)
 
```
StockManagerPro_v1.0.0/
│
├── StockManagerPro.exe       # Compiled standalone executable
│                             # (Windows — produced by PyInstaller --onefile)
│
└── stock.db                  # Auto-created on first launch
                              # Copy to migrate existing data between machines
```
 
**Included in deployment:**
- Single compiled binary with all dependencies bundled internally
- `stock.db` generated automatically beside the executable on first run
 
**Excluded from deployment:**
- `stock_manager.py` source code
- `requirements.txt`
- `tests/`, `docs/`
- PyInstaller build artefacts (`build/`, `.spec` file)
 
---
 
## ⚙️ Installation (Development)
 
### Requirements
 
- Python **3.9** or higher
- `pip` package manager
- Display environment (Tkinter requires a GUI — not compatible with headless servers)
 
### Linux — Tkinter Dependency
 
On Debian/Ubuntu-based systems, Tkinter is not bundled with Python by default:
 
```bash
sudo apt-get install python3-tk
```
 
### Setup
 
```bash
# 1. Clone the repository
git clone https://github.com/your-username/stock-manager-pro.git
cd stock-manager-pro
 
# 2. Checkout the appropriate branch
git checkout main        # Production stable (v1.0.0)
# or
git checkout develop     # Development (v1.1.0-beta)
 
# 3. Create and activate a virtual environment (recommended)
python -m venv venv
 
# Windows
venv\Scripts\activate
 
# macOS / Linux
source venv/bin/activate
 
# 4. Install dependencies
pip install -r requirements.txt
```
 
---
 
## 🔧 Configuration
 
All runtime configuration is stored in the `shop_settings` table within `stock.db` and managed through the in-app **System Settings** screen. No `.env` file or external config file is required.
 
**Settings managed in-app:**
 
```
app_lang          → Interface language: "th" (Thai) or "en" (English)
app_theme         → UI theme: "light" or "dark"
shop_name         → Store name printed on receipts
shop_address      → Store address for receipts and documents
shop_tax_id       → Tax identification number
bank_name         → Bank name for PromptPay display at checkout
bank_account      → PromptPay account number (phone number or national ID)
bank_type         → Account type label
bank_holder       → Account holder name
```
 
**Database path:**
 
```
Script mode:     ./stock.db   (same directory as stock_manager.py)
Compiled mode:   ./stock.db   (same directory as the .exe)
```
 
---
 
## ▶️ Usage
 
### Development
 
```bash
python stock_manager.py
```
 
On launch the application will:
1. Auto-create `stock.db` if it does not exist and seed the default admin account
2. Seed the HQ branch entry
3. Fire a startup low-stock alert if any products are below their minimum threshold (after 800 ms)
4. Display the login window
 
### Production (Compiled Executable)
 
```bash
# Windows — double-click or run from terminal
StockManagerPro.exe
 
# macOS / Linux
./StockManagerPro
```
 
### Default Login Credentials
 
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator |
 
> ⚠️ **Change the default password immediately after first launch in any production environment.**
 
### Application Navigation
 
| Sidebar Section | Sub-tabs |
|---|---|
| 📦 คลังสินค้า (Inventory) | Dashboard · Products · Categories · Barcode · Charts · CSV Import · Stock Count |
| 🔄 เคลื่อนไหวสต็อก (Stock) | Stock In · Stock Out · Transaction History |
| 🛒 การขาย (Sales) | POS Terminal · Sales History · Shift · Customers · Credit/Debt · Promotions |
| 📋 จัดซื้อ (Purchase) | Purchase Orders · Suppliers |
| 🏪 สาขา (Branch) | Branch Management · Stock Transfer |
| ⚙️ ระบบ (System) | Shop Settings |
 
### POS Keyboard Shortcuts
 
| Key | Action |
|---|---|
| `F12` | Confirm payment / Checkout |
| `F5` | Clear all items from cart |
| `F2` | Focus product search input |
| `Del` | Remove selected cart item |
 
---
 
## 🧪 Testing
 
### Manual Smoke Test (`v1.0.0`)
 
```bash
python stock_manager.py
 
# Verify the following flows:
# 1. Login with admin / admin123
# 2. Add a product:       Inventory > Products > ➕ เพิ่ม
# 3. Record stock-in:     Stock > Stock In
# 4. Complete a POS sale: Sales > POS → add items → F12
# 5. Dashboard KPIs reflect the completed sale
# 6. Export barcode PDF:  Inventory > Barcode > batch select > 🖨️ พิมพ์ (PDF)
```
 
### Direct Database Inspection
 
```bash
sqlite3 stock.db ".tables"
sqlite3 stock.db "SELECT username, role FROM users;"
sqlite3 stock.db "SELECT receipt_no, total, date FROM sales ORDER BY date DESC LIMIT 5;"
sqlite3 stock.db "SELECT * FROM audit_log ORDER BY date DESC LIMIT 10;"
```
 
### Automated Tests (`v1.1.0-beta` — `develop`)
 
```bash
# Install dev dependencies
pip install pytest pytest-cov
 
# Run full test suite
pytest tests/ -v
 
# Run with coverage report
pytest tests/ --cov=stock_manager --cov-report=term-missing
```
 
> The `tests/` directory is planned for `v1.1.0-beta`. It does not exist in the current `main` branch.
 
---
 
## 🚢 Deployment
 
### Option 1 — Script Mode (Development / Internal)
 
```bash
python stock_manager.py
```
 
Requires Python 3.9+ and installed dependencies on every machine.
 
### Option 2 — Standalone Executable via PyInstaller *(Recommended for Production)*
 
```bash
pip install pyinstaller
 
# Windows — no console window
pyinstaller --onefile --windowed --name "StockManagerPro" stock_manager.py
 
# macOS
pyinstaller --onefile --windowed --name "StockManagerPro" stock_manager.py
 
# Linux
pyinstaller --onefile --name "StockManagerPro" stock_manager.py
```
 
Output: `dist/StockManagerPro[.exe]` — distribute this single file.
 
### Option 3 — Portable ZIP Package
 
```bash
mkdir StockManagerPro_v1.0.0
cp dist/StockManagerPro.exe StockManagerPro_v1.0.0/
cp README.md StockManagerPro_v1.0.0/
zip -r StockManagerPro_v1.0.0.zip StockManagerPro_v1.0.0/
```
 
### Production Notes
 
- **Back up `stock.db` regularly** — it is the sole data store for all business records.
- Use OS-level scheduled tasks (Windows Task Scheduler / cron) to copy `stock.db` to a network drive or cloud-synced folder on a daily schedule.
- SQLite supports **single-writer access only**. For single-machine multi-user deployments, use the built-in role system. True multi-terminal concurrent access requires a PostgreSQL backend (planned for `v2.0`).
- Minimum recommended display resolution: **1280×768** (default window opens at 1440×880).
 
---
 
## 🔢 Versioning Strategy
 
This project follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`
 
| Stream | Version | Branch | Status |
|---|---|---|---|
| **Production** | `v1.0.0` | `main` | ✅ Stable — active production deployments |
| **Development** | `v1.1.0-beta` | `develop` | 🚧 Feature development and testing in progress |
| **Future** | `v2.0.0` | `develop` (planned) | 🗓️ PostgreSQL backend, multi-terminal POS support |
 
### Branch Strategy
 
```
main
 └── Stable, production-only commits
     Tagged: vX.Y.Z  (e.g., v1.0.0)
 
develop
 └── Active development for next release
     Tagged: vX.Y.Z-beta / vX.Y.Z-alpha  (e.g., v1.1.0-beta)
 
feature/xxx
 └── Short-lived branches merged into develop via Pull Request
```
 
**Suffix conventions:**
 
| Suffix | Meaning |
|---|---|
| *(none)* | Stable production release |
| `-beta` | Feature-complete, under testing |
| `-alpha` | Early development, potentially unstable |
| `-dev` | Major architectural revision in progress |
 
---
 
## 🔒 Security Notes
 
- **Password storage:** All passwords are stored as SHA-256 hashes. Plain-text passwords are never written to disk or recorded in any log.
- **Default credentials:** The `admin / admin123` account is seeded automatically on first run. **This password must be changed before any production deployment** via System Settings or direct database update.
- **Database file access:** `stock.db` contains all business data including customer records, financial transactions, and hashed user credentials. Restrict OS-level file access to authorised users and service accounts only.
- **No network exposure:** The application is entirely offline. There are no open ports, no REST endpoints, and no outbound network calls. PromptPay QR generation operates purely locally using the `qrcode` library.
- **Audit trail:** Stock adjustments, sales voids, PO approvals, and sensitive user actions are all logged to the `audit_log` table with user attribution and timestamp.
- **Single-machine trust model:** Any OS user with read access to the directory containing `stock.db` can open it directly with SQLite tooling. In shared environments, use OS-level user accounts and directory permissions to enforce access control.
 
---
 
## 🤝 Contributing
 
Contributions are welcome against the `develop` branch only. The `main` branch accepts only release merges from `develop`.
 
```bash
# 1. Fork the repository on GitHub
 
# 2. Clone your fork
git clone https://github.com/your-username/stock-manager-pro.git
cd stock-manager-pro
 
# 3. Create a feature branch from develop
git checkout develop
git checkout -b feature/your-feature-name
 
# 4. Make your changes, then commit
git add .
git commit -m "feat: describe the change clearly"
 
# 5. Push and open a Pull Request → develop
git push origin feature/your-feature-name
```
 
### Guidelines
 
- All PRs must target `develop`, never `main`
- New UI pages must follow the existing `Frame` class pattern: define `NAME`, `refresh()`, and `_build()`
- Bilingual support is mandatory: add new UI strings to both `_STRINGS["th"]` and `_STRINGS["en"]`
- Do not introduce C-extension or system-library dependencies without justification
- Write `pytest` tests in `tests/` for any new database or business logic
- Do not commit `stock.db` or any `dist/` build artefacts
 
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
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
 
---
 
*Built with ❤️ for Thai retail businesses. Bug reports and feature requests are welcome via GitHub Issues on the `develop` branch.*
 






