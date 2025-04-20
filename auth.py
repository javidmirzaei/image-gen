import sqlite3
import bcrypt
import streamlit as st
from datetime import datetime, timedelta
import os

# تنظیمات دیتابیس
DB_PATH = "users.db"

def init_db():
    """ایجاد دیتابیس و جدول کاربران"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """هش کردن پسورد"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """تایید پسورد"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(username, password, email):
    """ثبت نام کاربر جدید"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                 (username, hashed_password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    """ورود کاربر"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    
    if result and verify_password(password, result[0]):
        # بروزرسانی آخرین زمان ورود
        c.execute('UPDATE users SET last_login = ? WHERE username = ?',
                 (datetime.now(), username))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def check_authentication():
    """بررسی وضعیت احراز هویت کاربر"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login_page():
    """صفحه ورود"""
    st.title("🔐 ورود به سیستم")
    
    with st.form("login_form"):
        username = st.text_input("نام کاربری")
        password = st.text_input("رمز عبور", type="password")
        submit = st.form_submit_button("ورود")
        
        if submit:
            if login_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ ورود موفقیت‌آمیز!")
                st.rerun()
            else:
                st.error("❌ نام کاربری یا رمز عبور اشتباه است!")

def register_page():
    """صفحه ثبت نام"""
    st.title("📝 ثبت نام")
    
    with st.form("register_form"):
        username = st.text_input("نام کاربری")
        email = st.text_input("ایمیل")
        password = st.text_input("رمز عبور", type="password")
        confirm_password = st.text_input("تکرار رمز عبور", type="password")
        submit = st.form_submit_button("ثبت نام")
        
        if submit:
            if password != confirm_password:
                st.error("❌ رمز عبور و تکرار آن مطابقت ندارند!")
                return
            
            if register_user(username, password, email):
                st.success("✅ ثبت نام موفقیت‌آمیز! حالا می‌توانید وارد شوید.")
            else:
                st.error("❌ نام کاربری یا ایمیل قبلاً ثبت شده است!")

def logout():
    """خروج از سیستم"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()

def init_auth():
    """راه‌اندازی اولیه سیستم احراز هویت"""
    init_db()
    
    if not check_authentication():
        tab1, tab2 = st.tabs(["ورود", "ثبت نام"])
        with tab1:
            login_page()
        with tab2:
            register_page()
        return False
    return True 