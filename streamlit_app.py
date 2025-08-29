# -*- coding: utf-8 -*-
# Import necessary libraries
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

# ------------------------------
# General Settings
# ------------------------------
REPORTS_FILE = "reports.csv"
USERS_FILE = "users.csv"
tz = pytz.timezone("Asia/Riyadh")

# Define user roles for easy access
ROLES = {
    "admin": "admin",
    "evaluator": "evaluator",
    "viewer": "viewer"
}

# List of errors for the evaluation page
ERRORS_LIST = [
    "باب السائق", "حزام", "افضلية", "سرعة", "ضعف مراقبة",
    "عدم التقيد بالمسارات", "سرعة اثناء الانعطاف", "إشارة للموازي",
    "موقف موازي", "صدم بالموازي", "مراقبة اثناء الخروج", "استخدام كلتا القدمين",
    "ضعف تحكم بالمقود", "صدم ثمانية", "إشارة ٩٠خلفي", "موقف ٩٠خلفي",
    "صدم ٩٠خلفي", "عكس سير", "فلشر للرجوع", "الرجوع للخلف",
    "مراقبة اثناء الرجوع", "تسارع عالي", "تباطؤ", "فرامل", "علامةقف",
    "صدم رصيف", "خطوط المشاة", "تجاوز اشارة", "موقف نهائي", "صدم نهائي"
]

# ------------------------------
# Ensure files exist and handle user setup
# ------------------------------
def ensure_files_exist():
    """
    Creates the necessary CSV files if they don't exist.
    Initializes a new admin and viewer user if the users file is missing.
    """
    # Create reports.csv if it doesn't exist, including a 'username' column
    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=["اسم التقرير", "وقت البداية", "وقت النهاية", "الأخطاء", "ملاحظات", "اسم المستخدم"])
        df.to_csv(REPORTS_FILE, index=False)

    # Create users.csv if it doesn't exist
    if not os.path.exists(USERS_FILE):
        # Initial users with roles. Note that evaluator_access is now a column.
        initial_users = [
            {"username": "hus585", "password": "268450", "role": ROLES["admin"], "evaluator_access": True},
            {"username": "qwe", "password": "123123", "role": ROLES["viewer"], "evaluator_access": False}
        ]
        df = pd.DataFrame(initial_users)
        df.to_csv(USERS_FILE, index=False)
        st.success("تم إنشاء ملفات المستخدمين والتقارير بنجاح.")

# ------------------------------
# User Management Functions
# ------------------------------
def login(username, password):
    """Authenticates the user and returns their role and evaluator_access status."""
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
        df['username'] = df['username'].str.strip()
        df['password'] = df['password'].str.strip()
        user = df[(df["username"] == username) & (df["password"] == password)]
        if not user.empty:
            role = user.iloc[0]["role"]
            evaluator_access = user.iloc[0]["evaluator_access"] == "True"
            return role, evaluator_access
        return None, False
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة ملف المستخدمين: {e}")
        return None, False

def register_user(username, password):
    """
    Registers a new user with an 'evaluator' role and no access initially.
    """
    try:
        df = pd.read_csv(USERS_FILE, dtype=str)
        if username in df["username"].values:
            return False, "اسم المستخدم موجود بالفعل."
        
        new_row = pd.DataFrame([{
            "username": username,
            "password": password,
            "role": ROLES["evaluator"],
            "evaluator_access": False
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(USERS_FILE, index=False)
        return True, "تم التسجيل بنجاح. سيتم تفعيل حسابك لاحقًا من قِبل المسؤول."
    except Exception as e:
        return False, f"حدث خطأ أثناء التسجيل: {e}"

def save_report(report_name, start_time, end_time, errors, notes, username):
    """Saves a new report to the CSV file, including the user's name."""
    try:
        df = pd.read_csv(REPORTS_FILE)
        new_row = pd.DataFrame([{
            "اسم التقرير": report_name,
            "وقت البداية": start_time,
            "وقت النهاية": end_time,
            "الأخطاء": "; ".join(errors),
            "ملاحظات": notes,
            "اسم المستخدم": username
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(REPORTS_FILE, index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حفظ التقرير: {e}")

def delete_report(report_name):
    """Deletes a report by name from the CSV file."""
    try:
        df = pd.read_csv(REPORTS_FILE)
        df = df[df["اسم التقرير"] != report_name]
        df.to_csv(REPORTS_FILE, index=False)
    except Exception as e:
        st.error(f"حدث خطأ أثناء حذف التقرير: {e}")

# ------------------------------
# Application Interface
# ------------------------------
def main():
    st.set_page_config(page_title="تقييم", layout="centered")
    ensure_files_exist()

    # Session State management
    if "page" not in st.session_state: st.session_state.page = "login"
    if "role" not in st.session_state: st.session_state.role = None
    if "username" not in st.session_state: st.session_state.username = None
    if "evaluator_access" not in st.session_state: st.session_state.evaluator_access = False
    if "errors" not in st.session_state: st.session_state.errors = []
    if "report_name" not in st.session_state: st.session_state.report_name = ""
    if "start_time" not in st.session_state: st.session_state.start_time = None
    if "notes" not in st.session_state: st.session_state.notes = ""

    # -------------------- Login Page --------------------
    if st.session_state.page == "login":
        st.title("🔐 تسجيل الدخول")
        username = st.text_input("اسم المستخدم").strip()
        password = st.text_input("كلمة المرور", type="password").strip()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("دخول"):
                role, access = login(username, password)
                if role:
                    st.session_state.role = role
                    st.session_state.username = username
                    st.session_state.evaluator_access = access
                    st.session_state.page = "home"
                    st.success("تم تسجيل الدخول بنجاح")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيح")
        with col2:
            if st.button("تسجيل مستخدم جديد"):
                st.session_state.page = "register"
                st.rerun()

    # -------------------- Register Page --------------------
    elif st.session_state.page == "register":
        st.title("📝 تسجيل مستخدم جديد")
        new_username = st.text_input("اسم المستخدم الجديد").strip()
        new_password = st.text_input("كلمة المرور الجديدة", type="password").strip()
        
        if st.button("إنشاء حساب"):
            if not new_username or not new_password:
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور.")
            else:
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)
        
        if st.button("رجوع إلى تسجيل الدخول"):
            st.session_state.page = "login"
            st.rerun()

    # -------------------- Home Page --------------------
    elif st.session_state.page == "home":
        st.title("📊 صفحة الرئيسية")
        st.write(f"مرحباً، {st.session_state.username}!")
        now = datetime.now(tz)
        st.write(f"📅 التاريخ: {now.strftime('%Y-%m-%d')}")
        st.write(f"⏰ الوقت: {now.strftime('%H:%M')}")
        st.markdown("---")
        
        # Display options based on user role and evaluator_access
        is_admin = st.session_state.role == ROLES["admin"]
        has_evaluator_access = st.session_state.evaluator_access
        
        # Show 'Start Evaluation' button only to admin and evaluators with access
        if is_admin or has_evaluator_access:
            if st.button("ابدأ التقييم"):
                st.session_state.report_name = st.text_input("اسم التقرير", st.session_state.report_name)
                if not st.session_state.report_name.strip():
                    st.error("أدخل اسم التقرير أولاً")
                else:
                    st.session_state.start_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                    st.session_state.errors = []
                    st.session_state.notes = ""
                    st.session_state.page = "errors"
                    st.rerun()
        else:
            st.info("ليس لديك صلاحية لإجراء تقييمات.")

        st.markdown("---")
        
        # Show 'View Reports' button to all roles
        if st.button("📑 عرض السجلات"):
            st.session_state.page = "reports"
            st.rerun()

        st.markdown("---")
        if st.button("🚪 خروج"):
            st.session_state.page = "login"
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.evaluator_access = False
            st.rerun()

    # -------------------- Errors Page --------------------
    elif st.session_state.page == "errors":
        st.title("🚦 الأخطاء")
        st.write("اختر الأخطاء التي وقع فيها السائق:")

        if st.session_state.errors:
            st.write("الأخطاء المسجلة:")
            for i, err in enumerate(st.session_state.errors):
                st.info(f"{i + 1}. {err}")
            
            if st.button("إلغاء آخر خطأ"):
                st.session_state.errors.pop()
                st.rerun()

        # Display buttons in a 3-column, responsive grid
        cols = st.columns(3)
        # Use CSS to make the buttons uniform in size.
        st.markdown("""
        <style>
        div.stButton > button:first-child {
            width: 100%;
        }
        </style>""", unsafe_allow_html=True)
        for i, err in enumerate(ERRORS_LIST):
            button_disabled = err in st.session_state.errors
            if cols[i % 3].button(err, disabled=button_disabled, key=f"err_btn_{i}"):
                st.session_state.errors.append(err)
                st.success(f"تم تسجيل: {err}")
                st.rerun()
        
        st.session_state.notes = st.text_area("ملاحظات إضافية", st.session_state.notes)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("إنهاء التقييم"):
                end_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                save_report(st.session_state.report_name, st.session_state.start_time, end_time, st.session_state.errors, st.session_state.notes, st.session_state.username)
                st.success("✅ تم حفظ التقرير")
                st.session_state.page = "home"
                st.rerun()

        with col2:
            if st.button("إلغاء التقييم"):
                st.session_state.page = "home"
                st.rerun()

    # -------------------- Reports Page --------------------
    elif st.session_state.page == "reports":
        st.title("📑 السجلات")
        try:
            df = pd.read_csv(REPORTS_FILE)
            
            # Filter reports based on user role
            if st.session_state.role == ROLES["evaluator"]:
                # Evaluators only see their own reports
                df = df[df["اسم المستخدم"] == st.session_state.username]
                st.info("أنت تشاهد تقاريرك الخاصة فقط.")
            
            if not df.empty:
                st.dataframe(df)

                report_name = st.selectbox("اختر تقرير لحذفه", df["اسم التقرير"].unique())
                
                # Only admins can delete reports
                if st.session_state.role == ROLES["admin"]:
                    if st.button("🗑️ حذف التقرير"):
                        delete_report(report_name)
                        st.success("تم حذف التقرير")
                        st.rerun()
                else:
                    st.warning("ليس لديك صلاحية لحذف التقارير.")

            else:
                st.info("لا توجد تقارير متاحة.")
        except pd.errors.EmptyDataError:
            st.info("ملف التقارير فارغ. ابدأ بإضافة تقرير جديد.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة ملف التقارير: {e}")

        if st.button("🔙 رجوع"):
            st.session_state.page = "home"
            st.rerun()

# ------------------------------
# Run the application
# ------------------------------
if __name__ == "__main__":
    main()
