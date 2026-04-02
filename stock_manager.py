import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import csv
import hashlib
import math
import io

# ── optional matplotlib ────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── optional reportlab (PDF) ───────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_RL = True
except ImportError:
    HAS_RL = False

# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT UNIQUE NOT NULL,
                password  TEXT NOT NULL,
                role      TEXT DEFAULT 'staff',
                fullname  TEXT,
                branch_id INTEGER DEFAULT 1,
                created   TEXT
            )
        """)
        c.execute("""INSERT OR IGNORE INTO users(username,password,role,fullname,created)
                     VALUES(?,?,?,?,?)""",
                  ("admin", hash_pw("admin123"), "admin", "Administrator",
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        c.execute("""
            CREATE TABLE IF NOT EXISTS branches (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                code    TEXT UNIQUE NOT NULL,
                name    TEXT NOT NULL,
                address TEXT,
                phone   TEXT,
                active  INTEGER DEFAULT 1
            )
        """)
        c.execute("INSERT OR IGNORE INTO branches(code,name,address) VALUES(?,?,?)",
                  ("HQ","สำนักงานใหญ่","กรุงเทพฯ"))
        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                code    TEXT UNIQUE NOT NULL,
                name    TEXT NOT NULL,
                contact TEXT,
                phone   TEXT,
                address TEXT,
                active  INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#3B82F6'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                category    TEXT,
                unit        TEXT,
                quantity    REAL DEFAULT 0,
                min_qty     REAL DEFAULT 0,
                price       REAL DEFAULT 0,
                sell_price  REAL DEFAULT 0,
                updated     TEXT
            )
        """)
        try:
            c.execute("ALTER TABLE products ADD COLUMN sell_price REAL DEFAULT 0")
        except: pass
        try: c.execute("ALTER TABLE products ADD COLUMN unit2 TEXT")
        except: pass
        try: c.execute("ALTER TABLE products ADD COLUMN unit2_qty REAL DEFAULT 1")
        except: pass
        try: c.execute("ALTER TABLE products ADD COLUMN price_wholesale REAL DEFAULT 0")
        except: pass
        try: c.execute("ALTER TABLE products ADD COLUMN price_member REAL DEFAULT 0")
        except: pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS stock_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_no TEXT UNIQUE NOT NULL,
                counted_by TEXT, branch_id INTEGER DEFAULT 1,
                status TEXT DEFAULT 'draft', note TEXT, created TEXT, completed TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS stock_count_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_id INTEGER, product_id INTEGER,
                system_qty REAL DEFAULT 0, counted_qty REAL DEFAULT 0, diff REAL DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_credit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER, sale_id INTEGER DEFAULT NULL,
                type TEXT, amount REAL DEFAULT 0, balance REAL DEFAULT 0,
                note TEXT, date TEXT, created_by TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                refund_no TEXT UNIQUE NOT NULL,
                sale_id INTEGER, receipt_no TEXT, cashier TEXT,
                reason TEXT, total REAL DEFAULT 0, date TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS refund_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                refund_id INTEGER, product_id INTEGER,
                quantity REAL, unit_price REAL
            )
        """)
        try:
            c.execute("ALTER TABLE sales ADD COLUMN voided INTEGER DEFAULT 0")
        except: pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT, action TEXT, detail TEXT, date TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cashier TEXT NOT NULL, branch_id INTEGER DEFAULT 1,
                open_time TEXT, close_time TEXT,
                open_cash REAL DEFAULT 0, close_cash REAL DEFAULT 0,
                sales_total REAL DEFAULT 0, sales_count INTEGER DEFAULT 0,
                note TEXT, status TEXT DEFAULT 'open'
            )
        """)
        try: c.execute("ALTER TABLE customers ADD COLUMN credit_limit REAL DEFAULT 0")
        except: pass
        try: c.execute("ALTER TABLE customers ADD COLUMN credit_balance REAL DEFAULT 0")
        except: pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS branch_stock (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_id   INTEGER,
                product_id  INTEGER,
                quantity    REAL DEFAULT 0,
                UNIQUE(branch_id, product_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER,
                type        TEXT,
                quantity    REAL,
                note        TEXT,
                date        TEXT,
                user        TEXT,
                branch_id   INTEGER DEFAULT 1,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        try:
            c.execute("ALTER TABLE transactions ADD COLUMN user TEXT")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE transactions ADD COLUMN branch_id INTEGER DEFAULT 1")
        except Exception:
            pass
        # Purchase Orders
        c.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number   TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                branch_id   INTEGER DEFAULT 1,
                status      TEXT DEFAULT 'pending',
                total       REAL DEFAULT 0,
                note        TEXT,
                created_by  TEXT,
                created     TEXT,
                approved_by TEXT,
                approved    TEXT,
                received    TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS po_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id       INTEGER,
                product_id  INTEGER,
                quantity    REAL,
                unit_price  REAL,
                received_qty REAL DEFAULT 0,
                FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        # Sales
        c.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no  TEXT UNIQUE NOT NULL,
                branch_id   INTEGER DEFAULT 1,
                cashier     TEXT,
                payment     TEXT DEFAULT 'cash',
                subtotal    REAL DEFAULT 0,
                discount    REAL DEFAULT 0,
                total       REAL DEFAULT 0,
                note        TEXT,
                date        TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id     INTEGER,
                product_id  INTEGER,
                quantity    REAL,
                unit_price  REAL,
                subtotal    REAL,
                FOREIGN KEY(sale_id) REFERENCES sales(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        # Stock transfer between branches
        c.execute("""
            CREATE TABLE IF NOT EXISTS stock_transfers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                from_branch  INTEGER,
                to_branch    INTEGER,
                product_id   INTEGER,
                quantity     REAL,
                note         TEXT,
                status       TEXT DEFAULT 'done',
                created_by   TEXT,
                date         TEXT
            )
        """)
        # Customers
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                phone       TEXT,
                email       TEXT,
                address     TEXT,
                points      REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                note        TEXT,
                created     TEXT
            )
        """)
        # Promotions
        c.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                type        TEXT DEFAULT 'percent',
                value       REAL DEFAULT 0,
                min_amount  REAL DEFAULT 0,
                max_uses    INTEGER DEFAULT 0,
                used_count  INTEGER DEFAULT 0,
                active      INTEGER DEFAULT 1,
                start_date  TEXT,
                end_date    TEXT
            )
        """)
        # Add customer_id to sales
        try:
            c.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER DEFAULT NULL")
        except: pass
        try:
            c.execute("ALTER TABLE sales ADD COLUMN promo_code TEXT DEFAULT NULL")
        except: pass
        try:
            c.execute("ALTER TABLE sales ADD COLUMN points_earned REAL DEFAULT 0")
        except: pass
        # Shifts / กะ
        c.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                cashier      TEXT NOT NULL,
                branch_id    INTEGER DEFAULT 1,
                open_time    TEXT,
                close_time   TEXT,
                open_cash    REAL DEFAULT 0,
                close_cash   REAL DEFAULT 0,
                sales_total  REAL DEFAULT 0,
                sales_count  INTEGER DEFAULT 0,
                note         TEXT,
                status       TEXT DEFAULT 'open'
            )
        """)
        # Shop/bank settings
        c.execute("""
            CREATE TABLE IF NOT EXISTS shop_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


def _load_app_settings():
    """Called after init_db to restore persisted settings."""
    global _LANG, _current_theme
    lang = get_setting("app_lang", "th")
    if lang in ("th","en"):
        _LANG = lang
    theme = get_setting("app_theme","light")
    if theme in THEMES:
        set_theme(theme)

def get_setting(key, default=""):
    with get_conn() as conn:
        r = conn.execute("SELECT value FROM shop_settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(key, value):
    with get_conn() as conn:
        conn.execute("INSERT INTO shop_settings(key,value) VALUES(?,?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                     (key, value))
        conn.commit()


# ─────────────────────────────────────────────
#  Colours & Fonts  (Dark Mode support)
# ─────────────────────────────────────────────
THEMES = {
    "light": {
        "bg":        "#F0F4F8",
        "sidebar":   "#1E293B",
        "sidebar_h": "#334155",
        "accent":    "#3B82F6",
        "accent_dk": "#2563EB",
        "success":   "#10B981",
        "danger":    "#EF4444",
        "warning":   "#F59E0B",
        "white":     "#FFFFFF",
        "text":      "#1E293B",
        "text_lt":   "#64748B",
        "card":      "#FFFFFF",
        "border":    "#E2E8F0",
        "entry_bg":  "#FFFFFF",
        "tree_bg":   "#FFFFFF",
        "tree_even": "#F8FAFC",
    },
    "dark": {
        "bg":        "#0F172A",
        "sidebar":   "#020617",
        "sidebar_h": "#1E293B",
        "accent":    "#3B82F6",
        "accent_dk": "#2563EB",
        "success":   "#10B981",
        "danger":    "#EF4444",
        "warning":   "#F59E0B",
        "white":     "#F1F5F9",
        "text":      "#F1F5F9",
        "text_lt":   "#94A3B8",
        "card":      "#1E293B",
        "border":    "#334155",
        "entry_bg":  "#0F172A",
        "tree_bg":   "#1E293B",
        "tree_even": "#162032",
    },
}

_current_theme = "light"
CLR = dict(THEMES["light"])

def set_theme(name):
    global _current_theme
    _current_theme = name
    CLR.update(THEMES[name])

# ══════════════════════════════════════════════════════
#  LANGUAGE / TRANSLATION
# ══════════════════════════════════════════════════════
_LANG = "th"   # "th" | "en"

_STRINGS = {
    "th": {
        "app_title":      "Stock Manager Pro",
        "dashboard":      "🏠 Dashboard",
        "products":       "📋 สินค้า",
        "categories":     "📁 หมวดหมู่",
        "stock_in":       "📥 รับสินค้า",
        "stock_out":      "📤 จ่ายสินค้า",
        "transactions":   "📊 ประวัติ",
        "barcode":        "🔲 Barcode",
        "charts":         "📈 กราฟ",
        "sales":          "🛒 POS ขาย",
        "sales_history":  "📜 ประวัติขาย",
        "purchase_orders":"📋 ใบ PO",
        "suppliers":      "🏭 ซัพพลายเออร์",
        "branches":       "🏪 สาขา",
        "transfer":       "🔄 โอนย้าย",
        "users":          "👥 ผู้ใช้",
        "shop_settings":  "⚙️ ตั้งค่า",
        "sec_inventory":  "📦 คลังสินค้า",
        "sec_stock":      "🔄 เคลื่อนสต็อก",
        "sec_sales":      "🛒 การขาย",
        "sec_purchase":   "📋 จัดซื้อ",
        "sec_branch":     "🏪 สาขา",
        "sec_system":     "⚙️ ระบบ",
        "logout":         "🚪 ออก",
        "save":           "💾 บันทึก",
        "cancel":         "ยกเลิก",
        "edit":           "✏️ แก้ไข",
        "delete":         "🗑️ ลบ",
        "add":            "➕ เพิ่ม",
        "search":         "🔍 ค้นหา...",
        "export_csv":     "📊 Export CSV",
        "export_pdf":     "📄 Export PDF",
        "confirm_delete": "ยืนยันการลบ",
        "confirm_logout": "ต้องการออกจากระบบใช่ไหม?",
        "settings_title": "⚙️ ตั้งค่าระบบ",
        "settings_sub":   "จัดการร้าน ธีม ภาษา และระบบ",
        "tab_shop":       "🏪 ข้อมูลร้าน",
        "tab_bank":       "🏦 บัญชีธนาคาร",
        "tab_theme":      "🎨 ธีม",
        "tab_language":   "🌐 ภาษา",
        "tab_system":     "🔧 ระบบ",
    },
    "en": {
        "app_title":      "Stock Manager Pro",
        "dashboard":      "🏠 Dashboard",
        "products":       "📋 Products",
        "categories":     "📁 Categories",
        "stock_in":       "📥 Stock In",
        "stock_out":      "📤 Stock Out",
        "transactions":   "📊 History",
        "barcode":        "🔲 Barcode",
        "charts":         "📈 Charts",
        "sales":          "🛒 POS Sales",
        "sales_history":  "📜 Sales History",
        "purchase_orders":"📋 Purchase Orders",
        "suppliers":      "🏭 Suppliers",
        "branches":       "🏪 Branches",
        "transfer":       "🔄 Stock Transfer",
        "users":          "👥 Users",
        "shop_settings":  "⚙️ Settings",
        "sec_inventory":  "📦 Inventory",
        "sec_stock":      "🔄 Stock Moves",
        "sec_sales":      "🛒 Sales",
        "sec_purchase":   "📋 Purchasing",
        "sec_branch":     "🏪 Branches",
        "sec_system":     "⚙️ System",
        "logout":         "🚪 Logout",
        "save":           "💾 Save",
        "cancel":         "Cancel",
        "edit":           "✏️ Edit",
        "delete":         "🗑️ Delete",
        "add":            "➕ Add",
        "search":         "🔍 Search...",
        "export_csv":     "📊 Export CSV",
        "export_pdf":     "📄 Export PDF",
        "confirm_delete": "Confirm Delete",
        "confirm_logout": "Do you want to logout?",
        "settings_title": "⚙️ System Settings",
        "settings_sub":   "Shop, Theme, Language & System",
        "tab_shop":       "🏪 Shop Info",
        "tab_bank":       "🏦 Bank Account",
        "tab_theme":      "🎨 Theme",
        "tab_language":   "🌐 Language",
        "tab_system":     "🔧 System",
    },
}

def T(key):
    """Translate key using current language."""
    return _STRINGS.get(_LANG, _STRINGS["th"]).get(key, key)

def set_lang(lang):
    global _LANG
    _LANG = lang
    set_setting("app_lang", lang)


FONT   = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_H = ("Segoe UI", 14, "bold")
FONT_XL= ("Segoe UI", 22, "bold")

# ─────────────────────────────────────────────
#  Helper widgets
# ─────────────────────────────────────────────
def card(parent, **kw):
    return tk.Frame(parent, bg=CLR["card"], relief="flat",
                    highlightbackground=CLR["border"], highlightthickness=1, **kw)

def btn_primary(parent, text, cmd):
    return tk.Button(parent, text=text, font=FONT_B,
                     bg=CLR["accent"], fg=CLR["white"],
                     activebackground=CLR["accent_dk"], activeforeground=CLR["white"],
                     relief="flat", padx=14, pady=7, cursor="hand2", command=cmd)

def btn_danger(parent, text, cmd):
    return tk.Button(parent, text=text, font=FONT_B,
                     bg=CLR["danger"], fg=CLR["white"],
                     activebackground="#DC2626", activeforeground=CLR["white"],
                     relief="flat", padx=14, pady=7, cursor="hand2", command=cmd)

def btn_success(parent, text, cmd):
    return tk.Button(parent, text=text, font=FONT_B,
                     bg=CLR["success"], fg=CLR["white"],
                     activebackground="#059669", activeforeground=CLR["white"],
                     relief="flat", padx=14, pady=7, cursor="hand2", command=cmd)

def btn_warn(parent, text, cmd):
    return tk.Button(parent, text=text, font=FONT_B,
                     bg=CLR["warning"], fg=CLR["white"],
                     activebackground="#D97706", activeforeground=CLR["white"],
                     relief="flat", padx=14, pady=7, cursor="hand2", command=cmd)

def page_title(parent, title, subtitle=""):
    tk.Label(parent, text=title, font=FONT_XL,
             bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w")
    if subtitle:
        tk.Label(parent, text=subtitle, font=FONT,
                 bg=CLR["bg"], fg=CLR["text_lt"]).pack(anchor="w")

def make_tree(parent, cols, col_widths, height=18):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=CLR["tree_bg"], rowheight=28,
                    fieldbackground=CLR["tree_bg"], font=FONT, borderwidth=0,
                    foreground=CLR["text"])
    style.configure("Treeview.Heading", background=CLR["sidebar"],
                    foreground=CLR["white"], font=FONT_B, relief="flat")
    style.map("Treeview", background=[("selected", CLR["accent"])],
              foreground=[("selected", CLR["white"])])
    wrap = card(parent)
    tv = ttk.Treeview(wrap, columns=cols, show="headings", height=height)
    sb = ttk.Scrollbar(wrap, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    tv.pack(fill="both", expand=True)
    for col, w in zip(cols, col_widths):
        tv.heading(col, text=col)
        tv.column(col, width=w, anchor="w" if col in ("ชื่อสินค้า","ชื่อหมวดหมู่","หมายเหตุ","ชื่อ","ชื่อ-นามสกุล") else "center")
    return wrap, tv

def scrollable_page(parent, padx=30, pady=24):
    """Returns (outer, top, mid, bot) frames using grid so buttons stay visible."""
    outer = tk.Frame(parent, bg=CLR["bg"])
    outer.pack(fill="both", expand=True, padx=padx, pady=pady)
    outer.rowconfigure(2, weight=1)
    outer.columnconfigure(0, weight=1)
    top = tk.Frame(outer, bg=CLR["bg"])   # title + toolbar
    top.grid(row=0, column=0, sticky="ew")
    sep = tk.Frame(outer, bg=CLR["border"], height=1)
    sep.grid(row=1, column=0, sticky="ew", pady=(10,10))
    mid = tk.Frame(outer, bg=CLR["bg"])   # table area
    mid.grid(row=2, column=0, sticky="nsew")
    mid.rowconfigure(0, weight=1)
    mid.columnconfigure(0, weight=1)
    bot = tk.Frame(outer, bg=CLR["bg"])   # action buttons always visible
    bot.grid(row=3, column=0, sticky="ew", pady=(8,0))
    return outer, top, mid, bot


# ════════════════════════════════════════════════
#  LOGIN WINDOW
# ════════════════════════════════════════════════
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔐 Stock Manager Pro — เข้าสู่ระบบ")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(bg=CLR["bg"])
        self.result_user = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 420) // 2
        y = (self.winfo_screenheight() - 480) // 2
        self.geometry(f"420x480+{x}+{y}")

    def _build(self):
        outer = tk.Frame(self, bg=CLR["bg"])
        outer.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(outer, text="📦", font=("Segoe UI", 48),
                 bg=CLR["bg"], fg=CLR["accent"]).pack()
        tk.Label(outer, text="Stock Manager Pro",
                 font=("Segoe UI", 18, "bold"),
                 bg=CLR["bg"], fg=CLR["text"]).pack(pady=(4, 2))
        tk.Label(outer, text="กรุณาเข้าสู่ระบบเพื่อดำเนินการต่อ",
                 font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(pady=(0, 24))

        form = card(outer, padx=28, pady=28)
        form.pack(fill="x")

        for label, attr, show in [("👤  ชื่อผู้ใช้", "_user_var", ""),
                                   ("🔒  รหัสผ่าน",  "_pw_var",   "•")]:
            tk.Label(form, text=label, font=FONT_B,
                     bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(8,2))
            v = tk.StringVar()
            e = tk.Entry(form, textvariable=v, font=("Segoe UI",12),
                         show=show, relief="solid", bg=CLR["bg"],
                         highlightbackground=CLR["border"],
                         highlightthickness=1)
            e.pack(fill="x", ipady=8)
            setattr(self, attr, v)

        self._err_lbl = tk.Label(form, text="", font=FONT,
                                  bg=CLR["card"], fg=CLR["danger"])
        self._err_lbl.pack(pady=(8, 0))

        tk.Frame(form, bg=CLR["border"], height=1).pack(fill="x", pady=16)

        login_btn = tk.Button(form, text="เข้าสู่ระบบ  →",
                              font=("Segoe UI", 12, "bold"),
                              bg=CLR["accent"], fg=CLR["white"],
                              activebackground=CLR["accent_dk"],
                              relief="flat", pady=10, cursor="hand2",
                              command=self._login)
        login_btn.pack(fill="x")
        self.bind("<Return>", lambda _: self._login())

        tk.Label(outer, text="Default: admin / admin123",
                 font=("Segoe UI", 9), bg=CLR["bg"],
                 fg=CLR["text_lt"]).pack(pady=(12,0))

    def _login(self):
        uname = self._user_var.get().strip()
        pw    = self._pw_var.get()
        if not uname or not pw:
            self._err_lbl.config(text="กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id,username,role,fullname FROM users WHERE username=? AND password=?",
                (uname, hash_pw(pw))
            ).fetchone()
        if row:
            self.result_user = {"id": row[0], "username": row[1],
                                 "role": row[2], "fullname": row[3] or row[1]}
            self.destroy()
        else:
            self._err_lbl.config(text="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            self._pw_var.set("")


# ════════════════════════════════════════════════
#  BARCODE GENERATOR (pure Canvas — no extra lib)
# ════════════════════════════════════════════════
class BarcodeCanvas(tk.Canvas):
    """Draws a Code-128B barcode purely with Tkinter Canvas."""

    START_B = [11010010000]
    STOP    = [1100011101011]

    CODE128B = [
        "11011001100","11001101100","11001100110","10010011000","10010001100",
        "10001001100","10011001000","10011000100","10001100100","11001001000",
        "11001000100","11000100100","10110011100","10011011100","10011001110",
        "10111001100","10011101100","10011100110","11001110010","11001011100",
        "11001001110","11011100100","11001110100","11101101110","11101001100",
        "11100101100","11100100110","11101100100","11100110100","11100110010",
        "11011011000","11011000110","11000110110","10100011000","10001011000",
        "10001000110","10110001000","10001101000","10001100010","11010001000",
        "11000101000","11000100010","10110111000","10110001110","10001101110",
        "10111011000","10111000110","10001110110","11101110110","11010001110",
        "11000101110","11011101000","11011100010","11011101110","11101011000",
        "11101000110","11100010110","11011010000","11011010110","11011001010",
        "10100111000","10100001110","10001011100","10111100100","10011110100",
        "10011110010","11110100100","11110010100","11110010010","11011110100",
        "11011110010","11110110100","11110110010","10011011110","10011110110",
        "11110110110","10111011110","10111101110","11110101110","11010000100",
        "11010010000","11010011100","1100011101011",
    ]

    def draw_barcode(self, text, x=20, y=20, bar_w=2, bar_h=80):
        self.delete("all")
        encoded = self._encode(text)
        if not encoded:
            self.create_text(60, 40, text="Code error", fill="red")
            return
        px = x
        for bar_str in encoded:
            for ch in bar_str:
                color = "black" if ch == "1" else "white"
                self.create_rectangle(px, y, px + bar_w, y + bar_h,
                                      fill=color, outline="")
                px += bar_w
        self.create_text(x + (px - x) // 2, y + bar_h + 14,
                         text=text, font=("Courier", 11))
        self.config(width=px + x, height=y + bar_h + 32)

    def _encode(self, text):
        try:
            bars = ["11010010000"]  # START B
            checksum = 104
            for i, ch in enumerate(text):
                idx = ord(ch) - 32
                if idx < 0 or idx > 95:
                    return None
                bars.append(self.CODE128B[idx])
                checksum += (i + 1) * idx
            bars.append(self.CODE128B[checksum % 103])
            bars.append("1100011101011")  # STOP
            bars.append("11")
            return bars
        except Exception:
            return None


# ════════════════════════════════════════════════
#  BARCODE FRAME
# ════════════════════════════════════════════════
class BarcodeFrame(tk.Frame):
    NAME = "barcode"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)

        page_title(pad, "🔲 Barcode", "สร้างและพิมพ์ Barcode สินค้า")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        top = tk.Frame(pad, bg=CLR["bg"])
        top.pack(fill="x")

        # Left: product picker
        left = card(top, padx=20, pady=20)
        left.pack(side="left", fill="y")

        tk.Label(left, text="เลือกสินค้า", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))

        self._prod_var = tk.StringVar()
        with get_conn() as conn:
            prods = conn.execute("SELECT code,name FROM products ORDER BY name").fetchall()
        self._prod_map = {f"[{p[0]}] {p[1]}": p[0] for p in prods}

        cb = ttk.Combobox(left, textvariable=self._prod_var,
                          values=list(self._prod_map.keys()),
                          font=FONT, state="readonly", width=34)
        cb.pack(anchor="w", ipady=5)
        cb.bind("<<ComboboxSelected>>", lambda _: self._gen())

        tk.Label(left, text="หรือพิมพ์รหัสเอง", font=FONT,
                 bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w", pady=(14,4))
        self._custom_var = tk.StringVar()
        tk.Entry(left, textvariable=self._custom_var, font=FONT,
                 relief="solid", width=36,
                 highlightbackground=CLR["border"], highlightthickness=1
                 ).pack(anchor="w", ipady=5)

        tk.Frame(left, bg=CLR["border"], height=1).pack(fill="x", pady=14)
        btn_primary(left, "🔲 สร้าง Barcode", self._gen).pack(anchor="w")
        tk.Frame(left, bg=CLR["bg"], height=8).pack()
        btn_warn(left, "💾 บันทึก PNG", self._save_png).pack(anchor="w")

        # Right: preview
        right = card(top, padx=20, pady=20)
        right.pack(side="left", fill="both", expand=True, padx=(12,0))
        tk.Label(right, text="ตัวอย่าง Barcode", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))

        self._bc_canvas = BarcodeCanvas(right, bg="white",
                                         width=500, height=140)
        self._bc_canvas.pack()

        # Batch section
        batch_card = card(pad, padx=20, pady=16)
        batch_card.pack(fill="x", pady=(14,0))
        tk.Label(batch_card, text="🖨️ พิมพ์ Barcode หลายรายการพร้อมกัน",
                 font=FONT_B, bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,10))

        cols = ("รหัส","ชื่อสินค้า","หน่วย")
        wrap, self._batch_tv = make_tree(batch_card, cols, [100,280,80], height=6)
        wrap.pack(fill="x")
        self._load_batch()

        br = tk.Frame(batch_card, bg=CLR["card"])
        br.pack(fill="x", pady=(10,0))
        btn_primary(br, "🖨️ พิมพ์ที่เลือก (PDF)", self._batch_pdf).pack(side="left")

    def _load_batch(self):
        self._batch_tv.delete(*self._batch_tv.get_children())
        with get_conn() as conn:
            for r in conn.execute("SELECT code,name,unit FROM products ORDER BY name").fetchall():
                self._batch_tv.insert("", "end", values=r)

    def _gen(self):
        code = self._custom_var.get().strip()
        if not code and self._prod_var.get():
            code = self._prod_map.get(self._prod_var.get(), "")
        if not code:
            return
        self._current_code = code
        self._bc_canvas.draw_barcode(code, bar_w=2, bar_h=90)

    def _save_png(self):
        if not hasattr(self, "_current_code"):
            messagebox.showwarning("แจ้งเตือน", "กรุณาสร้าง Barcode ก่อน")
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            messagebox.showerror("ผิดพลาด", "ต้องการ Pillow: pip install pillow")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG","*.png")],
            initialfile=f"barcode_{self._current_code}.png")
        if not path: return
        # render via postscript → rasterize
        try:
            ps = self._bc_canvas.postscript(colormode="color")
            img = Image.open(io.BytesIO(ps.encode("latin-1")))
            img.save(path)
        except Exception:
            messagebox.showinfo("แจ้งเตือน",
                "บันทึกผ่าน postscript ไม่สำเร็จ\nกรุณาใช้ screenshot แทนครับ")

    def _batch_pdf(self):
        sels = self._batch_tv.selection()
        if not sels:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้าก่อน (Ctrl+คลิก)")
            return
        if not HAS_RL:
            messagebox.showerror("ผิดพลาด", "ต้องการ reportlab: pip install reportlab")
            return
        codes = [self._batch_tv.item(s)["values"][0] for s in sels]
        path  = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=f"barcodes_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not path: return
        _export_barcode_pdf(codes, path)
        messagebox.showinfo("สำเร็จ", f"บันทึก PDF สำเร็จ\n{path}")


def _export_barcode_pdf(codes, path):
    """Generate a PDF page with barcodes drawn via ReportLab."""
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    c = rl_canvas.Canvas(path, pagesize=A4)
    w, h = A4
    x0, y0 = 40, h - 80
    col_w  = (w - 80) / 2
    for i, code in enumerate(codes):
        col = i % 2
        row = (i % 8) // 2
        if i > 0 and i % 8 == 0:
            c.showPage()
            y0 = h - 80
        bx = x0 + col * col_w
        by = y0 - row * 110
        # draw barcode bars
        _draw_code128_rl(c, code, bx, by, bar_w=1.6, bar_h=50)
        c.setFont("Helvetica", 9)
        c.drawCentredString(bx + col_w / 2, by - 14, code)
    c.save()

def _draw_code128_rl(c, text, x, y, bar_w=1.6, bar_h=50):
    CODE128B = [
        "11011001100","11001101100","11001100110","10010011000","10010001100",
        "10001001100","10011001000","10011000100","10001100100","11001001000",
        "11001000100","11000100100","10110011100","10011011100","10011001110",
        "10111001100","10011101100","10011100110","11001110010","11001011100",
        "11001001110","11011100100","11001110100","11101101110","11101001100",
        "11100101100","11100100110","11101100100","11100110100","11100110010",
        "11011011000","11011000110","11000110110","10100011000","10001011000",
        "10001000110","10110001000","10001101000","10001100010","11010001000",
        "11000101000","11000100010","10110111000","10110001110","10001101110",
        "10111011000","10111000110","10001110110","11101110110","11010001110",
        "11000101110","11011101000","11011100010","11011101110","11101011000",
        "11101000110","11100010110","11011010000","11011010110","11011001010",
        "10100111000","10100001110","10001011100","10111100100","10011110100",
        "10011110010","11110100100","11110010100","11110010010","11011110100",
        "11011110010","11110110100","11110110010","10011011110","10011110110",
        "11110110110","10111011110","10111101110","11110101110","11010000100",
        "11010010000","11010011100","1100011101011",
    ]
    try:
        bars = ["11010010000"]
        chk  = 104
        for i, ch in enumerate(text):
            idx = ord(ch) - 32
            if idx < 0 or idx > 95: return
            bars.append(CODE128B[idx])
            chk += (i + 1) * idx
        bars.append(CODE128B[chk % 103])
        bars.append("1100011101011")
        bars.append("11")
        px = x
        for bar_str in bars:
            for bit in bar_str:
                if bit == "1":
                    c.setFillColorRGB(0, 0, 0)
                    c.rect(px, y, bar_w, bar_h, fill=1, stroke=0)
                px += bar_w
    except Exception:
        pass


# ════════════════════════════════════════════════
#  PDF REPORT HELPERS
# ════════════════════════════════════════════════
def _make_pdf_stock(path, rows, title="รายงานสต็อกสินค้า"):
    if not HAS_RL:
        return False
    doc = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elems  = []

    # Title
    elems.append(Paragraph(f"<b>{title}</b>",
                            ParagraphStyle("T", fontSize=16, spaceAfter=6,
                                           alignment=1)))
    elems.append(Paragraph(
        f"วันที่พิมพ์: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("S", fontSize=9, textColor=rl_colors.grey,
                        alignment=1, spaceAfter=16)))

    headers = ["รหัส","ชื่อสินค้า","หมวดหมู่","หน่วย","คงเหลือ","ขั้นต่ำ","ราคา/หน่วย","มูลค่า"]
    data = [headers] + [[str(c) for c in r] for r in rows]

    col_w = [2*cm, 5*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm]
    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), rl_colors.HexColor("#1E293B")),
        ("TEXTCOLOR",   (0,0), (-1,0), rl_colors.white),
        ("FONTSIZE",    (0,0), (-1,0), 9),
        ("FONTSIZE",    (0,1), (-1,-1), 8),
        ("ALIGN",       (4,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [rl_colors.white, rl_colors.HexColor("#F8FAFC")]),
        ("GRID",        (0,0), (-1,-1), 0.4, rl_colors.HexColor("#E2E8F0")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    elems.append(tbl)
    doc.build(elems)
    return True

def _make_pdf_transactions(path, rows, title="รายงานประวัติการเคลื่อนไหว"):
    if not HAS_RL:
        return False
    doc = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=1.5*cm)
    elems = []
    elems.append(Paragraph(f"<b>{title}</b>",
                            ParagraphStyle("T", fontSize=16, spaceAfter=6, alignment=1)))
    elems.append(Paragraph(
        f"วันที่พิมพ์: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("S", fontSize=9, textColor=rl_colors.grey,
                        alignment=1, spaceAfter=16)))

    headers = ["วันที่","รหัส","ชื่อสินค้า","ประเภท","จำนวน","ผู้ดำเนินการ","หมายเหตุ"]
    data = [headers] + [[str(c) for c in r] for r in rows]
    col_w = [3.5*cm, 2*cm, 4.5*cm, 1.8*cm, 2*cm, 2.5*cm, 3*cm]
    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), rl_colors.HexColor("#1E293B")),
        ("TEXTCOLOR",   (0,0), (-1,0), rl_colors.white),
        ("FONTSIZE",    (0,0), (-1,0), 9),
        ("FONTSIZE",    (0,1), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [rl_colors.white, rl_colors.HexColor("#F8FAFC")]),
        ("GRID",        (0,0), (-1,-1), 0.4, rl_colors.HexColor("#E2E8F0")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    elems.append(tbl)
    doc.build(elems)
    return True
    def __init__(self):
        super().__init__()
        self.title("📦 Stock Manager Pro")
        self.geometry("1280x760")
        self.minsize(960, 640)
        self.configure(bg=CLR["bg"])
        init_db()
        self._build_ui()
        self.show_frame("dashboard")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────
        sb = tk.Frame(self, bg=CLR["sidebar"], width=215)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        tk.Label(sb, text="📦", font=("Segoe UI", 28),
                 bg=CLR["sidebar"], fg=CLR["white"]).pack(pady=(28,0))
        tk.Label(sb, text="Stock Manager Pro",
                 font=("Segoe UI", 11, "bold"),
                 bg=CLR["sidebar"], fg=CLR["white"]).pack(pady=(4,30))

        self._nav_btns = {}
        nav_items = [
            ("dashboard",    "🏠  Dashboard"),
            ("products",     "📋  สินค้า"),
            ("categories",   "📁  หมวดหมู่"),
            ("stock_in",     "📥  รับสินค้า"),
            ("stock_out",    "📤  จ่ายสินค้า"),
            ("transactions", "📊  ประวัติ"),
            ("charts",       "📈  กราฟสถิติ"),
        ]
        for key, label in nav_items:
            b = tk.Button(sb, text=label, font=("Segoe UI", 11),
                          bg=CLR["sidebar"], fg="#CBD5E1",
                          activebackground=CLR["sidebar_h"],
                          activeforeground=CLR["white"],
                          relief="flat", anchor="w", padx=22, pady=10,
                          cursor="hand2",
                          command=lambda k=key: self.show_frame(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        # ── Content ──────────────────────────────
        self.content = tk.Frame(self, bg=CLR["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for F in (DashboardFrame, ProductsFrame, CategoriesFrame,
                  StockInFrame, StockOutFrame, TransactionsFrame, ChartsFrame):
            frame = F(self.content, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[F.NAME] = frame

    def show_frame(self, name):
        for key, btn in self._nav_btns.items():
            btn.configure(bg=CLR["accent"] if key == name else CLR["sidebar"],
                          fg=CLR["white"] if key == name else "#CBD5E1")
        self.frames[name].refresh()
        self.frames[name].tkraise()


# ═══════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════
class DashboardFrame(tk.Frame):
    NAME = "dashboard"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=20)

        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        month_start = datetime.now().strftime("%Y-%m-01")

        with get_conn() as conn:
            total_prod   = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            total_val    = conn.execute("SELECT SUM(quantity*price) FROM products").fetchone()[0] or 0
            low_stock    = conn.execute("SELECT COUNT(*) FROM products WHERE quantity<=min_qty AND min_qty>0").fetchone()[0]
            out_stock    = conn.execute("SELECT COUNT(*) FROM products WHERE quantity=0").fetchone()[0]
            sale_today   = conn.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?", (today+"%",)).fetchone()[0]
            sale_month   = conn.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date>=?", (month_start,)).fetchone()[0]
            sale_count   = conn.execute("SELECT COUNT(*) FROM sales WHERE date LIKE ?", (today+"%",)).fetchone()[0]
            cost_month   = conn.execute("""
                SELECT COALESCE(SUM(si.quantity*p.price),0)
                FROM sale_items si JOIN products p ON si.product_id=p.id
                JOIN sales s ON si.sale_id=s.id WHERE s.date>=?""", (month_start,)).fetchone()[0]
            top5 = conn.execute("""
                SELECT p.name, SUM(si.quantity) qty, SUM(si.subtotal) rev
                FROM sale_items si JOIN products p ON si.product_id=p.id
                JOIN sales s ON si.sale_id=s.id
                WHERE s.date>=? GROUP BY p.id ORDER BY qty DESC LIMIT 5""", (month_start,)).fetchall()
            low_items = conn.execute("""
                SELECT code,name,quantity,min_qty FROM products
                WHERE quantity<=min_qty AND min_qty>0 ORDER BY quantity ASC LIMIT 8""").fetchall()
            total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

        profit_month = sale_month - cost_month

        page_title(pad, "🏠 Dashboard", f"ข้อมูล ณ วันที่ {today}")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=(8,12))

        # ── Row 1: Sales KPIs ──────────────────────────────
        tk.Label(pad, text="📊 ยอดขาย", font=("Segoe UI",9,"bold"),
                 bg=CLR["bg"], fg=CLR["text_lt"]).pack(anchor="w")
        r1 = tk.Frame(pad, bg=CLR["bg"]); r1.pack(fill="x", pady=(4,12))
        for i,(title,val,unit,color) in enumerate([
            ("🛒 ยอดขายวันนี้",    f"{sale_today:,.0f}",  "บาท",    CLR["accent"]),
            ("📅 ยอดขายเดือนนี้",  f"{sale_month:,.0f}",  "บาท",    CLR["success"]),
            ("💹 กำไรเดือนนี้",    f"{profit_month:,.0f}","บาท",    "#A78BFA"),
            ("🧾 บิลวันนี้",       str(sale_count),       "ใบ",     CLR["warning"]),
            ("👥 ลูกค้าทั้งหมด",  str(total_customers),  "คน",     CLR["accent"]),
        ]):
            c = card(r1, padx=16, pady=14)
            c.grid(row=0, column=i, sticky="nsew", padx=(0,10) if i<4 else 0)
            r1.columnconfigure(i, weight=1)
            tk.Label(c, text=title, font=("Segoe UI",9), bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")
            tk.Label(c, text=val, font=("Segoe UI",20,"bold"), bg=CLR["card"], fg=color).pack(anchor="w")
            tk.Label(c, text=unit, font=("Segoe UI",9), bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")

        # ── Row 2: Inventory KPIs ──────────────────────────
        tk.Label(pad, text="📦 คลังสินค้า", font=("Segoe UI",9,"bold"),
                 bg=CLR["bg"], fg=CLR["text_lt"]).pack(anchor="w")
        r2 = tk.Frame(pad, bg=CLR["bg"]); r2.pack(fill="x", pady=(4,12))
        for i,(title,val,unit,color) in enumerate([
            ("📦 สินค้าทั้งหมด", str(total_prod),        "รายการ", CLR["accent"]),
            ("💰 มูลค่าคลัง",    f"{total_val:,.0f}",    "บาท",    CLR["success"]),
            ("⚠️ ใกล้หมด",       str(low_stock),         "รายการ", CLR["warning"]),
            ("🚫 หมดสต็อก",      str(out_stock),         "รายการ", CLR["danger"]),
        ]):
            c = card(r2, padx=16, pady=14)
            c.grid(row=0, column=i, sticky="nsew", padx=(0,10) if i<3 else 0)
            r2.columnconfigure(i, weight=1)
            tk.Label(c, text=title, font=("Segoe UI",9), bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")
            tk.Label(c, text=val, font=("Segoe UI",20,"bold"), bg=CLR["card"], fg=color).pack(anchor="w")
            tk.Label(c, text=unit, font=("Segoe UI",9), bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")

        # ── Row 3: Two columns (Top5 + Low Stock) ──────────
        r3 = tk.Frame(pad, bg=CLR["bg"]); r3.pack(fill="both", expand=True)
        r3.columnconfigure(0, weight=1); r3.columnconfigure(1, weight=1)

        # Top 5 สินค้าขายดี
        left = card(r3, padx=16, pady=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        tk.Label(left, text="🏆 สินค้าขายดีเดือนนี้ Top 5",
                 font=FONT_B, bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
        for rank,(name,qty,rev) in enumerate(top5, 1):
            row = tk.Frame(left, bg=CLR["card"]); row.pack(fill="x", pady=2)
            medal = ["🥇","🥈","🥉","4️⃣","5️⃣"][rank-1]
            tk.Label(row, text=f"{medal} {name[:24]}", font=FONT,
                     bg=CLR["card"], fg=CLR["text"]).pack(side="left")
            tk.Label(row, text=f"{qty:g} ชิ้น  ฿{rev:,.0f}",
                     font=FONT, bg=CLR["card"], fg=CLR["text_lt"]).pack(side="right")
        if not top5:
            tk.Label(left, text="ยังไม่มีข้อมูลการขาย", font=FONT,
                     bg=CLR["card"], fg=CLR["text_lt"]).pack(pady=20)

        # ⚠️ สินค้าใกล้หมด
        right = card(r3, padx=16, pady=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        tk.Label(right, text="⚠️ สินค้าต้องสั่งซื้อ",
                 font=FONT_B, bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
        for r in low_items:
            row = tk.Frame(right, bg=CLR["card"]); row.pack(fill="x", pady=2)
            icon = "🚫" if r[2]==0 else "⚠️"
            color = CLR["danger"] if r[2]==0 else CLR["warning"]
            tk.Label(row, text=f"{icon} {r[1][:26]}", font=FONT,
                     bg=CLR["card"], fg=CLR["text"]).pack(side="left")
            tk.Label(row, text=f"{r[2]:g}/{r[3]:g}", font=FONT,
                     bg=CLR["card"], fg=color).pack(side="right")
        if not low_items:
            tk.Label(right, text="✅ สินค้าครบทุกรายการ", font=FONT,
                     bg=CLR["card"], fg=CLR["success"]).pack(pady=20)


# ═══════════════════════════════════════════════
#  CATEGORIES
# ═══════════════════════════════════════════════
class CategoriesFrame(tk.Frame):
    NAME = "categories"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"])
        self._build()
        self._load()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        self._pad = pad

        page_title(pad, "📁 หมวดหมู่สินค้า", "จัดการหมวดหมู่สินค้าในระบบ")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        # Input card
        ic = card(pad, padx=24, pady=18)
        ic.pack(fill="x", pady=(0,12))
        tk.Label(ic, text="ชื่อหมวดหมู่ใหม่", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).grid(row=0, column=0, sticky="w", pady=4)
        self.cat_var = tk.StringVar()
        tk.Entry(ic, textvariable=self.cat_var, font=FONT, width=36,
                 bg=CLR["entry_bg"], fg=CLR["text"],
                 insertbackground=CLR["text"],
                 relief="solid", highlightbackground=CLR["border"],
                 highlightthickness=1).grid(row=0, column=1, padx=12, ipady=5)
        btn_primary(ic, "➕ เพิ่ม", self._add).grid(row=0, column=2)

        # Table
        cols = ("id","ชื่อหมวดหมู่","จำนวนสินค้า")
        wrap, self.tv = make_tree(pad, cols, [0, 320, 120], height=15)
        self.tv.column("id", width=0, stretch=False)
        ab = tk.Frame(pad, bg=CLR["bg"])
        ab.pack(fill="x", pady=(10,0))
        wrap.pack(fill="both", expand=True)
        self.tv.bind("<Double-1>", lambda _: self._edit())

        btn_primary(ab, "✏️ แก้ไขชื่อ", self._edit).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=8).pack(side="left")
        btn_danger(ab, "🗑️ ลบ", self._delete).pack(side="left")
        tk.Label(ab, text="💡 ดับเบิลคลิกเพื่อแก้ไข",
                 font=("Segoe UI",9), bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="right")

    def _load(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT c.id, c.name, COUNT(p.id)
                FROM categories c LEFT JOIN products p ON p.category=c.name
                GROUP BY c.id ORDER BY c.name
            """).fetchall()
        for r in rows:
            self.tv.insert("", "end", values=r)

    def _add(self):
        name = self.cat_var.get().strip()
        if not name:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกชื่อหมวดหมู่")
            return
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO categories(name) VALUES(?)", (name,))
                conn.commit()
            self.cat_var.set("")
            self._load()
        except Exception:
            messagebox.showerror("ผิดพลาด", f"ชื่อ '{name}' มีอยู่แล้ว")

    def _edit(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกหมวดหมู่ก่อน")
            return
        cat_id, old_name, _ = self.tv.item(sel[0])["values"]

        dlg = tk.Toplevel(self)
        dlg.title("แก้ไขหมวดหมู่")
        dlg.geometry("360x180")
        dlg.configure(bg=CLR["bg"])
        dlg.resizable(False, False)
        dlg.grab_set()

        pad = tk.Frame(dlg, bg=CLR["bg"], padx=24, pady=20)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text="แก้ไขชื่อหมวดหมู่", font=FONT_H,
                 bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))
        nv = tk.StringVar(value=old_name)
        tk.Entry(pad, textvariable=nv, font=FONT,
                 bg=CLR["entry_bg"], fg=CLR["text"],
                 insertbackground=CLR["text"],
                 relief="solid", highlightbackground=CLR["border"],
                 highlightthickness=1).pack(fill="x", ipady=7, pady=(0,14))

        def save():
            new_name = nv.get().strip()
            if not new_name:
                messagebox.showwarning("แจ้งเตือน", "กรุณากรอกชื่อ", parent=dlg); return
            try:
                with get_conn() as conn:
                    conn.execute("UPDATE categories SET name=? WHERE id=?", (new_name, cat_id))
                    conn.execute("UPDATE products SET category=? WHERE category=?", (new_name, old_name))
                    conn.commit()
                self._load()
                dlg.destroy()
            except Exception:
                messagebox.showerror("ผิดพลาด", "ชื่อนี้มีอยู่แล้ว", parent=dlg)

        br = tk.Frame(pad, bg=CLR["bg"])
        br.pack(fill="x")
        btn_primary(br, "💾 บันทึก", save).pack(side="right")
        tk.Button(br, text="ยกเลิก", font=FONT, bg=CLR["border"], fg=CLR["text"],
                  relief="flat", padx=14, pady=7, cursor="hand2",
                  command=dlg.destroy).pack(side="right", padx=(0,8))

    def _delete(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกหมวดหมู่ก่อน")
            return
        cat_id, name, count = self.tv.item(sel[0])["values"]
        if int(count) > 0:
            if not messagebox.askyesno("ยืนยัน",
                f"หมวดหมู่ '{name}' มีสินค้า {count} รายการ\nต้องการลบต่อไหม?\n(สินค้าจะถูกเปลี่ยนเป็นไม่มีหมวดหมู่)"):
                return
            with get_conn() as conn:
                conn.execute("UPDATE products SET category=NULL WHERE category=?", (name,))
        with get_conn() as conn:
            conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
            conn.commit()
        self._load()


# ═══════════════════════════════════════════════
#  PRODUCTS
# ═══════════════════════════════════════════════
class ProductsFrame(tk.Frame):
    NAME = "products"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        self._cat_filter = tk.StringVar(value="ทั้งหมด")

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self._build()
        self._load()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        self._pad = pad

        page_title(pad, "📋 สินค้า", "จัดการข้อมูลสินค้าในคลัง")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        # Toolbar
        tb = tk.Frame(pad, bg=CLR["bg"])
        tb.pack(fill="x", pady=(0,10))

        btn_primary(tb, "➕ เพิ่มสินค้า", self._add).pack(side="left")
        tk.Frame(tb, bg=CLR["bg"], width=8).pack(side="left")
        btn_warn(tb, "📊 Export CSV", self._export_csv).pack(side="left")
        tk.Frame(tb, bg=CLR["bg"], width=16).pack(side="left")

        # Category filter
        tk.Label(tb, text="หมวดหมู่:", font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="left")
        cats = ["ทั้งหมด"] + self._get_cats()
        self._cat_filter.set("ทั้งหมด")
        cb = ttk.Combobox(tb, textvariable=self._cat_filter,
                          values=cats, font=FONT, state="readonly", width=18)
        cb.pack(side="left", padx=8, ipady=4)
        cb.bind("<<ComboboxSelected>>", lambda _: self._load())

        # Search
        sf = tk.Frame(tb, bg=CLR["card"], highlightbackground=CLR["border"], highlightthickness=1)
        sf.pack(side="left", padx=8)
        tk.Label(sf, text="🔍", bg=CLR["card"], font=FONT).pack(side="left", padx=(8,0))
        tk.Entry(sf, textvariable=self._search_var, font=FONT,
                 bg=CLR["card"], relief="flat", width=26).pack(side="left", padx=6, pady=6)

        # Table
        cols = ("id","รหัส","ชื่อสินค้า","หมวดหมู่","หน่วย","คงเหลือ","ขั้นต่ำ","ราคา/หน่วย")
        wrap, self.tv = make_tree(pad, cols, [0,80,220,120,70,90,80,110])
        self.tv.column("id", width=0, stretch=False)
        ab = tk.Frame(pad, bg=CLR["bg"])
        ab.pack(fill="x", pady=(10,0))
        wrap.pack(fill="both", expand=True)
        self.tv.tag_configure("low",  background="#FEF9C3")
        self.tv.tag_configure("zero", background="#FEE2E2")

        btn_primary(ab, "✏️ แก้ไข", self._edit).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=8).pack(side="left")
        btn_danger(ab, "🗑️ ลบ", self._delete).pack(side="left")

    def _get_cats(self):
        with get_conn() as conn:
            return [r[0] for r in conn.execute("SELECT name FROM categories ORDER BY name").fetchall()]

    def _load(self):
        self.tv.delete(*self.tv.get_children())
        kw = f"%{self._search_var.get()}%"
        cat = self._cat_filter.get()
        sql = """SELECT id,code,name,category,unit,quantity,min_qty,price
                 FROM products WHERE (name LIKE ? OR code LIKE ? OR category LIKE ?)"""
        params = [kw, kw, kw]
        if cat != "ทั้งหมด":
            sql += " AND category=?"
            params.append(cat)
        sql += " ORDER BY name"
        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        for r in rows:
            tag = "zero" if r[5] == 0 else ("low" if r[6] > 0 and r[5] <= r[6] else "")
            self.tv.insert("", "end",
                           values=(r[0], r[1], r[2], r[3] or "-", r[4] or "-",
                                   f"{r[5]:g}", f"{r[6]:g}", f"{r[7]:,.2f}"),
                           tags=(tag,))

    def _selected_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้าก่อน")
            return None
        return self.tv.item(sel[0])["values"][0]

    def _add(self):    ProductDialog(self, None, self._load)
    def _edit(self):
        pid = self._selected_id()
        if pid: ProductDialog(self, pid, self._load)

    def _delete(self):
        pid = self._selected_id()
        if pid and messagebox.askyesno("ยืนยัน", "ต้องการลบสินค้านี้ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM products WHERE id=?", (pid,))
                conn.execute("DELETE FROM transactions WHERE product_id=?", (pid,))
                conn.commit()
            self._load()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files","*.csv")],
            initialfile=f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if not path: return
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT code,name,category,unit,quantity,min_qty,price,updated FROM products ORDER BY name"
            ).fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["รหัส","ชื่อสินค้า","หมวดหมู่","หน่วย","คงเหลือ","ขั้นต่ำ","ราคา/หน่วย","อัปเดตล่าสุด"])
            w.writerows(rows)
        messagebox.showinfo("สำเร็จ", f"Export สำเร็จ\n{path}")


# ─────────────────────────────────────────────
#  Product Dialog
# ─────────────────────────────────────────────
class ProductDialog(tk.Toplevel):
    def __init__(self, parent, product_id, callback):
        super().__init__(parent)
        self.product_id = product_id
        self.callback   = callback
        self.title("เพิ่มสินค้า" if product_id is None else "แก้ไขสินค้า")
        self.geometry("500x660")
        self.resizable(False, False)
        self.configure(bg=CLR["bg"])
        self.grab_set()
        self._build()
        if product_id: self._load()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"], padx=28, pady=20)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text="เพิ่มสินค้า" if self.product_id is None else "แก้ไขสินค้า",
                 font=FONT_H, bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w", pady=(0,16))

        self.vars = {}
        with get_conn() as conn:
            cats = [r[0] for r in conn.execute("SELECT name FROM categories ORDER BY name").fetchall()]

        for key, label, widget_type in [
            ("code",       "รหัสสินค้า *",  "entry"),
            ("name",       "ชื่อสินค้า *",  "entry"),
            ("category",   "หมวดหมู่",      "combo"),
            ("unit",       "หน่วย",         "entry"),
            ("quantity",   "จำนวนเริ่มต้น", "entry"),
            ("min_qty",    "จำนวนขั้นต่ำ",  "entry"),
            ("price",           "ราคาต้นทุน",         "entry"),
            ("sell_price",      "ราคาขาย (ปลีก)",    "entry"),
            ("price_wholesale", "ราคาส่ง",            "entry"),
            ("price_member",    "ราคาสมาชิก",         "entry"),
            ("unit2",           "หน่วยใหญ่ (เช่น กล่อง)","entry"),
            ("unit2_qty",       "1 หน่วยใหญ่ = กี่ชิ้น","entry"),
        ]:
            row = tk.Frame(pad, bg=CLR["bg"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=FONT, bg=CLR["bg"],
                     fg=CLR["text_lt"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar()
            if widget_type == "combo":
                w = ttk.Combobox(row, textvariable=v, values=cats, font=FONT, width=24)
            else:
                w = tk.Entry(row, textvariable=v, font=FONT, bg=CLR["white"],
                             relief="solid", highlightbackground=CLR["border"],
                             highlightthickness=1)
            w.pack(side="left", fill="x", expand=True, ipady=5)
            self.vars[key] = v

        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=16)
        br = tk.Frame(pad, bg=CLR["bg"])
        br.pack(fill="x")
        btn_primary(br, "💾 บันทึก", self._save).pack(side="right")
        tk.Button(br, text="ยกเลิก", font=FONT, bg=CLR["border"], relief="flat",
                  padx=14, pady=7, cursor="hand2", command=self.destroy).pack(side="right", padx=(0,8))

    def _load(self):
        with get_conn() as conn:
            r = conn.execute(
                "SELECT code,name,category,unit,quantity,min_qty,price,sell_price,price_wholesale,price_member,unit2,unit2_qty FROM products WHERE id=?",
                (self.product_id,)).fetchone()
        if r:
            for key, val in zip(["code","name","category","unit","quantity","min_qty","price","sell_price","price_wholesale","price_member","unit2","unit2_qty"], r):
                self.vars[key].set(val if val is not None else "")

    def _save(self):
        code = self.vars["code"].get().strip()
        name = self.vars["name"].get().strip()
        if not code or not name:
            messagebox.showerror("ผิดพลาด", "กรุณากรอกรหัสและชื่อสินค้า", parent=self)
            return
        try:
            qty        = float(self.vars["quantity"].get()   or 0)
            mq         = float(self.vars["min_qty"].get()    or 0)
            price      = float(self.vars["price"].get()      or 0)
            sell_price = float(self.vars["sell_price"].get() or 0)
            spw        = float(self.vars.get("price_wholesale",tk.StringVar()).get() or 0)
            spm        = float(self.vars.get("price_member",tk.StringVar()).get() or 0)
            u2q        = float(self.vars.get("unit2_qty",tk.StringVar()).get() or 1)
        except ValueError:
            messagebox.showerror("ผิดพลาด", "ตัวเลขไม่ถูกต้อง", parent=self)
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_conn() as conn:
            if self.product_id is None:
                conn.execute("""INSERT INTO products(code,name,category,unit,quantity,min_qty,price,sell_price,price_wholesale,price_member,unit2,unit2_qty,updated)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (code, name, self.vars["category"].get(),
                              self.vars["unit"].get(), qty, mq, price, sell_price,
                              spw, spm, self.vars.get("unit2",tk.StringVar()).get() or None, u2q, now))
            else:
                conn.execute("""UPDATE products SET code=?,name=?,category=?,unit=?,quantity=?,min_qty=?,price=?,sell_price=?,price_wholesale=?,price_member=?,unit2=?,unit2_qty=?,updated=? WHERE id=?""",
                             (code, name, self.vars["category"].get(),
                              self.vars["unit"].get(), qty, mq, price, sell_price,
                              spw, spm, self.vars.get("unit2",tk.StringVar()).get() or None, u2q, now, self.product_id))
            conn.commit()
        self.callback()
        self.destroy()


# ═══════════════════════════════════════════════
#  STOCK IN
# ═══════════════════════════════════════════════
class StockInFrame(tk.Frame):
    NAME = "stock_in"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, "📥 รับสินค้า", "เพิ่มสต็อกสินค้าเข้าคลัง")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        c = card(pad, padx=28, pady=24)
        c.pack(fill="x")

        # Combobox
        row = tk.Frame(c, bg=CLR["card"])
        row.pack(fill="x", pady=6)
        tk.Label(row, text="สินค้า *", font=FONT, bg=CLR["card"],
                 fg=CLR["text_lt"], width=16, anchor="w").pack(side="left")
        self.prod_var = tk.StringVar()
        with get_conn() as conn:
            products = conn.execute("SELECT id,code,name,quantity FROM products ORDER BY name").fetchall()
        self.prod_map = {f"[{p[1]}] {p[2]}  (คงเหลือ: {p[3]:g})": p[0] for p in products}
        ttk.Combobox(row, textvariable=self.prod_var, values=list(self.prod_map.keys()),
                     font=FONT, state="readonly", width=48).pack(side="left", ipady=5)

        self.vars = {}
        for key, label in [("qty","จำนวน *"),("note","หมายเหตุ")]:
            r2 = tk.Frame(c, bg=CLR["card"])
            r2.pack(fill="x", pady=6)
            tk.Label(r2, text=label, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r2, textvariable=v, font=FONT, bg=CLR["white"],
                     relief="solid", width=48, highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", ipady=5)
            self.vars[key] = v

        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=16)
        btn_success(c, "📥 บันทึกการรับสินค้า", self._save).pack(anchor="w")

    def _save(self):
        label = self.prod_var.get()
        if not label:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้า")
            return
        try:
            qty = float(self.vars["qty"].get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("ผิดพลาด", "กรุณากรอกจำนวนที่ถูกต้อง")
            return
        pid  = self.prod_map[label]
        note = self.vars["note"].get()
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_conn() as conn:
            conn.execute("UPDATE products SET quantity=quantity+?, updated=? WHERE id=?", (qty, now, pid))
            conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date) VALUES(?,?,?,?,?)",
                         (pid, "IN", qty, note, now))
            conn.commit()
        messagebox.showinfo("สำเร็จ", f"รับสินค้าเรียบร้อย (+{qty:g})")
        self.refresh()


# ═══════════════════════════════════════════════
#  STOCK OUT
# ═══════════════════════════════════════════════
class StockOutFrame(tk.Frame):
    NAME = "stock_out"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, "📤 จ่ายสินค้า", "ตัดสต็อกสินค้าออกจากคลัง")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        c = card(pad, padx=28, pady=24)
        c.pack(fill="x")

        row = tk.Frame(c, bg=CLR["card"])
        row.pack(fill="x", pady=6)
        tk.Label(row, text="สินค้า *", font=FONT, bg=CLR["card"],
                 fg=CLR["text_lt"], width=16, anchor="w").pack(side="left")
        self.prod_var = tk.StringVar()
        with get_conn() as conn:
            products = conn.execute("SELECT id,code,name,quantity FROM products ORDER BY name").fetchall()
        self.prod_map = {f"[{p[1]}] {p[2]}  (คงเหลือ: {p[3]:g})": p[0] for p in products}
        ttk.Combobox(row, textvariable=self.prod_var, values=list(self.prod_map.keys()),
                     font=FONT, state="readonly", width=48).pack(side="left", ipady=5)

        self.vars = {}
        for key, label in [("qty","จำนวน *"),("note","หมายเหตุ")]:
            r2 = tk.Frame(c, bg=CLR["card"])
            r2.pack(fill="x", pady=6)
            tk.Label(r2, text=label, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"], width=16, anchor="w").pack(side="left")
            v = tk.StringVar()
            tk.Entry(r2, textvariable=v, font=FONT, bg=CLR["white"],
                     relief="solid", width=48, highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", ipady=5)
            self.vars[key] = v

        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=16)
        btn_danger(c, "📤 บันทึกการจ่ายสินค้า", self._save).pack(anchor="w")

    def _save(self):
        label = self.prod_var.get()
        if not label:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้า")
            return
        try:
            qty = float(self.vars["qty"].get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("ผิดพลาด", "กรุณากรอกจำนวนที่ถูกต้อง")
            return
        pid = self.prod_map[label]
        with get_conn() as conn:
            cur = conn.execute("SELECT quantity FROM products WHERE id=?", (pid,)).fetchone()[0]
        if qty > cur:
            messagebox.showerror("ผิดพลาด", f"สินค้าคงเหลือไม่พอ (มี {cur:g} หน่วย)")
            return
        note = self.vars["note"].get()
        now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_conn() as conn:
            conn.execute("UPDATE products SET quantity=quantity-?, updated=? WHERE id=?", (qty, now, pid))
            conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date) VALUES(?,?,?,?,?)",
                         (pid, "OUT", qty, note, now))
            conn.commit()
        messagebox.showinfo("สำเร็จ", f"จ่ายสินค้าเรียบร้อย (-{qty:g})")
        self.refresh()


# ═══════════════════════════════════════════════
#  TRANSACTIONS  (with CSV export)
# ═══════════════════════════════════════════════
class TransactionsFrame(tk.Frame):
    NAME = "transactions"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, "📊 ประวัติการเคลื่อนไหว", "รายการรับ-จ่ายสินค้าทั้งหมด")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        fr = tk.Frame(pad, bg=CLR["bg"])
        fr.pack(fill="x", pady=(0,10))

        tk.Label(fr, text="ประเภท:", font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="left")
        self.type_var = tk.StringVar(value="ทั้งหมด")
        cb = ttk.Combobox(fr, textvariable=self.type_var,
                          values=["ทั้งหมด","IN","OUT"], font=FONT, state="readonly", width=12)
        cb.pack(side="left", padx=8, ipady=4)
        cb.bind("<<ComboboxSelected>>", lambda _: self._load())

        tk.Frame(fr, bg=CLR["bg"], width=20).pack(side="left")
        btn_warn(fr, "📊 Export CSV", self._export).pack(side="left")

        cols = ("วันที่","รหัส","ชื่อสินค้า","ประเภท","จำนวน","หมายเหตุ")
        wrap, self.tv = make_tree(pad, cols, [150,90,200,80,80,260], height=22)
        wrap.pack(fill="both", expand=True)
        self.tv.tag_configure("IN",  foreground=CLR["success"])
        self.tv.tag_configure("OUT", foreground=CLR["danger"])
        self._load()

    def _load(self):
        self.tv.delete(*self.tv.get_children())
        t = self.type_var.get()
        sql = """SELECT t.date,p.code,p.name,t.type,t.quantity,t.note
                 FROM transactions t JOIN products p ON t.product_id=p.id"""
        params = ()
        if t != "ทั้งหมด":
            sql += " WHERE t.type=?"
            params = (t,)
        sql += " ORDER BY t.date DESC LIMIT 500"
        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        for r in rows:
            sign = "+" if r[3] == "IN" else "-"
            self.tv.insert("", "end",
                           values=(r[0],r[1],r[2],r[3],f"{sign}{r[4]:g}",r[5] or "-"),
                           tags=(r[3],))

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files","*.csv")],
            initialfile=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if not path: return
        t = self.type_var.get()
        sql = """SELECT t.date,p.code,p.name,t.type,t.quantity,t.note
                 FROM transactions t JOIN products p ON t.product_id=p.id"""
        params = ()
        if t != "ทั้งหมด":
            sql += " WHERE t.type=?"
            params = (t,)
        sql += " ORDER BY t.date DESC"
        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["วันที่","รหัส","ชื่อสินค้า","ประเภท","จำนวน","หมายเหตุ"])
            for r in rows:
                sign = "+" if r[3]=="IN" else "-"
                w.writerow([r[0],r[1],r[2],r[3],f"{sign}{r[4]:g}",r[5] or ""])
        messagebox.showinfo("สำเร็จ", f"Export สำเร็จ\n{path}")


# ═══════════════════════════════════════════════
#  CHARTS
# ═══════════════════════════════════════════════
class ChartsFrame(tk.Frame):
    NAME = "charts"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        if not HAS_MPL:
            tk.Label(self, text="❌ กรุณาติดตั้ง matplotlib\npip install matplotlib",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(expand=True)
            return
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)

        page_title(pad, "📈 กราฟสถิติ", "วิเคราะห์สต็อกและการเคลื่อนไหวสินค้า")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        # Tab selector
        sel_row = tk.Frame(pad, bg=CLR["bg"])
        sel_row.pack(fill="x", pady=(0,12))

        self._chart_var = tk.StringVar(value="stock")
        charts = [
            ("stock",   "📦 Top สต็อก"),
            ("value",   "💰 มูลค่าตาม Category"),
            ("txn",     "📊 IN/OUT รายวัน"),
            ("cat_pie", "🥧 สัดส่วน Category"),
        ]
        for val, label in charts:
            rb = tk.Radiobutton(sel_row, text=label, variable=self._chart_var, value=val,
                                font=FONT_B, bg=CLR["bg"], fg=CLR["text"],
                                selectcolor=CLR["accent"], activebackground=CLR["bg"],
                                cursor="hand2", command=self._draw)
            rb.pack(side="left", padx=(0,12))

        # Canvas area
        self._canvas_frame = tk.Frame(pad, bg=CLR["bg"])
        self._canvas_frame.pack(fill="both", expand=True)
        self._draw()

    def _draw(self):
        for w in self._canvas_frame.winfo_children(): w.destroy()
        chart = self._chart_var.get()
        fig = Figure(figsize=(11, 5.5), dpi=96, facecolor=CLR["bg"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor("#F8FAFC")
        for spine in ax.spines.values():
            spine.set_edgecolor(CLR["border"])

        if chart == "stock":
            self._chart_top_stock(ax)
        elif chart == "value":
            self._chart_value_by_cat(ax)
        elif chart == "txn":
            self._chart_txn_daily(ax)
        elif chart == "cat_pie":
            self._chart_cat_pie(fig, ax)

        fig.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(fig, master=self._canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _chart_top_stock(self, ax):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT name, quantity FROM products ORDER BY quantity DESC LIMIT 15"
            ).fetchall()
        if not rows:
            ax.text(0.5, 0.5, "ไม่มีข้อมูล", ha="center", va="center", fontsize=14); return
        names  = [r[0][:20] for r in rows]
        qtys   = [r[1] for r in rows]
        colors = [CLR["danger"] if q == 0 else (CLR["warning"] if q < 10 else CLR["accent"])
                  for q in qtys]
        bars = ax.barh(names[::-1], qtys[::-1], color=colors[::-1], height=0.6)
        ax.set_xlabel("จำนวนคงเหลือ", fontsize=10)
        ax.set_title("Top 15 สินค้าตามจำนวนสต็อก", fontsize=13, fontweight="bold", pad=12)
        for bar, val in zip(bars, qtys[::-1]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                    f"{val:g}", va="center", fontsize=9)

    def _chart_value_by_cat(self, ax):
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT COALESCE(category,'ไม่ระบุ'), SUM(quantity*price)
                FROM products GROUP BY category ORDER BY 2 DESC
            """).fetchall()
        if not rows:
            ax.text(0.5, 0.5, "ไม่มีข้อมูล", ha="center", va="center", fontsize=14); return
        cats = [r[0] for r in rows]
        vals = [r[1] for r in rows]
        palette = ["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#06B6D4","#F97316"]
        bars = ax.bar(cats, vals, color=[palette[i % len(palette)] for i in range(len(cats))], width=0.5)
        ax.set_ylabel("มูลค่ารวม (บาท)", fontsize=10)
        ax.set_title("มูลค่าสต็อกแยกตามหมวดหมู่", fontsize=13, fontweight="bold", pad=12)
        ax.tick_params(axis="x", rotation=30)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.01,
                    f"{val:,.0f}", ha="center", fontsize=9)

    def _chart_txn_daily(self, ax):
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT substr(date,1,10) as d, type, SUM(quantity)
                FROM transactions GROUP BY d, type ORDER BY d DESC LIMIT 60
            """).fetchall()
        if not rows:
            ax.text(0.5, 0.5, "ไม่มีข้อมูล", ha="center", va="center", fontsize=14); return
        dates_in  = {}; dates_out = {}
        for d, t, q in rows:
            if t == "IN":  dates_in[d]  = q
            else:           dates_out[d] = q
        all_dates = sorted(set(list(dates_in.keys()) + list(dates_out.keys())))[-30:]
        ins  = [dates_in.get(d, 0)  for d in all_dates]
        outs = [dates_out.get(d, 0) for d in all_dates]
        x = range(len(all_dates))
        ax.bar([i - 0.2 for i in x], ins,  width=0.38, label="รับเข้า",  color=CLR["success"], alpha=0.85)
        ax.bar([i + 0.2 for i in x], outs, width=0.38, label="จ่ายออก", color=CLR["danger"],  alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels([d[5:] for d in all_dates], rotation=45, fontsize=8)
        ax.set_ylabel("จำนวน", fontsize=10)
        ax.set_title("การรับ-จ่ายสินค้ารายวัน (30 วันล่าสุด)", fontsize=13, fontweight="bold", pad=12)
        ax.legend(fontsize=10)

    def _chart_cat_pie(self, fig, ax):
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT COALESCE(category,'ไม่ระบุ'), COUNT(*)
                FROM products GROUP BY category ORDER BY 2 DESC
            """).fetchall()
        if not rows:
            ax.text(0.5, 0.5, "ไม่มีข้อมูล", ha="center", va="center", fontsize=14); return
        labels = [r[0] for r in rows]
        sizes  = [r[1] for r in rows]
        palette = ["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#06B6D4","#F97316","#EC4899"]
        wedge_props = {"edgecolor": "white", "linewidth": 2}
        ax.pie(sizes, labels=labels, autopct="%1.1f%%",
               colors=[palette[i % len(palette)] for i in range(len(labels))],
               wedgeprops=wedge_props, startangle=90, textprops={"fontsize": 10})
        ax.set_title("สัดส่วนสินค้าแยกตามหมวดหมู่", fontsize=13, fontweight="bold", pad=12)


# ════════════════════════════════════════════════
#  USER MANAGEMENT FRAME (admin only)
# ════════════════════════════════════════════════
class UsersFrame(tk.Frame):
    NAME = "users"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"])
        if self.app.current_user["role"] != "admin":
            tk.Label(self, text="⛔ เฉพาะ Admin เท่านั้น",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(expand=True)
            return
        self._build()
        self._load()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)

        page_title(pad, "👥 จัดการผู้ใช้งาน", "เพิ่ม/ลบ/แก้ไขบัญชีผู้ใช้ในระบบ")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        # Add user card
        ac = card(pad, padx=22, pady=16)
        ac.pack(fill="x", pady=(0, 12))
        tk.Label(ac, text="เพิ่มผู้ใช้ใหม่", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).grid(row=0, column=0, columnspan=9, sticky="w", pady=(0,10))

        self._vars = {}
        fields = [("username","ชื่อผู้ใช้",14),("fullname","ชื่อ-นามสกุล",18),("password","รหัสผ่าน",14)]
        for col, (key, lbl, w) in enumerate(fields):
            tk.Label(ac, text=lbl, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"]).grid(row=1, column=col*2, sticky="w", padx=(0,4))
            v = tk.StringVar()
            show = "•" if key == "password" else ""
            tk.Entry(ac, textvariable=v, font=FONT, width=w, show=show,
                     bg=CLR["entry_bg"], fg=CLR["text"], insertbackground=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).grid(row=1, column=col*2+1, padx=(0,12), ipady=5)
            self._vars[key] = v

        self._role_var = tk.StringVar(value="staff")
        tk.Label(ac, text="สิทธิ์", font=FONT, bg=CLR["card"],
                 fg=CLR["text_lt"]).grid(row=1, column=6, sticky="w")
        ttk.Combobox(ac, textvariable=self._role_var, values=["admin","staff"],
                     font=FONT, state="readonly", width=8
                     ).grid(row=1, column=7, padx=(4,12), ipady=4)
        btn_primary(ac, "➕ เพิ่ม", self._add).grid(row=1, column=8, padx=(8,0))

        # Table
        cols = ("id","ชื่อผู้ใช้","ชื่อ-นามสกุล","สิทธิ์","วันที่สร้าง")
        wrap, self.tv = make_tree(pad, cols, [0,140,200,80,160], height=13)
        self.tv.column("id", width=0, stretch=False)
        ab = tk.Frame(pad, bg=CLR["bg"])
        ab.pack(fill="x", pady=(10,0))
        wrap.pack(fill="both", expand=True)
        self.tv.bind("<Double-1>", lambda _: self._edit())

        btn_primary(ab, "✏️ แก้ไข", self._edit).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=8).pack(side="left")
        btn_warn(ab, "🔑 เปลี่ยนรหัสผ่าน", self._change_pw).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=8).pack(side="left")
        btn_danger(ab, "🗑️ ลบผู้ใช้", self._delete).pack(side="left")
        tk.Label(ab, text="💡 ดับเบิลคลิกเพื่อแก้ไข",
                 font=("Segoe UI",9), bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="right")

    def _load(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            for r in conn.execute(
                "SELECT id,username,fullname,role,created FROM users ORDER BY id"
            ).fetchall():
                self.tv.insert("", "end", values=r)

    def _add(self):
        uname = self._vars["username"].get().strip()
        pw    = self._vars["password"].get()
        full  = self._vars["fullname"].get().strip()
        role  = self._role_var.get()
        if not uname or not pw:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return
        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO users(username,password,role,fullname,created) VALUES(?,?,?,?,?)",
                    (uname, hash_pw(pw), role, full,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            for v in self._vars.values(): v.set("")
            self._load()
        except Exception:
            messagebox.showerror("ผิดพลาด", f"ชื่อผู้ใช้ '{uname}' มีอยู่แล้ว")

    def _sel_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกผู้ใช้ก่อน")
            return None, None
        vals = self.tv.item(sel[0])["values"]
        return vals[0], vals[1]

    def _edit(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกผู้ใช้ก่อน"); return
        uid, uname, fullname, role, _ = self.tv.item(sel[0])["values"]

        dlg = tk.Toplevel(self)
        dlg.title(f"แก้ไขผู้ใช้ — {uname}")
        dlg.geometry("380x260")
        dlg.configure(bg=CLR["bg"])
        dlg.resizable(False, False)
        dlg.grab_set()

        pad = tk.Frame(dlg, bg=CLR["bg"], padx=24, pady=20)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text=f"แก้ไขข้อมูล: {uname}", font=FONT_H,
                 bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w", pady=(0,14))

        ev = {}
        for key, label, show in [("fullname","ชื่อ-นามสกุล",""),("password","รหัสผ่านใหม่ (ว่าง=ไม่เปลี่ยน)","•")]:
            tk.Label(pad, text=label, font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(anchor="w")
            v = tk.StringVar(value=fullname if key=="fullname" else "")
            tk.Entry(pad, textvariable=v, show=show, font=FONT,
                     bg=CLR["entry_bg"], fg=CLR["text"], insertbackground=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).pack(fill="x", ipady=6, pady=(2,10))
            ev[key] = v

        rv = tk.StringVar(value=role)
        rf = tk.Frame(pad, bg=CLR["bg"])
        rf.pack(fill="x", pady=(0,14))
        tk.Label(rf, text="สิทธิ์:", font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="left")
        ttk.Combobox(rf, textvariable=rv, values=["admin","staff"],
                     font=FONT, state="readonly", width=12).pack(side="left", padx=8, ipady=4)

        def save():
            new_full = ev["fullname"].get().strip()
            new_pw   = ev["password"].get()
            new_role = rv.get()
            with get_conn() as conn:
                conn.execute("UPDATE users SET fullname=?, role=? WHERE id=?",
                             (new_full, new_role, uid))
                if new_pw:
                    conn.execute("UPDATE users SET password=? WHERE id=?",
                                 (hash_pw(new_pw), uid))
                conn.commit()
            self._load()
            dlg.destroy()

        br = tk.Frame(pad, bg=CLR["bg"])
        br.pack(fill="x")
        btn_primary(br, "💾 บันทึก", save).pack(side="right")
        tk.Button(br, text="ยกเลิก", font=FONT, bg=CLR["border"], fg=CLR["text"],
                  relief="flat", padx=14, pady=7, cursor="hand2",
                  command=dlg.destroy).pack(side="right", padx=(0,8))

    def _delete(self):
        uid, uname = self._sel_id()
        if uid is None: return
        if uname == "admin":
            messagebox.showerror("ผิดพลาด", "ไม่สามารถลบบัญชี admin ได้")
            return
        if messagebox.askyesno("ยืนยัน", f"ลบผู้ใช้ '{uname}' ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM users WHERE id=?", (uid,))
                conn.commit()
            self._load()

    def _change_pw(self):
        uid, uname = self._sel_id()
        if uid is None: return
        dlg = tk.Toplevel(self)
        dlg.title(f"เปลี่ยนรหัสผ่าน — {uname}")
        dlg.geometry("320x200")
        dlg.configure(bg=CLR["bg"])
        dlg.grab_set()
        pad = tk.Frame(dlg, bg=CLR["bg"], padx=24, pady=20)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text=f"เปลี่ยนรหัสผ่านของ: {uname}", font=FONT_B,
                 bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))
        pv = tk.StringVar()
        tk.Label(pad, text="รหัสผ่านใหม่", font=FONT, bg=CLR["bg"],
                 fg=CLR["text_lt"]).pack(anchor="w")
        tk.Entry(pad, textvariable=pv, show="•", font=FONT,
                 bg=CLR["entry_bg"], fg=CLR["text"], insertbackground=CLR["text"],
                 relief="solid", highlightbackground=CLR["border"], highlightthickness=1
                 ).pack(fill="x", ipady=6, pady=(4,12))
        def save():
            pw2 = pv.get()
            if not pw2:
                messagebox.showwarning("แจ้งเตือน", "กรุณากรอกรหัสผ่าน", parent=dlg); return
            with get_conn() as conn:
                conn.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(pw2), uid))
                conn.commit()
            messagebox.showinfo("สำเร็จ", "เปลี่ยนรหัสผ่านสำเร็จ", parent=dlg)
            dlg.destroy()
        btn_primary(pad, "💾 บันทึก", save).pack(anchor="w")


# ════════════════════════════════════════════════
#  MAIN APP WINDOW
# ════════════════════════════════════════════════
class StockApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self._current_page = "dashboard"
        self.title(f"📦 Stock Manager Pro  —  {user['fullname']}  [{user['role'].upper()}]")
        self.geometry("1340x780")
        self.minsize(1000, 640)
        self.configure(bg=CLR["bg"])
        self._build_ui()
        self.show_frame("dashboard")

    # ─── build sidebar + content ────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sb_frame = tk.Frame(self, bg=CLR["sidebar"], width=130)
        self._sb_frame.grid(row=0, column=0, sticky="nsew")
        self._sb_frame.grid_propagate(False)
        self.content = tk.Frame(self, bg=CLR["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_frames()
        self.bind('<Control-l>',lambda _:self._lock_screen())
        self.bind('<Control-L>',lambda _:self._lock_screen())

    def _build_sidebar(self):
        sb = self._sb_frame
        for w in sb.winfo_children(): w.destroy()

        tk.Label(sb, text="📦", font=("Segoe UI", 28),
                 bg=CLR["sidebar"], fg=CLR["white"]).pack(pady=(24,0))
        tk.Label(sb, text="Stock Manager Pro",
                 font=("Segoe UI", 11, "bold"),
                 bg=CLR["sidebar"], fg=CLR["white"]).pack(pady=(4,4))

        role_color = "#FCD34D" if self.current_user["role"] == "admin" else "#94A3B8"
        tk.Label(sb, text=f"👤 {self.current_user['fullname']}",
                 font=("Segoe UI", 9), bg=CLR["sidebar"],
                 fg=role_color).pack(pady=(0, 16))

        # Dark mode toggle
        theme_lbl = "☀️  Light Mode" if _current_theme == "dark" else "🌙  Dark Mode"
        tk.Button(sb, text=theme_lbl, font=("Segoe UI", 9),
                  bg=CLR["sidebar_h"], fg=CLR["white"],
                  activebackground=CLR["sidebar"], activeforeground=CLR["white"],
                  relief="flat", anchor="w", padx=22, pady=6, cursor="hand2",
                  command=self._toggle_theme).pack(fill="x", pady=(0,10))

        self._nav_btns = {}
        nav_items = [
            ("dashboard",    "🏠  Dashboard"),
            ("products",     "📋  สินค้า"),
            ("categories",   "📁  หมวดหมู่"),
            ("stock_in",     "📥  รับสินค้า"),
            ("stock_out",    "📤  จ่ายสินค้า"),
            ("transactions", "📊  ประวัติ"),
            ("barcode",      "🔲  Barcode"),
            ("charts",       "📈  กราฟสถิติ"),
            ("users",        "👥  ผู้ใช้งาน"),
        ]
        for key, label in nav_items:
            b = tk.Button(sb, text=label, font=("Segoe UI", 11),
                          bg=CLR["accent"] if key == self._current_page else CLR["sidebar"],
                          fg=CLR["white"],
                          activebackground=CLR["sidebar_h"],
                          activeforeground=CLR["white"],
                          relief="flat", anchor="w", padx=22, pady=10,
                          cursor="hand2",
                          command=lambda k=key: self.show_frame(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        tk.Frame(sb, bg="#0F172A", height=1).pack(fill="x", pady=(20,0))
        tk.Button(sb, text="🚪  ออกจากระบบ", font=("Segoe UI", 10),
                  bg=CLR["sidebar"], fg="#F87171",
                  activebackground="#7F1D1D", activeforeground=CLR["white"],
                  relief="flat", anchor="w", padx=22, pady=10, cursor="hand2",
                  command=self._logout).pack(fill="x", side="bottom")
        tk.Button(sb, text="🔒 ล็อค  Ctrl+L",
                  font=("Segoe UI",8), bg=CLR["sidebar"], fg="#64748B",
                  activebackground=CLR["sidebar_h"], activeforeground=CLR["white"],
                  relief="flat", anchor="w", padx=12, pady=5, cursor="hand2",
                  command=self._lock_screen).pack(fill="x", side="bottom")

    def _build_frames(self):
        self.frames = {}
        for F in (DashboardFrame, ProductsFrame, CategoriesFrame,
                  StockInFrame, StockOutFrame, TransactionsFrame,
                  BarcodeFrame, ChartsFrame, UsersFrame):
            frame = F(self.content, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[F.NAME] = frame

    def show_frame(self, name):
        self._current_page = name
        for key, btn in self._nav_btns.items():
            btn.configure(bg=CLR["accent"] if key == name else CLR["sidebar"],
                          fg=CLR["white"])
        self.frames[name].refresh()
        self.frames[name].tkraise()

    def _toggle_theme(self):
        new_theme = "dark" if _current_theme == "light" else "light"
        set_theme(new_theme)
        set_setting("app_theme", new_theme)
        self.configure(bg=CLR["bg"])
        self.content.configure(bg=CLR["bg"])
        self._build_sidebar()
        self.show_frame(self._current_page)

    def _lock_screen(self):
        audit(self.current_user["username"],"LOCK_SCREEN")
        ScreenLockWindow(self)
    def _logout(self):
        if messagebox.askyesno("ยืนยัน","ต้องการออกจากระบบใช่ไหม?"):
            audit(self.current_user["username"],"LOGOUT")
            self.destroy(); _run_app()


# ════════════════════════════════════════════════
#  Override StockIn/StockOut to record user
# ════════════════════════════════════════════════
_orig_stock_in_save  = StockInFrame._save
_orig_stock_out_save = StockOutFrame._save

def _stock_in_save_v3(self):
    label = self.prod_var.get()
    if not label:
        messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้า"); return
    try:
        qty = float(self.vars["qty"].get())
        if qty <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("ผิดพลาด", "กรุณากรอกจำนวนที่ถูกต้อง"); return
    pid  = self.prod_map[label]
    note = self.vars["note"].get()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = self.app.current_user["username"]
    with get_conn() as conn:
        conn.execute("UPDATE products SET quantity=quantity+?, updated=? WHERE id=?", (qty, now, pid))
        conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date,user) VALUES(?,?,?,?,?,?)",
                     (pid, "IN", qty, note, now, user))
        conn.commit()
    messagebox.showinfo("สำเร็จ", f"รับสินค้าเรียบร้อย (+{qty:g})")
    self.refresh()

def _stock_out_save_v3(self):
    label = self.prod_var.get()
    if not label:
        messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้า"); return
    try:
        qty = float(self.vars["qty"].get())
        if qty <= 0: raise ValueError
    except ValueError:
        messagebox.showerror("ผิดพลาด", "กรุณากรอกจำนวนที่ถูกต้อง"); return
    pid = self.prod_map[label]
    with get_conn() as conn:
        cur = conn.execute("SELECT quantity FROM products WHERE id=?", (pid,)).fetchone()[0]
    if qty > cur:
        messagebox.showerror("ผิดพลาด", f"สินค้าคงเหลือไม่พอ (มี {cur:g} หน่วย)"); return
    note = self.vars["note"].get()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = self.app.current_user["username"]
    with get_conn() as conn:
        conn.execute("UPDATE products SET quantity=quantity-?, updated=? WHERE id=?", (qty, now, pid))
        conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date,user) VALUES(?,?,?,?,?,?)",
                     (pid, "OUT", qty, note, now, user))
        conn.commit()
    messagebox.showinfo("สำเร็จ", f"จ่ายสินค้าเรียบร้อย (-{qty:g})")
    self.refresh()

StockInFrame._save  = _stock_in_save_v3
StockOutFrame._save = _stock_out_save_v3


# ── Also upgrade TransactionsFrame to show user + PDF export ────────────────
_orig_txn_build = TransactionsFrame._build

def _txn_build_v3(self):
    pad = tk.Frame(self, bg=CLR["bg"])
    pad.pack(fill="both", expand=True, padx=30, pady=24)
    page_title(pad, "📊 ประวัติการเคลื่อนไหว", "รายการรับ-จ่ายสินค้าทั้งหมด")
    tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

    fr = tk.Frame(pad, bg=CLR["bg"])
    fr.pack(fill="x", pady=(0,10))
    tk.Label(fr, text="ประเภท:", font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="left")
    self.type_var = tk.StringVar(value="ทั้งหมด")
    cb = ttk.Combobox(fr, textvariable=self.type_var,
                      values=["ทั้งหมด","IN","OUT"], font=FONT, state="readonly", width=12)
    cb.pack(side="left", padx=8, ipady=4)
    cb.bind("<<ComboboxSelected>>", lambda _: self._load())
    tk.Frame(fr, bg=CLR["bg"], width=12).pack(side="left")
    btn_warn(fr, "📊 Export CSV", self._export).pack(side="left")
    tk.Frame(fr, bg=CLR["bg"], width=8).pack(side="left")
    btn_danger(fr, "📄 Export PDF", self._export_pdf).pack(side="left")

    cols = ("วันที่","รหัส","ชื่อสินค้า","ประเภท","จำนวน","ผู้ดำเนินการ","หมายเหตุ")
    wrap, self.tv = make_tree(pad, cols, [150,90,190,80,80,110,230], height=20)
    wrap.pack(fill="both", expand=True)
    self.tv.tag_configure("IN",  foreground=CLR["success"])
    self.tv.tag_configure("OUT", foreground=CLR["danger"])
    self._load()

def _txn_load_v3(self):
    self.tv.delete(*self.tv.get_children())
    t = self.type_var.get()
    sql = """SELECT t.date,p.code,p.name,t.type,t.quantity,
                    COALESCE(t.user,'-'),t.note
             FROM transactions t JOIN products p ON t.product_id=p.id"""
    params = ()
    if t != "ทั้งหมด":
        sql += " WHERE t.type=?"
        params = (t,)
    sql += " ORDER BY t.date DESC LIMIT 500"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    for r in rows:
        sign = "+" if r[3] == "IN" else "-"
        self.tv.insert("", "end",
                       values=(r[0],r[1],r[2],r[3],f"{sign}{r[4]:g}",r[5],r[6] or "-"),
                       tags=(r[3],))

def _txn_export_pdf(self):
    if not HAS_RL:
        messagebox.showerror("ผิดพลาด", "ต้องการ reportlab: pip install reportlab")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
        initialfile=f"transactions_{datetime.now().strftime('%Y%m%d')}.pdf")
    if not path: return
    t = self.type_var.get()
    sql = """SELECT t.date,p.code,p.name,t.type,t.quantity,
                    COALESCE(t.user,'-'),COALESCE(t.note,'-')
             FROM transactions t JOIN products p ON t.product_id=p.id"""
    params = ()
    if t != "ทั้งหมด":
        sql += " WHERE t.type=?"
        params = (t,)
    sql += " ORDER BY t.date DESC LIMIT 1000"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    fmt_rows = []
    for r in rows:
        sign = "+" if r[3]=="IN" else "-"
        fmt_rows.append((r[0],r[1],r[2],r[3],f"{sign}{r[4]:g}",r[5],r[6]))
    _make_pdf_transactions(path, fmt_rows)
    messagebox.showinfo("สำเร็จ", f"Export PDF สำเร็จ\n{path}")

TransactionsFrame._build      = _txn_build_v3
TransactionsFrame._load       = _txn_load_v3
TransactionsFrame._export_pdf = _txn_export_pdf


# ── PDF export button in ProductsFrame ──────────────────────────────────────
_orig_products_build = ProductsFrame._build

def _products_build_v3(self):
    pad = tk.Frame(self, bg=CLR["bg"])
    pad.pack(fill="both", expand=True, padx=30, pady=24)
    self._pad = pad
    page_title(pad, "📋 สินค้า", "จัดการข้อมูลสินค้าในคลัง")
    tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

    tb = tk.Frame(pad, bg=CLR["bg"])
    tb.pack(fill="x", pady=(0,10))
    btn_primary(tb, "➕ เพิ่มสินค้า", self._add).pack(side="left")
    tk.Frame(tb, bg=CLR["bg"], width=8).pack(side="left")
    btn_warn(tb, "📊 Export CSV", self._export_csv).pack(side="left")
    tk.Frame(tb, bg=CLR["bg"], width=8).pack(side="left")
    btn_danger(tb, "📄 Export PDF", self._export_pdf).pack(side="left")
    tk.Frame(tb, bg=CLR["bg"], width=16).pack(side="left")

    tk.Label(tb, text="หมวดหมู่:", font=FONT, bg=CLR["bg"], fg=CLR["text_lt"]).pack(side="left")
    cats = ["ทั้งหมด"] + self._get_cats()
    self._cat_filter.set("ทั้งหมด")
    cb = ttk.Combobox(tb, textvariable=self._cat_filter,
                      values=cats, font=FONT, state="readonly", width=18)
    cb.pack(side="left", padx=8, ipady=4)
    cb.bind("<<ComboboxSelected>>", lambda _: self._load())

    sf = tk.Frame(tb, bg=CLR["card"], highlightbackground=CLR["border"], highlightthickness=1)
    sf.pack(side="left", padx=8)
    tk.Label(sf, text="🔍", bg=CLR["card"], font=FONT).pack(side="left", padx=(8,0))
    tk.Entry(sf, textvariable=self._search_var, font=FONT,
             bg=CLR["card"], relief="flat", width=24).pack(side="left", padx=6, pady=6)

    cols = ("id","รหัส","ชื่อสินค้า","หมวดหมู่","หน่วย","คงเหลือ","ขั้นต่ำ","ราคา/หน่วย")
    wrap, self.tv = make_tree(pad, cols, [0,80,210,120,70,90,80,110])
    self.tv.column("id", width=0, stretch=False)
    ab = tk.Frame(pad, bg=CLR["bg"])
    ab.pack(fill="x", pady=(10,0))
    wrap.pack(fill="both", expand=True)
    self.tv.tag_configure("low",  background="#FEF9C3")
    self.tv.tag_configure("zero", background="#FEE2E2")

    btn_primary(ab, "✏️ แก้ไข", self._edit).pack(side="left")
    tk.Frame(ab, bg=CLR["bg"], width=8).pack(side="left")
    btn_danger(ab, "🗑️ ลบ", self._delete).pack(side="left")

def _products_export_pdf(self):
    if not HAS_RL:
        messagebox.showerror("ผิดพลาด", "ต้องการ reportlab: pip install reportlab")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
        initialfile=f"stock_report_{datetime.now().strftime('%Y%m%d')}.pdf")
    if not path: return
    kw  = f"%{self._search_var.get()}%"
    cat = self._cat_filter.get()
    sql = """SELECT code,name,category,unit,quantity,min_qty,price
             FROM products WHERE (name LIKE ? OR code LIKE ? OR category LIKE ?)"""
    params = [kw, kw, kw]
    if cat != "ทั้งหมด":
        sql += " AND category=?"
        params.append(cat)
    sql += " ORDER BY name"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    fmt = []
    for r in rows:
        val = r[4] * r[6]
        fmt.append((r[0], r[1], r[2] or "-", r[3] or "-",
                    f"{r[4]:g}", f"{r[5]:g}", f"{r[6]:,.2f}", f"{val:,.2f}"))
    _make_pdf_stock(path, fmt)
    messagebox.showinfo("สำเร็จ", f"Export PDF สำเร็จ\n{path}")

ProductsFrame._build      = _products_build_v3
ProductsFrame._export_pdf = _products_export_pdf


# ══════════════════════════════════════════════════════
#  HELPER: auto-number generator
# ══════════════════════════════════════════════════════
def next_number(prefix, table, col):
    today = datetime.now().strftime("%Y%m%d")
    like  = f"{prefix}-{today}-%"
    with get_conn() as conn:
        row = conn.execute(f"SELECT {col} FROM {table} WHERE {col} LIKE ? ORDER BY {col} DESC LIMIT 1",
                           (like,)).fetchone()
    seq = 1
    if row:
        try: seq = int(row[0].split("-")[-1]) + 1
        except: pass
    return f"{prefix}-{today}-{seq:03d}"


# ══════════════════════════════════════════════════════
#  PROMPTPAY QR HELPER
# ══════════════════════════════════════════════════════

def audit(user, action, detail=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("INSERT INTO audit_log(user,action,detail,date) VALUES(?,?,?,?)", (user,action,detail,now))
        conn.commit()

class ScreenLockWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app); self.app=app
        self.title("🔒 ล็อคหน้าจอ")
        self.attributes("-fullscreen",True); self.attributes("-topmost",True)
        self.configure(bg="#0F172A"); self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda:None)
        pad=tk.Frame(self,bg="#0F172A"); pad.place(relx=0.5,rely=0.5,anchor="center")
        tk.Label(pad,text="🔒",font=("Segoe UI",64),bg="#0F172A",fg="#3B82F6").pack(pady=(0,8))
        tk.Label(pad,text="หน้าจอถูกล็อค",font=("Segoe UI",22,"bold"),bg="#0F172A",fg="white").pack()
        tk.Label(pad,text=f"👤 {app.current_user['fullname']}",font=("Segoe UI",12),bg="#0F172A",fg="#94A3B8").pack(pady=(4,24))
        tk.Label(pad,text="กรอกรหัสผ่านเพื่อปลดล็อค",font=("Segoe UI",11),bg="#0F172A",fg="#64748B").pack()
        self._pw=tk.StringVar()
        e=tk.Entry(pad,textvariable=self._pw,font=("Segoe UI",14),show="●",width=24,
                   justify="center",bg="#1E293B",fg="white",insertbackground="white",
                   relief="flat",highlightbackground="#3B82F6",highlightthickness=2)
        e.pack(pady=12,ipady=10); e.focus_set()
        e.bind("<Return>",lambda _:self._unlock())
        self._msg=tk.Label(pad,text="",font=("Segoe UI",10),bg="#0F172A",fg="#F87171"); self._msg.pack()
        tk.Button(pad,text="🔓 ปลดล็อค",font=("Segoe UI",12,"bold"),bg="#3B82F6",fg="white",
                  relief="flat",padx=32,pady=10,cursor="hand2",command=self._unlock).pack(pady=(12,0))
    def _unlock(self):
        pw=self._pw.get()
        uid=self.app.current_user["id"]
        with get_conn() as conn:
            r=conn.execute("SELECT password FROM users WHERE id=?",(uid,)).fetchone()
        if r and r[0]==hash_pw(pw):
            audit(self.app.current_user["username"],"UNLOCK_SCREEN")
            self.grab_release(); self.destroy()
        else:
            self._msg.config(text="รหัสผ่านไม่ถูกต้อง"); self._pw.set("")


def _make_promptpay_qr(account: str, amount: float = 0) -> str:
    """Generate PromptPay EMV QR string (phone or national ID)."""
    def crc16(data: bytes) -> str:
        crc = 0xFFFF
        for b in data:
            crc ^= b << 8
            for _ in range(8):
                crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
        return format(crc, "04X")

    def tlv(tag: str, val: str) -> str:
        return f"{tag}{len(val):02d}{val}"

    # Normalize account
    acct = account.strip().replace("-", "").replace(" ", "")
    if acct.startswith("0") and len(acct) == 10:          # phone
        target_id = f"0066{acct[1:]}"
        guid = "A000000677010111"
    else:                                                   # national ID / tax ID
        target_id = acct
        guid = "A000000677010111"

    aid  = tlv("00", guid)
    tid  = tlv("01", target_id)
    maid = tlv("29", aid + tid)

    parts = (
        tlv("00", "01") +           # Payload format
        tlv("01", "11") +           # Static QR
        maid +
        tlv("53", "764") +          # THB
        (tlv("54", f"{amount:.2f}") if amount > 0 else "") +
        tlv("58", "TH") +
        tlv("59", "N/A") +
        tlv("60", "Bangkok")
    )
    raw = parts + "6304"
    return raw + crc16(raw.encode("ascii"))


# ══════════════════════════════════════════════════════
#  SHOP SETTINGS FRAME  (Admin only)
# ══════════════════════════════════════════════════════
class ShopSettingsFrame(tk.Frame):
    NAME = "shop_settings"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"])
        self._build()

    def _build(self):
        is_admin = self.app.current_user["role"] == "admin"
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, T("settings_title"), T("settings_sub"))
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=10)

        # ── Tab strip ───────────────────────────────────────
        tabs = [
            ("shop",     T("tab_shop")),
            ("bank",     T("tab_bank")),
            ("theme",    T("tab_theme")),
            ("language", T("tab_language")),
            ("users_mgmt", "👥 ผู้ใช้งาน"),
            ("backup",   "💾 Backup/Restore"),
            ("system",   T("tab_system")),
        ]
        self._active_tab = tk.StringVar(value="shop")
        tab_bar = tk.Frame(pad, bg=CLR["card"],
                           highlightbackground=CLR["border"], highlightthickness=1)
        tab_bar.pack(fill="x", pady=(0,14))
        self._tab_btns = {}
        for key, label in tabs:
            b = tk.Button(tab_bar, text=label, font=FONT_B,
                          bg=CLR["accent"], fg=CLR["white"],
                          activebackground=CLR["accent_dk"],
                          relief="flat", padx=16, pady=8, cursor="hand2",
                          command=lambda k=key: self._switch_tab(k))
            b.pack(side="left")
            self._tab_btns[key] = b

        # Content area (changes per tab)
        self._content = tk.Frame(pad, bg=CLR["bg"])
        self._content.pack(fill="both", expand=True)
        self._is_admin = is_admin
        self._switch_tab("shop")

    def _switch_tab(self, key):
        self._active_tab.set(key)
        # Update tab button colours
        for k, b in self._tab_btns.items():
            b.configure(bg=CLR["accent"] if k==key else CLR["card"],
                        fg=CLR["white"]  if k==key else CLR["text_lt"])
        for w in self._content.winfo_children():
            w.destroy()
        getattr(self, f"_tab_{key}")(self._content)

    # ── Tab: ข้อมูลร้าน ─────────────────────────────────
    def _tab_shop(self, parent):
        if not self._is_admin:
            tk.Label(parent, text="🔒 เฉพาะ Admin เท่านั้น",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(pady=40)
            return
        c = card(parent, padx=24, pady=20); c.pack(fill="x")
        tk.Label(c, text="ข้อมูลร้านค้า", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))
        self._shop_vars = {}
        for key, lbl, default in [
            ("shop_name",    "ชื่อร้าน",       ""),
            ("shop_address", "ที่อยู่",         ""),
            ("shop_phone",   "เบอร์โทร",       ""),
            ("shop_tax_id",  "เลขผู้เสียภาษี", ""),
            ("shop_note",    "หมายเหตุใบเสร็จ","ขอบคุณที่ใช้บริการ 🙏"),
        ]:
            row = tk.Frame(c, bg=CLR["card"]); row.pack(fill="x", pady=4)
            tk.Label(row, text=lbl, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"], width=18, anchor="w").pack(side="left")
            v = tk.StringVar(value=get_setting(key, default))
            tk.Entry(row, textvariable=v, font=FONT, width=32,
                     bg=CLR["entry_bg"], fg=CLR["text"],
                     insertbackground=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", ipady=5)
            self._shop_vars[key] = v
        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=12)
        btn_primary(c, T("save"), self._save_shop).pack(anchor="w")

    def _save_shop(self):
        for k, v in self._shop_vars.items():
            set_setting(k, v.get().strip())
        messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลร้านเรียบร้อย")

    # ── Tab: บัญชีธนาคาร ────────────────────────────────
    def _tab_bank(self, parent):
        if not self._is_admin:
            tk.Label(parent, text="🔒 เฉพาะ Admin เท่านั้น",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(pady=40)
            return
        c = card(parent, padx=24, pady=20); c.pack(fill="x")
        tk.Label(c, text="บัญชีธนาคาร / PromptPay", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))
        self._fvars = {}
        banks  = ["ธนาคารกสิกรไทย","ธนาคารไทยพาณิชย์","ธนาคารกรุงเทพ",
                  "ธนาคารกรุงไทย","ธนาคารกรุงศรีอยุธยา","ธนาคารออมสิน",
                  "ธนาคารทหารไทยธนชาต","ธนาคารอาคารสงเคราะห์","อื่นๆ"]
        btypes = ["ออมทรัพย์","กระแสรายวัน","เงินฝากประจำ","เบอร์โทรศัพท์","เลขบัตรประชาชน"]
        for key, lbl, placeholder in [
            ("bank_name",    "ชื่อธนาคาร",   "ธนาคารกสิกรไทย"),
            ("bank_type",    "ประเภทบัญชี",  "ออมทรัพย์"),
            ("bank_account", "เลขที่บัญชี / เบอร์ PromptPay", ""),
            ("bank_holder",  "ชื่อบัญชี",    ""),
        ]:
            row = tk.Frame(c, bg=CLR["card"]); row.pack(fill="x", pady=6)
            tk.Label(row, text=lbl, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"], width=22, anchor="w").pack(side="left")
            v = tk.StringVar(value=get_setting(key, placeholder))
            if key == "bank_name":
                w = ttk.Combobox(row, textvariable=v, values=banks, font=FONT, width=28)
            elif key == "bank_type":
                w = ttk.Combobox(row, textvariable=v, values=btypes, font=FONT, width=28)
            else:
                w = tk.Entry(row, textvariable=v, font=FONT, width=30,
                             bg=CLR["entry_bg"], fg=CLR["text"],
                             insertbackground=CLR["text"],
                             relief="solid", highlightbackground=CLR["border"],
                             highlightthickness=1)
            w.pack(side="left", ipady=5)
            self._fvars[key] = v
        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=12)
        # QR Preview
        prev = tk.Frame(c, bg=CLR["card"]); prev.pack(fill="x", pady=(0,8))
        tk.Label(prev, text="ตัวอย่าง QR:", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,6))
        self._prev_canvas = tk.Canvas(prev, bg=CLR["card"],
                                       highlightthickness=0, width=160, height=160)
        self._prev_canvas.pack(side="left")
        self._prev_info = tk.Label(prev, text="", font=FONT, bg=CLR["card"],
                                    fg=CLR["text"], justify="left", wraplength=200)
        self._prev_info.pack(side="left", padx=12, anchor="nw")
        bf = tk.Frame(c, bg=CLR["card"]); bf.pack(fill="x")
        btn_warn(bf, "👁 ดูตัวอย่าง QR", self._preview_qr).pack(side="left", padx=(0,8))
        btn_primary(bf, T("save"), self._save_bank).pack(side="left")

    def _save_bank(self):
        for k, v in self._fvars.items():
            set_setting(k, v.get().strip())
        messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลบัญชีเรียบร้อย")
        self._preview_qr()

    def _preview_qr(self):
        acct = self._fvars["bank_account"].get().strip()
        bank = self._fvars["bank_name"].get()
        atype= self._fvars["bank_type"].get()
        aname= self._fvars["bank_holder"].get()
        self._prev_canvas.delete("all")
        self._prev_info.config(
            text=f"ธนาคาร: {bank}\nประเภท: {atype}\nเลขที่: {acct}\nชื่อ: {aname}")
        if not acct:
            self._prev_canvas.create_text(80,80,text="กรอกเลขที่บัญชีก่อน",
                                           fill=CLR["text_lt"],font=FONT); return
        try:
            import qrcode as _qr
            img = _qr.make(_make_promptpay_qr(acct,0)).resize((155,155))
            from PIL import ImageTk
            self._qr_img = ImageTk.PhotoImage(img)
            self._prev_canvas.create_image(0,0,anchor="nw",image=self._qr_img)
        except ImportError:
            self._prev_canvas.create_rectangle(5,5,155,155,outline=CLR["border"],dash=(4,4))
            self._prev_canvas.create_text(80,80,
                text="pip install qrcode pillow",fill=CLR["text_lt"],font=("Segoe UI",9))

    # ── Tab: ธีม ────────────────────────────────────────
    def _tab_theme(self, parent):
        c = card(parent, padx=24, pady=20); c.pack(fill="x")
        tk.Label(c, text="เลือกธีมสี", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,14))
        themes = [
            ("light",    "☀️  Light",       "#F0F4F8", "#1E293B"),
            ("dark",     "🌙  Dark",        "#0F172A", "#3B82F6"),
        ]
        self._theme_var = tk.StringVar(value=_current_theme)
        for key, label, bg_c, accent_c in themes:
            row = tk.Frame(c, bg=CLR["card"],
                           highlightbackground=CLR["accent"] if key==_current_theme else CLR["border"],
                           highlightthickness=2)
            row.pack(fill="x", pady=4)
            tk.Radiobutton(row, text=label, variable=self._theme_var, value=key,
                           font=FONT_B, bg=CLR["card"], fg=CLR["text"],
                           selectcolor=CLR["accent"],
                           activebackground=CLR["card"],
                           cursor="hand2").pack(side="left", padx=12, pady=8)
            # Preview swatch
            sw = tk.Frame(row, bg=bg_c, width=36, height=20)
            sw.pack(side="left", padx=4)
            tk.Frame(row, bg=accent_c, width=36, height=20).pack(side="left", padx=2)
        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=12)
        btn_primary(c, "🎨 ใช้ธีมนี้", self._apply_theme).pack(anchor="w")

    def _apply_theme(self):
        t = self._theme_var.get()
        set_theme(t)
        set_setting("app_theme", t)
        self.app.configure(bg=CLR["bg"])
        self.app.content.configure(bg=CLR["bg"])
        self.app._build_sidebar()
        self.app.show_frame("shop_settings")

    # ── Tab: ภาษา ────────────────────────────────────────
    def _tab_language(self, parent):
        c = card(parent, padx=24, pady=20); c.pack(fill="x")
        tk.Label(c, text="เลือกภาษา / Select Language", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,14))
        self._lang_var = tk.StringVar(value=_LANG)
        for key, label, desc in [
            ("th", "🇹🇭  ภาษาไทย",   "Thai — ใช้ภาษาไทยทั่วทั้งระบบ"),
            ("en", "🇬🇧  English",    "English — Use English throughout"),
        ]:
            row = tk.Frame(c, bg=CLR["card"],
                           highlightbackground=CLR["accent"] if key==_LANG else CLR["border"],
                           highlightthickness=2)
            row.pack(fill="x", pady=4)
            inner = tk.Frame(row, bg=CLR["card"]); inner.pack(fill="x", padx=12, pady=8)
            tk.Radiobutton(inner, text=label, variable=self._lang_var, value=key,
                           font=FONT_B, bg=CLR["card"], fg=CLR["text"],
                           selectcolor=CLR["accent"],
                           activebackground=CLR["card"],
                           cursor="hand2").pack(anchor="w")
            tk.Label(inner, text=desc, font=("Segoe UI",9),
                     bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")
        tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=12)
        btn_primary(c, "🌐 ใช้ภาษานี้", self._apply_lang).pack(anchor="w")

    def _apply_lang(self):
        set_lang(self._lang_var.get())
        self.app._build_sidebar()
        self.app.show_frame("shop_settings")
        messagebox.showinfo("สำเร็จ", "เปลี่ยนภาษาเรียบร้อย\nSome labels require app restart.")

    # ── Tab: ระบบ ────────────────────────────────────────
    def _tab_system(self, parent):
        c = card(parent, padx=24, pady=20); c.pack(fill="x")
        tk.Label(c, text="ข้อมูลระบบ", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,12))

        info_rows = [
            ("เวอร์ชัน",         "1.0 (Full Edition)"),
            ("ฐานข้อมูล",        "SQLite (stock.db)"),
            ("Python",            f"{__import__('sys').version.split()[0]}"),
            ("Tkinter",           f"{__import__('tkinter').TkVersion}"),
            ("ภาษาปัจจุบัน",     "ไทย" if _LANG=="th" else "English"),
            ("ธีมปัจจุบัน",      _current_theme.capitalize()),
        ]
        for lbl, val in info_rows:
            row = tk.Frame(c, bg=CLR["card"]); row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl, font=FONT, bg=CLR["card"],
                     fg=CLR["text_lt"], width=20, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_B, bg=CLR["card"],
                     fg=CLR["text"]).pack(side="left")

        if self._is_admin:
            tk.Frame(c, bg=CLR["border"], height=1).pack(fill="x", pady=12)
            tk.Label(c, text="เครื่องมือ Admin", font=FONT_B,
                     bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
            bf = tk.Frame(c, bg=CLR["card"]); bf.pack(fill="x")
            btn_warn(bf, "🗑️ ล้างประวัติ Transactions (เก่ากว่า 1 ปี)",
                     self._purge_old).pack(anchor="w", pady=2)
            btn_danger(bf, "⚠️ Reset ฐานข้อมูลทั้งหมด",
                       self._confirm_reset).pack(anchor="w", pady=2)

    def _purge_old(self):
        if not messagebox.askyesno("ยืนยัน","ลบ transactions เก่ากว่า 1 ปีใช่ไหม?"): return
        from datetime import datetime, timedelta
        cutoff = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d")
        with get_conn() as conn:
            n = conn.execute("DELETE FROM transactions WHERE date<?", (cutoff,)).rowcount
            conn.commit()
        messagebox.showinfo("สำเร็จ", f"ลบ {n} รายการเรียบร้อย")

    def _confirm_reset(self):
        ans = messagebox.askstring if hasattr(messagebox,"askstring") else None
        from tkinter.simpledialog import askstring
        pw = askstring("ยืนยัน Reset","พิมพ์ 'RESET' เพื่อยืนยัน:", parent=self)
        if pw == "RESET":
            import os
            if messagebox.askyesno("สุดท้าย","จะลบข้อมูลทั้งหมด แน่ใจ?"):
                db = "stock.db"
                if os.path.exists(db): os.remove(db)
                messagebox.showinfo("Done","ลบฐานข้อมูลแล้ว กรุณารีสตาร์ทโปรแกรม")
                self.app.destroy()


    def _tab_users_mgmt(self, parent):
        """Embed user management directly inside settings tab."""
        from tkinter import ttk as _ttk
        is_admin = self._is_admin
        pad = tk.Frame(parent, bg=CLR["bg"]); pad.pack(fill="both", expand=True)

        if not is_admin:
            tk.Label(pad, text="🔒 เฉพาะ Admin เท่านั้น",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(pady=40)
            return

        tb = tk.Frame(pad, bg=CLR["bg"]); tb.pack(fill="x", pady=(0,8))
        sv = tk.StringVar()
        se = tk.Frame(tb, bg=CLR["border"], padx=1, pady=1); se.pack(side="left")
        tk.Entry(se, textvariable=sv, font=FONT, width=24,
                 bg=CLR["entry_bg"], fg=CLR["text"], relief="flat",
                 insertbackground=CLR["text"]).pack(padx=6, pady=4)

        cols = ("id","ชื่อผู้ใช้","ชื่อจริง","บทบาท","วันที่สร้าง")
        ab = tk.Frame(pad, bg=CLR["bg"]); ab.pack(fill="x", pady=(0,4))
        wrap, tv = make_tree(pad, cols, [0,120,160,80,140], height=14)
        tv.column("id", width=0, stretch=False)
        wrap.pack(fill="both", expand=True)

        def _load_users(*_):
            kw = f"%{sv.get()}%"
            tv.delete(*tv.get_children())
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT id,username,fullname,role,created FROM users "
                    "WHERE username LIKE ? OR fullname LIKE ? ORDER BY role,username",
                    (kw,kw)).fetchall()
            for r in rows:
                tv.insert("","end", values=r)

        sv.trace_add("write", _load_users)

        def _add_user():
            from tkinter.simpledialog import askstring
            uname = askstring("เพิ่มผู้ใช้","ชื่อผู้ใช้:", parent=self)
            if not uname: return
            pw = askstring("เพิ่มผู้ใช้","รหัสผ่าน:", parent=self, show="*")
            if not pw: return
            fn = askstring("เพิ่มผู้ใช้","ชื่อจริง:", parent=self) or uname
            role = askstring("เพิ่มผู้ใช้","บทบาท (admin/staff):", parent=self) or "staff"
            role = role.strip().lower()
            if role not in ("admin","staff"): role="staff"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with get_conn() as conn:
                    conn.execute("INSERT INTO users(username,password,role,fullname,created) VALUES(?,?,?,?,?)",
                                 (uname, hash_pw(pw), role, fn, now))
                    conn.commit()
                _load_users()
            except Exception as e:
                messagebox.showerror("ผิดพลาด", str(e), parent=self)

        def _reset_pw():
            sel = tv.selection()
            if not sel: return
            uid = tv.item(sel[0])["values"][0]
            uname = tv.item(sel[0])["values"][1]
            from tkinter.simpledialog import askstring
            pw = askstring("รีเซ็ตรหัสผ่าน", f"รหัสผ่านใหม่สำหรับ '{uname}':", parent=self, show="*")
            if not pw: return
            with get_conn() as conn:
                conn.execute("UPDATE users SET password=? WHERE id=?", (hash_pw(pw), uid))
                conn.commit()
            messagebox.showinfo("สำเร็จ","รีเซ็ตรหัสผ่านเรียบร้อย", parent=self)

        def _del_user():
            sel = tv.selection()
            if not sel: return
            uid = tv.item(sel[0])["values"][0]
            uname = tv.item(sel[0])["values"][1]
            if uname == self.app.current_user["username"]:
                messagebox.showwarning("ไม่ได้","ไม่สามารถลบตัวเองได้", parent=self); return
            if messagebox.askyesno("ยืนยัน",f"ลบผู้ใช้ '{uname}' ใช่ไหม?"):
                with get_conn() as conn:
                    conn.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit()
                _load_users()

        btn_primary(ab, "➕ เพิ่มผู้ใช้", _add_user).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=6).pack(side="left")
        btn_warn(ab, "🔑 รีเซ็ตรหัสผ่าน", _reset_pw).pack(side="left")
        tk.Frame(ab, bg=CLR["bg"], width=6).pack(side="left")
        btn_danger(ab, "🗑️ ลบ", _del_user).pack(side="left")
        _load_users()

    def _tab_backup(self, parent):
        """Backup & Restore DB tab."""
        import os, shutil, glob
        pad = tk.Frame(parent, bg=CLR["bg"]); pad.pack(fill="both", expand=True)

        if not self._is_admin:
            tk.Label(pad, text="🔒 เฉพาะ Admin เท่านั้น",
                     font=FONT_H, bg=CLR["bg"], fg=CLR["danger"]).pack(pady=40)
            return

        # Backup section
        bc = card(pad, padx=24, pady=20); bc.pack(fill="x", pady=(0,12))
        tk.Label(bc, text="💾 สำรองข้อมูล (Backup)", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
        tk.Label(bc, text="สำรองไฟล์ stock.db ไปยังโฟลเดอร์ที่เลือก",
                 font=FONT, bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w", pady=(0,12))

        def _backup():
            import shutil
            dest_dir = filedialog.askdirectory(title="เลือกโฟลเดอร์สำรองข้อมูล")
            if not dest_dir: return
            src = "stock.db"
            if not os.path.exists(src):
                messagebox.showerror("ผิดพลาด","ไม่พบไฟล์ stock.db"); return
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(dest_dir, f"stock_backup_{ts}.db")
            shutil.copy2(src, dest)
            _refresh_backups()
            messagebox.showinfo("สำเร็จ",
                f"สำรองข้อมูลเรียบร้อย\n📁 {dest}")

        def _auto_backup():
            """Quick backup to ./backups/ folder."""
            import shutil
            os.makedirs("backups", exist_ok=True)
            src = "stock.db"
            if not os.path.exists(src):
                messagebox.showerror("ผิดพลาด","ไม่พบไฟล์ stock.db"); return
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join("backups", f"stock_backup_{ts}.db")
            shutil.copy2(src, dest)
            _refresh_backups()
            messagebox.showinfo("สำเร็จ",
                f"✅ Backup อัตโนมัติสำเร็จ\n📁 {dest}")

        bf = tk.Frame(bc, bg=CLR["card"]); bf.pack(fill="x")
        btn_success(bf, "⚡ Backup ด่วน (./backups/)", _auto_backup).pack(side="left")
        tk.Frame(bf, bg=CLR["card"], width=8).pack(side="left")
        btn_primary(bf, "📂 Backup ไปยังโฟลเดอร์...", _backup).pack(side="left")

        # Restore section
        rc = card(pad, padx=24, pady=20); rc.pack(fill="x", pady=(0,12))
        tk.Label(rc, text="♻️ กู้คืนข้อมูล (Restore)", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
        tk.Label(rc, text="⚠️ การ Restore จะเขียนทับข้อมูลปัจจุบันทั้งหมด กรุณาระวัง",
                 font=FONT, bg=CLR["card"], fg=CLR["warning"]).pack(anchor="w", pady=(0,12))

        def _restore():
            import shutil
            src = filedialog.askopenfilename(
                title="เลือกไฟล์ Backup",
                filetypes=[("Database","*.db"),("All","*.*")])
            if not src: return
            if not messagebox.askyesno("ยืนยัน Restore",
                f"จะแทนที่ด้วย: {src}\n\nแน่ใจใช่ไหม?"):
                return
                return
            # Auto-backup current before restoring
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("backups", exist_ok=True)
            if os.path.exists("stock.db"):
                shutil.copy2("stock.db", f"backups/pre_restore_{ts}.db")
            shutil.copy2(src, "stock.db")
            messagebox.showinfo("สำเร็จ", "✅ Restore สำเร็จ\nกรุณาปิดแล้วเปิดโปรแกรมใหม่")

        btn_warn(rc, "♻️ Restore จากไฟล์...", _restore).pack(anchor="w")

        # Existing backups list
        lc = card(pad, padx=24, pady=20); lc.pack(fill="x")
        hdr = tk.Frame(lc, bg=CLR["card"]); hdr.pack(fill="x", pady=(0,8))
        tk.Label(hdr, text="📋 Backup ล่าสุด (./backups/)", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(side="left")
        self._backup_list_frame = tk.Frame(lc, bg=CLR["card"])
        self._backup_list_frame.pack(fill="x")

        def _refresh_backups():
            for w in self._backup_list_frame.winfo_children(): w.destroy()
            files = sorted(glob.glob("backups/stock_backup_*.db"), reverse=True)[:10]
            if not files:
                tk.Label(self._backup_list_frame, text="ยังไม่มี Backup",
                         font=FONT, bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")
                return
            for f in files:
                sz = os.path.getsize(f) / 1024
                name = os.path.basename(f)
                row = tk.Frame(self._backup_list_frame, bg=CLR["card"]); row.pack(fill="x", pady=2)
                tk.Label(row, text=f"💾 {name}  ({sz:.1f} KB)",
                         font=("Segoe UI",9), bg=CLR["card"], fg=CLR["text"]).pack(side="left")

        btn_warn(hdr, "🔄 รีเฟรช", _refresh_backups).pack(side="right")
        _refresh_backups()



# ══════════════════════════════════════════════════════
#  CUSTOMERS FRAME
# ══════════════════════════════════════════════════════
class CustomersFrame(tk.Frame):
    NAME = "customers"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"])
        pad.pack(fill="both",expand=True,padx=30,pady=24)
        self._pad=pad
        page_title(pad,"👥 ระบบลูกค้า","จัดการข้อมูลลูกค้าและแต้มสะสม")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,8))
        self._sv=tk.StringVar(); self._sv.trace_add("write",lambda *_:self._load())
        se=tk.Frame(tb,bg=CLR["border"],padx=1,pady=1); se.pack(side="left")
        tk.Entry(se,textvariable=self._sv,font=FONT,width=28,
                 bg=CLR["entry_bg"],fg=CLR["text"],relief="flat",
                 insertbackground=CLR["text"]).pack(padx=6,pady=4)
        btn_primary(tb,"➕ เพิ่มลูกค้า",self._add).pack(side="left",padx=(8,0))
        btn_warn(tb,"📊 Export CSV",self._export_csv).pack(side="left",padx=(4,0))
        cols=("id","รหัส","ชื่อ","เบอร์โทร","แต้มสะสม","ยอดซื้อรวม","หมายเหตุ")
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(0,4))
        btn_primary(ab,"✏️ แก้ไข",self._edit).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=6).pack(side="left")
        btn_danger(ab,"🗑️ ลบ",self._delete).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=6).pack(side="left")
        btn_warn(ab,"🎁 ปรับแต้ม",self._adjust_points).pack(side="left")
        wrap,self.tv=make_tree(pad,cols,[0,80,160,110,90,110,120],height=18)
        self.tv.column("id",width=0,stretch=False)
        wrap.pack(fill="both",expand=True)
        self.tv.bind("<Double-1>",lambda _:self._edit())
    def _load(self):
        kw=f"%{self._sv.get()}%"
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            rows=conn.execute(
                "SELECT id,code,name,phone,points,total_spent,note FROM customers "
                "WHERE name LIKE ? OR code LIKE ? OR phone LIKE ? ORDER BY name",
                (kw,kw,kw)).fetchall()
        for r in rows:
            self.tv.insert("","end",values=(r[0],r[1],r[2],r[3] or "",
                f"{r[4]:,.1f}",f"{r[5]:,.2f}",r[6] or ""))
    def _add(self): CustomerDialog(self,None,self._load)
    def _edit(self):
        sel=self.tv.selection()
        if sel: CustomerDialog(self,self.tv.item(sel[0])["values"][0],self._load)
    def _delete(self):
        sel=self.tv.selection()
        if not sel: return
        cid=self.tv.item(sel[0])["values"][0]
        name=self.tv.item(sel[0])["values"][2]
        if messagebox.askyesno("ยืนยัน",f"ลบลูกค้า '{name}' ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM customers WHERE id=?",(cid,)); conn.commit()
            self._load()
    def _adjust_points(self):
        sel=self.tv.selection()
        if not sel: return
        cid=self.tv.item(sel[0])["values"][0]
        name=self.tv.item(sel[0])["values"][2]
        from tkinter.simpledialog import askfloat
        pts=askfloat("ปรับแต้ม",f"เพิ่ม/ลดแต้ม '{name}' (ลบ=หักแต้ม):",parent=self)
        if pts is None: return
        with get_conn() as conn:
            conn.execute("UPDATE customers SET points=MAX(0,points+?) WHERE id=?",(pts,cid)); conn.commit()
        self._load()
    def _export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not path: return
        import csv
        with get_conn() as conn:
            rows=conn.execute("SELECT code,name,phone,email,points,total_spent,note,created FROM customers ORDER BY name").fetchall()
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(["รหัส","ชื่อ","เบอร์","อีเมล","แต้ม","ยอดซื้อ","หมายเหตุ","วันที่เพิ่ม"])
            w.writerows(rows)
        messagebox.showinfo("สำเร็จ",f"Export CSV สำเร็จ\n{path}")


class CustomerDialog(tk.Toplevel):
    def __init__(self,parent,cid,callback):
        super().__init__(parent); self.cid=cid; self.callback=callback
        self.title("เพิ่มลูกค้า" if cid is None else "แก้ไขลูกค้า")
        self.geometry("440x440"); self.configure(bg=CLR["bg"]); self.grab_set()
        pad=tk.Frame(self,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text="ข้อมูลลูกค้า",font=FONT_H,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,12))
        self._v={}
        for key,lbl,default in [
            ("code","รหัสลูกค้า *",""),("name","ชื่อ *",""),
            ("phone","เบอร์โทร",""),("email","อีเมล",""),
            ("address","ที่อยู่",""),("note","หมายเหตุ",""),
        ]:
            row=tk.Frame(pad,bg=CLR["bg"]); row.pack(fill="x",pady=3)
            tk.Label(row,text=lbl,font=FONT,bg=CLR["bg"],fg=CLR["text_lt"],width=14,anchor="w").pack(side="left")
            v=tk.StringVar(value=default)
            tk.Entry(row,textvariable=v,font=FONT,bg=CLR["entry_bg"],fg=CLR["text"],
                     relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                     ).pack(side="left",fill="x",expand=True,ipady=5)
            self._v[key]=v
        if cid: self._load()
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        bf=tk.Frame(pad,bg=CLR["bg"]); bf.pack(fill="x")
        btn_primary(bf,"💾 บันทึก",self._save).pack(side="right")
        tk.Button(bf,text="ยกเลิก",font=FONT,bg=CLR["border"],relief="flat",
                  padx=14,pady=7,cursor="hand2",command=self.destroy).pack(side="right",padx=(0,8))
    def _load(self):
        with get_conn() as conn:
            r=conn.execute("SELECT code,name,phone,email,address,note FROM customers WHERE id=?",(self.cid,)).fetchone()
        if r:
            for key,val in zip(["code","name","phone","email","address","note"],r):
                self._v[key].set(val or "")
    def _save(self):
        code=self._v["code"].get().strip(); name=self._v["name"].get().strip()
        if not code or not name:
            messagebox.showerror("ผิดพลาด","กรุณากรอกรหัสและชื่อลูกค้า",parent=self); return
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_conn() as conn:
            if self.cid is None:
                conn.execute("INSERT INTO customers(code,name,phone,email,address,note,created) VALUES(?,?,?,?,?,?,?)",
                             (code,name,self._v["phone"].get(),self._v["email"].get(),
                              self._v["address"].get(),self._v["note"].get(),now))
            else:
                conn.execute("UPDATE customers SET code=?,name=?,phone=?,email=?,address=?,note=? WHERE id=?",
                             (code,name,self._v["phone"].get(),self._v["email"].get(),
                              self._v["address"].get(),self._v["note"].get(),self.cid))
            conn.commit()
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════
#  PROMOTIONS FRAME
# ══════════════════════════════════════════════════════
class PromotionsFrame(tk.Frame):
    NAME = "promotions"
    def __init__(self,parent,app):
        super().__init__(parent,bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"])
        pad.pack(fill="both",expand=True,padx=30,pady=24)
        self._pad=pad
        page_title(pad,"🎁 โปรโมชั่น","จัดการส่วนลดและโปรโมชั่น")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,8))
        btn_primary(tb,"➕ เพิ่มโปรโมชั่น",self._add).pack(side="left")
        btn_success(tb,"✅ เปิดใช้งาน",self._toggle_active).pack(side="left",padx=(6,0))
        btn_danger(tb,"🗑️ ลบ",self._delete).pack(side="left",padx=(6,0))
        cols=("id","รหัส","ชื่อโปรโมชั่น","ประเภท","ส่วนลด","ขั้นต่ำ","ใช้แล้ว","สถานะ","วันหมดอายุ")
        wrap,self.tv=make_tree(pad,cols,[0,90,180,90,80,80,70,70,110],height=18)
        self.tv.column("id",width=0,stretch=False)
        wrap.pack(fill="both",expand=True)
        self.tv.tag_configure("active",foreground=CLR["success"])
        self.tv.tag_configure("inactive",foreground=CLR["text_lt"])
        self.tv.bind("<Double-1>",lambda _:self._add())
    def _load(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            rows=conn.execute("SELECT id,code,name,type,value,min_amount,used_count,active,end_date FROM promotions ORDER BY active DESC,name").fetchall()
        type_map={"percent":"% ลด","fixed":"฿ ลด","free_ship":"ส่งฟรี"}
        for r in rows:
            tag="active" if r[7] else "inactive"
            status="✅ เปิด" if r[7] else "❌ ปิด"
            val=f"{r[4]:g}%" if r[3]=="percent" else f"฿{r[4]:,.0f}"
            self.tv.insert("","end",values=(r[0],r[1],r[2],
                type_map.get(r[3],r[3]),val,f"฿{r[5]:,.0f}",f"{r[6]} ครั้ง",
                status,r[8] or "ไม่มีกำหนด"),tags=(tag,))
    def _add(self):
        sel=self.tv.selection()
        pid=self.tv.item(sel[0])["values"][0] if sel else None
        PromotionDialog(self,pid,self._load)
    def _toggle_active(self):
        sel=self.tv.selection()
        if not sel: return
        pid=self.tv.item(sel[0])["values"][0]
        with get_conn() as conn:
            cur=conn.execute("SELECT active FROM promotions WHERE id=?",(pid,)).fetchone()[0]
            conn.execute("UPDATE promotions SET active=? WHERE id=?",(0 if cur else 1,pid)); conn.commit()
        self._load()
    def _delete(self):
        sel=self.tv.selection()
        if not sel: return
        pid=self.tv.item(sel[0])["values"][0]
        if messagebox.askyesno("ยืนยัน","ลบโปรโมชั่นนี้ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM promotions WHERE id=?",(pid,)); conn.commit()
            self._load()


class PromotionDialog(tk.Toplevel):
    def __init__(self,parent,pid,callback):
        super().__init__(parent); self.pid=pid; self.callback=callback
        self.title("เพิ่มโปรโมชั่น" if pid is None else "แก้ไขโปรโมชั่น")
        self.geometry("420x460"); self.configure(bg=CLR["bg"]); self.grab_set()
        pad=tk.Frame(self,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text="ข้อมูลโปรโมชั่น",font=FONT_H,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,12))
        self._v={}
        for key,lbl,default in [
            ("code","รหัสโปรโมชั่น *",""),
            ("name","ชื่อโปรโมชั่น *",""),
            ("value","ส่วนลด (% หรือ ฿) *","0"),
            ("min_amount","ยอดขั้นต่ำ (฿)","0"),
            ("max_uses","จำนวนครั้งสูงสุด (0=ไม่จำกัด)","0"),
            ("end_date","วันหมดอายุ (YYYY-MM-DD)",""),
        ]:
            row=tk.Frame(pad,bg=CLR["bg"]); row.pack(fill="x",pady=3)
            tk.Label(row,text=lbl,font=FONT,bg=CLR["bg"],fg=CLR["text_lt"],width=22,anchor="w").pack(side="left")
            v=tk.StringVar(value=default)
            tk.Entry(row,textvariable=v,font=FONT,bg=CLR["entry_bg"],fg=CLR["text"],
                     relief="solid",highlightbackground=CLR["border"],highlightthickness=1,width=16
                     ).pack(side="left",ipady=5)
            self._v[key]=v
        row=tk.Frame(pad,bg=CLR["bg"]); row.pack(fill="x",pady=3)
        tk.Label(row,text="ประเภทส่วนลด",font=FONT,bg=CLR["bg"],fg=CLR["text_lt"],width=22,anchor="w").pack(side="left")
        self._type_v=tk.StringVar(value="percent")
        for val,lbl in [("percent","% ลด"),("fixed","฿ ลด")]:
            tk.Radiobutton(row,text=lbl,variable=self._type_v,value=val,font=FONT,
                           bg=CLR["bg"],fg=CLR["text"],selectcolor=CLR["accent"],
                           cursor="hand2").pack(side="left",padx=(0,8))
        if pid: self._load()
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=10)
        bf=tk.Frame(pad,bg=CLR["bg"]); bf.pack(fill="x")
        btn_primary(bf,"💾 บันทึก",self._save).pack(side="right")
        tk.Button(bf,text="ยกเลิก",font=FONT,bg=CLR["border"],relief="flat",
                  padx=14,pady=7,cursor="hand2",command=self.destroy).pack(side="right",padx=(0,8))
    def _load(self):
        with get_conn() as conn:
            r=conn.execute("SELECT code,name,type,value,min_amount,max_uses,end_date FROM promotions WHERE id=?",(self.pid,)).fetchone()
        if r:
            for key,val in zip(["code","name","value","min_amount","max_uses","end_date"],[r[0],r[1],r[3],r[4],r[5],r[6]]):
                self._v[key].set(str(val) if val is not None else "")
            self._type_v.set(r[2])
    def _save(self):
        code=self._v["code"].get().strip(); name=self._v["name"].get().strip()
        if not code or not name:
            messagebox.showerror("ผิดพลาด","กรุณากรอกรหัสและชื่อ",parent=self); return
        try:
            val=float(self._v["value"].get() or 0)
            min_amt=float(self._v["min_amount"].get() or 0)
            max_u=int(self._v["max_uses"].get() or 0)
        except ValueError:
            messagebox.showerror("ผิดพลาด","ตัวเลขไม่ถูกต้อง",parent=self); return
        end=self._v["end_date"].get().strip() or None
        with get_conn() as conn:
            if self.pid is None:
                conn.execute("INSERT INTO promotions(code,name,type,value,min_amount,max_uses,end_date) VALUES(?,?,?,?,?,?,?)",
                             (code,name,self._type_v.get(),val,min_amt,max_u,end))
            else:
                conn.execute("UPDATE promotions SET code=?,name=?,type=?,value=?,min_amount=?,max_uses=?,end_date=? WHERE id=?",
                             (code,name,self._type_v.get(),val,min_amt,max_u,end,self.pid))
            conn.commit()
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════
#  CSV IMPORT FRAME
# ══════════════════════════════════════════════════════
class CSVImportFrame(tk.Frame):
    NAME = "csv_import"
    def __init__(self,parent,app):
        super().__init__(parent,bg=CLR["bg"]); self.app=app
        self._preview_data=[]
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._preview_data=[]; self._build()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"])
        pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"📥 นำเข้า CSV","Import สินค้าจากไฟล์ CSV หรือ Excel")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)

        # Template download
        tc=card(pad,padx=20,pady=14); tc.pack(fill="x",pady=(0,12))
        tk.Label(tc,text="📋 รูปแบบไฟล์ CSV",font=FONT_B,bg=CLR["card"],fg=CLR["text"]).pack(anchor="w")
        cols_info="คอลัมน์ที่รองรับ: code, name, category, unit, quantity, min_qty, price, sell_price"
        tk.Label(tc,text=cols_info,font=("Segoe UI",9),bg=CLR["card"],fg=CLR["text_lt"]).pack(anchor="w",pady=(4,8))
        btn_warn(tc,"💾 ดาวน์โหลด Template CSV",self._download_template).pack(anchor="w")

        # Upload
        uc=card(pad,padx=20,pady=14); uc.pack(fill="x",pady=(0,12))
        tk.Label(uc,text="📂 เลือกไฟล์ CSV",font=FONT_B,bg=CLR["card"],fg=CLR["text"]).pack(anchor="w",pady=(0,8))
        bf=tk.Frame(uc,bg=CLR["card"]); bf.pack(fill="x")
        self._file_lbl=tk.Label(bf,text="ยังไม่ได้เลือกไฟล์",font=FONT,
                                 bg=CLR["card"],fg=CLR["text_lt"])
        self._file_lbl.pack(side="left")
        btn_primary(bf,"📂 เลือกไฟล์",self._choose_file).pack(side="left",padx=(12,0))

        # Mode
        mf=tk.Frame(uc,bg=CLR["card"]); mf.pack(fill="x",pady=(8,0))
        tk.Label(mf,text="โหมดนำเข้า:",font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._mode=tk.StringVar(value="update")
        for val,lbl in [("update","อัปเดตถ้ามีอยู่แล้ว"),("skip","ข้ามถ้ามีอยู่แล้ว"),("overwrite","เขียนทับทั้งหมด")]:
            tk.Radiobutton(mf,text=lbl,variable=self._mode,value=val,font=("Segoe UI",9),
                           bg=CLR["card"],fg=CLR["text"],selectcolor=CLR["accent"],
                           cursor="hand2").pack(side="left",padx=(8,0))

        # Preview table
        tk.Label(pad,text="🔍 ตัวอย่างข้อมูล (50 แถวแรก)",font=FONT_B,
                 bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,6))
        pcols=("code","name","category","unit","quantity","min_qty","price","sell_price")
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(0,4))
        self._import_btn=btn_success(ab,"✅ นำเข้าทั้งหมด",self._do_import)
        self._import_btn.pack(side="left")
        self._status_lbl=tk.Label(ab,text="",font=FONT,bg=CLR["bg"],fg=CLR["success"])
        self._status_lbl.pack(side="left",padx=12)
        wrap,self.tv=make_tree(pad,pcols,[80,160,90,60,70,70,80,80],height=16)
        wrap.pack(fill="both",expand=True)

    def _download_template(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",
            initialfile="template_products.csv",filetypes=[("CSV","*.csv")])
        if not path: return
        import csv
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["code","name","category","unit","quantity","min_qty","price","sell_price"])
            w.writerow(["P001","สินค้าตัวอย่าง","ทั่วไป","ชิ้น","100","10","50","65"])
        messagebox.showinfo("สำเร็จ",f"ดาวน์โหลด Template แล้ว\n{path}")

    def _choose_file(self):
        path=filedialog.askopenfilename(filetypes=[("CSV files","*.csv"),("All","*.*")])
        if not path: return
        self._file_lbl.config(text=path.split("/")[-1],fg=CLR["text"])
        import csv
        self._preview_data=[]
        self.tv.delete(*self.tv.get_children())
        try:
            with open(path,newline="",encoding="utf-8-sig") as f:
                reader=csv.DictReader(f)
                for i,row in enumerate(reader):
                    self._preview_data.append(row)
                    if i<50:
                        self.tv.insert("","end",values=(
                            row.get("code",""),row.get("name",""),
                            row.get("category",""),row.get("unit",""),
                            row.get("quantity","0"),row.get("min_qty","0"),
                            row.get("price","0"),row.get("sell_price","0")))
            self._status_lbl.config(text=f"พบ {len(self._preview_data)} แถว",fg=CLR["success"])
        except Exception as e:
            messagebox.showerror("ผิดพลาด",f"อ่านไฟล์ไม่ได้: {e}")

    def _do_import(self):
        if not self._preview_data:
            messagebox.showwarning("แจ้งเตือน","กรุณาเลือกไฟล์ก่อน"); return
        mode=self._mode.get()
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok=skip=err=0
        with get_conn() as conn:
            for row in self._preview_data:
                try:
                    code=str(row.get("code","")).strip()
                    name=str(row.get("name","")).strip()
                    if not code or not name: skip+=1; continue
                    exists=conn.execute("SELECT id FROM products WHERE code=?",(code,)).fetchone()
                    qty=float(row.get("quantity",0) or 0)
                    mq=float(row.get("min_qty",0) or 0)
                    price=float(row.get("price",0) or 0)
                    sp=float(row.get("sell_price",0) or 0)
                    cat=str(row.get("category","")).strip()
                    unit=str(row.get("unit","")).strip()
                    if exists:
                        if mode=="skip": skip+=1; continue
                        conn.execute("""UPDATE products SET name=?,category=?,unit=?,
                            quantity=?,min_qty=?,price=?,sell_price=?,updated=? WHERE code=?""",
                            (name,cat,unit,qty,mq,price,sp,now,code))
                    else:
                        conn.execute("INSERT INTO products(code,name,category,unit,quantity,min_qty,price,sell_price,updated) VALUES(?,?,?,?,?,?,?,?,?)",
                            (code,name,cat,unit,qty,mq,price,sp,now))
                    ok+=1
                except Exception:
                    err+=1
            conn.commit()
        self._status_lbl.config(
            text=f"✅ สำเร็จ {ok}  ⏭️ ข้าม {skip}  ❌ ผิดพลาด {err}",
            fg=CLR["success"] if err==0 else CLR["warning"])
        messagebox.showinfo("นำเข้าเสร็จสิ้น",
            f"นำเข้าสำเร็จ: {ok} รายการ\nข้าม: {skip} รายการ\nผิดพลาด: {err} รายการ")


# ══════════════════════════════════════════════════════
#  ALERT HELPERS
# ══════════════════════════════════════════════════════
def check_low_stock_alert(app):
    """Show badge count on sidebar and popup if critical items."""
    with get_conn() as conn:
        count=conn.execute(
            "SELECT COUNT(*) FROM products WHERE quantity<=min_qty AND min_qty>0"
        ).fetchone()[0]
    return count


# ══════════════════════════════════════════════════════
#  SHIFT FRAME  (เปิด-ปิดกะ)
# ══════════════════════════════════════════════════════
class ShiftFrame(tk.Frame):
    NAME = "shift"

    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"])
        self.app = app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"])
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, "🕐 ระบบกะ / Shift", "เปิด-ปิดกะ และสรุปยอดเงินสด")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)

        user = self.app.current_user["username"]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if current user has open shift
        with get_conn() as conn:
            open_shift = conn.execute(
                "SELECT id,cashier,open_time,open_cash FROM shifts "
                "WHERE cashier=? AND status='open' ORDER BY id DESC LIMIT 1",
                (user,)).fetchone()

        # ── Current shift status card ────────────────────────
        sc = card(pad, padx=24, pady=20)
        sc.pack(fill="x", pady=(0,16))

        if open_shift:
            sid, cashier, open_time, open_cash = open_shift
            tk.Label(sc, text="🟢 กะปัจจุบัน: เปิดอยู่",
                     font=FONT_H, bg=CLR["card"], fg=CLR["success"]).pack(anchor="w")
            info_rows = [
                ("แคชเชียร์:", cashier),
                ("เปิดกะเมื่อ:", open_time),
                ("ยอดเงินเปิดกะ:", f"฿{open_cash:,.2f}"),
            ]
            for lbl, val in info_rows:
                row = tk.Frame(sc, bg=CLR["card"]); row.pack(fill="x", pady=3)
                tk.Label(row, text=lbl, font=FONT, bg=CLR["card"],
                         fg=CLR["text_lt"], width=18, anchor="w").pack(side="left")
                tk.Label(row, text=val, font=FONT_B, bg=CLR["card"],
                         fg=CLR["text"]).pack(side="left")

            # Sales in this shift
            with get_conn() as conn:
                sales = conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(total),0), "
                    "COALESCE(SUM(CASE WHEN payment='cash' THEN total ELSE 0 END),0), "
                    "COALESCE(SUM(CASE WHEN payment='transfer' THEN total ELSE 0 END),0), "
                    "COALESCE(SUM(CASE WHEN payment='card' THEN total ELSE 0 END),0) "
                    "FROM sales WHERE date>=? AND cashier=?",
                    (open_time, user)).fetchone()
            cnt, total, cash_s, transfer_s, card_s = sales

            tk.Frame(sc, bg=CLR["border"], height=1).pack(fill="x", pady=10)
            tk.Label(sc, text="📊 ยอดในกะนี้", font=FONT_B,
                     bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
            sr = tk.Frame(sc, bg=CLR["card"]); sr.pack(fill="x")
            for i, (lbl, val, col) in enumerate([
                ("🧾 จำนวนบิล",    f"{cnt}",             CLR["accent"]),
                ("💰 ยอดรวม",      f"฿{total:,.2f}",     CLR["success"]),
                ("💵 เงินสด",      f"฿{cash_s:,.2f}",    CLR["warning"]),
                ("📱 โอน",         f"฿{transfer_s:,.2f}",CLR["accent"]),
                ("💳 บัตร",        f"฿{card_s:,.2f}",    "#A78BFA"),
            ]):
                c2 = card(sr, padx=12, pady=10)
                c2.grid(row=0, column=i, sticky="nsew", padx=(0,8) if i<4 else 0)
                sr.columnconfigure(i, weight=1)
                tk.Label(c2, text=lbl, font=("Segoe UI",8),
                         bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w")
                tk.Label(c2, text=val, font=("Segoe UI",14,"bold"),
                         bg=CLR["card"], fg=col).pack(anchor="w")

            tk.Frame(sc, bg=CLR["border"], height=1).pack(fill="x", pady=12)

            # Close shift section
            tk.Label(sc, text="🔒 ปิดกะ", font=FONT_B,
                     bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
            cf = tk.Frame(sc, bg=CLR["card"]); cf.pack(fill="x", pady=(0,8))
            tk.Label(cf, text="ยอดเงินสดที่นับได้ (บาท):", font=FONT,
                     bg=CLR["card"], fg=CLR["text_lt"]).pack(side="left")
            self._close_cash_var = tk.StringVar(value="0")
            tk.Entry(cf, textvariable=self._close_cash_var, font=FONT, width=14,
                     bg=CLR["entry_bg"], fg=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", padx=8, ipady=5)

            nf = tk.Frame(sc, bg=CLR["card"]); nf.pack(fill="x", pady=(0,12))
            tk.Label(nf, text="หมายเหตุ:", font=FONT,
                     bg=CLR["card"], fg=CLR["text_lt"]).pack(side="left")
            self._note_var = tk.StringVar()
            tk.Entry(nf, textvariable=self._note_var, font=FONT, width=30,
                     bg=CLR["entry_bg"], fg=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", padx=8, ipady=5)

            def _close_shift():
                try:
                    close_cash = float(self._close_cash_var.get() or 0)
                except ValueError:
                    messagebox.showerror("ผิดพลาด","กรุณากรอกยอดเงินที่ถูกต้อง"); return
                if not messagebox.askyesno("ยืนยันปิดกะ","ต้องการปิดกะนี้ใช่ไหม?"): return
                with get_conn() as conn:
                    conn.execute("""UPDATE shifts SET close_time=?,close_cash=?,
                        sales_total=?,sales_count=?,note=?,status='closed'
                        WHERE id=?""",
                        (now_str, close_cash, total, cnt,
                         self._note_var.get().strip(), sid))
                    conn.commit()
                _show_shift_summary(sid, open_time, open_cash, close_cash, total, cnt, cash_s, transfer_s, card_s)
                self.refresh()

            btn_danger(sc, "🔒 ปิดกะและพิมพ์สรุป", _close_shift).pack(anchor="w")

        else:
            # No open shift — show open form
            tk.Label(sc, text="🔴 ไม่มีกะที่เปิดอยู่",
                     font=FONT_H, bg=CLR["card"], fg=CLR["danger"]).pack(anchor="w", pady=(0,12))
            tk.Label(sc, text="กรุณาเปิดกะก่อนเริ่มรับเงิน",
                     font=FONT, bg=CLR["card"], fg=CLR["text_lt"]).pack(anchor="w", pady=(0,12))

            of = tk.Frame(sc, bg=CLR["card"]); of.pack(fill="x", pady=(0,8))
            tk.Label(of, text="ยอดเงินเปิดกะ (บาท):", font=FONT,
                     bg=CLR["card"], fg=CLR["text_lt"]).pack(side="left")
            self._open_cash_var = tk.StringVar(value="0")
            tk.Entry(of, textvariable=self._open_cash_var, font=FONT, width=14,
                     bg=CLR["entry_bg"], fg=CLR["text"],
                     relief="solid", highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left", padx=8, ipady=5)

            def _open_shift():
                try:
                    open_cash = float(self._open_cash_var.get() or 0)
                except ValueError:
                    messagebox.showerror("ผิดพลาด","กรุณากรอกยอดเงินที่ถูกต้อง"); return
                with get_conn() as conn:
                    conn.execute(
                        "INSERT INTO shifts(cashier,open_time,open_cash,status) VALUES(?,?,?,'open')",
                        (user, now_str, open_cash))
                    conn.commit()
                messagebox.showinfo("เปิดกะสำเร็จ",
                    f"✅ เปิดกะเรียบร้อย\n⏰ {now_str}\n💵 เงินเปิดกะ: ฿{open_cash:,.2f}")
                self.refresh()

            btn_success(sc, "▶️ เปิดกะ", _open_shift).pack(anchor="w")

        # ── Shift history ────────────────────────────────────
        hc = card(pad, padx=24, pady=20); hc.pack(fill="both", expand=True)
        tk.Label(hc, text="📋 ประวัติกะ", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).pack(anchor="w", pady=(0,8))
        cols = ("id","แคชเชียร์","เปิดกะ","ปิดกะ","เงินเปิด","เงินปิด","ยอดขาย","บิล","สถานะ")
        wrap, htv = make_tree(hc, cols, [0,100,140,140,80,80,90,50,70], height=8)
        htv.column("id", width=0, stretch=False)
        wrap.pack(fill="both", expand=True)
        htv.tag_configure("open", foreground=CLR["success"])
        htv.tag_configure("closed", foreground=CLR["text_lt"])

        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id,cashier,open_time,close_time,open_cash,close_cash,"
                "sales_total,sales_count,status FROM shifts ORDER BY id DESC LIMIT 30"
            ).fetchall()
        for r in rows:
            tag = "open" if r[8]=="open" else "closed"
            status = "🟢 เปิดอยู่" if r[8]=="open" else "✅ ปิดแล้ว"
            htv.insert("","end", values=(
                r[0], r[1], r[2] or "-", r[3] or "-",
                f"฿{r[4]:,.0f}", f"฿{r[5]:,.0f}" if r[5] else "-",
                f"฿{r[6]:,.0f}", r[7] or 0, status), tags=(tag,))


def _show_shift_summary(sid, open_time, open_cash, close_cash, total, cnt, cash_s, transfer_s, card_s):
    """Pop-up summary when closing shift."""
    win = tk.Toplevel()
    win.title("สรุปกะ")
    win.geometry("360x420")
    win.configure(bg=CLR["bg"])
    pad = tk.Frame(win, bg=CLR["bg"], padx=24, pady=20); pad.pack(fill="both", expand=True)
    tk.Label(pad, text="📊 สรุปกะ", font=FONT_H, bg=CLR["bg"], fg=CLR["text"]).pack(anchor="w")
    tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=10)
    rows = [
        ("เปิดกะ:",        open_time),
        ("เงินเปิดกะ:",    f"฿{open_cash:,.2f}"),
        ("",               ""),
        ("จำนวนบิล:",      f"{cnt} ใบ"),
        ("ยอดขายรวม:",     f"฿{total:,.2f}"),
        ("  เงินสด:",      f"฿{cash_s:,.2f}"),
        ("  โอนเงิน:",     f"฿{transfer_s:,.2f}"),
        ("  บัตร:",        f"฿{card_s:,.2f}"),
        ("",               ""),
        ("เงินสดที่นับได้:", f"฿{close_cash:,.2f}"),
        ("ผลต่างเงินสด:",  f"฿{close_cash - open_cash - cash_s:,.2f}"),
    ]
    for lbl, val in rows:
        if not lbl:
            tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=4)
            continue
        r = tk.Frame(pad, bg=CLR["bg"]); r.pack(fill="x", pady=2)
        tk.Label(r, text=lbl, font=FONT, bg=CLR["bg"],
                 fg=CLR["text_lt"], width=20, anchor="w").pack(side="left")
        tk.Label(r, text=val, font=FONT_B, bg=CLR["bg"],
                 fg=CLR["text"]).pack(side="left")
    btn_primary(pad, "✅ ปิด", win.destroy).pack(fill="x", pady=(16,0))


# ══════════════════════════════════════════════════════
#  STOCK COUNT FRAME
# ══════════════════════════════════════════════════════
class StockCountFrame(tk.Frame):
    NAME = "stock_count"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"📋 นับสต็อก (Stock Count)","ตรวจนับสินค้าจริงและปรับยอด")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,10))
        btn_primary(tb,"➕ เปิดรอบนับใหม่",self._new_count).pack(side="left")
        btn_success(tb,"✅ อนุมัติ & ปรับยอด",self._approve).pack(side="left",padx=(6,0))
        btn_danger(tb,"🗑️ ลบ",self._delete).pack(side="left",padx=(6,0))
        cols=("id","เลขที่","ผู้นับ","สถานะ","หมายเหตุ","วันที่")
        wrap,self.tv=make_tree(pad,cols,[0,120,120,90,180,140],height=8)
        self.tv.column("id",width=0,stretch=False)
        wrap.pack(fill="x")
        self.tv.tag_configure("draft",foreground=CLR["warning"])
        self.tv.tag_configure("approved",foreground=CLR["success"])
        self.tv.bind("<Double-1>",lambda _:self._open_count())
        tk.Label(pad,text="รายการในรอบนับ (ดับเบิลคลิกเพื่อเปิด / ดับเบิลคลิกแถวขวาเพื่อแก้ยอด)",
                 font=FONT_B,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(12,6))
        dcols=("cid","รหัส","ชื่อสินค้า","ยอดระบบ","ยอดนับ","ผลต่าง")
        wrap2,self.dtv=make_tree(pad,dcols,[0,80,220,80,80,80],height=14)
        self.dtv.column("cid",width=0,stretch=False)
        wrap2.pack(fill="both",expand=True)
        self.dtv.tag_configure("diff",foreground=CLR["danger"])
        self.dtv.tag_configure("ok",foreground=CLR["success"])
        self.dtv.bind("<Double-1>",self._edit_qty)
        self._load_counts()
    def _load_counts(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            rows=conn.execute("SELECT id,count_no,counted_by,status,note,created FROM stock_counts ORDER BY id DESC").fetchall()
        for r in rows:
            tag="approved" if r[3]=="approved" else "draft"
            self.tv.insert("","end",values=(r[0],r[1],r[2],"✅ อนุมัติ" if r[3]=="approved" else "📝 ร่าง",r[4] or "",r[5]),tags=(tag,))
    def _new_count(self):
        user=self.app.current_user["username"]
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cno=next_number("CNT","stock_counts","count_no")
        with get_conn() as conn:
            cid=conn.execute("INSERT INTO stock_counts(count_no,counted_by,status,created) VALUES(?,?,'draft',?)",(cno,user,now)).lastrowid
            for pid,qty in conn.execute("SELECT id,quantity FROM products").fetchall():
                conn.execute("INSERT INTO stock_count_items(count_id,product_id,system_qty,counted_qty) VALUES(?,?,?,?)",(cid,pid,qty,qty))
            conn.commit()
        self._load_counts()
        messagebox.showinfo("สำเร็จ",f"เปิดรอบนับ {cno} แล้ว")
    def _open_count(self):
        sel=self.tv.selection()
        if not sel: return
        self._cur_cid=self.tv.item(sel[0])["values"][0]
        self._cur_status=self.tv.item(sel[0])["values"][3]
        self.dtv.delete(*self.dtv.get_children())
        with get_conn() as conn:
            rows=conn.execute("""SELECT ci.id,p.code,p.name,ci.system_qty,ci.counted_qty,ci.diff
                FROM stock_count_items ci JOIN products p ON ci.product_id=p.id
                WHERE ci.count_id=? ORDER BY p.name""",(self._cur_cid,)).fetchall()
        for r in rows:
            diff=r[5] or 0
            tag="diff" if diff!=0 else "ok"
            self.dtv.insert("","end",values=(r[0],r[1],r[2],f"{r[3]:g}",f"{r[4]:g}",f"{'+' if diff>0 else ''}{diff:g}"),tags=(tag,))
    def _edit_qty(self,event):
        if not hasattr(self,"_cur_status") or "อนุมัติ" in str(self._cur_status): return
        sel=self.dtv.selection()
        if not sel: return
        v=self.dtv.item(sel[0])["values"]
        ciid,name,sys_qty=v[0],v[2],float(v[3])
        from tkinter.simpledialog import askfloat
        nq=askfloat("กรอกยอดนับ",f"{name}\nระบบ: {sys_qty:g}  นับจริง:",minvalue=0,parent=self)
        if nq is None: return
        with get_conn() as conn:
            conn.execute("UPDATE stock_count_items SET counted_qty=?,diff=? WHERE id=?",(nq,nq-sys_qty,ciid)); conn.commit()
        self._open_count()
    def _approve(self):
        sel=self.tv.selection()
        if not sel: return
        cid=self.tv.item(sel[0])["values"][0]
        if "อนุมัติ" in str(self.tv.item(sel[0])["values"][3]):
            messagebox.showinfo("แจ้งเตือน","รอบนี้อนุมัติแล้ว"); return
        if not messagebox.askyesno("ยืนยัน","อนุมัติและปรับสต็อกตามยอดนับ? ไม่สามารถย้อนกลับได้"): return
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user=self.app.current_user["username"]
        with get_conn() as conn:
            for pid,counted,diff in conn.execute("SELECT product_id,counted_qty,diff FROM stock_count_items WHERE count_id=?",(cid,)).fetchall():
                if diff!=0:
                    conn.execute("UPDATE products SET quantity=?,updated=? WHERE id=?",(counted,now,pid))
                    conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date,user) VALUES(?,?,?,?,?,?)",(pid,"ADJ",diff,"ปรับยอดจากนับสต็อก",now,user))
            conn.execute("UPDATE stock_counts SET status='approved',completed=? WHERE id=?",(now,cid))
            conn.commit()
        audit(user,"STOCK_COUNT_APPROVE",f"count_id={cid}")
        messagebox.showinfo("สำเร็จ","ปรับยอดสต็อกเรียบร้อย")
        self._load_counts(); self._open_count()
    def _delete(self):
        sel=self.tv.selection()
        if not sel: return
        cid=self.tv.item(sel[0])["values"][0]
        if messagebox.askyesno("ยืนยัน","ลบรอบนับนี้ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM stock_count_items WHERE count_id=?",(cid,))
                conn.execute("DELETE FROM stock_counts WHERE id=?",(cid,))
                conn.commit()
            self.dtv.delete(*self.dtv.get_children())
            self._load_counts()


# ══════════════════════════════════════════════════════
#  CUSTOMER CREDIT FRAME
# ══════════════════════════════════════════════════════
class CustomerCreditFrame(tk.Frame):
    NAME = "customer_credit"
    def __init__(self,parent,app):
        super().__init__(parent,bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"💳 เครดิต / หนี้ลูกค้า","ติดตามยอดค้างชำระและรับชำระหนี้")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        with get_conn() as conn:
            total_debt=conn.execute("SELECT COALESCE(SUM(credit_balance),0) FROM customers WHERE credit_balance>0").fetchone()[0]
            debtors=conn.execute("SELECT COUNT(*) FROM customers WHERE credit_balance>0").fetchone()[0]
        r1=tk.Frame(pad,bg=CLR["bg"]); r1.pack(fill="x",pady=(0,12))
        for i,(t,v,col) in enumerate([("💳 ลูกหนี้",f"{debtors} คน",CLR["warning"]),("💰 ยอดค้างรวม",f"฿{total_debt:,.2f}",CLR["danger"])]):
            c=card(r1,padx=20,pady=14); c.grid(row=0,column=i,sticky="nsew",padx=(0,12) if i<1 else 0)
            r1.columnconfigure(i,weight=1)
            tk.Label(c,text=t,font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(anchor="w")
            tk.Label(c,text=v,font=("Segoe UI",18,"bold"),bg=CLR["card"],fg=col).pack(anchor="w")
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,8))
        self._sv=tk.StringVar(); self._sv.trace_add("write",lambda *_:self._load())
        se=tk.Frame(tb,bg=CLR["border"],padx=1,pady=1); se.pack(side="left")
        tk.Entry(se,textvariable=self._sv,font=FONT,width=22,bg=CLR["entry_bg"],fg=CLR["text"],relief="flat",insertbackground=CLR["text"]).pack(padx=6,pady=4)
        btn_success(tb,"💵 รับชำระหนี้",self._receive).pack(side="left",padx=(8,0))
        btn_primary(tb,"💳 ตั้งวงเงิน",self._set_limit).pack(side="left",padx=(6,0))
        btn_warn(tb,"📋 ประวัติ",self._history).pack(side="left",padx=(6,0))
        cols=("id","รหัส","ชื่อ","วงเงิน","ยอดค้าง","คงเหลือ")
        wrap,self.tv=make_tree(pad,cols,[0,80,160,100,100,110],height=10)
        self.tv.column("id",width=0,stretch=False); wrap.pack(fill="x")
        self.tv.tag_configure("debt",foreground=CLR["danger"])
        tk.Label(pad,text="📜 ประวัติ",font=FONT_B,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(10,4))
        hcols=("วันที่","ประเภท","จำนวน","ยอดคงเหลือ","หมายเหตุ")
        hwrap,self.htv=make_tree(pad,hcols,[140,90,90,100,200],height=8)
        hwrap.pack(fill="both",expand=True)
    def _load(self,*_):
        kw=f"%{self._sv.get()}%"
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            rows=conn.execute("SELECT id,code,name,credit_limit,credit_balance FROM customers WHERE name LIKE ? OR code LIKE ? ORDER BY credit_balance DESC",(kw,kw)).fetchall()
        for r in rows:
            tag="debt" if r[4]>0 else ""
            self.tv.insert("","end",values=(r[0],r[1],r[2],f"฿{r[3]:,.0f}",f"฿{r[4]:,.2f}",f"฿{r[3]-r[4]:,.2f}"),tags=(tag,) if tag else ())
    def _sel(self):
        sel=self.tv.selection()
        if not sel: messagebox.showwarning("แจ้งเตือน","เลือกลูกค้าก่อน"); return None
        return self.tv.item(sel[0])["values"]
    def _receive(self):
        v=self._sel()
        if not v: return
        cid,name=v[0],v[2]
        from tkinter.simpledialog import askfloat
        amt=askfloat("รับชำระ",f"รับชำระจาก '{name}' (฿):",minvalue=0.01,parent=self)
        if not amt: return
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user=self.app.current_user["username"]
        with get_conn() as conn:
            conn.execute("UPDATE customers SET credit_balance=MAX(0,credit_balance-?) WHERE id=?",(amt,cid))
            nb=conn.execute("SELECT credit_balance FROM customers WHERE id=?",(cid,)).fetchone()[0]
            conn.execute("INSERT INTO customer_credit(customer_id,type,amount,balance,note,date,created_by) VALUES(?,?,?,?,?,?,?)",(cid,"PAYMENT",amt,nb,"รับชำระหนี้",now,user))
            conn.commit()
        audit(user,"CREDIT_PAYMENT",f"cust={name} amt={amt}")
        messagebox.showinfo("สำเร็จ",f"รับชำระ ฿{amt:,.2f}  ค้าง ฿{nb:,.2f}")
        self.refresh()
    def _set_limit(self):
        v=self._sel()
        if not v: return
        cid,name=v[0],v[2]
        from tkinter.simpledialog import askfloat
        lim=askfloat("วงเงิน",f"วงเงินสูงสุด '{name}' (฿):",minvalue=0,parent=self)
        if lim is None: return
        with get_conn() as conn:
            conn.execute("UPDATE customers SET credit_limit=? WHERE id=?",(lim,cid)); conn.commit()
        messagebox.showinfo("สำเร็จ",f"ตั้งวงเงิน ฿{lim:,.0f} ให้ {name}")
        self._load()
    def _history(self):
        v=self._sel()
        if not v: return
        cid=v[0]
        self.htv.delete(*self.htv.get_children())
        type_map={"CHARGE":"🔴 ค้าง","PAYMENT":"🟢 รับชำระ","ADJUST":"🔧 ปรับ"}
        with get_conn() as conn:
            for r in conn.execute("SELECT date,type,amount,balance,note FROM customer_credit WHERE customer_id=? ORDER BY id DESC LIMIT 50",(cid,)).fetchall():
                self.htv.insert("","end",values=(r[0],type_map.get(r[1],r[1]),f"฿{r[2]:,.2f}",f"฿{r[3]:,.2f}",r[4] or ""))


# ══════════════════════════════════════════════════════
#  GENERIC PDF HELPER
# ══════════════════════════════════════════════════════
def _make_pdf_generic(path, title, headers, rows, footer=""):
    if not HAS_RL: return
    doc = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=2*cm, bottomMargin=1.5*cm)
    elems = []
    elems.append(Paragraph(f"<b>{title}</b>",
                            ParagraphStyle("T", fontSize=15, spaceAfter=4, alignment=1)))
    elems.append(Paragraph(
        f"วันที่พิมพ์: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("S", fontSize=9, textColor=rl_colors.grey, alignment=1, spaceAfter=14)))
    n = len(headers)
    avail = 18*cm
    col_w = [avail/n]*n
    data  = [headers] + [[str(c) for c in r] for r in rows]
    tbl   = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0), rl_colors.HexColor("#1E293B")),
        ("TEXTCOLOR",   (0,0),(-1,0), rl_colors.white),
        ("FONTSIZE",    (0,0),(-1,0), 9),
        ("FONTSIZE",    (0,1),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.white,rl_colors.HexColor("#F8FAFC")]),
        ("GRID",        (0,0),(-1,-1),0.4,rl_colors.HexColor("#E2E8F0")),
        ("TOPPADDING",  (0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    elems.append(tbl)
    if footer:
        elems.append(Spacer(1,12))
        elems.append(Paragraph(footer,
                                ParagraphStyle("F",fontSize=10,
                                               textColor=rl_colors.HexColor("#1E293B"))))
    doc.build(elems)


# ══════════════════════════════════════════════════════
#  BRANCHES FRAME
# ══════════════════════════════════════════════════════
class BranchesFrame(tk.Frame):
    NAME = "branches"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app = app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad = tk.Frame(self, bg=CLR["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)
        page_title(pad, "🏪 จัดการสาขา", "เพิ่ม/แก้ไข/ลบสาขาในระบบ")
        tk.Frame(pad, bg=CLR["border"], height=1).pack(fill="x", pady=12)
        ic = card(pad, padx=22, pady=16); ic.pack(fill="x", pady=(0,12))
        tk.Label(ic, text="เพิ่มสาขาใหม่", font=FONT_B,
                 bg=CLR["card"], fg=CLR["text"]).grid(row=0,column=0,columnspan=10,sticky="w",pady=(0,8))
        self._bvars = {}
        for col,(k,lbl,w) in enumerate([("code","รหัส",8),("name","ชื่อสาขา",20),
                                         ("address","ที่อยู่",28),("phone","เบอร์",12)]):
            tk.Label(ic,text=lbl,font=FONT,bg=CLR["card"],fg=CLR["text_lt"]
                     ).grid(row=1,column=col*2,sticky="w",padx=(0,4))
            v = tk.StringVar()
            tk.Entry(ic,textvariable=v,font=FONT,width=w,bg=CLR["entry_bg"],fg=CLR["text"],
                     insertbackground=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],highlightthickness=1
                     ).grid(row=1,column=col*2+1,padx=(0,10),ipady=5)
            self._bvars[k] = v
        btn_primary(ic,"➕ เพิ่ม",self._add).grid(row=1,column=8)
        cols=("id","รหัส","ชื่อสาขา","ที่อยู่","เบอร์","สถานะ")
        wrap,self.tv=make_tree(pad,cols,[0,70,180,250,120,80],height=14)
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(10,0))
        self.tv.column("id",width=0,stretch=False); wrap.pack(fill="both",expand=True)
        self.tv.bind("<Double-1>",lambda _:self._edit())
        btn_primary(ab,"✏️ แก้ไข",self._edit).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_warn(ab,"📦 ดูสต็อก",self._view_stock).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_danger(ab,"🗑️ ลบ",self._delete).pack(side="left")
    def _load(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            for r in conn.execute("SELECT id,code,name,address,phone,active FROM branches ORDER BY id").fetchall():
                self.tv.insert("","end",values=(r[0],r[1],r[2],r[3] or "-",r[4] or "-",
                                                "✅ เปิด" if r[5] else "❌ ปิด"))
    def _add(self):
        code=self._bvars["code"].get().strip(); name=self._bvars["name"].get().strip()
        if not code or not name:
            messagebox.showwarning("แจ้งเตือน","กรุณากรอกรหัสและชื่อสาขา"); return
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO branches(code,name,address,phone) VALUES(?,?,?,?)",
                             (code,name,self._bvars["address"].get(),self._bvars["phone"].get()))
                conn.commit()
            for v in self._bvars.values(): v.set("")
            self._load()
        except: messagebox.showerror("ผิดพลาด","รหัสสาขานี้มีอยู่แล้ว")
    def _sel(self):
        sel=self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน","กรุณาเลือกสาขาก่อน"); return None
        return self.tv.item(sel[0])["values"]
    def _edit(self):
        row=self._sel()
        if not row: return
        bid,code,name,addr,phone,_=row
        dlg=tk.Toplevel(self); dlg.title(f"แก้ไข — {name}")
        dlg.geometry("400x260"); dlg.configure(bg=CLR["bg"]); dlg.grab_set()
        pad=tk.Frame(dlg,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text=f"แก้ไข: {name}",font=FONT_H,bg=CLR["bg"],fg=CLR["text"]
                 ).pack(anchor="w",pady=(0,12))
        ev={}
        for k,lbl,val in [("name","ชื่อสาขา",name),
                           ("address","ที่อยู่",addr if addr!="-" else ""),
                           ("phone","เบอร์",phone if phone!="-" else "")]:
            tk.Label(pad,text=lbl,font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(anchor="w")
            v=tk.StringVar(value=val)
            tk.Entry(pad,textvariable=v,font=FONT,bg=CLR["entry_bg"],fg=CLR["text"],
                     insertbackground=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],highlightthickness=1
                     ).pack(fill="x",ipady=5,pady=(2,6))
            ev[k]=v
        def save():
            with get_conn() as conn:
                conn.execute("UPDATE branches SET name=?,address=?,phone=? WHERE id=?",
                             (ev["name"].get(),ev["address"].get(),ev["phone"].get(),bid))
                conn.commit()
            self._load(); dlg.destroy()
        br=tk.Frame(pad,bg=CLR["bg"]); br.pack(fill="x",pady=(6,0))
        btn_primary(br,"💾 บันทึก",save).pack(side="right")
        tk.Button(br,text="ยกเลิก",font=FONT,bg=CLR["border"],fg=CLR["text"],
                  relief="flat",padx=14,pady=7,cursor="hand2",
                  command=dlg.destroy).pack(side="right",padx=(0,8))
    def _delete(self):
        row=self._sel()
        if not row: return
        bid,code,name=row[0],row[1],row[2]
        if code=="HQ":
            messagebox.showerror("ผิดพลาด","ไม่สามารถลบสาขาหลักได้"); return
        if messagebox.askyesno("ยืนยัน",f"ลบสาขา '{name}' ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM branches WHERE id=?",(bid,)); conn.commit()
            self._load()
    def _view_stock(self):
        row=self._sel()
        if not row: return
        bid,_,bname=row[0],row[1],row[2]
        dlg=tk.Toplevel(self); dlg.title(f"สต็อก — {bname}")
        dlg.geometry("680x460"); dlg.configure(bg=CLR["bg"])
        pad=tk.Frame(dlg,bg=CLR["bg"],padx=16,pady=16); pad.pack(fill="both",expand=True)
        tk.Label(pad,text=f"📦 สต็อกสาขา: {bname}",font=FONT_H,
                 bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,10))
        cols=("รหัส","ชื่อสินค้า","หน่วย","คงเหลือ")
        wrap,tv=make_tree(pad,cols,[90,250,80,100],height=15)
        wrap.pack(fill="both",expand=True)
        with get_conn() as conn:
            rows=conn.execute("""
                SELECT p.code,p.name,p.unit,
                       COALESCE(bs.quantity,p.quantity) as qty
                FROM products p
                LEFT JOIN branch_stock bs ON bs.product_id=p.id AND bs.branch_id=?
                ORDER BY p.name
            """,(bid,)).fetchall()
        for r in rows: tv.insert("","end",values=r)


# ══════════════════════════════════════════════════════
#  SUPPLIERS FRAME
# ══════════════════════════════════════════════════════
class SuppliersFrame(tk.Frame):
    NAME = "suppliers"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"🏭 ซัพพลายเออร์","จัดการข้อมูลผู้จัดจำหน่าย")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        ic=card(pad,padx=22,pady=16); ic.pack(fill="x",pady=(0,12))
        tk.Label(ic,text="เพิ่มซัพพลายเออร์",font=FONT_B,bg=CLR["card"],fg=CLR["text"]
                 ).grid(row=0,column=0,columnspan=12,sticky="w",pady=(0,8))
        self._sv={}
        for col,(k,lbl,w) in enumerate([("code","รหัส",8),("name","ชื่อ",22),
                                         ("contact","ผู้ติดต่อ",16),("phone","เบอร์",12),("address","ที่อยู่",24)]):
            tk.Label(ic,text=lbl,font=FONT,bg=CLR["card"],fg=CLR["text_lt"]
                     ).grid(row=1,column=col*2,sticky="w",padx=(0,3))
            v=tk.StringVar()
            tk.Entry(ic,textvariable=v,font=FONT,width=w,bg=CLR["entry_bg"],fg=CLR["text"],
                     insertbackground=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],highlightthickness=1
                     ).grid(row=1,column=col*2+1,padx=(0,8),ipady=5)
            self._sv[k]=v
        btn_primary(ic,"➕ เพิ่ม",self._add).grid(row=1,column=10)
        cols=("id","รหัส","ชื่อ","ผู้ติดต่อ","เบอร์","ที่อยู่")
        wrap,self.tv=make_tree(pad,cols,[0,70,180,130,110,220],height=14)
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(10,0))
        self.tv.column("id",width=0,stretch=False); wrap.pack(fill="both",expand=True)
        self.tv.bind("<Double-1>",lambda _:self._edit())
        btn_primary(ab,"✏️ แก้ไข",self._edit).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_danger(ab,"🗑️ ลบ",self._delete).pack(side="left")
    def _load(self):
        self.tv.delete(*self.tv.get_children())
        with get_conn() as conn:
            for r in conn.execute("SELECT id,code,name,contact,phone,address FROM suppliers ORDER BY name").fetchall():
                self.tv.insert("","end",values=(r[0],r[1],r[2],r[3] or "-",r[4] or "-",r[5] or "-"))
    def _add(self):
        code=self._sv["code"].get().strip(); name=self._sv["name"].get().strip()
        if not code or not name:
            messagebox.showwarning("แจ้งเตือน","กรุณากรอกรหัสและชื่อ"); return
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO suppliers(code,name,contact,phone,address) VALUES(?,?,?,?,?)",
                             (code,name,self._sv["contact"].get(),
                              self._sv["phone"].get(),self._sv["address"].get()))
                conn.commit()
            for v in self._sv.values(): v.set("")
            self._load()
        except: messagebox.showerror("ผิดพลาด","รหัสนี้มีอยู่แล้ว")
    def _sel(self):
        sel=self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน","กรุณาเลือกก่อน"); return None
        return self.tv.item(sel[0])["values"]
    def _edit(self):
        row=self._sel()
        if not row: return
        sid=row[0]
        dlg=tk.Toplevel(self); dlg.title("แก้ไขซัพพลายเออร์")
        dlg.geometry("400x300"); dlg.configure(bg=CLR["bg"]); dlg.grab_set()
        pad=tk.Frame(dlg,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text="แก้ไขข้อมูล",font=FONT_H,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,12))
        ev={}
        for k,lbl,val in [("name","ชื่อ",row[2]),
                           ("contact","ผู้ติดต่อ",row[3] if row[3]!="-" else ""),
                           ("phone","เบอร์",row[4] if row[4]!="-" else ""),
                           ("address","ที่อยู่",row[5] if row[5]!="-" else "")]:
            tk.Label(pad,text=lbl,font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(anchor="w")
            v=tk.StringVar(value=val)
            tk.Entry(pad,textvariable=v,font=FONT,bg=CLR["entry_bg"],fg=CLR["text"],
                     insertbackground=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],highlightthickness=1
                     ).pack(fill="x",ipady=5,pady=(2,6))
            ev[k]=v
        def save():
            with get_conn() as conn:
                conn.execute("UPDATE suppliers SET name=?,contact=?,phone=?,address=? WHERE id=?",
                             (ev["name"].get(),ev["contact"].get(),ev["phone"].get(),ev["address"].get(),sid))
                conn.commit()
            self._load(); dlg.destroy()
        br=tk.Frame(pad,bg=CLR["bg"]); br.pack(fill="x",pady=(6,0))
        btn_primary(br,"💾 บันทึก",save).pack(side="right")
        tk.Button(br,text="ยกเลิก",font=FONT,bg=CLR["border"],fg=CLR["text"],
                  relief="flat",padx=14,pady=7,cursor="hand2",
                  command=dlg.destroy).pack(side="right",padx=(0,8))
    def _delete(self):
        row=self._sel()
        if not row: return
        if messagebox.askyesno("ยืนยัน",f"ลบ '{row[2]}' ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM suppliers WHERE id=?",(row[0],)); conn.commit()
            self._load()


# ══════════════════════════════════════════════════════
#  PURCHASE ORDER FRAME
# ══════════════════════════════════════════════════════
class POFrame(tk.Frame):
    NAME = "purchase_orders"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"📋 ใบสั่งซื้อ (PO)","จัดการใบสั่งซื้อและรับสินค้าจากซัพพลายเออร์")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,10))
        btn_primary(tb,"➕ สร้าง PO ใหม่",self._new_po).pack(side="left")
        tk.Frame(tb,bg=CLR["bg"],width=8).pack(side="left")
        tk.Label(tb,text="สถานะ:",font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(side="left")
        self._status_var=tk.StringVar(value="ทั้งหมด")
        cb=ttk.Combobox(tb,textvariable=self._status_var,
                        values=["ทั้งหมด","pending","approved","received"],
                        font=FONT,state="readonly",width=14)
        cb.pack(side="left",padx=8,ipady=4)
        cb.bind("<<ComboboxSelected>>",lambda _:self._load())
        cols=("id","เลขที่ PO","ซัพพลายเออร์","สาขา","สถานะ","ยอดรวม","วันที่","สร้างโดย")
        wrap,self.tv=make_tree(pad,cols,[0,140,180,100,90,100,140,110],height=16)
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(10,0))
        self.tv.column("id",width=0,stretch=False); wrap.pack(fill="both",expand=True)
        self.tv.bind("<Double-1>",lambda _:self._open_po())
        self.tv.tag_configure("pending", foreground=CLR["warning"])
        self.tv.tag_configure("approved",foreground=CLR["accent"])
        self.tv.tag_configure("received",foreground=CLR["success"])
        btn_primary(ab,"📄 เปิด PO",self._open_po).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_success(ab,"✅ Approve",self._approve).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_warn(ab,"📦 รับสินค้า",self._receive).pack(side="left")
        tk.Frame(ab,bg=CLR["bg"],width=8).pack(side="left")
        btn_danger(ab,"🗑️ ลบ",self._delete).pack(side="left")
        tk.Label(ab,text="💡 ดับเบิลคลิกเพื่อเปิด",
                 font=("Segoe UI",9),bg=CLR["bg"],fg=CLR["text_lt"]).pack(side="right")
    def _load(self):
        self.tv.delete(*self.tv.get_children())
        st=self._status_var.get()
        sql="""SELECT po.id,po.po_number,COALESCE(s.name,'-'),COALESCE(b.name,'-'),
                      po.status,po.total,po.created,po.created_by
               FROM purchase_orders po
               LEFT JOIN suppliers s ON s.id=po.supplier_id
               LEFT JOIN branches  b ON b.id=po.branch_id"""
        params=()
        if st!="ทั้งหมด": sql+=" WHERE po.status=?"; params=(st,)
        sql+=" ORDER BY po.created DESC"
        with get_conn() as conn:
            for r in conn.execute(sql,params).fetchall():
                self.tv.insert("","end",
                               values=(r[0],r[1],r[2],r[3],r[4],f"{r[5]:,.2f}",r[6],r[7] or "-"),
                               tags=(r[4],))
    def _sel(self):
        sel=self.tv.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน","กรุณาเลือก PO ก่อน"); return None
        return self.tv.item(sel[0])["values"]
    def _new_po(self): PODialog(self,None,self.app,self._load)
    def _open_po(self):
        row=self._sel()
        if row: PODialog(self,row[0],self.app,self._load)
    def _approve(self):
        row=self._sel()
        if not row: return
        pid,pno,_,_,status=row[0],row[1],row[2],row[3],row[4]
        if status!="pending":
            messagebox.showinfo("แจ้งเตือน","อนุมัติได้เฉพาะ PO ที่ pending"); return
        if messagebox.askyesno("ยืนยัน",f"อนุมัติ {pno} ใช่ไหม?"):
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with get_conn() as conn:
                conn.execute("UPDATE purchase_orders SET status='approved',approved_by=?,approved=? WHERE id=?",
                             (self.app.current_user["username"],now,pid))
                conn.commit()
            self._load()
    def _receive(self):
        row=self._sel()
        if not row: return
        pid,pno,_,_,status=row[0],row[1],row[2],row[3],row[4]
        if status not in ("approved","pending"):
            messagebox.showinfo("แจ้งเตือน","รับสินค้าได้เฉพาะ PO ที่ approved/pending"); return
        if not messagebox.askyesno("ยืนยัน",f"รับสินค้าตาม PO {pno} และอัปเดตสต็อก ใช่ไหม?"): return
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user=self.app.current_user["username"]
        with get_conn() as conn:
            items=conn.execute("SELECT product_id,quantity FROM po_items WHERE po_id=?",(pid,)).fetchall()
            branch_id=conn.execute("SELECT branch_id FROM purchase_orders WHERE id=?",(pid,)).fetchone()[0]
            for product_id,qty in items:
                conn.execute("UPDATE products SET quantity=quantity+?,updated=? WHERE id=?",(qty,now,product_id))
                conn.execute("""INSERT INTO branch_stock(branch_id,product_id,quantity) VALUES(?,?,?)
                                ON CONFLICT(branch_id,product_id) DO UPDATE SET quantity=quantity+?""",
                             (branch_id,product_id,qty,qty))
                conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date,user,branch_id) VALUES(?,?,?,?,?,?,?)",
                             (product_id,"IN",qty,f"รับตาม PO {pno}",now,user,branch_id))
            conn.execute("UPDATE purchase_orders SET status='received',received=? WHERE id=?",(now,pid))
            conn.commit()
        messagebox.showinfo("สำเร็จ","รับสินค้าและอัปเดตสต็อกสำเร็จ"); self._load()
    def _delete(self):
        row=self._sel()
        if not row: return
        pid,pno,_,_,status=row[0],row[1],row[2],row[3],row[4]
        if status=="received":
            messagebox.showerror("ผิดพลาด","ไม่สามารถลบ PO ที่รับสินค้าแล้ว"); return
        if messagebox.askyesno("ยืนยัน",f"ลบ {pno} ใช่ไหม?"):
            with get_conn() as conn:
                conn.execute("DELETE FROM po_items WHERE po_id=?",(pid,))
                conn.execute("DELETE FROM purchase_orders WHERE id=?",(pid,)); conn.commit()
            self._load()


class PODialog(tk.Toplevel):
    def __init__(self, parent, po_id, app, callback):
        super().__init__(parent)
        self.po_id=po_id; self.app=app; self.callback=callback; self.cart=[]
        self.title("ดู PO" if po_id else "สร้าง PO ใหม่")
        self.geometry("860x620"); self.configure(bg=CLR["bg"]); self.grab_set()
        self._build()
        if po_id: self._load_existing()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"],padx=20,pady=16); pad.pack(fill="both",expand=True)
        tk.Label(pad,text="📋 ใบสั่งซื้อ (PO)",font=FONT_H,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,10))
        hf=card(pad,padx=18,pady=14); hf.pack(fill="x",pady=(0,10))
        hf.columnconfigure(1,weight=1); hf.columnconfigure(3,weight=1)
        self._hvars={}
        with get_conn() as conn:
            suppliers=conn.execute("SELECT id,name FROM suppliers ORDER BY name").fetchall()
            branches=conn.execute("SELECT id,name FROM branches WHERE active=1 ORDER BY name").fetchall()
        sup_map={s[1]:s[0] for s in suppliers}; bra_map={b[1]:b[0] for b in branches}
        self._sup_map=sup_map; self._bra_map=bra_map
        for row_i,items in enumerate([
            [("ซัพพลายเออร์","supplier","combo",list(sup_map.keys())),
             ("สาขา","branch","combo",list(bra_map.keys()))],
            [("หมายเหตุ","note","entry",None),("","","","")]
        ]):
            for col_i,(lbl,key,wtype,vals) in enumerate(items):
                if not lbl: continue
                tk.Label(hf,text=lbl,font=FONT,bg=CLR["card"],fg=CLR["text_lt"]
                         ).grid(row=row_i,column=col_i*2,sticky="w",padx=(0,6),pady=4)
                v=tk.StringVar()
                if wtype=="combo":
                    w=ttk.Combobox(hf,textvariable=v,values=vals,font=FONT,
                                   state="readonly" if self.po_id else "normal",width=26)
                else:
                    w=tk.Entry(hf,textvariable=v,font=FONT,width=30,
                               bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                               relief="solid",highlightbackground=CLR["border"],highlightthickness=1,
                               state="readonly" if self.po_id else "normal")
                w.grid(row=row_i,column=col_i*2+1,sticky="ew",padx=(0,16),ipady=5)
                self._hvars[key]=v
        if not self.po_id:
            af=card(pad,padx=14,pady=10); af.pack(fill="x",pady=(0,8))
            tk.Label(af,text="เพิ่มสินค้า:",font=FONT_B,bg=CLR["card"],fg=CLR["text"]
                     ).grid(row=0,column=0,sticky="w",columnspan=8)
            with get_conn() as conn:
                prods=conn.execute("SELECT id,code,name,price FROM products ORDER BY name").fetchall()
            self._prod_map2={f"[{p[1]}] {p[2]}":(p[0],p[3]) for p in prods}
            self._item_prod=tk.StringVar(); self._item_qty=tk.StringVar(value="1")
            self._item_price=tk.StringVar()
            cb=ttk.Combobox(af,textvariable=self._item_prod,
                            values=list(self._prod_map2.keys()),font=FONT,state="readonly",width=34)
            cb.grid(row=1,column=0,padx=(0,8),ipady=4)
            cb.bind("<<ComboboxSelected>>",self._fill_price)
            col_idx=1
            for lbl,v,w in [("จำนวน",self._item_qty,8),("ราคา/หน่วย",self._item_price,10)]:
                tk.Label(af,text=lbl,font=FONT,bg=CLR["card"],fg=CLR["text_lt"]
                         ).grid(row=1,column=col_idx,sticky="w",padx=(8,4))
                tk.Entry(af,textvariable=v,font=FONT,width=w,
                         bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                         relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                         ).grid(row=1,column=col_idx+1,ipady=4)
                col_idx+=2
            btn_success(af,"➕ เพิ่ม",self._add_item).grid(row=1,column=col_idx+1,padx=(12,0))
        cols=("product_id","สินค้า","จำนวน","ราคา/หน่วย","รวม")
        wrap,self.itv=make_tree(pad,cols,[0,320,90,110,110],height=10)
        self.itv.column("product_id",width=0,stretch=False); wrap.pack(fill="both",expand=True)
        bf=tk.Frame(pad,bg=CLR["bg"]); bf.pack(fill="x",pady=(10,0))
        self._total_lbl=tk.Label(bf,text="ยอดรวม: 0.00 บาท",
                                  font=("Segoe UI",13,"bold"),bg=CLR["bg"],fg=CLR["success"])
        self._total_lbl.pack(side="left")
        if not self.po_id:
            btn_primary(bf,"💾 บันทึก PO",self._save).pack(side="right")
        tk.Button(bf,text="📄 Export PDF",font=FONT_B,bg=CLR["warning"],fg=CLR["white"],
                  activebackground="#D97706",relief="flat",padx=14,pady=7,cursor="hand2",
                  command=self._export_pdf).pack(side="right",padx=(0,8))
        tk.Button(bf,text="ปิด",font=FONT,bg=CLR["border"],fg=CLR["text"],
                  relief="flat",padx=14,pady=7,cursor="hand2",
                  command=self.destroy).pack(side="right",padx=(0,8))
    def _fill_price(self,_=None):
        key=self._item_prod.get()
        if key in self._prod_map2: self._item_price.set(f"{self._prod_map2[key][1]:.2f}")
    def _add_item(self):
        key=self._item_prod.get()
        if not key: return
        try:
            qty=float(self._item_qty.get()); price=float(self._item_price.get())
        except: messagebox.showerror("ผิดพลาด","จำนวน/ราคาไม่ถูกต้อง"); return
        pid,_=self._prod_map2[key]; name=key.split("] ",1)[-1]
        self.cart.append((pid,name,qty,price)); self._refresh_items()
    def _refresh_items(self):
        self.itv.delete(*self.itv.get_children())
        total=0
        for pid,name,qty,price in self.cart:
            sub=qty*price; total+=sub
            self.itv.insert("","end",values=(pid,name,f"{qty:g}",f"{price:,.2f}",f"{sub:,.2f}"))
        self._total_lbl.config(text=f"ยอดรวม: {total:,.2f} บาท")
    def _load_existing(self):
        with get_conn() as conn:
            po=conn.execute("""SELECT po.po_number,COALESCE(s.name,''),COALESCE(b.name,''),po.note,po.total
                               FROM purchase_orders po
                               LEFT JOIN suppliers s ON s.id=po.supplier_id
                               LEFT JOIN branches  b ON b.id=po.branch_id
                               WHERE po.id=?""",(self.po_id,)).fetchone()
            items=conn.execute("""SELECT pi.product_id,p.name,pi.quantity,pi.unit_price
                                  FROM po_items pi JOIN products p ON p.id=pi.product_id
                                  WHERE pi.po_id=?""",(self.po_id,)).fetchall()
        if po:
            self._hvars["supplier"].set(po[1]); self._hvars["branch"].set(po[2])
            self._hvars["note"].set(po[3] or "")
        self.cart=[(r[0],r[1],r[2],r[3]) for r in items]; self._refresh_items()
    def _save(self):
        sup_name=self._hvars["supplier"].get(); bra_name=self._hvars["branch"].get()
        if not sup_name or not bra_name:
            messagebox.showwarning("แจ้งเตือน","กรุณาเลือกซัพพลายเออร์และสาขา"); return
        if not self.cart:
            messagebox.showwarning("แจ้งเตือน","กรุณาเพิ่มสินค้าอย่างน้อย 1 รายการ"); return
        sup_id=self._sup_map.get(sup_name); bra_id=self._bra_map.get(bra_name)
        total=sum(q*p for _,_,q,p in self.cart)
        po_no=next_number("PO","purchase_orders","po_number")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); user=self.app.current_user["username"]
        with get_conn() as conn:
            cur=conn.execute("""INSERT INTO purchase_orders(po_number,supplier_id,branch_id,total,note,created_by,created)
                                VALUES(?,?,?,?,?,?,?)""",(po_no,sup_id,bra_id,total,self._hvars["note"].get(),user,now))
            po_id=cur.lastrowid
            for pid,_,qty,price in self.cart:
                conn.execute("INSERT INTO po_items(po_id,product_id,quantity,unit_price) VALUES(?,?,?,?)",
                             (po_id,pid,qty,price))
            conn.commit()
        messagebox.showinfo("สำเร็จ",f"สร้าง PO {po_no} สำเร็จ")
        self.callback(); self.destroy()
    def _export_pdf(self):
        if not HAS_RL: messagebox.showerror("ผิดพลาด","ต้องการ reportlab"); return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",
             filetypes=[("PDF","*.pdf")],initialfile="PO_export.pdf")
        if not path: return
        rows=[(r[1],f"{r[2]:g}",f"{r[3]:,.2f}",f"{r[2]*r[3]:,.2f}") for r in self.cart]
        total=sum(r[2]*r[3] for r in self.cart)
        _make_pdf_generic(path,"ใบสั่งซื้อ (PO)",["สินค้า","จำนวน","ราคา/หน่วย","รวม"],
                          rows,footer=f"ยอดรวม: {total:,.2f} บาท")
        messagebox.showinfo("สำเร็จ",f"Export PDF สำเร็จ\n{path}")


# ══════════════════════════════════════════════════════
#  SALES POS
# ══════════════════════════════════════════════════════
class SalesFrame(tk.Frame):
    NAME = "sales"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app; self.cart=[]
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self.cart=[]; self._build()
        self.after(100,self._bind_keys)
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=24,pady=20)
        page_title(pad,"🛒 ระบบขาย (POS)","บันทึกการขายและออกใบเสร็จ")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=10)
        main=tk.Frame(pad,bg=CLR["bg"]); main.pack(fill="both",expand=True)
        main.columnconfigure(0,weight=3); main.columnconfigure(1,weight=2)
        left=tk.Frame(main,bg=CLR["bg"]); left.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        sf=card(left,padx=12,pady=8); sf.pack(fill="x",pady=(0,8))
        self._srch=tk.StringVar(); self._srch.trace_add("write",lambda *_:self._load_products())
        tk.Label(sf,text="🔍",bg=CLR["card"],font=FONT).pack(side="left")
        tk.Entry(sf,textvariable=self._srch,font=FONT,bg=CLR["card"],relief="flat",width=30).pack(side="left",padx=6)
        pf=card(left); pf.pack(fill="both",expand=True,pady=(0,8))
        self._prod_canvas=tk.Canvas(pf,bg=CLR["card"],highlightthickness=0)
        sb=ttk.Scrollbar(pf,orient="vertical",command=self._prod_canvas.yview)
        self._prod_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self._prod_canvas.pack(fill="both",expand=True)
        self._prod_inner=tk.Frame(self._prod_canvas,bg=CLR["card"])
        self._prod_canvas.create_window((0,0),window=self._prod_inner,anchor="nw")
        self._prod_inner.bind("<Configure>",
            lambda e: self._prod_canvas.configure(scrollregion=self._prod_canvas.bbox("all")))
        self._load_products()
        # Right panel — grid layout: row0=label, row1=cart(expand), row2=del btn, row3=payment(fixed)
        right=tk.Frame(main,bg=CLR["bg"]); right.grid(row=0,column=1,sticky="nsew")
        main.rowconfigure(0,weight=1)
        right.rowconfigure(1,weight=1)   # cart table expands
        right.columnconfigure(0,weight=1)

        tk.Label(right,text="🛒 ตะกร้า",font=FONT_B,
                 bg=CLR["bg"],fg=CLR["text"]).grid(row=0,column=0,sticky="w")

        cols=("pid","สินค้า","จำนวน","ราคา","รวม")
        wrap,self.ctv=make_tree(right,cols,[0,180,60,80,80],height=11)
        self.ctv.column("pid",width=0,stretch=False)
        wrap.grid(row=1,column=0,sticky="nsew")

        btn_danger(right,"🗑️ ลบรายการ",self._remove_item).grid(
            row=2,column=0,sticky="w",pady=(6,0))

        # Payment card — always pinned at bottom (row 3, no expand)
        pc=card(right,padx=16,pady=14)
        pc.grid(row=3,column=0,sticky="ew",pady=(10,0))
        pc.columnconfigure(0,weight=1)

        # ── ส่วนลด ──────────────────────────────
        df=tk.Frame(pc,bg=CLR["card"]); df.pack(fill="x",pady=(0,6))
        tk.Label(df,text="ส่วนลด (บาท):",font=FONT,
                 bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._disc_var=tk.StringVar(value="0")
        self._disc_var.trace_add("write",lambda *_:self._update_total())
        tk.Entry(df,textvariable=self._disc_var,font=FONT,width=10,
                 bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                 relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                 ).pack(side="left",padx=8,ipady=4)

        # ── วิธีชำระ ────────────────────────────
        pf2=tk.Frame(pc,bg=CLR["card"]); pf2.pack(fill="x",pady=(0,6))
        tk.Label(pf2,text="วิธีชำระ:",font=FONT,
                 bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._pay_var=tk.StringVar(value="cash")
        self._pay_var.trace_add("write",lambda *_:self._on_pay_change())
        for val,lbl in [("cash","💵 เงินสด"),("transfer","📱 โอน"),("card","💳 บัตร")]:
            tk.Radiobutton(pf2,text=lbl,variable=self._pay_var,value=val,font=FONT,
                           bg=CLR["card"],fg=CLR["text"],selectcolor=CLR["accent"],
                           activebackground=CLR["card"],cursor="hand2"
                           ).pack(side="left",padx=(8,0))

        # ── ยอดรวม ──────────────────────────────
        # ── ระดับราคา ────────────────────────────
        ptf=tk.Frame(pc,bg=CLR["card"]); ptf.pack(fill="x",pady=(0,6))
        tk.Label(ptf,text="ระดับราคา:",font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._price_tier=tk.StringVar(value="retail")
        for val,lbl in [("retail","ปลีก"),("wholesale","ส่ง"),("member","สมาชิก")]:
            tk.Radiobutton(ptf,text=lbl,variable=self._price_tier,value=val,
                           font=("Segoe UI",9),bg=CLR["card"],fg=CLR["text"],
                           selectcolor=CLR["accent"],activebackground=CLR["card"],
                           cursor="hand2",command=self._load_products
                           ).pack(side="left",padx=(6,0))
        # ── ลูกค้า ──────────────────────────────
        cf2=tk.Frame(pc,bg=CLR["card"]); cf2.pack(fill="x",pady=(0,6))
        tk.Label(cf2,text="ลูกค้า:",font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._cust_var=tk.StringVar()
        tk.Entry(cf2,textvariable=self._cust_var,font=FONT,width=16,
                 bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                 relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                 ).pack(side="left",padx=(6,4),ipady=3)
        tk.Button(cf2,text="🔍",font=FONT,bg=CLR["border"],relief="flat",
                  padx=6,pady=3,cursor="hand2",
                  command=self._lookup_customer).pack(side="left")
        self._cust_info=tk.Label(cf2,text="",font=("Segoe UI",8),
                                  bg=CLR["card"],fg=CLR["accent"])
        self._cust_info.pack(side="left",padx=6)
        self._cust_id=None

        # ── โปรโมชั่น ────────────────────────────
        prf=tk.Frame(pc,bg=CLR["card"]); prf.pack(fill="x",pady=(0,6))
        tk.Label(prf,text="โปรโมชั่น:",font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._promo_var=tk.StringVar()
        tk.Entry(prf,textvariable=self._promo_var,font=FONT,width=14,
                 bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                 relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                 ).pack(side="left",padx=(6,4),ipady=3)
        tk.Button(prf,text="✔ ใช้",font=FONT,bg=CLR["border"],relief="flat",
                  padx=6,pady=3,cursor="hand2",
                  command=self._apply_promo).pack(side="left")
        self._promo_info=tk.Label(prf,text="",font=("Segoe UI",8),
                                   bg=CLR["card"],fg=CLR["success"])
        self._promo_info.pack(side="left",padx=6)
        self._promo_discount=0.0

        self._total_var=tk.StringVar(value="ยอดรวม: 0.00 บาท")
        tk.Label(pc,textvariable=self._total_var,font=("Segoe UI",15,"bold"),
                 bg=CLR["card"],fg=CLR["success"]).pack(anchor="w",pady=(0,4))

        # ── กรอกเงิน (เงินสด) ───────────────────
        self._cash_frame=tk.Frame(pc,bg=CLR["card"])
        self._cash_frame.pack(fill="x",pady=(0,6))
        cf_row=tk.Frame(self._cash_frame,bg=CLR["card"]); cf_row.pack(fill="x")
        tk.Label(cf_row,text="รับเงินมา (บาท):",font=FONT,
                 bg=CLR["card"],fg=CLR["text_lt"]).pack(side="left")
        self._recv_var=tk.StringVar(value="")
        self._recv_var.trace_add("write",lambda *_:self._update_change())
        tk.Entry(cf_row,textvariable=self._recv_var,font=FONT,width=12,
                 bg=CLR["entry_bg"],fg=CLR["text"],insertbackground=CLR["text"],
                 relief="solid",highlightbackground=CLR["border"],highlightthickness=1
                 ).pack(side="left",padx=8,ipady=4)
        # Quick-fill buttons
        qf=tk.Frame(self._cash_frame,bg=CLR["card"]); qf.pack(fill="x",pady=(4,0))
        for amt in [20,50,100,500,1000]:
            tk.Button(qf,text=f"฿{amt}",font=("Segoe UI",9),
                      bg=CLR["border"],fg=CLR["text"],relief="flat",
                      padx=6,pady=3,cursor="hand2",
                      command=lambda a=amt:self._recv_var.set(str(a))
                      ).pack(side="left",padx=(0,4))
        self._change_var=tk.StringVar(value="เงินทอน: —")
        tk.Label(self._cash_frame,textvariable=self._change_var,
                 font=FONT_B,bg=CLR["card"],fg=CLR["warning"]).pack(anchor="w",pady=(4,0))

        # ── QR Code (โอนเงิน) ───────────────────
        self._qr_frame=tk.Frame(pc,bg=CLR["card"])
        self._qr_frame.pack(fill="x",pady=(0,6))
        self._qr_canvas=tk.Canvas(self._qr_frame,bg=CLR["card"],
                                   highlightthickness=0,width=160,height=160)
        self._qr_canvas.pack(side="left",padx=(0,12))
        self._bank_lbl=tk.Label(self._qr_frame,text="",font=FONT,
                                 bg=CLR["card"],fg=CLR["text"],justify="left",wraplength=180)
        self._bank_lbl.pack(side="left",anchor="w")

        # initial state
        self._on_pay_change()

        btn_success(pc,"✅ ชำระเงิน [F12]",self._checkout).pack(fill="x",ipady=6)
        tk.Label(pc,text="⌨ F12=ชำระ  Del=ลบ  F5=ล้างตะกร้า  F2=ค้นหา  Ctrl+L=ล็อค",
                 font=("Segoe UI",7),bg=CLR["card"],fg=CLR["text_lt"]).pack(anchor="w")
    def _bind_keys(self):
        top=self.winfo_toplevel()
        top.bind("<F12>",lambda _:self._checkout())
        top.bind("<Delete>",lambda _:self._remove_item())
        top.bind("<F5>",lambda _:self._clear_cart())
        top.bind("<F2>",lambda _:self._srch_entry.focus_set() if hasattr(self,"_srch_entry") else None)
    def _clear_cart(self):
        if self.cart and messagebox.askyesno("ยืนยัน","ล้างตะกร้าทั้งหมด?"):
            self.cart=[]; self._refresh_cart()
    def _load_products(self):
        for w in self._prod_inner.winfo_children(): w.destroy()
        kw=f"%{self._srch.get()}%"
        tier=getattr(self,"_price_tier",None)
        t=tier.get() if tier else "retail"
        pc_sql={
            "retail":    "CASE WHEN sell_price>0 THEN sell_price ELSE price END",
            "wholesale": "CASE WHEN price_wholesale>0 THEN price_wholesale WHEN sell_price>0 THEN sell_price ELSE price END",
            "member":    "CASE WHEN price_member>0 THEN price_member WHEN sell_price>0 THEN sell_price ELSE price END",
        }.get(t,"CASE WHEN sell_price>0 THEN sell_price ELSE price END")
        with get_conn() as conn:
            prods=conn.execute(
                f"SELECT id,code,name,{pc_sql} as display_price,"
                "quantity FROM products "
                "WHERE (name LIKE ? OR code LIKE ?) AND quantity>0 ORDER BY name LIMIT 60",
                (kw,kw)).fetchall()
        cols=3
        for i,p in enumerate(prods):
            r,c=divmod(i,cols)
            f=tk.Frame(self._prod_inner,bg=CLR["card"],highlightbackground=CLR["border"],
                       highlightthickness=1,cursor="hand2",padx=8,pady=8)
            f.grid(row=r,column=c,padx=4,pady=4,sticky="ew")
            self._prod_inner.columnconfigure(c,weight=1)
            tk.Label(f,text=p[2][:22],font=FONT_B,bg=CLR["card"],fg=CLR["text"],
                     wraplength=130,justify="left").pack(anchor="w")
            price=p[3] if p[3] else 0.0
            tk.Label(f,text=f"฿{price:,.2f}  คงเหลือ:{p[4]:g}",
                     font=("Segoe UI",9),bg=CLR["card"],fg=CLR["text_lt"]).pack(anchor="w")
            pid=p[0]; pname=p[2]
            for w2 in (f,*f.winfo_children()):
                w2.bind("<Button-1>",lambda e,pid=pid,pn=pname,pr=price:self._add_to_cart(pid,pn,pr))
    def _add_to_cart(self,pid,name,price):
        for item in self.cart:
            if item[0]==pid:
                item[2]+=1; self._refresh_cart(); return
        self.cart.append([pid,name,1,price]); self._refresh_cart()
    def _refresh_cart(self):
        self.ctv.delete(*self.ctv.get_children())
        for item in self.cart:
            self.ctv.insert("","end",values=(item[0],item[1],f"{item[2]:g}",
                                             f"{item[3]:,.2f}",f"{item[2]*item[3]:,.2f}"))
        self._update_total()
    def _update_total(self):
        sub=sum(i[2]*i[3] for i in self.cart)
        try: disc=float(self._disc_var.get() or 0)
        except: disc=0
        self._total_var.set(f"ยอดรวม: {max(0,sub-disc):,.2f} บาท")
        self._update_change()

    def _get_total(self):
        sub=sum(i[2]*i[3] for i in self.cart)
        try: disc=float(self._disc_var.get() or 0)
        except: disc=0
        promo=getattr(self,"_promo_discount",0)
        return max(0, sub-disc-promo)

    def _update_change(self):
        try:
            recv=float(self._recv_var.get() or 0)
        except: recv=0
        total=self._get_total()
        change=recv-total
        if recv<=0:
            self._change_var.set("เงินทอน: —")
        elif change<0:
            self._change_var.set(f"เงินขาด: {abs(change):,.2f} บาท")
        else:
            self._change_var.set(f"เงินทอน: {change:,.2f} บาท")

    def _on_pay_change(self, *_):
        pay=self._pay_var.get()
        # Show/hide cash frame
        if pay=="cash":
            self._cash_frame.pack(fill="x",pady=(0,6))
            self._qr_frame.pack_forget()
        elif pay=="transfer":
            self._cash_frame.pack_forget()
            self._qr_frame.pack(fill="x",pady=(0,6))
            self._refresh_qr()
        else:
            self._cash_frame.pack_forget()
            self._qr_frame.pack_forget()

    def _refresh_qr(self):
        """Generate PromptPay QR and show bank info."""
        acct   = get_setting("bank_account","")
        bank   = get_setting("bank_name","")
        atype  = get_setting("bank_type","")
        aname  = get_setting("bank_holder","")
        total  = self._get_total()

        # Bank info label
        if acct:
            info=(f"ธนาคาร: {bank}\n"
                  f"ประเภท: {atype}\n"
                  f"เลขที่: {acct}\n"
                  f"ชื่อ: {aname}\n"
                  f"ยอด: {total:,.2f} บาท")
        else:
            info="ยังไม่ได้ตั้งค่าบัญชี\nไปที่ Settings > บัญชีร้าน"
        self._bank_lbl.config(text=info)

        # Generate QR (PromptPay EMV)
        self._qr_canvas.delete("all")
        if acct:
            try:
                qr_data=_make_promptpay_qr(acct, total)
                import qrcode as _qrlib
                img=_qrlib.make(qr_data)
                img=img.resize((155,155))
                from PIL import ImageTk
                self._qr_img=ImageTk.PhotoImage(img)
                self._qr_canvas.create_image(0,0,anchor="nw",image=self._qr_img)
            except Exception:
                # Fallback: show text QR placeholder
                self._qr_canvas.create_rectangle(5,5,155,155,outline=CLR["border"],width=2)
                self._qr_canvas.create_text(80,70,text="QR Code\n(ติดตั้ง qrcode\nและ pillow)",
                                             fill=CLR["text_lt"],font=("Segoe UI",9),
                                             justify="center")
        else:
            self._qr_canvas.create_rectangle(5,5,155,155,outline=CLR["border"],
                                              dash=(4,4),width=1)
            self._qr_canvas.create_text(80,80,text="ไม่มีข้อมูลบัญชี",
                                         fill=CLR["text_lt"],font=("Segoe UI",9))
    def _remove_item(self):
        sel=self.ctv.selection()
        if not sel: return
        pid=self.ctv.item(sel[0])["values"][0]
        self.cart=[i for i in self.cart if i[0]!=pid]; self._refresh_cart()
    def _lookup_customer(self):
        kw=self._cust_var.get().strip()
        if not kw: return
        with get_conn() as conn:
            r=conn.execute(
                "SELECT id,name,points FROM customers WHERE code=? OR phone=? OR name LIKE ?",
                (kw,kw,f"%{kw}%")).fetchone()
        if r:
            self._cust_id=r[0]
            self._cust_info.config(text=f"{r[1]}  แต้ม:{r[2]:,.1f}",fg=CLR["accent"])
        else:
            self._cust_id=None
            self._cust_info.config(text="ไม่พบลูกค้า",fg=CLR["danger"])

    def _apply_promo(self):
        code=self._promo_var.get().strip()
        if not code: return
        from datetime import date
        today=date.today().isoformat()
        with get_conn() as conn:
            r=conn.execute(
                "SELECT id,name,type,value,min_amount,max_uses,used_count FROM promotions "
                "WHERE code=? AND active=1 AND (end_date IS NULL OR end_date>=?)",
                (code,today)).fetchone()
        if not r:
            self._promo_info.config(text="โค้ดไม่ถูกต้องหรือหมดอายุ",fg=CLR["danger"])
            self._promo_discount=0; self._update_total(); return
        pid,name,ptype,pval,min_amt,max_u,used=r
        sub=sum(i[2]*i[3] for i in self.cart)
        if sub<min_amt:
            self._promo_info.config(text=f"ยอดขั้นต่ำ ฿{min_amt:,.0f}",fg=CLR["warning"])
            self._promo_discount=0; self._update_total(); return
        if max_u>0 and used>=max_u:
            self._promo_info.config(text="โค้ดถูกใช้ครบแล้ว",fg=CLR["danger"])
            self._promo_discount=0; self._update_total(); return
        self._active_promo_id=pid
        if ptype=="percent":
            self._promo_discount=sub*(pval/100)
            self._promo_info.config(text=f"✅ {name}  -{pval:.0f}%  (฿{self._promo_discount:,.2f})",fg=CLR["success"])
        else:
            self._promo_discount=min(pval,sub)
            self._promo_info.config(text=f"✅ {name}  -฿{self._promo_discount:,.2f}",fg=CLR["success"])
        self._update_total()

    def _checkout(self):
        if not self.cart:
            messagebox.showwarning("แจ้งเตือน","ตะกร้าว่าง"); return
        sub=sum(i[2]*i[3] for i in self.cart)
        try: disc=float(self._disc_var.get() or 0)
        except: disc=0
        total=max(0,sub-disc); pay=self._pay_var.get()
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user=self.app.current_user["username"]
        rcpt=next_number("INV","sales","receipt_no")
        with get_conn() as conn:
            cur=conn.execute("INSERT INTO sales(receipt_no,cashier,payment,subtotal,discount,total,date) VALUES(?,?,?,?,?,?,?)",
                             (rcpt,user,pay,sub,disc,total,now))
            sid=cur.lastrowid
            for pid,name,qty,price in self.cart:
                conn.execute("INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,subtotal) VALUES(?,?,?,?,?)",
                             (sid,pid,qty,price,qty*price))
                conn.execute("UPDATE products SET quantity=quantity-?,updated=? WHERE id=?",(qty,now,pid))
                conn.execute("INSERT INTO transactions(product_id,type,quantity,note,date,user) VALUES(?,?,?,?,?,?)",
                             (pid,"OUT",qty,f"ขาย {rcpt}",now,user))
            conn.commit()
        # Award points to customer (1 point per 10 baht)
        if getattr(self,"_cust_id",None):
            pts_earned=round(total/10,1)
            with get_conn() as conn:
                conn.execute("UPDATE customers SET points=points+?,total_spent=total_spent+? WHERE id=?",
                             (pts_earned,total,self._cust_id)); conn.commit()
        # Increment promo used_count
        if getattr(self,"_promo_discount",0)>0 and getattr(self,"_active_promo_id",None):
            with get_conn() as conn:
                conn.execute("UPDATE promotions SET used_count=used_count+1 WHERE id=?",
                             (self._active_promo_id,)); conn.commit()
        self._cust_id=None; self._cust_info.config(text="")
        self._promo_discount=0; self._promo_info.config(text=""); self._promo_var.set("")
        ReceiptWindow(self,rcpt,self.cart,disc,total,pay,now,user)
        self.cart=[]; self._refresh_cart(); self._load_products()


class ReceiptWindow(tk.Toplevel):
    def __init__(self, parent, rcpt_no, items, discount, total, payment, date, cashier):
        super().__init__(parent)
        self.title(f"ใบเสร็จ {rcpt_no}")
        self.geometry("420x580"); self.configure(bg=CLR["bg"])
        self.rcpt_no=rcpt_no; self.items=list(items)
        self.discount=discount; self.total=total
        self.payment=payment; self.date=date; self.cashier=cashier
        self._build()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"],padx=20,pady=20); pad.pack(fill="both",expand=True)
        rc=card(pad,padx=18,pady=16); rc.pack(fill="both",expand=True)
        tk.Label(rc,text="🏪 Stock Manager Pro",font=("Segoe UI",14,"bold"),
                 bg=CLR["card"],fg=CLR["text"]).pack()
        tk.Label(rc,text="ใบเสร็จรับเงิน",font=FONT_H,bg=CLR["card"],fg=CLR["text"]).pack()
        tk.Label(rc,text=f"เลขที่: {self.rcpt_no}",font=FONT_B,
                 bg=CLR["card"],fg=CLR["accent"]).pack()
        tk.Label(rc,text=f"วันที่: {self.date}  |  แคชเชียร์: {self.cashier}",
                 font=("Segoe UI",9),bg=CLR["card"],fg=CLR["text_lt"]).pack(pady=(0,10))
        tk.Frame(rc,bg=CLR["border"],height=1).pack(fill="x",pady=4)
        for item in self.items:
            pid,name,qty,price=item[0],item[1],item[2],item[3]
            row=tk.Frame(rc,bg=CLR["card"]); row.pack(fill="x",pady=1)
            tk.Label(row,text=f"{name[:28]}",font=FONT,bg=CLR["card"],fg=CLR["text"]).pack(side="left")
            tk.Label(row,text=f"{qty:g} x {price:,.2f} = {qty*price:,.2f}",
                     font=FONT,bg=CLR["card"],fg=CLR["text_lt"]).pack(side="right")
        tk.Frame(rc,bg=CLR["border"],height=1).pack(fill="x",pady=8)
        subtotal=sum(i[2]*i[3] for i in self.items)
        for lbl,val in [("ราคาก่อนลด",f"{subtotal:,.2f} บาท"),
                         ("ส่วนลด",f"-{self.discount:,.2f} บาท"),
                         ("ยอดรวม",f"{self.total:,.2f} บาท")]:
            row=tk.Frame(rc,bg=CLR["card"]); row.pack(fill="x",pady=2)
            font=("Segoe UI",12,"bold") if lbl=="ยอดรวม" else FONT
            color=CLR["success"] if lbl=="ยอดรวม" else CLR["text"]
            tk.Label(row,text=lbl,font=font,bg=CLR["card"],fg=color).pack(side="left")
            tk.Label(row,text=val,font=font,bg=CLR["card"],fg=color).pack(side="right")
        pay_th={"cash":"💵 เงินสด","transfer":"📱 โอนเงิน","card":"💳 บัตรเครดิต"}
        tk.Label(rc,text=f"ชำระด้วย: {pay_th.get(self.payment,'')}",font=FONT_B,
                 bg=CLR["card"],fg=CLR["accent"]).pack(pady=(10,0))
        tk.Label(rc,text="ขอบคุณที่ใช้บริการ 🙏",font=FONT,
                 bg=CLR["card"],fg=CLR["text_lt"]).pack(pady=(4,0))
        bf=tk.Frame(pad,bg=CLR["bg"]); bf.pack(fill="x",pady=(12,0))
        btn_warn(bf,"📄 บันทึก PDF",self._export_pdf).pack(side="left")
        tk.Button(bf,text="ปิด",font=FONT,bg=CLR["border"],fg=CLR["text"],
                  relief="flat",padx=14,pady=7,cursor="hand2",command=self.destroy).pack(side="right")
    def _export_pdf(self):
        if not HAS_RL: messagebox.showerror("ผิดพลาด","ต้องการ reportlab"); return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",
             filetypes=[("PDF","*.pdf")],initialfile=f"receipt_{self.rcpt_no}.pdf")
        if not path: return
        rows=[(name[:40],f"{qty:g}",f"{price:,.2f}",f"{qty*price:,.2f}")
              for _,name,qty,price in self.items]
        sub=sum(i[2]*i[3] for i in self.items)
        footer=(f"ราคาก่อนลด: {sub:,.2f}    ส่วนลด: {self.discount:,.2f}"
                f"    ยอดรวม: {self.total:,.2f} บาท\nชำระ: {self.payment}    แคชเชียร์: {self.cashier}")
        _make_pdf_generic(path,f"ใบเสร็จรับเงิน  {self.rcpt_no}",
                          ["สินค้า","จำนวน","ราคา/หน่วย","รวม"],rows,footer=footer)
        messagebox.showinfo("สำเร็จ",f"บันทึก PDF สำเร็จ\n{path}")


# ══════════════════════════════════════════════════════
#  SALES HISTORY
# ══════════════════════════════════════════════════════
class SalesHistoryFrame(tk.Frame):
    NAME = "sales_history"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build(); self._load()

    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=20)
        page_title(pad,"📜 ประวัติการขาย","รายการขาย รายละเอียด และคืนสินค้า")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=10)

        # ── Filter bar ────────────────────────────────────────
        tb=tk.Frame(pad,bg=CLR["bg"]); tb.pack(fill="x",pady=(0,8))
        self._srch2=tk.StringVar()
        self._srch2.trace_add("write", lambda *_: self._load())
        sf=tk.Frame(tb,bg=CLR["card"],highlightbackground=CLR["border"],highlightthickness=1)
        sf.pack(side="left")
        tk.Label(sf,text="🔍",bg=CLR["card"],font=FONT).pack(side="left",padx=(8,0))
        tk.Entry(sf,textvariable=self._srch2,font=FONT,bg=CLR["card"],
                 relief="flat",width=18).pack(side="left",padx=6,pady=6)

        tk.Label(tb,text="จาก",font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(side="left",padx=(10,4))
        self._d_from = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        self._d_to   = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        for sv in [self._d_from, self._d_to]:
            tk.Entry(tb,textvariable=sv,font=FONT,width=11,
                     bg=CLR["entry_bg"],fg=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left",ipady=4,padx=(0,4))
        btn_primary(tb,"🔍",self._load).pack(side="left")

        # ── Action buttons ────────────────────────────────────
        ab=tk.Frame(pad,bg=CLR["bg"]); ab.pack(fill="x",pady=(0,8))
        btn_primary(ab,"👁 รายละเอียด",  self._view_detail).pack(side="left")
        tk.Frame(ab,width=6,bg=CLR["bg"]).pack(side="left")
        btn_danger(ab,"🔄 คืนสินค้า / Refund", self._do_refund).pack(side="left")
        tk.Frame(ab,width=6,bg=CLR["bg"]).pack(side="left")
        btn_warn(ab,"📈 รายงานสรุป",    self._show_report).pack(side="left")
        tk.Frame(ab,width=6,bg=CLR["bg"]).pack(side="left")
        btn_warn(ab,"📊 Export CSV",    self._export_csv).pack(side="left")
        tk.Frame(ab,width=6,bg=CLR["bg"]).pack(side="left")
        btn_danger(ab,"📄 Export PDF",   self._export_pdf).pack(side="left")

        # ── Split view: list (left) | detail (right) ─────────
        main=tk.Frame(pad,bg=CLR["bg"]); main.pack(fill="both",expand=True)
        main.columnconfigure(0,weight=3); main.columnconfigure(1,weight=2)

        left=tk.Frame(main,bg=CLR["bg"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        cols=("id","เลขที่","แคชเชียร์","ชำระ","ลด","ยอด","สถานะ","วันที่")
        wrap,self.tv=make_tree(left,cols,[0,120,100,55,65,85,55,140],height=22)
        self.tv.column("id",width=0,stretch=False)
        wrap.pack(fill="both",expand=True)
        self.tv.tag_configure("voided", foreground=CLR["danger"])
        self.tv.bind("<<TreeviewSelect>>", lambda _: self._on_select())
        self.tv.bind("<Double-1>",         lambda _: self._view_detail())

        right=card(main,padx=14,pady=12)
        right.grid(row=0,column=1,sticky="nsew")
        self._rcpt_lbl=tk.Label(right,text="เลือกใบเสร็จเพื่อดูรายการ",
                                 font=FONT_B,bg=CLR["card"],fg=CLR["text_lt"],
                                 justify="left",wraplength=260)
        self._rcpt_lbl.pack(anchor="w",pady=(0,8))
        tk.Frame(right,bg=CLR["border"],height=1).pack(fill="x",pady=(0,6))
        dwrap,self.dtv=make_tree(right,("สินค้า","จำนวน","ราคา","รวม"),
                                  [150,55,75,75],height=12)
        dwrap.pack(fill="both",expand=True)
        self._tot_lbl=tk.Label(right,text="",font=FONT_B,
                                bg=CLR["card"],fg=CLR["success"])
        self._tot_lbl.pack(anchor="e",pady=(6,0))

    # ── Data helpers ──────────────────────────────────────────
    def _date_range(self):
        d0 = self._d_from.get().strip() + " 00:00:00"
        d1 = self._d_to.get().strip()   + " 23:59:59"
        return d0, d1

    def _load(self):
        self.tv.delete(*self.tv.get_children())
        kw = f"%{self._srch2.get()}%"
        d0, d1 = self._date_range()
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT id, receipt_no, cashier, payment,
                       discount, total, COALESCE(voided,0), date
                FROM   sales
                WHERE  (receipt_no LIKE ? OR cashier LIKE ?)
                  AND  date BETWEEN ? AND ?
                ORDER  BY date DESC
                LIMIT  500""", (kw, kw, d0, d1)).fetchall()
        pay_th = {"cash":"💵","transfer":"📱","card":"💳"}
        for r in rows:
            tag    = "voided" if r[6] else ""
            status = "🔴 คืน" if r[6] else "✅"
            self.tv.insert("","end",
                values=(r[0],r[1],r[2],pay_th.get(r[3],r[3]),
                        f"{r[4]:,.2f}",f"{r[5]:,.2f}",status,r[7]),
                tags=(tag,) if tag else ())

    def _on_select(self):
        sel = self.tv.selection()
        if not sel: return
        sid = self.tv.item(sel[0])["values"][0]
        with get_conn() as conn:
            sale  = conn.execute(
                "SELECT receipt_no,cashier,payment,discount,total,date"
                " FROM sales WHERE id=?", (sid,)).fetchone()
            items = conn.execute("""
                SELECT p.name, si.quantity, si.unit_price, si.subtotal
                FROM   sale_items si
                JOIN   products p ON p.id = si.product_id
                WHERE  si.sale_id = ?""", (sid,)).fetchall()
        if not sale: return
        rcpt,cashier,pay,disc,total,date = sale
        pay_th = {"cash":"💵 เงินสด","transfer":"📱 โอน","card":"💳 บัตร"}
        self._rcpt_lbl.config(
            text=(f"📄 {rcpt}\n"
                  f"👤 {cashier}  {pay_th.get(pay,pay)}\n"
                  f"📅 {date}\n"
                  f"💸 ลด ฿{float(str(disc)):,.2f}"),
            fg=CLR["text"])
        self.dtv.delete(*self.dtv.get_children())
        for r in items:
            self.dtv.insert("","end",
                values=(r[0][:22], f"{r[1]:g}",
                        f"{r[2]:,.2f}", f"{r[3]:,.2f}"))
        self._tot_lbl.config(
            text=f"ยอดรวม: ฿{float(str(total)):,.2f} บาท")

    def _view_detail(self):
        sel = self.tv.selection()
        if not sel: return
        sid = self.tv.item(sel[0])["values"][0]
        with get_conn() as conn:
            sale = conn.execute(
                "SELECT receipt_no,cashier,payment,discount,total,date"
                " FROM sales WHERE id=?", (sid,)).fetchone()
            raw  = conn.execute("""
                SELECT p.name, si.quantity, si.unit_price
                FROM   sale_items si
                JOIN   products p ON p.id = si.product_id
                WHERE  si.sale_id = ?""", (sid,)).fetchall()
        items = [(0, r[0], r[1], r[2]) for r in raw]
        ReceiptWindow(self, sale[0], items, sale[3], sale[4],
                      sale[2], sale[5], sale[1])

    def _do_refund(self):
        sel = self.tv.selection()
        if not sel: return
        v   = self.tv.item(sel[0])["values"]
        sid, rcpt = v[0], v[1]
        if "คืน" in str(v[6]):
            messagebox.showwarning("แจ้งเตือน","ใบเสร็จนี้ถูกคืนไปแล้ว"); return
        with get_conn() as conn:
            items = conn.execute("""
                SELECT si.id, p.id, p.name, si.quantity, si.unit_price
                FROM   sale_items si
                JOIN   products p ON p.id = si.product_id
                WHERE  si.sale_id = ?""", (sid,)).fetchall()
        RefundDialog(self, sid, rcpt, items,
                     self.app.current_user["username"], self.refresh)

    def _show_report(self):
        SalesReportWindow(self, self.app)

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV","*.csv")],
            initialfile=f"sales_{datetime.now().strftime('%Y%m%d')}.csv")
        if not path: return
        kw = f"%{self._srch2.get()}%"
        d0, d1 = self._date_range()
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT receipt_no,cashier,payment,subtotal,discount,total,date
                FROM   sales
                WHERE  (receipt_no LIKE ? OR cashier LIKE ?)
                  AND  date BETWEEN ? AND ?
                ORDER  BY date DESC""", (kw,kw,d0,d1)).fetchall()
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["เลขที่","แคชเชียร์","ชำระ","ก่อนลด","ลด","ยอด","วันที่"])
            w.writerows(rows)
        messagebox.showinfo("สำเร็จ","Export CSV\n"+str(path))

    def _export_pdf(self):
        if not HAS_RL:
            messagebox.showerror("ผิดพลาด","ต้องการ reportlab"); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=f"sales_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not path: return
        kw = f"%{self._srch2.get()}%"
        d0, d1 = self._date_range()
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT receipt_no,cashier,payment,discount,total,date
                FROM   sales
                WHERE  (receipt_no LIKE ? OR cashier LIKE ?)
                  AND  date BETWEEN ? AND ?
                  AND  COALESCE(voided,0) = 0
                ORDER  BY date DESC""", (kw,kw,d0,d1)).fetchall()
        pay_th = {"cash":"เงินสด","transfer":"โอน","card":"บัตร"}
        fmt = [(r[0],r[1],pay_th.get(r[2],r[2]),
                f"{r[3]:,.2f}",f"{r[4]:,.2f}",r[5]) for r in rows]
        s = sum(r[4] for r in rows)
        _make_pdf_generic(
            path,"รายงานประวัติการขาย",
            ["เลขที่","แคชเชียร์","ชำระ","ลด","ยอด","วันที่"], fmt,
            footer=f"รวม {len(rows)} ใบ   ยอดรวม: {s:,.2f} บาท")
        messagebox.showinfo("สำเร็จ","Export PDF\n"+str(path))

# ══════════════════════════════════════════════════════
#  REFUND DIALOG
# ══════════════════════════════════════════════════════
class RefundDialog(tk.Toplevel):
    def __init__(self, parent, sale_id, receipt_no, items, cashier, callback):
        super().__init__(parent)
        self.sale_id=sale_id; self.receipt_no=receipt_no
        self.items=items; self.cashier=cashier; self.callback=callback
        self.title(f"Refund — {receipt_no}")
        self.geometry("560x540"); self.configure(bg=CLR["bg"]); self.grab_set()
        self._build()

    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text=f"🔄 คืนสินค้า — {self.receipt_no}",
                 font=FONT_H,bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,4))
        tk.Label(pad,
                 text="ดับเบิลคลิกแถวเพื่อแก้จำนวนที่คืน (0 = ไม่คืน)",
                 font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(anchor="w",pady=(0,10))
        wrap,self.tv=make_tree(pad,("สินค้า / ราคา","ขายไป","คืน"),
                                [240,70,110],height=9)
        wrap.pack(fill="x",pady=(0,10))
        self._qty_vars={}
        for siid,pid,name,qty,price in self.items:
            v=tk.StringVar(value=f"{qty:g}")
            self._qty_vars[str(siid)]=(pid,qty,price,v)
            self.tv.insert("","end",iid=str(siid),
                values=(f"{name[:30]}  ฿{price:,.2f}",f"{qty:g}",v.get()))
        self.tv.bind("<Double-1>",self._edit_qty)

        tk.Label(pad,text="เหตุผล:",font=FONT,bg=CLR["bg"],fg=CLR["text_lt"]).pack(anchor="w")
        self._reason=tk.StringVar()
        ttk.Combobox(pad,textvariable=self._reason,font=FONT,width=38,
                     values=["สินค้าชำรุด/ผิด","สินค้าไม่ตรงตามสั่ง",
                             "เปลี่ยนใจ","อื่นๆ"]).pack(anchor="w",pady=(4,10))

        mf=tk.Frame(pad,bg=CLR["bg"]); mf.pack(fill="x",pady=(0,12))
        tk.Label(mf,text="คืนเงินผ่าน:",font=FONT,bg=CLR["bg"],
                 fg=CLR["text_lt"]).pack(side="left")
        self._method=tk.StringVar(value="cash")
        for val,lbl in [("cash","💵 เงินสด"),
                        ("transfer","📱 โอน"),
                        ("credit","💳 เครดิต")]:
            tk.Radiobutton(mf,text=lbl,variable=self._method,value=val,
                           font=FONT,bg=CLR["bg"],fg=CLR["text"],
                           selectcolor=CLR["accent"],cursor="hand2",
                           activebackground=CLR["bg"]).pack(side="left",padx=(0,12))

        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=10)
        bf=tk.Frame(pad,bg=CLR["bg"]); bf.pack(fill="x")
        btn_danger(bf,"✅ ยืนยันการคืนสินค้า",self._confirm).pack(side="right")
        tk.Button(bf,text="ยกเลิก",font=FONT,bg=CLR["border"],relief="flat",
                  padx=14,pady=7,cursor="hand2",
                  command=self.destroy).pack(side="right",padx=(0,8))

    def _edit_qty(self, event):
        sel=self.tv.selection()
        if not sel: return
        siid=sel[0]
        pid,orig,price,v=self._qty_vars[siid]
        from tkinter.simpledialog import askfloat
        nq=askfloat("จำนวนคืน",
                    f"จำนวนที่คืน (สูงสุด {orig:g}):",
                    minvalue=0, maxvalue=orig, parent=self)
        if nq is None: return
        v.set(f"{nq:g}")
        cur=self.tv.item(siid)["values"]
        self.tv.item(siid, values=(cur[0],cur[1],f"{nq:g}"))

    def _confirm(self):
        reason=self._reason.get().strip()
        if not reason:
            messagebox.showerror("ผิดพลาด","กรุณาระบุเหตุผล",parent=self); return
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rno=next_number("REF","refunds","refund_no")
        total_refund=0; refund_items=[]
        for siid,(pid,orig,price,v) in self._qty_vars.items():
            try: rq=float(v.get() or 0)
            except: rq=0
            if rq<=0: continue
            rq=min(rq,orig)
            refund_items.append((pid,rq,price)); total_refund+=rq*price
        if not refund_items:
            messagebox.showerror("ผิดพลาด","ไม่มีรายการที่คืน",parent=self); return
        msg=(f"ยืนยันการคืน?\n"
             f"เลขที่: {self.receipt_no}\n"
             f"สินค้า: {len(refund_items)} รายการ\n"
             f"ยอดคืน: {total_refund:,.2f} บาท")
        if not messagebox.askyesno("ยืนยัน",msg,parent=self): return
        with get_conn() as conn:
            rid=conn.execute(
                "INSERT INTO refunds"
                "(refund_no,sale_id,receipt_no,cashier,reason,total,date)"
                " VALUES(?,?,?,?,?,?,?)",
                (rno,self.sale_id,self.receipt_no,
                 self.cashier,reason,total_refund,now)).lastrowid
            for pid,rq,price in refund_items:
                conn.execute(
                    "INSERT INTO refund_items"
                    "(refund_id,product_id,quantity,unit_price)"
                    " VALUES(?,?,?,?)", (rid,pid,rq,price))
                conn.execute(
                    "UPDATE products SET quantity=quantity+?,updated=? WHERE id=?",
                    (rq,now,pid))
                conn.execute(
                    "INSERT INTO transactions"
                    "(product_id,type,quantity,note,date,user)"
                    " VALUES(?,?,?,?,?,?)",
                    (pid,"IN",rq,f"คืนสินค้า {rno}",now,self.cashier))
            conn.execute("UPDATE sales SET voided=1 WHERE id=?",(self.sale_id,))
            conn.commit()
        audit(self.cashier,"REFUND",
              f"ref={rno} sale={self.receipt_no} total={total_refund}")
        messagebox.showinfo("สำเร็จ",
            f"คืนสินค้าสำเร็จ\nเลขที่: {rno}\nยอดคืน: {total_refund:,.2f} บาท",
            parent=self)
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════
#  SALES REPORT WINDOW
# ══════════════════════════════════════════════════════
class SalesReportWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app=app; self.title("📊 รายงานยอดขาย")
        self.geometry("820x660"); self.configure(bg=CLR["bg"])
        self._build(); self._load()

    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"],padx=24,pady=20); pad.pack(fill="both",expand=True)
        tk.Label(pad,text="📊 รายงานยอดขาย",font=FONT_H,
                 bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=10)

        # Period selector
        pf=tk.Frame(pad,bg=CLR["bg"]); pf.pack(fill="x",pady=(0,12))
        tk.Label(pf,text="ช่วงเวลา:",font=FONT,bg=CLR["bg"],
                 fg=CLR["text_lt"]).pack(side="left")
        self._period=tk.StringVar(value="month")
        for val,lbl in [("today","วันนี้"),("week","7 วัน"),
                        ("month","เดือนนี้"),("custom","กำหนดเอง")]:
            tk.Radiobutton(pf,text=lbl,variable=self._period,value=val,
                           font=FONT,bg=CLR["bg"],fg=CLR["text"],
                           selectcolor=CLR["accent"],cursor="hand2",
                           activebackground=CLR["bg"],
                           command=self._load).pack(side="left",padx=(8,0))
        tk.Label(pf,text="จาก",font=FONT,bg=CLR["bg"],
                 fg=CLR["text_lt"]).pack(side="left",padx=(16,4))
        self._cf=tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        self._ct=tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        for sv in [self._cf, self._ct]:
            tk.Entry(pf,textvariable=sv,font=FONT,width=11,
                     bg=CLR["entry_bg"],fg=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],
                     highlightthickness=1).pack(side="left",ipady=4,padx=(0,4))
        btn_primary(pf,"🔍",self._load).pack(side="left")

        # KPI row
        self._kpi_frame=tk.Frame(pad,bg=CLR["bg"])
        self._kpi_frame.pack(fill="x",pady=(0,14))

        # Tables
        cf=tk.Frame(pad,bg=CLR["bg"]); cf.pack(fill="both",expand=True)
        cf.columnconfigure(0,weight=3); cf.columnconfigure(1,weight=2)

        lc=tk.Frame(cf,bg=CLR["bg"]); lc.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        tk.Label(lc,text="📅 ยอดขายรายวัน",font=FONT_B,
                 bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,6))
        wrap,self.daily_tv=make_tree(
            lc,("วันที่","บิล","ยอดขาย","คืน","สุทธิ"),
            [105,50,95,90,95],height=14)
        wrap.pack(fill="both",expand=True)

        rc=tk.Frame(cf,bg=CLR["bg"]); rc.grid(row=0,column=1,sticky="nsew")
        tk.Label(rc,text="🏆 สินค้าขายดี Top 10",font=FONT_B,
                 bg=CLR["bg"],fg=CLR["text"]).pack(anchor="w",pady=(0,6))
        wrap2,self.prod_tv=make_tree(
            rc,("สินค้า","จำนวน","ยอด"),
            [160,55,85],height=14)
        wrap2.pack(fill="both",expand=True)

        # Export bar
        ebf=tk.Frame(pad,bg=CLR["bg"]); ebf.pack(fill="x",pady=(12,0))
        btn_danger(ebf,"📄 Export PDF รายงาน",self._export_pdf).pack(side="left")
        btn_warn(ebf,"📊 Export CSV รายวัน",self._export_csv).pack(side="left",padx=(8,0))
        tk.Button(ebf,text="ปิด",font=FONT,bg=CLR["border"],relief="flat",
                  padx=14,pady=7,cursor="hand2",
                  command=self.destroy).pack(side="right")

    def _get_range(self):
        from datetime import timedelta
        today=datetime.now(); p=self._period.get()
        if   p=="today":  return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        elif p=="week":   return (today-timedelta(days=6)).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        elif p=="month":  return today.strftime("%Y-%m-01"), today.strftime("%Y-%m-%d")
        else:             return self._cf.get().strip(), self._ct.get().strip()

    def _load(self):
        d0,d1=self._get_range()
        d0s=d0+" 00:00:00"; d1s=d1+" 23:59:59"
        with get_conn() as conn:
            kpis=conn.execute("""
                SELECT COUNT(*), COALESCE(SUM(total),0),
                  COALESCE(SUM(CASE WHEN payment='cash'     THEN total ELSE 0 END),0),
                  COALESCE(SUM(CASE WHEN payment='transfer' THEN total ELSE 0 END),0),
                  COALESCE(SUM(CASE WHEN payment='card'     THEN total ELSE 0 END),0)
                FROM sales
                WHERE date BETWEEN ? AND ?
                  AND COALESCE(voided,0)=0""",(d0s,d1s)).fetchone()
            ref_total=conn.execute(
                "SELECT COALESCE(SUM(total),0) FROM refunds"
                " WHERE date BETWEEN ? AND ?",(d0s,d1s)).fetchone()[0]
            cost=conn.execute("""
                SELECT COALESCE(SUM(si.quantity*p.price),0)
                FROM   sale_items si
                JOIN   products p ON si.product_id=p.id
                JOIN   sales    s ON si.sale_id=s.id
                WHERE  s.date BETWEEN ? AND ?
                  AND  COALESCE(s.voided,0)=0""",(d0s,d1s)).fetchone()[0]
            daily=conn.execute("""
                SELECT DATE(date), COUNT(*), COALESCE(SUM(total),0)
                FROM   sales
                WHERE  date BETWEEN ? AND ?
                  AND  COALESCE(voided,0)=0
                GROUP  BY DATE(date)
                ORDER  BY DATE(date) DESC""",(d0s,d1s)).fetchall()
            daily_ref=dict(conn.execute("""
                SELECT DATE(date), COALESCE(SUM(total),0)
                FROM   refunds
                WHERE  date BETWEEN ? AND ?
                GROUP  BY DATE(date)""",(d0s,d1s)).fetchall())
            top=conn.execute("""
                SELECT p.name, SUM(si.quantity), SUM(si.subtotal)
                FROM   sale_items si
                JOIN   products p ON si.product_id=p.id
                JOIN   sales    s ON si.sale_id=s.id
                WHERE  s.date BETWEEN ? AND ?
                  AND  COALESCE(s.voided,0)=0
                GROUP  BY p.id
                ORDER  BY SUM(si.quantity) DESC
                LIMIT  10""",(d0s,d1s)).fetchall()

        cnt,total,cash_t,transfer_t,card_t=kpis
        profit=total-cost-ref_total

        for w in self._kpi_frame.winfo_children(): w.destroy()
        for i,(t,v,col) in enumerate([
            ("🧾 บิล",          f"{cnt}",           CLR["accent"]),
            ("💰 ยอดขาย",       f"{total:,.0f}",     CLR["success"]),
            ("💹 กำไรประมาณ",   f"{profit:,.0f}",    "#A78BFA"),
            ("🔄 ยอดคืน",       f"{ref_total:,.0f}", CLR["danger"]),
            ("💵 เงินสด",       f"{cash_t:,.0f}",    CLR["warning"]),
            ("📱 โอน",          f"{transfer_t:,.0f}",CLR["accent"]),
        ]):
            c=card(self._kpi_frame,padx=10,pady=8)
            c.grid(row=0,column=i,sticky="nsew",padx=(0,6) if i<5 else 0)
            self._kpi_frame.columnconfigure(i,weight=1)
            tk.Label(c,text=t,font=("Segoe UI",8),
                     bg=CLR["card"],fg=CLR["text_lt"]).pack(anchor="w")
            tk.Label(c,text=v,font=("Segoe UI",13,"bold"),
                     bg=CLR["card"],fg=col).pack(anchor="w")

        self.daily_tv.delete(*self.daily_tv.get_children())
        for r in daily:
            ref=daily_ref.get(r[0],0); net=r[2]-ref
            self.daily_tv.insert("","end",
                values=(r[0],r[1],f"{r[2]:,.0f}",f"{ref:,.0f}",f"{net:,.0f}"))

        self.prod_tv.delete(*self.prod_tv.get_children())
        for i,r in enumerate(top,1):
            self.prod_tv.insert("","end",
                values=(f"{i}. {r[0][:18]}",f"{r[1]:g}",f"{r[2]:,.0f}"))

        self._last={"d0":d0,"d1":d1,"kpis":kpis,"ref":ref_total,
                    "profit":profit,"daily":daily,"daily_ref":daily_ref}

    def _export_pdf(self):
        if not HAS_RL:
            messagebox.showerror("ผิดพลาด","ต้องการ reportlab"); return
        d=self._last
        path=filedialog.asksaveasfilename(
            defaultextension=".pdf",filetypes=[("PDF","*.pdf")],
            initialfile=f"report_{d['d0']}_{d['d1']}.pdf")
        if not path: return
        cnt,total,cash_t,transfer_t,card_t=d["kpis"]
        rows=[(r[0],str(r[1]),f"{r[2]:,.2f}",
               f"{d['daily_ref'].get(r[0],0):,.2f}",
               f"{r[2]-d['daily_ref'].get(r[0],0):,.2f}")
              for r in d["daily"]]
        footer=(f"บิลรวม: {cnt}  ยอดขาย: {total:,.2f}"
                f"  คืน: {d['ref']:,.2f}"
                f"  กำไรประมาณ: {d['profit']:,.2f} บาท")
        _make_pdf_generic(
            path, f"รายงานยอดขาย {d['d0']} — {d['d1']}",
            ["วันที่","บิล","ยอดขาย","ยอดคืน","สุทธิ"],
            rows, footer=footer)
        messagebox.showinfo("สำเร็จ","Export PDF\n"+str(path))

    def _export_csv(self):
        d=self._last
        path=filedialog.asksaveasfilename(
            defaultextension=".csv",filetypes=[("CSV","*.csv")],
            initialfile=f"daily_{d['d0']}_{d['d1']}.csv")
        if not path: return
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f)
            w.writerow(["วันที่","จำนวนบิล","ยอดขาย","ยอดคืน","สุทธิ"])
            for r in d["daily"]:
                ref=d["daily_ref"].get(r[0],0)
                w.writerow([r[0],r[1],f"{r[2]:.2f}",
                            f"{ref:.2f}",f"{r[2]-ref:.2f}"])
        messagebox.showinfo("สำเร็จ","Export CSV\n"+str(path))


# ══════════════════════════════════════════════════════
#  STOCK TRANSFER
# ══════════════════════════════════════════════════════
class TransferFrame(tk.Frame):
    NAME = "transfer"
    def __init__(self, parent, app):
        super().__init__(parent, bg=CLR["bg"]); self.app=app
    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=CLR["bg"]); self._build()
    def _build(self):
        pad=tk.Frame(self,bg=CLR["bg"]); pad.pack(fill="both",expand=True,padx=30,pady=24)
        page_title(pad,"🔄 โอนย้ายสต็อก","โอนสินค้าระหว่างสาขา")
        tk.Frame(pad,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        main=tk.Frame(pad,bg=CLR["bg"]); main.pack(fill="both",expand=True)
        main.columnconfigure(0,weight=1); main.columnconfigure(1,weight=2)
        fc=card(main,padx=22,pady=20); fc.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        tk.Label(fc,text="โอนย้ายสินค้า",font=FONT_B,bg=CLR["card"],fg=CLR["text"]).pack(anchor="w",pady=(0,12))
        with get_conn() as conn:
            branches=conn.execute("SELECT id,name FROM branches WHERE active=1").fetchall()
            prods=conn.execute("SELECT id,code,name FROM products ORDER BY name").fetchall()
        bra_map={b[1]:b[0] for b in branches}
        prod_map={f"[{p[1]}] {p[2]}":p[0] for p in prods}
        self._tvars={}; self._bra_map_t=bra_map; self._prod_map_t=prod_map
        for lbl,key,vals in [("จากสาขา","from_branch",list(bra_map.keys())),
                              ("ไปสาขา","to_branch",list(bra_map.keys()))]:
            r=tk.Frame(fc,bg=CLR["card"]); r.pack(fill="x",pady=4)
            tk.Label(r,text=lbl,font=FONT,bg=CLR["card"],fg=CLR["text_lt"],width=14,anchor="w").pack(side="left")
            v=tk.StringVar()
            ttk.Combobox(r,textvariable=v,values=vals,font=FONT,state="readonly",width=24
                         ).pack(side="left",ipady=4)
            self._tvars[key]=v
        r=tk.Frame(fc,bg=CLR["card"]); r.pack(fill="x",pady=4)
        tk.Label(r,text="สินค้า",font=FONT,bg=CLR["card"],fg=CLR["text_lt"],width=14,anchor="w").pack(side="left")
        self._tvars["product"]=tk.StringVar()
        ttk.Combobox(r,textvariable=self._tvars["product"],values=list(prod_map.keys()),
                     font=FONT,state="readonly",width=24).pack(side="left",ipady=4)
        for key2,lbl2 in [("qty","จำนวน"),("note","หมายเหตุ")]:
            r2=tk.Frame(fc,bg=CLR["card"]); r2.pack(fill="x",pady=4)
            tk.Label(r2,text=lbl2,font=FONT,bg=CLR["card"],fg=CLR["text_lt"],width=14,anchor="w").pack(side="left")
            v=tk.StringVar(); self._tvars[key2]=v
            tk.Entry(r2,textvariable=v,font=FONT,width=24,bg=CLR["entry_bg"],fg=CLR["text"],
                     insertbackground=CLR["text"],relief="solid",
                     highlightbackground=CLR["border"],highlightthickness=1
                     ).pack(side="left",ipady=5)
        tk.Frame(fc,bg=CLR["border"],height=1).pack(fill="x",pady=12)
        btn_primary(fc,"🔄 โอนย้าย",self._transfer).pack(anchor="w")
        hc=card(main,padx=14,pady=14); hc.grid(row=0,column=1,sticky="nsew")
        tk.Label(hc,text="ประวัติการโอนย้าย",font=FONT_B,bg=CLR["card"],fg=CLR["text"]).pack(anchor="w",pady=(0,8))
        cols=("จากสาขา","ไปสาขา","สินค้า","จำนวน","วันที่")
        wrap,self.htv=make_tree(hc,cols,[100,100,180,70,140],height=18)
        wrap.pack(fill="both",expand=True)
        self._load_history()
    def _load_history(self):
        self.htv.delete(*self.htv.get_children())
        with get_conn() as conn:
            rows=conn.execute("""SELECT fb.name,tb.name,p.name,st.quantity,st.date
                                 FROM stock_transfers st
                                 JOIN branches fb ON fb.id=st.from_branch
                                 JOIN branches tb ON tb.id=st.to_branch
                                 JOIN products p  ON p.id=st.product_id
                                 ORDER BY st.date DESC LIMIT 200""").fetchall()
        for r in rows: self.htv.insert("","end",values=r)
    def _transfer(self):
        frm=self._tvars["from_branch"].get(); to=self._tvars["to_branch"].get()
        prod=self._tvars["product"].get()
        if not frm or not to or not prod:
            messagebox.showwarning("แจ้งเตือน","กรุณากรอกข้อมูลให้ครบ"); return
        if frm==to:
            messagebox.showwarning("แจ้งเตือน","ต้นทางและปลายทางต้องไม่ใช่สาขาเดียวกัน"); return
        try:
            qty=float(self._tvars["qty"].get())
            if qty<=0: raise ValueError
        except: messagebox.showerror("ผิดพลาด","จำนวนไม่ถูกต้อง"); return
        from_id=self._bra_map_t[frm]; to_id=self._bra_map_t[to]
        pid=self._prod_map_t[prod]; note=self._tvars["note"].get()
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); user=self.app.current_user["username"]
        with get_conn() as conn:
            src=conn.execute("""SELECT COALESCE(bs.quantity,p.quantity)
                                FROM products p
                                LEFT JOIN branch_stock bs ON bs.product_id=p.id AND bs.branch_id=?
                                WHERE p.id=?""",(from_id,pid)).fetchone()
            if not src or src[0]<qty:
                messagebox.showerror("ผิดพลาด",f"สต็อกในสาขา {frm} ไม่พอ"); return
            conn.execute("""INSERT INTO branch_stock(branch_id,product_id,quantity) VALUES(?,?,?)
                            ON CONFLICT(branch_id,product_id) DO UPDATE SET quantity=quantity-?""",
                         (from_id,pid,-qty,qty))
            conn.execute("""INSERT INTO branch_stock(branch_id,product_id,quantity) VALUES(?,?,?)
                            ON CONFLICT(branch_id,product_id) DO UPDATE SET quantity=quantity+?""",
                         (to_id,pid,qty,qty))
            conn.execute("INSERT INTO stock_transfers(from_branch,to_branch,product_id,quantity,note,created_by,date) VALUES(?,?,?,?,?,?,?)",
                         (from_id,to_id,pid,qty,note,user,now))
            conn.commit()
        messagebox.showinfo("สำเร็จ",f"โอนย้ายสำเร็จ {qty:g} หน่วย\n{frm} → {to}")
        self._load_history()
        for v in self._tvars.values(): v.set("")


# ══════════════════════════════════════════════════════
#  Patch StockApp — add new nav + frames
# ══════════════════════════════════════════════════════
_orig_build_sidebar = StockApp._build_sidebar
_orig_build_frames  = StockApp._build_frames

# ══════════════════════════════════════════════════════
#  COLLAPSIBLE SIDEBAR SECTION WIDGET
# ══════════════════════════════════════════════════════
class SidebarSection:
    """Collapsible group of nav buttons in sidebar."""
    def __init__(self, parent, title, icon, expanded=True):
        self.parent   = parent
        self.expanded = expanded
        self._btns    = {}

        # Header row (click to toggle)
        self.hdr = tk.Frame(parent, bg=CLR["sidebar_h"], cursor="hand2")
        self.hdr.pack(fill="x", pady=(6,0))
        self._arrow = tk.Label(self.hdr, text="▾" if expanded else "▸",
                               font=("Segoe UI",9), bg=CLR["sidebar_h"],
                               fg=CLR["text_lt"])
        self._arrow.pack(side="right", padx=8)
        tk.Label(self.hdr, text=f"{icon}  {title}",
                 font=("Segoe UI",8,"bold"), bg=CLR["sidebar_h"],
                 fg=CLR["text_lt"], anchor="w"
                 ).pack(side="left", padx=14, pady=5)
        self.hdr.bind("<Button-1>", lambda _: self.toggle())
        self._arrow.bind("<Button-1>", lambda _: self.toggle())

        # Body frame that holds buttons
        self.body = tk.Frame(parent, bg=CLR["sidebar"])
        if expanded:
            self.body.pack(fill="x")

    def toggle(self):
        self.expanded = not self.expanded
        self._arrow.config(text="▾" if self.expanded else "▸")
        if self.expanded:
            self.body.pack(fill="x")
        else:
            self.body.pack_forget()

    def add_btn(self, key, label, active, command):
        b = tk.Button(self.body, text=label,
                      font=("Segoe UI",10),
                      bg=CLR["accent"] if active else CLR["sidebar"],
                      fg=CLR["white"],
                      activebackground=CLR["sidebar_h"],
                      activeforeground=CLR["white"],
                      relief="flat", anchor="w",
                      padx=28, pady=8, cursor="hand2",
                      command=command)
        b.pack(fill="x")
        self._btns[key] = b
        return b


# ══════════════════════════════════════════════════════
#  TAB BAR WIDGET  (shown at top of content area)
# ══════════════════════════════════════════════════════
class TabBar(tk.Frame):
    """Horizontal tab strip that switches sub-pages within a section."""
    def __init__(self, parent, tabs, on_change, **kw):
        super().__init__(parent, bg=CLR["card"],
                         highlightbackground=CLR["border"],
                         highlightthickness=1, **kw)
        self._tabs      = tabs   # [(key, label), ...]
        self._on_change = on_change
        self._active    = tabs[0][0] if tabs else None
        self._btns      = {}
        self._build()

    def _build(self):
        for key, label in self._tabs:
            b = tk.Button(self, text=label,
                          font=FONT_B,
                          bg=CLR["accent"] if key == self._active else CLR["card"],
                          fg=CLR["white"] if key == self._active else CLR["text_lt"],
                          activebackground=CLR["accent"],
                          activeforeground=CLR["white"],
                          relief="flat", padx=18, pady=8,
                          cursor="hand2",
                          command=lambda k=key: self.select(k))
            b.pack(side="left")
            self._btns[key] = b
        # right-side filler
        tk.Frame(self, bg=CLR["card"]).pack(side="left", fill="both", expand=True)

    def select(self, key):
        self._active = key
        for k, b in self._btns.items():
            b.configure(
                bg=CLR["accent"] if k == key else CLR["card"],
                fg=CLR["white"]  if k == key else CLR["text_lt"])
        self._on_change(key)

    def set_active(self, key):
        """Update tab highlight only — does NOT trigger on_change callback."""
        if key not in self._btns:
            return
        self._active = key
        for k, b in self._btns.items():
            b.configure(
                bg=CLR["accent"] if k == key else CLR["card"],
                fg=CLR["white"]  if k == key else CLR["text_lt"])


# ══════════════════════════════════════════════════════
#  TABBED CONTENT WRAPPER
#  Each "section" has a TabBar + stacked sub-frames
# ══════════════════════════════════════════════════════
SECTION_TABS = {
    "inventory": [
        ("dashboard",   "🏠 Dashboard"),
        ("products",    "📋 สินค้า"),
        ("categories",  "📁 หมวดหมู่"),
        ("barcode",     "🔲 Barcode"),
        ("charts",      "📈 กราฟ"),
        ("csv_import",  "📥 นำเข้า CSV"),
        ("stock_count", "📋 นับสต็อก"),
    ],
    "stock": [
        ("stock_in",     "📥 รับสินค้า"),
        ("stock_out",    "📤 จ่ายสินค้า"),
        ("transactions", "📊 ประวัติ"),
    ],
    "sales": [
        ("sales",           "🛒 ขาย (POS)"),
        ("sales_history",   "📜 ประวัติขาย"),
        ("shift",           "🕐 กะ/Shift"),
        ("customers",       "👥 ลูกค้า"),
        ("customer_credit", "💳 เครดิต/หนี้"),
        ("promotions",      "🎁 โปรโมชั่น"),
    ],
    "purchase": [
        ("purchase_orders","📋 ใบสั่งซื้อ PO"),
        ("suppliers",      "🏭 ซัพพลายเออร์"),
    ],
    "branch": [
        ("branches",  "🏪 สาขา"),
        ("transfer",  "🔄 โอนย้ายสต็อก"),
    ],
    "system": [
        ("shop_settings", "⚙️ ตั้งค่าระบบ"),
    ],
}

# Map every page key -> its section
PAGE_SECTION = {pg: sec for sec, pages in SECTION_TABS.items() for pg, _ in pages}

SECTION_META = {
    "inventory": ("📦", "คลังสินค้า"),
    "stock":     ("🔄", "เคลื่อนไหวสต็อก"),
    "sales":     ("🛒", "การขาย"),
    "purchase":  ("📋", "จัดซื้อ"),
    "branch":    ("🏪", "สาขา"),
    "system":    ("⚙️",  "ระบบ"),
}


def _new_build_sidebar(self):
    sb = self._sb_frame
    for w in sb.winfo_children(): w.destroy()
    sb.configure(bg=CLR["sidebar"], width=130)

    # Logo
    tk.Label(sb, text="📦", font=("Segoe UI",18),
             bg=CLR["sidebar"], fg=CLR["white"]).pack(pady=(14,0))
    tk.Label(sb, text="SMP", font=("Segoe UI",8,"bold"),
             bg=CLR["sidebar"], fg=CLR["white"]).pack()
    role_color = "#FCD34D" if self.current_user["role"]=="admin" else "#94A3B8"
    tk.Label(sb, text=self.current_user["fullname"][:12],
             font=("Segoe UI",7), bg=CLR["sidebar"],
             fg=role_color).pack(pady=(1,6))
    tk.Frame(sb, bg=CLR["sidebar_h"], height=1).pack(fill="x", padx=8, pady=(0,4))

    # Section buttons — one per group, no sub-menu
    # Clicking a section shows its first tab
    self._nav_btns = {}
    sections = [
        ("inventory", T("sec_inventory"), "dashboard"),
        ("stock",     T("sec_stock"),     "stock_in"),
        ("sales",     T("sec_sales"),     "sales"),
        ("purchase",  T("sec_purchase"),  "purchase_orders"),
        ("branch",    T("sec_branch"),    "branches"),
        ("system",    T("sec_system"),    "shop_settings"),
    ]

    self._nav_btns = {}
    cur_sec = PAGE_SECTION.get(self._current_page, "inventory")

    for sec_key, label, first_page in sections:
        is_active = (sec_key == cur_sec)
        b = tk.Button(sb, text=label,
                      font=("Segoe UI",9,"bold" if is_active else "normal"),
                      bg=CLR["accent"] if is_active else CLR["sidebar"],
                      fg=CLR["white"],
                      activebackground=CLR["sidebar_h"],
                      activeforeground=CLR["white"],
                      relief="flat", anchor="w",
                      padx=12, pady=8,
                      cursor="hand2",
                      command=lambda fp=first_page: self.show_frame(fp))
        b.pack(fill="x")
        self._nav_btns[sec_key] = b

    # (Theme toggle moved to Settings page)
    tk.Frame(sb, bg=CLR["sidebar_h"], height=1).pack(fill="x", padx=8, pady=(8,4))

    # Lock + Logout
    tk.Frame(sb, bg=CLR["sidebar_h"], height=1).pack(fill="x", padx=8, side="bottom")
    tk.Button(sb, text="🚪 ออก",
              font=("Segoe UI",9), bg=CLR["sidebar"], fg="#F87171",
              activebackground="#7F1D1D", activeforeground=CLR["white"],
              relief="flat", anchor="w", padx=12, pady=8, cursor="hand2",
              command=self._logout).pack(fill="x", side="bottom")


def _new_build_frames(self):
    """Build stacked frames AND a tab bar per section inside content area."""
    self.frames = {}

    # Main content area: row0 = tab bar, row1 = page frames
    self.content.grid_rowconfigure(0, weight=0)
    self.content.grid_rowconfigure(1, weight=1)

    # Tab bar container (swapped per section)
    self._tab_container = tk.Frame(self.content, bg=CLR["bg"])
    self._tab_container.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

    # Page frame stack
    page_stack = tk.Frame(self.content, bg=CLR["bg"])
    page_stack.grid(row=1, column=0, sticky="nsew")
    page_stack.grid_columnconfigure(0, weight=1)
    page_stack.grid_rowconfigure(0, weight=1)
    self._page_stack = page_stack

    all_frames = (DashboardFrame, ProductsFrame, CategoriesFrame,
                  StockInFrame, StockOutFrame, TransactionsFrame,
                  BarcodeFrame, ChartsFrame, UsersFrame,
                  SalesFrame, SalesHistoryFrame, POFrame,
                  SuppliersFrame, BranchesFrame, TransferFrame,
                  ShopSettingsFrame, CustomersFrame, PromotionsFrame,
                  CSVImportFrame, ShiftFrame,
                  StockCountFrame, CustomerCreditFrame)
    for F in all_frames:
        frame = F(page_stack, self)
        frame.grid(row=0, column=0, sticky="nsew")
        self.frames[F.NAME] = frame

    # Build tab bars for each section (hidden initially)
    self._tab_bars = {}
    for sec_key, tabs in SECTION_TABS.items():
        tb = TabBar(self._tab_container, tabs,
                    on_change=lambda k: self.show_frame(k))
        self._tab_bars[sec_key] = tb


def _new_show_frame(self, name):
    self._current_page = name
    sec = PAGE_SECTION.get(name, "inventory")

    # Highlight active section button in sidebar
    for s_key, btn in self._nav_btns.items():
        is_sec = (s_key == sec)
        btn.configure(
            bg=CLR["accent"] if is_sec else CLR["sidebar"],
            fg=CLR["white"],
            font=("Segoe UI", 9, "bold" if is_sec else "normal"))

    # Swap tab bar
    for s, tb in self._tab_bars.items():
        tb.pack_forget()
    self._tab_bars[sec].pack(fill="x")
    self._tab_bars[sec].set_active(name)

    # Show page
    self.frames[name].refresh()
    self.frames[name].tkraise()


StockApp._build_sidebar = _new_build_sidebar
StockApp._build_frames  = _new_build_frames
StockApp.show_frame     = _new_show_frame

_orig_sa_init = StockApp.__init__
def _new_sa_init(self, user):
    _orig_sa_init(self, user)
    self.geometry("1440x880")
StockApp.__init__ = _new_sa_init


# ─────────────────────────────────────────────
def _run_app():
    init_db()
    _load_app_settings()
    login = LoginWindow()
    login.mainloop()
    if login.result_user:
        app = StockApp(login.result_user)
        # Low stock alert on startup
        def _startup_alert():
            cnt = check_low_stock_alert(app)
            if cnt > 0:
                messagebox.showwarning(
                    "⚠️ แจ้งเตือนสินค้าใกล้หมด",
                    f"มีสินค้า {cnt} รายการที่ต่ำกว่าจำนวนขั้นต่ำ\n"
                    "กรุณาตรวจสอบที่หน้า Dashboard",
                    parent=app)
        app.after(800, _startup_alert)
        app.mainloop()

if __name__ == "__main__":
    _run_app()


