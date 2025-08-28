import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ملف المستخدمين
USERS_FILE = "users.csv"
# ملف التقارير
REPORTS_FILE = "reports.csv"

# إنشاء ملف المستخدمين إذا ما كان موجود
if not os.path.exists(USERS_FILE):
    users = pd.DataFrame(columns=["username", "password", "role", "active"])
    users.to_csv(USERS_FILE, index=False)

# إنشاء ملف التقارير إذا ما كان موجود
if not os.path.exists(REPORTS_FILE):
    reports = pd.DataFrame(columns=["username", "start_time", "end_time", "errors", "notes"])
    reports.to_csv(REPORTS_FILE, index=False)

# تحميل المستخدمين
users = pd.read_csv(USERS_FILE)

# إضافة المستخدم الرئيسي إذا غير موجود
if not ((users["username"] == "hus585") & (users["password"] == "268450")).any():
    new_user = pd.DataFrame([{
        "username": "hus585",
        "password": "268450",
        "role": "admin",
        "active": True
    }])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS_FILE, index=False)

# تهيئة الحالة
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "errors" not in st.session_state:
    st.session_state.errors = []
if "notes" not in st.session_state:
    st.session_state.notes = ""

# واجهة تسجيل الدخول
def show_login():
    st.title("تسجيل الدخول")

    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
        users = pd.read_csv(USERS_FILE)
        user = users[(users["username"] == username) & (users["password"] == password)]

        if not user.empty:
            if user.iloc[0]["active"]:
                st.session_state.username = username
                role = user.iloc[0]["role"]

                if role == "admin":
                    st.session_state.page = "admin"
                else:
                    st.session_state.page = "home"
            else:
                st.error("الحساب غير مفعل")
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# واجهة الرئيسية
def show_home():
    st.title("تقييم")
    st.write(f"مرحباً {st.session_state.username}")

    # التاريخ والوقت
    now = datetime.now()
    st.write(f"التاريخ: {now.strftime('%Y-%m-%d')}")
    st.write(f"الوقت: {now.strftime('%H:%M:%S')}")

    if st.button("ابدأ التقييم"):
        st.session_state.page = "evaluation"
        st.session_state.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.errors = []
        st.session_state.notes = ""

    if st.button("سجل التقارير"):
        st.session_state.page = "reports"

    if st.button("تسجيل خروج"):
        st.session_state.page = "login"
        st.session_state.username = None

# واجهة التقييم
def show_evaluation():
    st.title("تقييم السائق")

    error_list = [
        "باب السائق", "حزام", "افضلية", "سرعة", "ضعف مراقبة",
        "عدم التقيد بالمسارات", "سرعة اثناء الانعطاف", "إشارة للموازي",
        "موقف موازي", "صدم بالموازي", "مراقبة اثناء الخروج",
        "استخدام كلتا القدمين", "ضعف تحكم بالمقود", "صدم ثمانية",
        "إشارة ٩٠خلفي", "موقف ٩٠خلفي", "صدم ٩٠خلفي", "عكس سير",
        "فلشر للرجوع", "الرجوع للخلف", "مراقبة اثناء الرجوع",
        "تسارع عالي", "تباطؤ", "فرامل", "علامةقف", "صدم رصيف",
        "خطوط المشاة", "تجاوز اشارة", "موقف نهائي", "صدم نهائي"
    ]

    selected = st.multiselect("اختر الأخطاء:", error_list)
    st.session_state.errors = selected

    st.session_state.notes = st.text_area("ملاحظات إضافية", st.session_state.notes)

    if st.button("إنهاء التقييم"):
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        reports = pd.read_csv(REPORTS_FILE)
        new_report = pd.DataFrame([{
            "username": st.session_state.username,
            "start_time": st.session_state.start_time,
            "end_time": end_time,
            "errors": ", ".join(st.session_state.errors),
            "notes": st.session_state.notes
        }])
        reports = pd.concat([reports, new_report], ignore_index=True)
        reports.to_csv(REPORTS_FILE, index=False)

        st.success("تم حفظ التقرير")
        st.session_state.page = "home"

# واجهة التقارير
def show_reports():
    st.title("سجل التقارير")

    reports = pd.read_csv(REPORTS_FILE)
    my_reports = reports[reports["username"] == st.session_state.username]

    st.dataframe(my_reports)

    if st.button("عودة"):
        st.session_state.page = "home"

# واجهة الإدارة
def show_admin():
    st.title("لوحة الإدارة")

    users = pd.read_csv(USERS_FILE)

    st.dataframe(users)

    st.write("تفعيل/إلغاء الحسابات:")

    for i, row in users.iterrows():
        if row["username"] != "hus585":
            status = st.checkbox(f"{row['username']} ({row['role']})", value=row["active"])
            users.loc[i, "active"] = status

    users.to_csv(USERS_FILE, index=False)

    if st.button("عودة"):
        st.session_state.page = "home"

# تشغيل الصفحات
if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "home":
    show_home()
elif st.session_state.page == "evaluation":
    show_evaluation()
elif st.session_state.page == "reports":
    show_reports()
elif st.session_state.page == "admin":
    show_admin()
