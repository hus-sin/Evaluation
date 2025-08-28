import streamlit as st
import pandas as pd
import os
import pytz
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------
# الإعدادات العامة
# ------------------------------
REPORTS_FILE = "reports.csv"
USERS_FILE = "users.csv"
tz = pytz.timezone("Asia/Riyadh")

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
# إنشاء الملفات إذا مفقودة
# ------------------------------
def ensure_files_exist():
    if not os.path.exists(REPORTS_FILE):
        df = pd.DataFrame(columns=["اسم التقرير", "وقت البداية", "وقت النهاية", "الأخطاء", "ملاحظات"])
        df.to_csv(REPORTS_FILE, index=False)

    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame([{"username": "hus585", "password": "268450", "role": "admin"}])
        df.to_csv(USERS_FILE, index=True)

# ------------------------------
# تسجيل الدخول
# ------------------------------
def login(username, password):
    df = pd.read_csv(USERS_FILE)
    user = df[(df["username"] == username) & (df["password"] == password)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

# ------------------------------
# حفظ تقرير
# ------------------------------
def save_report(report_name, start_time, end_time, errors, notes):
    df = pd.read_csv(REPORTS_FILE)
    new_row = pd.DataFrame([{
        "اسم التقرير": report_name,
        "وقت البداية": start_time,
        "وقت النهاية": end_time,
        "الأخطاء": "; ".join(errors),
        "ملاحظات": notes
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(REPORTS_FILE, index=False)

# ------------------------------
# توليد PDF
# ------------------------------
def generate_pdf(report):
    file_name = f"{report['اسم التقرير']}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("تقرير التقييم", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"اسم التقرير: {report['اسم التقرير']}", styles['Normal']))
    story.append(Paragraph(f"وقت البداية: {report['وقت البداية']}", styles['Normal']))
    story.append(Paragraph(f"وقت النهاية: {report['وقت النهاية']}", styles['Normal']))
    story.append(Paragraph(f"الأخطاء: {report['الأخطاء']}", styles['Normal']))
    story.append(Paragraph(f"ملاحظات: {report['ملاحظات']}", styles['Normal']))

    doc.build(story)
    return file_name

# ------------------------------
# واجهة التطبيق
# ------------------------------
def main():
    st.set_page_config(page_title="تقييم", layout="centered")
    ensure_files_exist()

    # جلسة
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "role" not in st.session_state:
        st.session_state.role = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "errors" not in st.session_state:
        st.session_state.errors = []
    if "report_name" not in st.session_state:
        st.session_state.report_name = ""
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    # -------------------- تسجيل الدخول --------------------
    if st.session_state.page == "login":
        st.title("🔐 تسجيل الدخول")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            role = login(username, password)
            if role:
                st.session_state.role = role
                st.session_state.username = username
                st.session_state.page = "home"
                st.success("تم تسجيل الدخول بنجاح")
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيح")

    # -------------------- الصفحة الرئيسية --------------------
    elif st.session_state.page == "home":
        st.title("📊 تقييم")
        now = datetime.now(tz)
        st.write(f"📅 التاريخ: {now.strftime('%Y-%m-%d')}")
        st.write(f"⏰ الوقت: {now.strftime('%H:%M')}")

        st.session_state.report_name = st.text_input("اسم التقرير", st.session_state.report_name)

        if st.button("ابدأ التقييم"):
            if st.session_state.report_name.strip() == "":
                st.error("أدخل اسم التقرير أولاً")
            else:
                st.session_state.start_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
                st.session_state.errors = []
                st.session_state.page = "errors"

        if st.button("📑 عرض السجلات"):
            st.session_state.page = "reports"

    # -------------------- صفحة الأخطاء --------------------
    elif st.session_state.page == "errors":
        st.title("🚦 الأخطاء")
        st.write("اختر الأخطاء التي وقع فيها السائق:")

        cols = st.columns(3)
        for i, err in enumerate(ERRORS_LIST):
            if cols[i % 3].button(err):
                st.session_state.errors.append(err)
                st.success(f"تم تسجيل: {err}")

        notes = st.text_area("ملاحظات إضافية", "")

        if st.button("إنهاء التقييم"):
            end_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
            save_report(st.session_state.report_name, st.session_state.start_time, end_time, st.session_state.errors, notes)
            st.success("✅ تم حفظ التقرير")
            st.session_state.page = "home"

    # -------------------- صفحة التقارير --------------------
    elif st.session_state.page == "reports":
        st.title("📑 السجلات")
        df = pd.read_csv(REPORTS_FILE)
        st.dataframe(df)

        if not df.empty:
            report_name = st.selectbox("اختر تقرير", df["اسم التقرير"].unique())
            if st.button("⬇️ تحميل PDF"):
                report = df[df["اسم التقرير"] == report_name].iloc[0]
                pdf_file = generate_pdf(report)
                with open(pdf_file, "rb") as f:
                    st.download_button("تحميل التقرير كملف PDF", f, file_name=pdf_file)

            if st.button("🗑️ حذف التقرير"):
                df = df[df["اسم التقرير"] != report_name]
                df.to_csv(REPORTS_FILE, index=False)
                st.success("تم حذف التقرير")

        if st.button("🔙 رجوع"):
            st.session_state.page = "home"

# ------------------------------
# تشغيل البرنامج
# ------------------------------
if __name__ == "__main__":
    main()
