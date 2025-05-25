import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
import os
import traceback
import base64
from auth import init_auth, logout
import shutil
import glob
import json

# تابع کمکی برای شکستن متن به چند خط
def wrap_text_to_lines(draw, text, font, max_width):
    """
    متن را فقط بر اساس خطوط جدید (اینتر) جدا می‌کند
    و هیچ شکستن خط خودکاری انجام نمی‌دهد
    """
    # فقط متن را بر اساس خطوط جدید (اینتر) جدا می‌کنیم
    return text.split('\n')

# تابع پردازش متن فارسی با مدیریت خطا برای سرور
def process_persian_text(text):
    """
    پردازش متن فارسی با مدیریت خطا برای سرورها
    استراتژی‌های مختلف fallback برای نمایش صحیح متن
    """
    if not text:
        return ""
    
    # بررسی تنظیم دستی کاربر
    strategy = st.session_state.get('text_processing_strategy', 'auto')
    
    # اگر کاربر "متن اصلی" را انتخاب کرده، بدون تغییر برگردان
    if strategy == "original":
        return text
    
    # اگر کاربر "اجباری معکوس" را انتخاب کرده
    if strategy == "force_reverse":
        try:
            lines = text.split('\n')
            processed_lines = []
            for line in lines:
                # معکوس کردن هر خط به صورت character-level
                reversed_line = line[::-1]
                processed_lines.append(reversed_line)
            return '\n'.join(processed_lines)
        except:
            return text
    
    # حالت خودکار (auto) - استراتژی‌های پیشین
    # استراتژی 1: فقط از arabic_reshaper استفاده کنیم (بدون bidi)
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        # حذف get_display و استفاده مستقیم از reshaped_text
        if reshaped_text and len(reshaped_text) >= len(text):
            return reshaped_text
    except Exception as e:
        print(f"استراتژی 1 ناموفق: {str(e)}")
    
    # استراتژی 2: پردازش دستی با تشخیص حروف فارسی
    try:
        # تشخیص حروف فارسی/عربی
        persian_chars = 'آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
        has_persian = any(char in persian_chars for char in text)
        
        if has_persian:
            # برای متن فارسی: معکوس کردن کل متن
            lines = text.split('\n')
            processed_lines = []
            for line in lines:
                # معکوس کردن هر خط به صورت character-level
                reversed_line = line[::-1]
                processed_lines.append(reversed_line)
            return '\n'.join(processed_lines)
        else:
            # برای متن انگلیسی: بدون تغییر
            return text
    except Exception as e:
        print(f"استراتژی 2 ناموفق: {str(e)}")
    
    # استراتژی 3: معکوس کردن کلمات (fallback ساده)
    try:
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            words = line.split()
            if len(words) > 1:
                # معکوس کردن ترتیب کلمات در هر خط
                reversed_words = words[::-1]
                processed_lines.append(' '.join(reversed_words))
            else:
                # اگر فقط یک کلمه است، کل خط را معکوس کن
                processed_lines.append(line[::-1])
        return '\n'.join(processed_lines)
    except Exception as e:
        print(f"استراتژی 3 ناموفق: {str(e)}")
    
    # استراتژی 4: در نهایت متن اصلی (worst case)
    print("همه استراتژی‌ها ناموفق، بازگشت به متن اصلی")
    return text

# تابع بررسی وضعیت کتابخانه‌های RTL
def check_rtl_libraries():
    """
    بررسی وضعیت کتابخانه‌های پردازش متن راست به چپ
    """
    try:
        # تست کتابخانه‌ها با متن نمونه
        test_text = "تست متن فارسی"
        reshaped = arabic_reshaper.reshape(test_text)
        # حذف get_display از تست
        if reshaped and len(reshaped) > 0:
            return True, "کتابخانه arabic_reshaper به درستی کار می‌کند"
        else:
            return False, "مشکل در خروجی arabic_reshaper"
    except ImportError as e:
        return False, f"کتابخانه‌های RTL نصب نیستند: {str(e)}"
    except Exception as e:
        return False, f"خطا در کتابخانه‌های RTL: {str(e)}"

# تنظیمات اولیه صفحه
st.set_page_config(
    page_title="تصویرساز فارسی",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنظیم مسیر فونت‌ها و تمپلیت‌ها
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Regular.ttf")
FONT_BOLD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Vazirmatn-Bold.ttf")

# استفاده از مسیر tmp برای پوشه‌های قابل نوشتن
TEMPLATES_DIR = os.path.join("/tmp", "templates")
SETTINGS_DIR = os.path.join("/tmp", "settings")

# اطمینان از وجود پوشه تمپلیت‌ها و تنظیمات
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)
if not os.path.exists(SETTINGS_DIR):
    os.makedirs(SETTINGS_DIR)

# تبدیل مسیر فایل‌ها به URL
FONT_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_PATH, 'rb').read()).decode()}"
FONT_BOLD_URL = f"data:font/ttf;base64,{base64.b64encode(open(FONT_BOLD_PATH, 'rb').read()).decode()}"

# تنظیمات استایل
st.markdown(f"""
    <style>
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_URL}') format('truetype');
        font-weight: normal;
        font-style: normal;
    }}
    
    @font-face {{
        font-family: 'Vazir';
        src: url('{FONT_BOLD_URL}') format('truetype');
        font-weight: bold;
        font-style: normal;
    }}
    
    html, body, [class*="st-"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    input, button, textarea, select {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTextInput > div > div > input {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stButton > button {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stMarkdown {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stAlert {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSelectbox > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSlider > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stColorPicker > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stFileUploader > div > div {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .stSidebar [data-testid="stSidebar"] {{
        font-family: 'Vazir', sans-serif !important;
    }}
    
    .layer-card {{
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .layer-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .layer-title {{
        font-size: 1.2rem;
        font-weight: bold;
        color: #1a237e;
    }}
    
    .layer-controls {{
        display: flex;
        gap: 0.5rem;
    }}
    
    .layer-content {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }}
    
    .layer-preview {{
        width: 100%;
        height: 150px;
        object-fit: contain;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }}
    
    .layer-settings {{
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }}
    
    .add-layer-button {{
        width: 100%;
        padding: 1rem;
        background-color: #e3f2fd;
        border: 2px dashed #2196F3;
        border-radius: 10px;
        color: #1976D2;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .add-layer-button:hover {{
        background-color: #bbdefb;
    }}
    
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .settings-button {{
        margin-left: 1rem;
    }}

    /* استایل مخصوص دکمه‌های انتخاب رنگ */
    .color-button > button {{
        position: relative;
        min-height: 60px;
        height: auto !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        padding: 5px 2px;
        text-align: center;
        color: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        overflow: hidden;
    }}

    .color-button > button::after {{
        content: attr(data-color-name);
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        color: #333;
        font-size: 0.7rem;
        padding: 2px;
        background-color: rgba(255, 255, 255, 0.7);
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    }}

    .color-button > button::before {{
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        bottom: 25px;
        left: 0;
        background-color: attr(data-color);
        border-radius: 4px;
        border: 1px solid #ccc;
    }}
    </style>
""", unsafe_allow_html=True)

# بررسی احراز هویت
if not init_auth():
    st.stop()

# بررسی وضعیت کتابخانه‌های RTL
rtl_status, rtl_message = check_rtl_libraries()
if not rtl_status:
    # نمایش هشدار در expander تا کمتر مزاحم باشد
    with st.expander("⚠️ هشدار: مشکل در نمایش متن فارسی"):
        st.warning(f"علت: {rtl_message}")
        st.info("💡 برای رفع این مشکل، دستورات زیر را در سرور اجرا کنید:")
        st.code("pip install arabic-reshaper python-bidi")
        st.warning("🔧 در حال حاضر از حالت جایگزین استفاده می‌شود.")
# اگر همه چیز درست است، پیغام موفقیت نمایش نده که صفحه شلوغ نشود

# مسیر فایل دیتابیس رنگ‌ها
COLORS_DB_PATH = os.path.join("/tmp", "colors.json")

# اطمینان از وجود پوشه data
if not os.path.exists(os.path.dirname(COLORS_DB_PATH)):
    os.makedirs(os.path.dirname(COLORS_DB_PATH))

# تابع بارگذاری رنگ‌ها از فایل
def load_colors():
    if os.path.exists(COLORS_DB_PATH):
        try:
            with open(COLORS_DB_PATH, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"خطا در بارگذاری رنگ‌ها: {str(e)}")
    return []

# تابع ذخیره رنگ‌ها در فایل
def save_colors(colors):
    try:
        with open(COLORS_DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(colors, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره رنگ‌ها: {str(e)}")
        return False

# تابع ذخیره تنظیمات پیش‌فرض تمپلیت
def save_template_settings(template_name, settings):
    try:
        settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
        with open(settings_path, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره تنظیمات تمپلیت: {str(e)}")
        return False

# تابع بارگذاری تنظیمات پیش‌فرض تمپلیت
def load_template_settings(template_name):
    settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات تمپلیت: {str(e)}")
    return None

# تابع بررسی وجود تنظیمات پیش‌فرض برای تمپلیت
def has_template_settings(template_name):
    settings_path = os.path.join(SETTINGS_DIR, f"{template_name}.json")
    return os.path.exists(settings_path)

# کلاس برای مدیریت لایه‌ها
class Layer:
    def __init__(self, name, image=None):
        self.name = name
        self.image = image
        self.x_percent = 50
        self.y_percent = 0
        self.size_percent = 100
        self.opacity = 100
        self.visible = True
        self.image_key = None  # کلید یکتا برای هر تصویر

# مدیریت لایه‌ها در session state
if 'layers' not in st.session_state:
    st.session_state.layers = []

# برای ذخیره نام تمپلیت انتخاب شده
if 'selected_template_name' not in st.session_state:
    st.session_state.selected_template_name = None

# برای ذخیره مسیر تمپلیت انتخاب شده
if 'selected_template_path' not in st.session_state:
    st.session_state.selected_template_path = None

# برای ذخیره تمپلیت آپلود شده
if 'template_file' not in st.session_state:
    st.session_state.template_file = None

# برای ذخیره متن
if 'text' not in st.session_state:
    st.session_state.text = ""

# برای ذخیره عنوان
if 'title_text' not in st.session_state:
    st.session_state.title_text = ""

# برای ذخیره تنظیمات متن
if 'font_size_percent' not in st.session_state:
    st.session_state.font_size_percent = 4
if 'text_color' not in st.session_state:
    st.session_state.text_color = "#000000"
if 'is_bold' not in st.session_state:
    st.session_state.is_bold = False
if 'text_x_percent' not in st.session_state:
    st.session_state.text_x_percent = 50
if 'text_y_percent' not in st.session_state:
    st.session_state.text_y_percent = 98
if 'max_text_width_percent' not in st.session_state:
    st.session_state.max_text_width_percent = 80
if 'line_spacing_percent' not in st.session_state:
    st.session_state.line_spacing_percent = 120

# برای ذخیره تنظیمات عنوان
if 'title_font_size_percent' not in st.session_state:
    st.session_state.title_font_size_percent = 6
if 'title_text_color' not in st.session_state:
    st.session_state.title_text_color = "#000000"
if 'title_is_bold' not in st.session_state:
    st.session_state.title_is_bold = True
if 'title_text_x_percent' not in st.session_state:
    st.session_state.title_text_x_percent = 50
if 'title_text_y_percent' not in st.session_state:
    st.session_state.title_text_y_percent = 10
if 'title_max_text_width_percent' not in st.session_state:
    st.session_state.title_max_text_width_percent = 80
if 'title_line_spacing_percent' not in st.session_state:
    st.session_state.title_line_spacing_percent = 120

# برای ذخیره وضعیت صفحه‌ای که کاربر در آن قرار دارد
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'main'  # صفحه اصلی به عنوان پیش‌فرض

# برای ذخیره رنگ‌های پیش‌فرض
if 'default_colors' not in st.session_state:
    st.session_state.default_colors = load_colors()

# برای ذخیره نام رنگ جدید
if 'new_color_name' not in st.session_state:
    st.session_state.new_color_name = ""

# برای ذخیره مقدار رنگ جدید
if 'new_color_value' not in st.session_state:
    st.session_state.new_color_value = "#000000"

# برای کنترل استراتژی پردازش متن فارسی
if 'text_processing_strategy' not in st.session_state:
    st.session_state.text_processing_strategy = "auto"  # auto, force_reverse, original

# نمایش صفحه متناسب با وضعیت
if st.session_state.current_page == 'settings':
    # صفحه تنظیمات
    
    # ایجاد هدر با دکمه بازگشت
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("⚙️ تنظیمات")
    with col2:
        if st.button("🔙 بازگشت", key="header_back_button"):
            st.session_state.current_page = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # ایجاد تب‌های اصلی تنظیمات
    settings_tab1, settings_tab2 = st.tabs(["📁 مدیریت تمپلیت‌ها", "🎨 مدیریت رنگ‌ها"])
    
    with settings_tab1:
        # نمایش تب‌های مدیریت تمپلیت
        template_tab1, template_tab2 = st.tabs(["📂 تمپلیت‌های موجود", "⬆️ آپلود تمپلیت جدید"])
        
        with template_tab1:
            # دریافت لیست تمپلیت‌های موجود
            template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
            template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
            
            if template_files:
                # ساخت لیست نمایشی از تمپلیت‌ها
                template_names = [os.path.basename(f) for f in template_files]
                
                # نمایش لیست تمپلیت‌ها
                st.markdown("تمپلیت‌های ذخیره شده:")
                for i, template in enumerate(template_names):
                    # بررسی آیا تمپلیت دارای تنظیمات پیش‌فرض است
                    template_basename = os.path.splitext(template)[0]
                    has_settings = has_template_settings(template_basename)
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # نمایش ستاره برای تمپلیت‌هایی که تنظیمات پیش‌فرض دارند
                        if has_settings:
                            st.write(f"{i+1}. ⭐ {template}")
                        else:
                            st.write(f"{i+1}. {template}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{i}"):
                            try:
                                os.remove(os.path.join(TEMPLATES_DIR, template))
                                # حذف فایل تنظیمات اگر وجود داشته باشد
                                if has_settings:
                                    settings_path = os.path.join(SETTINGS_DIR, f"{template_basename}.json")
                                    if os.path.exists(settings_path):
                                        os.remove(settings_path)
                                
                                # اگر تمپلیت حذف شده با تمپلیت انتخاب شده یکسان است، انتخاب را پاک کن
                                if st.session_state.selected_template_name == template:
                                    st.session_state.selected_template_name = None
                                    st.session_state.selected_template_path = None
                                st.success(f"تمپلیت {template} با موفقیت حذف شد!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطا در حذف تمپلیت: {str(e)}")
            else:
                st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از تب آپلود، یک تمپلیت جدید اضافه کنید.")
        
        with template_tab2:
            st.markdown("### 📁 آپلود تمپلیت جدید")
            
            # فرم آپلود تمپلیت
            template_file = st.file_uploader("تمپلیت جدید را انتخاب کنید", type=["png", "jpg", "jpeg"], help="یک تصویر تمپلیت با فرمت PNG یا JPEG آپلود کنید")
            template_name = st.text_input("نام تمپلیت (اختیاری)", help="اگر خالی بماند، از نام فایل استفاده می‌شود")
            
            if template_file:
                try:
                    # نمایش پیش‌نمایش تمپلیت
                    template_preview = Image.open(template_file)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.image(template_preview, caption="پیش‌نمایش تمپلیت جدید", width=300)
                        
                        # دکمه refresh برای پیش‌نمایش
                        if st.button("🔄 بروزرسانی پیش‌نمایش", key="refresh_template_preview"):
                            st.rerun()
                    
                    with col2:
                        st.markdown("### ⚙️ تنظیمات پیش‌فرض")
                        st.info("تنظیمات پیش‌فرض برای این تمپلیت، هنگام استفاده از آن به‌طور خودکار اعمال خواهند شد.")
                        
                        # تنظیمات اساسی عنوان
                        st.markdown("**🏷️ تنظیمات عنوان:**")
                        title_col1, title_col2 = st.columns(2)
                        with title_col1:
                            default_title_font_size = st.slider("سایز فونت عنوان (% ارتفاع)", 1, 20, 6, key="default_title_font_size")
                            default_title_x = st.slider("موقعیت افقی عنوان (%)", 0, 100, 50, key="default_title_x")
                        with title_col2:
                            default_title_y = st.slider("موقعیت عمودی عنوان (%)", 0, 100, 10, key="default_title_y")
                            default_title_color = st.color_picker("رنگ عنوان", "#000000", key="default_title_color")
                        
                        default_title_is_bold = st.checkbox("عنوان بولد", value=True, key="default_title_is_bold")
                        
                        # تنظیمات اساسی متن
                        st.markdown("**📝 تنظیمات متن:**")
                        default_font_size = st.slider("سایز فونت (% ارتفاع)", 1, 20, 4, key="default_font_size")
                        default_text_color = st.color_picker("رنگ متن", "#000000", key="default_text_color")
                        
                        # تنظیمات موقعیت متن
                        pos_col1, pos_col2 = st.columns(2)
                        with pos_col1:
                            default_text_x = st.slider("موقعیت افقی (%)", 0, 100, 50, key="default_text_x")
                        with pos_col2:
                            default_text_y = st.slider("موقعیت عمودی (%)", 0, 100, 98, key="default_text_y")
                        
                        # تنظیمات اساسی لایه
                        st.markdown("**🖼️ تنظیمات لایه:**")
                        layer_col1, layer_col2 = st.columns(2)
                        with layer_col1:
                            default_layer_x = st.slider("موقعیت افقی لایه (%)", 0, 100, 50, key="default_layer_x")
                            default_layer_size = st.slider("اندازه لایه (%)", 10, 300, 100, key="default_layer_size")
                        with layer_col2:
                            default_layer_y = st.slider("موقعیت عمودی لایه (%)", 0, 100, 0, key="default_layer_y")
                            default_layer_opacity = st.slider("شفافیت لایه (%)", 0, 100, 100, key="default_layer_opacity")
                    
                    # تنظیمات پیشرفته (اختیاری)
                    st.markdown("---")
                    show_advanced = st.checkbox("نمایش تنظیمات پیشرفته", value=False, key="show_advanced_template")
                    if show_advanced:
                        adv_col1, adv_col2 = st.columns(2)
                        with adv_col1:
                            st.markdown("**تنظیمات پیشرفته عنوان:**")
                            default_title_max_width = st.slider("عرض عنوان (%)", 10, 100, 80, key="default_title_max_width")
                            default_title_line_spacing = st.slider("فاصله خطوط عنوان (%)", 100, 200, 120, key="default_title_line_spacing")
                        with adv_col2:
                            st.markdown("**تنظیمات پیشرفته متن:**")
                            default_max_text_width = st.slider("عرض متن (%)", 10, 100, 80, key="default_max_text_width")
                            default_line_spacing = st.slider("فاصله خطوط متن (%)", 100, 200, 120, key="default_line_spacing")
                        
                        default_is_bold = st.checkbox("متن بولد", value=False, key="default_is_bold")
                    else:
                        # مقادیر پیش‌فرض
                        default_title_max_width = 80
                        default_title_line_spacing = 120
                        default_max_text_width = 80
                        default_line_spacing = 120
                        default_is_bold = False
                    
                    # بخش تست و پیش‌نمایش
                    st.markdown("---")
                    st.markdown("### 🧪 تست و پیش‌نمایش تنظیمات")
                    st.info("در این بخش می‌توانید تنظیمات را با متن و لایه نمونه تست کنید.")
                    
                    # ایجاد دو ستون برای تست
                    test_col1, test_col2 = st.columns([1, 1])
                    
                    with test_col1:
                        st.markdown("**📝 متن‌های نمونه:**")
                        
                        # متن نمونه عنوان
                        test_title = st.text_input(
                            "عنوان نمونه:",
                            value="عنوان تست",
                            key="test_title_input",
                            help="عنوان نمونه برای تست تنظیمات"
                        )
                        
                        # متن نمونه اصلی
                        test_text = st.text_area(
                            "متن نمونه:",
                            value="این یک متن نمونه برای تست تنظیمات است.\nمی‌توانید چندین خط متن وارد کنید.",
                            height=100,
                            key="test_text_input",
                            help="متن نمونه برای تست تنظیمات"
                        )
                        
                        # آپلود لایه نمونه (اختیاری)
                        st.markdown("**🖼️ لایه نمونه (اختیاری):**")
                        test_layer_file = st.file_uploader(
                            "تصویر نمونه برای لایه:",
                            type=["png", "jpg", "jpeg"],
                            key="test_layer_upload",
                            help="یک تصویر نمونه برای تست لایه آپلود کنید (اختیاری)"
                        )
                        
                        # دکمه بروزرسانی پیش‌نمایش
                        if st.button("🔄 بروزرسانی پیش‌نمایش تست", key="refresh_test_preview"):
                            st.rerun()
                    
                    with test_col2:
                        st.markdown("**👁️ پیش‌نمایش تست:**")
                        
                        # ایجاد پیش‌نمایش تست
                        try:
                            # محاسبه ابعاد تصویر
                            template_width, template_height = template_preview.size
                            min_dimension = min(template_width, template_height)
                            
                            # ایجاد یک تصویر پایه خالی (سفید)
                            test_preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                            
                            # اضافه کردن لایه نمونه اگر آپلود شده
                            if test_layer_file:
                                try:
                                    test_layer_image = Image.open(test_layer_file)
                                    
                                    # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                                    max_dimension = int(min_dimension * (default_layer_size / 100))
                                    
                                    # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                                    original_width, original_height = test_layer_image.size
                                    aspect_ratio = original_width / original_height
                                    
                                    if aspect_ratio >= 1:
                                        new_width = max_dimension
                                        new_height = int(max_dimension / aspect_ratio)
                                    else:
                                        new_height = max_dimension
                                        new_width = int(max_dimension * aspect_ratio)
                                    
                                    test_layer_image = test_layer_image.resize((new_width, new_height), Image.LANCZOS)
                                    
                                    # تبدیل به RGBA
                                    if test_layer_image.mode != 'RGBA':
                                        test_layer_image = test_layer_image.convert('RGBA')
                                    
                                    # اعمال شفافیت
                                    if default_layer_opacity < 100:
                                        test_layer_image.putalpha(int(255 * default_layer_opacity / 100))
                                    
                                    # محاسبه موقعیت
                                    img_x = int((template_width - new_width) * (default_layer_x / 100))
                                    img_y = int((template_height - new_height) * (default_layer_y / 100))
                                    
                                    # اضافه کردن تصویر به پیش‌نمایش
                                    test_preview_image.paste(test_layer_image, (img_x, img_y), test_layer_image)
                                except Exception as e:
                                    st.warning(f"خطا در پردازش لایه نمونه: {str(e)}")
                            
                            # اضافه کردن تمپلیت به عنوان لایه بالایی
                            if template_preview.mode == 'RGBA':
                                test_preview_image = Image.alpha_composite(test_preview_image, template_preview)
                            else:
                                template_rgba = template_preview.convert('RGBA')
                                test_preview_image = Image.alpha_composite(test_preview_image, template_rgba)
                            
                            # اضافه کردن عنوان نمونه
                            if test_title:
                                title_bidi_text = process_persian_text(test_title)
                                title_font_size = int(template_height * (default_title_font_size / 100))
                                
                                try:
                                    title_font_path = FONT_BOLD_PATH if default_title_is_bold else FONT_PATH
                                    title_font = ImageFont.truetype(title_font_path, title_font_size)
                                    
                                    title_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                                    title_draw = ImageDraw.Draw(title_image)
                                    
                                    title_max_width = template_width * (default_title_max_width / 100)
                                    title_lines = wrap_text_to_lines(title_draw, title_bidi_text, title_font, title_max_width)
                                    
                                    title_line_spacing_factor = default_title_line_spacing / 100
                                    title_line_height = int(title_font_size * title_line_spacing_factor)
                                    title_total_text_height = title_line_height * len(title_lines)
                                    
                                    title_start_y = int((template_height - title_total_text_height) * (default_title_y / 100))
                                    
                                    for i, line in enumerate(title_lines):
                                        line_width = title_draw.textlength(line, font=title_font)
                                        line_x = int((template_width - line_width) * (default_title_x / 100))
                                        line_y = title_start_y + i * title_line_height
                                        title_draw.text((line_x, line_y), line, font=title_font, fill=default_title_color)
                                    
                                    test_preview_image = Image.alpha_composite(test_preview_image, title_image)
                                except Exception as e:
                                    st.warning(f"خطا در رندر عنوان: {str(e)}")
                            
                            # اضافه کردن متن نمونه
                            if test_text:
                                bidi_text = process_persian_text(test_text)
                                font_size = int(template_height * (default_font_size / 100))
                                
                                try:
                                    font_path = FONT_BOLD_PATH if default_is_bold else FONT_PATH
                                    font = ImageFont.truetype(font_path, font_size)
                                    
                                    text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                                    text_draw = ImageDraw.Draw(text_image)
                                    
                                    max_width = template_width * (default_max_text_width / 100)
                                    lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                                    
                                    line_spacing_factor = default_line_spacing / 100
                                    line_height = int(font_size * line_spacing_factor)
                                    total_text_height = line_height * len(lines)
                                    
                                    start_y = int((template_height - total_text_height) * (default_text_y / 100))
                                    
                                    for i, line in enumerate(lines):
                                        line_width = text_draw.textlength(line, font=font)
                                        line_x = int((template_width - line_width) * (default_text_x / 100))
                                        line_y = start_y + i * line_height
                                        text_draw.text((line_x, line_y), line, font=font, fill=default_text_color)
                                    
                                    test_preview_image = Image.alpha_composite(test_preview_image, text_image)
                                except Exception as e:
                                    st.warning(f"خطا در رندر متن: {str(e)}")
                            
                            # نمایش پیش‌نمایش تست
                            st.image(test_preview_image, caption="پیش‌نمایش تست تنظیمات", width=300)
                            
                            # نمایش اطلاعات تکمیلی
                            st.success("✅ پیش‌نمایش تست با موفقیت ساخته شد!")
                            st.info(f"📏 ابعاد: {template_width}x{template_height}")
                            
                        except Exception as e:
                            st.error(f"❌ خطا در ساخت پیش‌نمایش تست: {str(e)}")
                            st.info("💡 لطفاً تنظیمات را بررسی کنید و دوباره تلاش کنید.")
                    
                    # دکمه ذخیره تمپلیت
                    if st.button("💾 ذخیره تمپلیت", key="save_template_btn"):
                        # تعیین نام تمپلیت
                        if template_name.strip():
                            final_template_name = template_name.strip()
                        else:
                            final_template_name = os.path.splitext(template_file.name)[0]
                        
                        # ذخیره فایل تمپلیت
                        template_extension = os.path.splitext(template_file.name)[1]
                        template_save_path = os.path.join(TEMPLATES_DIR, f"{final_template_name}{template_extension}")
                        
                        try:
                            with open(template_save_path, "wb") as f:
                                f.write(template_file.getbuffer())
                            
                            # ذخیره تنظیمات پیش‌فرض
                            template_settings = {
                                "title": {
                                    "font_size_percent": default_title_font_size,
                                    "text_color": default_title_color,
                                    "is_bold": default_title_is_bold,
                                    "text_x_percent": default_title_x,
                                    "text_y_percent": default_title_y,
                                    "max_text_width_percent": default_title_max_width,
                                    "line_spacing_percent": default_title_line_spacing
                                },
                                "text": {
                                    "font_size_percent": default_font_size,
                                    "text_color": default_text_color,
                                    "is_bold": default_is_bold,
                                    "text_x_percent": default_text_x,
                                    "text_y_percent": default_text_y,
                                    "max_text_width_percent": default_max_text_width,
                                    "line_spacing_percent": default_line_spacing
                                },
                                "layer": {
                                    "x_percent": default_layer_x,
                                    "y_percent": default_layer_y,
                                    "size_percent": default_layer_size,
                                    "opacity": default_layer_opacity
                                }
                            }
                            
                            if save_template_settings(final_template_name, template_settings):
                                st.success(f"✅ تمپلیت '{final_template_name}' با تنظیمات پیش‌فرض ذخیره شد!")
                                st.info("🔄 برای استفاده از تمپلیت جدید، به صفحه اصلی بروید.")
                            else:
                                st.warning(f"⚠️ تمپلیت ذخیره شد اما تنظیمات پیش‌فرض ذخیره نشد.")
                        
                        except Exception as e:
                            st.error(f"❌ خطا در ذخیره تمپلیت: {str(e)}")
                
                except Exception as e:
                    st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    
    with settings_tab2:
        # بخش مدیریت رنگ‌های پیش‌فرض
        # کارت رنگ‌های موجود
        with st.container():
            st.subheader("📋 رنگ‌های ذخیره شده")
            
            if st.session_state.default_colors:
                # تعداد ستون‌ها برای نمایش رنگ‌ها
                num_cols = 3
                color_rows = [st.session_state.default_colors[i:i+num_cols] for i in range(0, len(st.session_state.default_colors), num_cols)]
                
                for row_idx, row in enumerate(color_rows):
                    cols = st.columns(num_cols)
                    for col_idx, color_item in enumerate(row):
                        idx = row_idx * num_cols + col_idx
                        with cols[col_idx]:
                            # نمایش نام و مقدار رنگ
                            st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 10px;'>"
                                        f"<div style='width: 30px; height: 30px; background-color: {color_item['value']}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                                        f"<span>{color_item['name']} ({color_item['value']})</span>"
                                        f"</div>", unsafe_allow_html=True)
                            
                            # دکمه حذف رنگ
                            if st.button("🗑️ حذف", key=f"delete_color_{idx}"):
                                st.session_state.default_colors.pop(idx)
                                
                                # ذخیره تغییرات در فایل دیتابیس
                                if save_colors(st.session_state.default_colors):
                                    st.success(f"رنگ با موفقیت حذف شد!")
                                else:
                                    st.error("خطا در ذخیره‌سازی تغییرات. تغییرات موقت اعمال شد.")
                                
                                st.rerun()
            else:
                st.info("🔍 هنوز رنگی ذخیره نشده است. لطفاً از فرم زیر، رنگ مورد نظر خود را اضافه کنید.")
        
        # کارت افزودن رنگ جدید
        with st.container():
            st.subheader("➕ افزودن رنگ جدید")
            
            # فرم افزودن رنگ جدید
            col1, col2 = st.columns(2)
            
            with col1:
                new_color_name = st.text_input("نام رنگ", value=st.session_state.new_color_name, key="new_color_name_input", 
                                              help="یک نام معنادار برای رنگ خود وارد کنید (مثلا: آبی آسمانی، قرمز لوگو، و...)")
                
                # بروزرسانی مقدار در session state
                if st.session_state.new_color_name != new_color_name:
                    st.session_state.new_color_name = new_color_name
            
            with col2:
                new_color_value = st.color_picker("انتخاب رنگ", value=st.session_state.new_color_value, key="new_color_value_picker")
                
                # بروزرسانی مقدار در session state
                if st.session_state.new_color_value != new_color_value:
                    st.session_state.new_color_value = new_color_value
            
            # نمایش پیش‌نمایش رنگ
            st.markdown(f"<div style='display: flex; align-items: center; margin: 15px 0;'>"
                       f"<div style='width: 50px; height: 30px; background-color: {new_color_value}; margin-right: 10px; border: 1px solid #ccc;'></div>"
                       f"<span>پیش‌نمایش رنگ انتخاب شده: {new_color_value}</span>"
                       f"</div>", unsafe_allow_html=True)
            
            # دکمه ذخیره رنگ
            if st.button("💾 ذخیره این رنگ", key="save_color_btn"):
                if new_color_name.strip() == "":
                    st.error("❌ لطفاً یک نام برای رنگ وارد کنید.")
                else:
                    # بررسی تکراری نبودن نام
                    existing_names = [color["name"] for color in st.session_state.default_colors]
                    if new_color_name in existing_names:
                        st.warning(f"⚠️ رنگی با نام '{new_color_name}' قبلاً ذخیره شده است. لطفاً نام دیگری انتخاب کنید.")
                    else:
                        # افزودن رنگ جدید به لیست
                        st.session_state.default_colors.append({
                            "name": new_color_name,
                            "value": new_color_value
                        })
                        
                        # ذخیره رنگ‌ها در فایل
                        if save_colors(st.session_state.default_colors):
                            # پاک کردن مقادیر فرم برای رنگ بعدی
                            st.session_state.new_color_name = ""
                            st.session_state.new_color_value = "#000000"
                            
                            st.success(f"✅ رنگ '{new_color_name}' با موفقیت ذخیره شد!")
                        else:
                            st.error("❌ خطا در ذخیره‌سازی رنگ. لطفاً دوباره تلاش کنید.")
                        
                        st.rerun()
    
    # فضای خالی برای تنظیمات بیشتر در آینده
    st.markdown("---")
    st.markdown("### تنظیمات بیشتر")
    # در اینجا می‌توانید تنظیمات بیشتری اضافه کنید
    
    # بخش Debug برای تشخیص مشکل متن فارسی
    st.markdown("---")
    st.markdown("### 🔧 تشخیص مشکل متن فارسی")
    
    with st.expander("🔍 تست پردازش متن فارسی"):
        st.info("این بخش برای تشخیص مشکل متن‌های برعکس روی سرور است.")
        
        # کنترل دستی استراتژی پردازش متن
        st.markdown("#### ⚙️ انتخاب روش پردازش متن")
        strategy_options = {
            "auto": "🤖 خودکار (پیشنهادی)",
            "force_reverse": "🔄 اجباری معکوس",
            "original": "📝 بدون تغییر"
        }
        
        selected_strategy = st.selectbox(
            "روش پردازش متن:",
            options=list(strategy_options.keys()),
            format_func=lambda x: strategy_options[x],
            index=0,
            help="اگر متن‌ها برعکس نمایش داده می‌شوند، گزینه 'اجباری معکوس' را امتحان کنید"
        )
        
        if selected_strategy != st.session_state.text_processing_strategy:
            st.session_state.text_processing_strategy = selected_strategy
            st.success(f"✅ روش پردازش متن به '{strategy_options[selected_strategy]}' تغییر کرد.")
            st.info("🔄 لطفاً صفحه را refresh کنید یا متن جدیدی وارد کنید تا تغییرات اعمال شود.")
        
        test_text = st.text_input(
            "متن تست را وارد کنید:",
            value="سلام دنیا",
            help="متن فارسی برای تست وارد کنید"
        )
        
        if st.button("🧪 تست پردازش متن"):
            if test_text:
                debug_result = debug_persian_text(test_text)
                st.code(debug_result)
                
                # نمایش نتیجه نهایی
                final_result = process_persian_text(test_text)
                st.success(f"نتیجه نهایی تابع process_persian_text: '{final_result}'")
            else:
                st.warning("لطفاً ابتدا متنی وارد کنید.")
        
        # راهنمای سریع
        st.markdown("""
        **راهنمای تفسیر نتایج:**
        - ✅ **استراتژی 1 موفق**: کتابخانه‌های RTL کار می‌کنند
        - ❌ **استراتژی 1 ناموفق**: مشکل در کتابخانه‌ها، fallback فعال می‌شود
        - **تشخیص فارسی True**: متن دارای حروف فارسی است
        - **تشخیص فارسی False**: متن انگلیسی است
        """)
        
        # نمایش وضعیت فعلی کتابخانه‌ها
        rtl_ok, rtl_msg = check_rtl_libraries()
        if rtl_ok:
            st.success(f"✅ وضعیت کتابخانه‌ها: {rtl_msg}")
        else:
            st.error(f"❌ وضعیت کتابخانه‌ها: {rtl_msg}")

else:
    # صفحه اصلی
    # عنوان اصلی
    
    # ایجاد هدر با دکمه تنظیمات
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("🎨 تصویرساز فارسی")
    with col2:
        if st.button("⚙️ تنظیمات", key="header_settings_button"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    st.markdown("---")
    
    # سایدبار
    with st.sidebar:
        # تب‌های سایدبار
        tab1, tab2 = st.tabs(["📝 راهنما", "👁️ پیش‌نمایش"])
        
        with tab1:
            st.header("راهنمای استفاده")
            st.markdown("""
            ### نحوه استفاده:
            1. یک تمپلیت آپلود یا انتخاب کنید
            2. لایه‌های مورد نظر را اضافه کنید
            3. برای هر لایه:
               - تصویر را آپلود کنید
               - موقعیت و اندازه را تنظیم کنید
               - شفافیت را تنظیم کنید
            4. متن فارسی را وارد کنید
            5. دکمه ساخت تصویر را بزنید
            
            ### نکات مهم:
            - از فونت وزیر برای نمایش متن فارسی استفاده می‌شود
            - می‌توانید ترتیب لایه‌ها را تغییر دهید
            - هر لایه را می‌توانید فعال یا غیرفعال کنید
            - تصویر نهایی در فایل output.png ذخیره می‌شود
            """)
        
        with tab2:
            st.header("پیش‌نمایش")
            
            # ایجاد یک placeholder برای پیش‌نمایش که به‌روزرسانی می‌شود
            preview_placeholder = st.empty()
            
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text or st.session_state.title_text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی
                    if template.mode == 'RGBA':
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن عنوان
                    if st.session_state.title_text:
                        title_bidi_text = process_persian_text(st.session_state.title_text)
                        title_font_size = int(template_height * (st.session_state.title_font_size_percent / 100))
                        
                        try:
                            title_font_path = FONT_BOLD_PATH if st.session_state.title_is_bold else FONT_PATH
                            title_font = ImageFont.truetype(title_font_path, title_font_size)
                            
                            title_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            title_draw = ImageDraw.Draw(title_image)
                            
                            title_max_width = template_width * (st.session_state.title_max_text_width_percent / 100)
                            title_lines = wrap_text_to_lines(title_draw, title_bidi_text, title_font, title_max_width)
                            
                            title_line_spacing_factor = st.session_state.title_line_spacing_percent / 100
                            title_line_height = int(title_font_size * title_line_spacing_factor)
                            title_total_text_height = title_line_height * len(title_lines)
                            
                            title_start_y = int((template_height - title_total_text_height) * (st.session_state.title_text_y_percent / 100))
                            
                            for i, line in enumerate(title_lines):
                                line_width = title_draw.textlength(line, font=title_font)
                                line_x = int((template_width - line_width) * (st.session_state.title_text_x_percent / 100))
                                line_y = title_start_y + i * title_line_height
                                title_draw.text((line_x, line_y), line, font=title_font, fill=st.session_state.title_text_color)
                            
                            preview_image = Image.alpha_composite(preview_image, title_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت عنوان: {str(e)}")

                    # اضافه کردن متن
                    if st.session_state.text:
                        bidi_text = process_persian_text(st.session_state.text)
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                    
                    # نمایش تصویر با سایز محدود شده در placeholder
                    with preview_placeholder.container():
                        st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", width=300)
                        
                        # اضافه کردن دکمه refresh برای بروزرسانی دستی
                        if st.button("🔄 بروزرسانی پیش‌نمایش", key="refresh_preview"):
                            st.rerun()
                    
                except Exception as e:
                    with preview_placeholder.container():
                        st.error(f"❌ خطا در ساخت پیش‌نمایش: {str(e)}")
            else:
                with preview_placeholder.container():
                    st.info("👆 برای مشاهده پیش‌نمایش، ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه، عنوان یا متن اضافه کنید.")
        
        # نمایش اطلاعات کاربر و دکمه خروج
        st.markdown("---")
        st.markdown(f"👤 کاربر: {st.session_state.username}")
        if st.button("🚪 خروج"):
            logout()
    
    # آپلود و مدیریت تمپلیت
    st.markdown('<p class="upload-header">1️⃣ انتخاب تمپلیت</p>', unsafe_allow_html=True)
    
    # دریافت لیست تمپلیت‌های موجود
    template_files = glob.glob(os.path.join(TEMPLATES_DIR, "*.png")) + glob.glob(os.path.join(TEMPLATES_DIR, "*.jpg"))
    template_files.sort(key=os.path.getmtime, reverse=True)  # مرتب‌سازی بر اساس زمان ایجاد
    
    if template_files:
        # ساخت لیست نمایشی از تمپلیت‌ها
        template_names = [os.path.basename(f) for f in template_files]
        
        # ایجاد لیست نمایشی با ستاره برای تمپلیت‌هایی که تنظیمات پیش‌فرض دارند
        display_template_names = []
        for template in template_names:
            template_basename = os.path.splitext(template)[0]
            if has_template_settings(template_basename):
                display_template_names.append(f"⭐ {template}")
            else:
                display_template_names.append(template)
        
        template_options = ["انتخاب کنید..."] + display_template_names
        
        # انتخاب تمپلیت
        selected_display_template = st.selectbox(
            "تمپلیت موردنظر را انتخاب کنید",
            template_options,
            index=0,
            help="یک تمپلیت از لیست انتخاب کنید یا از بخش 'تنظیمات' تمپلیت جدید اضافه کنید"
        )
        
        if selected_display_template != "انتخاب کنید...":
            # حذف ستاره از نام تمپلیت برای پیدا کردن فایل
            selected_template = selected_display_template.replace("⭐ ", "")
            selected_template_path = os.path.join(TEMPLATES_DIR, selected_template)
            
            # ذخیره انتخاب کاربر
            st.session_state.selected_template_name = selected_template
            st.session_state.selected_template_path = selected_template_path
            
            # بررسی و بارگذاری تنظیمات پیش‌فرض
            template_basename = os.path.splitext(selected_template)[0]
            template_settings = load_template_settings(template_basename)
            
            # فقط در صورتی تنظیمات پیش‌فرض را اعمال کن که تمپلیت تغییر کرده باشد
            if template_settings and st.session_state.get('last_loaded_template') != selected_template:
                # اعمال تنظیمات پیش‌فرض برای متن
                text_settings = template_settings.get("text", {})
                st.session_state.font_size_percent = text_settings.get("font_size_percent", 4)
                st.session_state.text_color = text_settings.get("text_color", "#000000")
                st.session_state.is_bold = text_settings.get("is_bold", False)
                st.session_state.text_x_percent = text_settings.get("text_x_percent", 50)
                st.session_state.text_y_percent = text_settings.get("text_y_percent", 98)
                st.session_state.max_text_width_percent = text_settings.get("max_text_width_percent", 80)
                st.session_state.line_spacing_percent = text_settings.get("line_spacing_percent", 120)
                
                # اعمال تنظیمات پیش‌فرض برای عنوان
                title_settings = template_settings.get("title", {})
                st.session_state.title_font_size_percent = title_settings.get("font_size_percent", 6)
                st.session_state.title_text_color = title_settings.get("text_color", "#000000")
                st.session_state.title_is_bold = title_settings.get("is_bold", True)
                st.session_state.title_text_x_percent = title_settings.get("text_x_percent", 50)
                st.session_state.title_text_y_percent = title_settings.get("text_y_percent", 10)
                st.session_state.title_max_text_width_percent = title_settings.get("max_text_width_percent", 80)
                st.session_state.title_line_spacing_percent = title_settings.get("line_spacing_percent", 120)
                
                # ذخیره نام تمپلیت فعلی
                st.session_state.last_loaded_template = selected_template
                
                # ذخیره تنظیمات پیش‌فرض لایه برای استفاده در هنگام ایجاد لایه جدید
                if "default_layer_settings" not in st.session_state:
                    st.session_state.default_layer_settings = {}
                
                st.session_state.default_layer_settings = template_settings.get("layer", {})
            
            # نمایش پیش‌نمایش تمپلیت
            try:
                template_preview = Image.open(selected_template_path)
                st.image(template_preview, caption=f"پیش‌نمایش تمپلیت: {selected_template}", width=300)
                
                if template_settings:
                    st.success(f"✅ تمپلیت '{selected_template}' با تنظیمات پیش‌فرض انتخاب شد. حالا می‌توانید لایه‌ها و متن را اضافه کنید.")
                else:
                    st.success(f"✅ تمپلیت '{selected_template}' انتخاب شد. حالا می‌توانید لایه‌ها و متن را اضافه کنید.")
            except Exception as e:
                st.error(f"خطا در بارگذاری تمپلیت: {str(e)}")
    else:
        st.info("🔍 هنوز تمپلیتی ذخیره نشده است. لطفاً از بخش 'تنظیمات'، تمپلیت جدید اضافه کنید.")
        # دکمه رفتن به بخش تنظیمات
        if st.button("رفتن به بخش تنظیمات"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    # بررسی وضعیت انتخاب تمپلیت برای نمایش بخش‌های بعدی
    if st.session_state.selected_template_path:
        # نمایش بخش مدیریت لایه‌ها
        st.markdown('<p class="upload-header">2️⃣ مدیریت لایه‌ها</p>', unsafe_allow_html=True)
        
        # دکمه افزودن لایه جدید
        if st.button("➕ افزودن لایه جدید"):
            new_layer = Layer(f"لایه {len(st.session_state.layers) + 1}")
            
            # اعمال تنظیمات پیش‌فرض لایه اگر موجود باشد
            if "default_layer_settings" in st.session_state and st.session_state.default_layer_settings:
                new_layer.x_percent = st.session_state.default_layer_settings.get("x_percent", 50)
                new_layer.y_percent = st.session_state.default_layer_settings.get("y_percent", 0)
                new_layer.size_percent = st.session_state.default_layer_settings.get("size_percent", 100)
                new_layer.opacity = st.session_state.default_layer_settings.get("opacity", 100)
            
            st.session_state.layers.append(new_layer)
            st.rerun()
        
        # نمایش لایه‌ها
        for i, layer in enumerate(st.session_state.layers):
            with st.container():
                st.markdown(f"### 🖼️ {layer.name}")
                
                # آپلود تصویر برای لایه
                uploaded_file = st.file_uploader(
                    "تصویر را انتخاب کنید",
                    type=["png", "jpg", "jpeg"],
                    key=f"layer_{i}_upload",
                    help="تصویری که می‌خواهید در این لایه قرار دهید را آپلود کنید"
                )
                
                if uploaded_file:
                    try:
                        # ایجاد کلید یکتا برای تصویر
                        if layer.image_key != uploaded_file.name:
                            layer.image_key = uploaded_file.name
                            layer.image = Image.open(uploaded_file)
                            st.rerun()  # بروزرسانی صفحه برای نمایش تصویر جدید
                        
                        st.image(layer.image, caption="پیش‌نمایش تصویر", width=200)
                    except Exception as e:
                        st.error(f"خطا در بارگذاری تصویر: {str(e)}")
                
                # تنظیمات لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_x = st.slider(
                        "موقعیت افقی (%)",
                        0, 100, layer.x_percent,
                        key=f"layer_{i}_x",
                        help="0: چپ، 50: وسط، 100: راست"
                    )
                    new_size = st.slider(
                        "اندازه (%)",
                        10, 300, layer.size_percent,
                        key=f"layer_{i}_size",
                        help="سایز تصویر به صورت درصدی از کوچکترین بعد تمپلیت (مقادیر بزرگتر از 100% تصویر را بزرگتر از حالت اصلی نمایش می‌دهند)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_x != layer.x_percent or new_size != layer.size_percent:
                        layer.x_percent = new_x
                        layer.size_percent = new_size
                        st.rerun()
                
                with col2:
                    new_y = st.slider(
                        "موقعیت عمودی (%)",
                        0, 100, layer.y_percent,
                        key=f"layer_{i}_y",
                        help="0: بالا، 50: وسط، 100: پایین"
                    )
                    new_opacity = st.slider(
                        "شفافیت (%)",
                        0, 100, layer.opacity,
                        key=f"layer_{i}_opacity",
                        help="شفافیت تصویر (0: کاملاً شفاف، 100: کاملاً مات)"
                    )
                    
                    # بروزرسانی مقادیر و رفرش صفحه
                    if new_y != layer.y_percent or new_opacity != layer.opacity:
                        layer.y_percent = new_y
                        layer.opacity = new_opacity
                        st.rerun()
                
                # کنترل‌های لایه
                col1, col2 = st.columns(2)
                with col1:
                    new_visible = st.checkbox(
                        "نمایش لایه",
                        value=layer.visible,
                        key=f"layer_{i}_visible"
                    )
                    
                    # بروزرسانی وضعیت نمایش و رفرش صفحه
                    if new_visible != layer.visible:
                        layer.visible = new_visible
                        st.rerun()
                    
                with col2:
                    if st.button("🗑️ حذف لایه", key=f"layer_{i}_delete"):
                        st.session_state.layers.pop(i)
                        st.rerun()
                
                st.markdown("---")

        # ورود عنوان
        st.markdown('<p class="upload-header">3️⃣ وارد کردن عنوان</p>', unsafe_allow_html=True)
        title_input = st.text_input("عنوان مورد نظر را وارد کنید", value=st.session_state.title_text, key="title_input", help="عنوان فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید.")

        # ذخیره عنوان در session state
        if 'title_input' in st.session_state and st.session_state.title_input != st.session_state.title_text:
            st.session_state.title_text = st.session_state.title_input
        
        # تنظیمات عنوان
        st.markdown('<p class="settings-header">⚙️ تنظیمات عنوان</p>', unsafe_allow_html=True)
        title_col1, title_col2 = st.columns(2)

        with title_col1:
            title_font_size = st.slider("سایز فونت عنوان (% ارتفاع تصویر)", 1, 20, st.session_state.title_font_size_percent, key="title_font_size_slider", help="سایز فونت عنوان به صورت درصدی از ارتفاع تصویر")
            # بروزرسانی session state
            if 'title_font_size_slider' in st.session_state:
                st.session_state.title_font_size_percent = st.session_state.title_font_size_slider
                
            title_color = st.color_picker("رنگ عنوان", st.session_state.title_text_color, key="title_color_picker", help="رنگ عنوان را انتخاب کنید")
            if 'title_color_picker' in st.session_state and st.session_state.title_color_picker != st.session_state.title_text_color:
                st.session_state.title_text_color = st.session_state.title_color_picker
            title_is_bold = st.checkbox("عنوان بولد", value=st.session_state.title_is_bold, key="title_is_bold_checkbox", help="نمایش عنوان به صورت بولد")
            if 'title_is_bold_checkbox' in st.session_state and st.session_state.title_is_bold_checkbox != st.session_state.title_is_bold:
                st.session_state.title_is_bold = st.session_state.title_is_bold_checkbox

        with title_col2:
            title_x = st.slider("موقعیت افقی عنوان (%)", 0, 100, st.session_state.title_text_x_percent, key="title_x_slider", help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت")
            # بروزرسانی session state
            if 'title_x_slider' in st.session_state:
                st.session_state.title_text_x_percent = st.session_state.title_x_slider
                
            title_y = st.slider("موقعیت عمودی عنوان (%)", 0, 100, st.session_state.title_text_y_percent, key="title_y_slider", help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت")
            # بروزرسانی session state
            if 'title_y_slider' in st.session_state:
                st.session_state.title_text_y_percent = st.session_state.title_y_slider
                
            title_max_width = st.slider("عرض عنوان (%)", 10, 100, st.session_state.title_max_text_width_percent, key="title_max_width_slider", help="حداکثر عرض عنوان به صورت درصدی از عرض تمپلیت")
            # بروزرسانی session state
            if 'title_max_width_slider' in st.session_state:
                st.session_state.title_max_text_width_percent = st.session_state.title_max_width_slider
                
            title_line_spacing = st.slider("فاصله خطوط عنوان (%)", 100, 200, st.session_state.title_line_spacing_percent, key="title_line_spacing_slider", help="فاصله بین خطوط عنوان به صورت درصدی از ارتفاع خط")
            # بروزرسانی session state
            if 'title_line_spacing_slider' in st.session_state:
                st.session_state.title_line_spacing_percent = st.session_state.title_line_spacing_slider

        # ورود متن
        st.markdown('<p class="upload-header">4️⃣ وارد کردن متن</p>', unsafe_allow_html=True)
        text_input = st.text_area("متن مورد نظر را وارد کنید", value=st.session_state.text, height=150, key="text_input", help="متن فارسی که می‌خواهید روی تصویر قرار دهید را وارد کنید. هر خط جدید در تصویر نیز به عنوان خط جدید نمایش داده می‌شود.")

        # ذخیره متن در session state
        if 'text_input' in st.session_state and st.session_state.text_input != st.session_state.text:
            st.session_state.text = st.session_state.text_input
        
        # تنظیمات متن
        st.markdown('<p class="settings-header">⚙️ تنظیمات متن</p>', unsafe_allow_html=True)
        text_col1, text_col2 = st.columns(2)

        with text_col1:
            font_size = st.slider("سایز فونت (% ارتفاع تصویر)", 1, 20, st.session_state.font_size_percent, key="font_size_slider", help="سایز فونت به صورت درصدی از ارتفاع تصویر")
            # بروزرسانی session state
            if 'font_size_slider' in st.session_state:
                st.session_state.font_size_percent = st.session_state.font_size_slider
                
            text_color = st.color_picker("رنگ متن", st.session_state.text_color, key="text_color_picker", help="رنگ متن را انتخاب کنید")
            if 'text_color_picker' in st.session_state and st.session_state.text_color_picker != st.session_state.text_color:
                st.session_state.text_color = st.session_state.text_color_picker
            is_bold = st.checkbox("متن بولد", value=st.session_state.is_bold, key="is_bold_checkbox", help="نمایش متن به صورت بولد")
            if 'is_bold_checkbox' in st.session_state and st.session_state.is_bold_checkbox != st.session_state.is_bold:
                st.session_state.is_bold = st.session_state.is_bold_checkbox

        with text_col2:
            text_x = st.slider("موقعیت افقی متن (%)", 0, 100, st.session_state.text_x_percent, key="text_x_slider", help="0: کاملاً چپ تمپلیت، 50: وسط تمپلیت، 100: کاملاً راست تمپلیت")
            # بروزرسانی session state
            if 'text_x_slider' in st.session_state:
                st.session_state.text_x_percent = st.session_state.text_x_slider
                
            text_y = st.slider("موقعیت عمودی متن (%)", 0, 100, st.session_state.text_y_percent, key="text_y_slider", help="0: کاملاً بالای تمپلیت، 50: وسط تمپلیت، 100: کاملاً پایین تمپلیت")
            # بروزرسانی session state
            if 'text_y_slider' in st.session_state:
                st.session_state.text_y_percent = st.session_state.text_y_slider
                
            max_text_width = st.slider("عرض متن (%)", 10, 100, st.session_state.max_text_width_percent, key="max_text_width_slider", help="حداکثر عرض متن به صورت درصدی از عرض تمپلیت")
            # بروزرسانی session state
            if 'max_text_width_slider' in st.session_state:
                st.session_state.max_text_width_percent = st.session_state.max_text_width_slider
                
            line_spacing = st.slider("فاصله خطوط (%)", 100, 200, st.session_state.line_spacing_percent, key="line_spacing_slider", help="فاصله بین خطوط متن به صورت درصدی از ارتفاع خط")
            # بروزرسانی session state
            if 'line_spacing_slider' in st.session_state:
                st.session_state.line_spacing_percent = st.session_state.line_spacing_slider

        # دکمه ساخت تصویر
        st.markdown("---")
        if st.button("🎨 ساخت تصویر"):
            # بررسی وجود تمپلیت (از فایل آپلود شده یا انتخاب شده)
            template_path = None
            if st.session_state.template_file:
                template_path = st.session_state.template_file
            elif st.session_state.selected_template_path:
                template_path = st.session_state.selected_template_path
            
            if template_path and (st.session_state.layers or st.session_state.text or st.session_state.title_text):
                try:
                    # باز کردن تمپلیت
                    template = Image.open(template_path)
                    
                    # محاسبه ابعاد تصویر
                    template_width, template_height = template.size
                    min_dimension = min(template_width, template_height)
                    
                    # ایجاد یک تصویر پایه خالی (سفید)
                    preview_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(preview_image)
                    
                    # اضافه کردن لایه‌ها به زمینه سفید
                    for layer in st.session_state.layers:
                        if layer.visible and layer.image:
                            # محاسبه سایز تصویر بر اساس درصد کوچکترین بعد تمپلیت
                            max_dimension = int(min_dimension * (layer.size_percent / 100))
                            
                            # تغییر سایز تصویر لایه با حفظ نسبت تصویر
                            original_width, original_height = layer.image.size
                            aspect_ratio = original_width / original_height
                            
                            if aspect_ratio >= 1:  # عرض بزرگتر یا مساوی ارتفاع است
                                new_width = max_dimension
                                new_height = int(max_dimension / aspect_ratio)
                            else:  # ارتفاع بزرگتر از عرض است
                                new_height = max_dimension
                                new_width = int(max_dimension * aspect_ratio)
                            
                            layer_image = layer.image.resize((new_width, new_height), Image.LANCZOS)
                            
                            # تبدیل به RGBA اگر PNG است
                            if layer_image.mode != 'RGBA':
                                layer_image = layer_image.convert('RGBA')
                            
                            # اعمال شفافیت
                            if layer.opacity < 100:
                                layer_image.putalpha(int(255 * layer.opacity / 100))
                            
                            # محاسبه موقعیت مرکز تصویر
                            img_x = int((template_width - new_width) * (layer.x_percent / 100))
                            img_y = int((template_height - new_height) * (layer.y_percent / 100))
                            
                            # اضافه کردن تصویر به پیش‌نمایش
                            preview_image.paste(layer_image, (img_x, img_y), layer_image)
                    
                    # اضافه کردن تمپلیت به عنوان لایه بالایی
                    if template.mode == 'RGBA':
                        preview_image = Image.alpha_composite(preview_image, template)
                    else:
                        template_rgba = template.convert('RGBA')
                        preview_image = Image.alpha_composite(preview_image, template_rgba)
                    
                    # اضافه کردن عنوان
                    if st.session_state.title_text:
                        title_bidi_text = process_persian_text(st.session_state.title_text)
                        title_font_size = int(template_height * (st.session_state.title_font_size_percent / 100))
                        
                        try:
                            title_font_path = FONT_BOLD_PATH if st.session_state.title_is_bold else FONT_PATH
                            title_font = ImageFont.truetype(title_font_path, title_font_size)
                            
                            title_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            title_draw = ImageDraw.Draw(title_image)
                            
                            title_max_width = template_width * (st.session_state.title_max_text_width_percent / 100)
                            title_lines = wrap_text_to_lines(title_draw, title_bidi_text, title_font, title_max_width)
                            
                            title_line_spacing_factor = st.session_state.title_line_spacing_percent / 100
                            title_line_height = int(title_font_size * title_line_spacing_factor)
                            title_total_text_height = title_line_height * len(title_lines)
                            
                            title_start_y = int((template_height - title_total_text_height) * (st.session_state.title_text_y_percent / 100))
                            
                            for i, line in enumerate(title_lines):
                                line_width = title_draw.textlength(line, font=title_font)
                                line_x = int((template_width - line_width) * (st.session_state.title_text_x_percent / 100))
                                line_y = title_start_y + i * title_line_height
                                title_draw.text((line_x, line_y), line, font=title_font, fill=st.session_state.title_text_color)
                            
                            preview_image = Image.alpha_composite(preview_image, title_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت عنوان: {str(e)}")

                    # اضافه کردن متن
                    if st.session_state.text:
                        bidi_text = process_persian_text(st.session_state.text)
                        font_size = int(template_height * (st.session_state.font_size_percent / 100))
                        
                        try:
                            font_path = FONT_BOLD_PATH if st.session_state.is_bold else FONT_PATH
                            font = ImageFont.truetype(font_path, font_size)
                            
                            text_image = Image.new('RGBA', (template_width, template_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            
                            max_width = template_width * (st.session_state.max_text_width_percent / 100)
                            lines = wrap_text_to_lines(text_draw, bidi_text, font, max_width)
                            
                            line_spacing_factor = st.session_state.line_spacing_percent / 100
                            line_height = int(font_size * line_spacing_factor)
                            total_text_height = line_height * len(lines)
                            
                            start_y = int((template_height - total_text_height) * (st.session_state.text_y_percent / 100))
                            
                            for i, line in enumerate(lines):
                                line_width = text_draw.textlength(line, font=font)
                                line_x = int((template_width - line_width) * (st.session_state.text_x_percent / 100))
                                line_y = start_y + i * line_height
                                text_draw.text((line_x, line_y), line, font=font, fill=st.session_state.text_color)
                            
                            preview_image = Image.alpha_composite(preview_image, text_image)
                        except Exception as e:
                            st.error(f"خطا در بارگذاری فونت: {str(e)}")
                    
                    # نمایش تصویر با سایز محدود شده
                    st.image(preview_image, caption=f"پیش‌نمایش ({template_width}x{template_height})", width=300)
                    
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                    with open("output.png", "rb") as file:
                        btn = st.download_button(
                            label="⬇️ دانلود تصویر",
                            data=file,
                            file_name="output.png",
                            mime="image/png",
                            key="main_download_btn"
                        )
                    
                    st.success(f"✅ تصویر با موفقیت ساخته شد! (سایز: {template_width}x{template_height})")
                    
                    # ذخیره تصویر با سایز اصلی
                    final_image = preview_image.copy()
                    final_image.save("output.png", quality=100)
                    
                except Exception as e:
                    st.error(f"❌ خطا در ساخت تصویر: {str(e)}")
                    st.error("جزئیات خطا:")
                    st.code(traceback.format_exc())
            else:
                st.error("❌ لطفاً ابتدا یک تمپلیت انتخاب کنید و حداقل یک لایه، عنوان یا متن وارد کنید!")
        else:
            st.warning("⚠️ لطفاً ابتدا یک تمپلیت انتخاب کنید یا یک تمپلیت جدید آپلود کنید.")

# تابع تست و debug برای متن فارسی
def debug_persian_text(text):
    """
    تابع debug برای بررسی وضعیت پردازش متن فارسی
    """
    if not text:
        return "متن خالی است"
    
    results = []
    results.append(f"متن ورودی: '{text}'")
    results.append(f"طول متن: {len(text)}")
    
    # تست استراتژی 1
    try:
        import arabic_reshaper
        reshaped = arabic_reshaper.reshape(text)
        # تست روش جدید (بدون get_display)
        results.append(f"✅ استراتژی 1 (فقط reshape): '{reshaped}'")
        results.append(f"طول نتیجه: {len(reshaped)}")
        
        # تست روش قدیمی (با get_display) 
        try:
            from bidi.algorithm import get_display
            bidi_result = get_display(reshaped)
            results.append(f"✅ استراتژی 1 (با bidi): '{bidi_result}'")
        except:
            results.append(f"❌ get_display کار نمی‌کند")
    except Exception as e:
        results.append(f"❌ استراتژی 1 ناموفق: {str(e)}")
    
    # تست استراتژی 2
    try:
        persian_chars = 'آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
        has_persian = any(char in persian_chars for char in text)
        results.append(f"تشخیص فارسی: {has_persian}")
        if has_persian:
            reversed_text = text[::-1]
            results.append(f"✅ استراتژی 2: '{reversed_text}'")
        else:
            results.append(f"✅ استراتژی 2: متن انگلیسی، تغییری نداده شد")
    except Exception as e:
        results.append(f"❌ استراتژی 2 ناموفق: {str(e)}")
    
    # تست استراتژی 3
    try:
        words = text.split()
        if len(words) > 1:
            reversed_words = words[::-1]
            result3 = ' '.join(reversed_words)
        else:
            result3 = text[::-1]
        results.append(f"✅ استراتژی 3: '{result3}'")
    except Exception as e:
        results.append(f"❌ استراتژی 3 ناموفق: {str(e)}")
    
    return "\n".join(results)