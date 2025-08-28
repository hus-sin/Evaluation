import streamlit as st
import pandas as pd
from datetime import datetime

# ملفات التخزين
REPORTS_FILE = "reports.csv"

# إنشاء ملف تقارير إذا غير موجود
try:
    reports = pd.read_csv(REPORTS_FILE)
except FileNotFoundError:
    reports = pd.DataFrame(columns=["report_name", "start_time", "end_time", "errors", "notes"])
    reports.to_csv(REPORTS_FILE, index=False)

# تهيئة session_state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "report_name" not in st.session_state:
    st.session_state.report_name = ""
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "errors" not in st.session_state:
    st.session_state.errors = []
if "notes" not in st.session_state:
    st.session_state.notes = ""

# الصفحة الرئيسية
def show_home():
    st.title("تقييم")
    
    # التاريخ والوقت أعلى يسار
    col1, col2 = st.columns([3,1])
    with col2:
        st.write(datetime.now().strftime("%Y-%m-%d"))
        st.write(datetime.now().strftime("%H:%M"))
    
    # إدخال اسم التقرير
    st.session_state.report_name = st.text_input("اسم التقرير")
    
    # الأزرار
    if st.button("ابدأ التقييم"):
        if st.session_state.report_name.strip() == "":
            st.warning("الرجاء إدخال اسم التقرير أولاً")
        else:
            st.session_state.start_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.page = "evaluation"
    if st.button("سجل التقييمات"):
        st.session_state.page = "reports"

# صفحة التقييم (الأخطاء)
def show_evaluation():
    st.header(f"التقييم - {st.session_state.report_name}")
    
    # قائمة الأخطاء
    errors_list = [
        "باب السائق", "حزام", "افضلية", "سرعة", "ضعف مراقبة",
        "عدم التقيد بالمسارات", "سرعة اثناء الانعطاف", "إشارة للموازي", "موقف موازي",
        "صدم بالموازي", "مراقبة اثناء الخروج", "استخدام كلتا القدمين", "ضعف تحكم بالمقود",
        "صدم ثمانية", "إشارة ٩٠خلفي", "موقف ٩٠خلفي", "صدم ٩٠خلفي", "عكس سير",
        "فلشر للرجوع", "الرجوع للخلف", "مراقبة اثناء الرجوع", "تسارع عالي", "تباطؤ",
        "فرامل", "علامةقف", "صدم رصيف", "خطوط المشاة", "تجاوز اشارة",
        "موقف نهائي", "صدم نهائي"
    ]
    
    cols = st.columns(3)
    for i, error in enumerate(errors_list):
        if cols[i % 3].button(error):
            st.session_state.errors.append(error)
    
    st.session_state.notes = st.text_area("ملاحظات")
    
    if st.button("إنهاء التقييم"):
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_report = {
            "report_name": st.session_state.report_name,
            "start_time": st.session_state.start_time,
            "end_time": end_time,
            "errors": "; ".join(st.session_state.errors),
            "notes": st.session_state.notes
        }
        reports.loc[len(reports)] = new_report
        reports.to_csv(REPORTS_FILE, index=False)
        
        # تصفير البيانات
        st.session_state.errors = []
        st.session_state.notes = ""
        st.session_state.page = "home"
        st.success("تم حفظ التقييم بنجاح!")

# صفحة السجل
def show_reports():
    st.header("سجل التقييمات السابقة")
    st.dataframe(reports)
    if st.button("رجوع للصفحة الرئيسية"):
        st.session_state.page = "home"

# تشغيل البرنامج
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "evaluation":
    show_evaluation()
elif st.session_state.page == "reports":
    show_reports()
