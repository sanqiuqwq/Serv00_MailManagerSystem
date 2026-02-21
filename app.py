from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import secrets
import string

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(24))

# 数据库配置
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'email_registration')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 邮件配置
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

# serv00配置
SERV00_USERNAME = os.getenv('SERV00_USERNAME')
SERV00_PASSWORD = os.getenv('SERV00_PASSWORD')
SERV00_PANEL = os.getenv('SERV00_PANEL')

# reCAPTCHA v2配置
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY')
RECAPTCHA_USE_CN = os.getenv('RECAPTCHA_USE_CN', 'true').lower() == 'true'
RECAPTCHA_ENABLED = os.getenv('RECAPTCHA_ENABLED', 'true').lower() == 'true'

if RECAPTCHA_USE_CN:
    RECAPTCHA_API_URL = 'https://www.recaptcha.net/recaptcha/api.js'
    RECAPTCHA_VERIFY_URL = 'https://www.recaptcha.net/recaptcha/api/siteverify'
else:
    RECAPTCHA_API_URL = 'https://www.google.com/recaptcha/api.js'
    RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


def verify_recaptcha(response_token):
    if not RECAPTCHA_ENABLED:
        return True
    
    if not RECAPTCHA_SECRET_KEY or not RECAPTCHA_SITE_KEY:
        return True
    
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': response_token,
        'remoteip': request.remote_addr
    }
    try:
        r = requests.post(RECAPTCHA_VERIFY_URL, data=data, timeout=10)
        result = r.json()
        return result.get('success', False)
    except:
        return False


def validate_password(password):
    errors = []
    
    if len(password) < 6:
        errors.append('密码至少需要6个字符')
    
    if not any(c.isdigit() for c in password):
        errors.append('密码至少需要包含一个数字')
    
    if not any(c.islower() for c in password):
        errors.append('密码至少需要包含一个小写字母')
    
    if not any(c.isupper() for c in password):
        errors.append('密码至少需要包含一个大写字母')
    
    return errors


def generate_uid():
    return ''.join(secrets.choice(string.digits) for _ in range(8))


# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(20), unique=True, nullable=False, default=generate_uid)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')
    max_emails = db.Column(db.Integer, default=2)
    extra_emails = db.Column(db.Integer, default=0)
    temp_extra_emails = db.Column(db.Integer, default=0)
    temp_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    emails = db.relationship('RegisteredEmail', backref='owner', lazy=True)
    verification_tokens = db.relationship('VerificationToken', backref='user', lazy=True)
    tickets = db.relationship('Ticket', backref='user', lazy=True)
    redeemed_codes = db.relationship('RedemptionCode', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_max_emails(self):
        if self.role == 'owner':
            return 999999
        
        total = self.max_emails + self.extra_emails
        
        if self.temp_expires_at and self.temp_expires_at > datetime.utcnow():
            total += self.temp_extra_emails
        
        return total

    def get_email_count(self):
        return RegisteredEmail.query.filter_by(user_id=self.id).count()

    def can_create_email(self):
        return self.get_email_count() < self.get_max_emails()

    def is_owner(self):
        return self.role == 'owner'

    def can_access_admin(self):
        return self.role == 'owner'


class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    emails = db.relationship('RegisteredEmail', backref='domain_obj', lazy=True)


class RegisteredEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(100), unique=True, nullable=False)
    email_password = db.Column(db.String(100), nullable=False)
    prefix = db.Column(db.String(50), nullable=False)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VerificationToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token_type = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='邮箱注册系统')
    site_description = db.Column(db.Text, default='免费邮箱注册服务')
    site_url = db.Column(db.String(200), default='http://localhost:5000')
    purchase_code_url = db.Column(db.String(500), default='')
    tg_group_url = db.Column(db.String(500), default='')
    default_user_max_emails = db.Column(db.Integer, default=2)
    default_pro_max_emails = db.Column(db.Integer, default=5)
    min_user_prefix_length = db.Column(db.Integer, default=7)
    min_pro_prefix_length = db.Column(db.Integer, default=3)
    smtp_server = db.Column(db.String(200), default='smtp.example.com')
    imap_server = db.Column(db.String(200), default='imap.example.com')
    pop3_server = db.Column(db.String(200), default='pop3.example.com')
    webmail_url = db.Column(db.String(500), default='https://mail.example.com')


class PrefixBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AllowedEmailSuffix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suffix = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    replies = db.relationship('TicketReply', backref='ticket', lazy=True, cascade='all, delete-orphan')


class TicketReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='ticket_replies')


class AboutPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, default='关于我们')


class UserAgreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, default='''
## 用户协议

欢迎使用本邮箱注册服务！

### 重要声明

本服务按"现状"提供，不保证服务的可靠性、可用性、持续性或安全性。使用本服务的风险由用户自行承担。

### 免责声明

1. 我们不对服务的中断、延迟、错误或数据丢失承担任何责任。
2. 我们不保证服务能够满足您的特定需求。
3. 因使用或无法使用本服务而产生的任何直接或间接损失，运营方不承担任何责任。
4. 我们不对任何第三方内容或链接的准确性、完整性或可用性负责。

### 数据安全

我们尽力保护用户数据，但不保证数据的绝对安全。用户应自行承担数据丢失或泄露的风险。

### 服务变更

我们保留随时修改、暂停或终止服务的权利，无需提前通知，也不承担任何责任。

### 使用条款

- 用户不得利用本服务从事任何违法活动
- 用户不得滥用或干扰本服务的正常运行
- 我们保留随时终止违规用户账户的权利

### 协议修改

我们有权随时修改本协议。继续使用服务即表示同意修改后的协议。

---

**使用本服务即表示您已阅读、理解并同意本协议的所有条款。**
''')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RedemptionCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    extra_emails = db.Column(db.Integer, default=1)
    duration_days = db.Column(db.Integer)
    is_permanent = db.Column(db.Boolean, default=False)
    is_used = db.Column(db.Boolean, default=False)
    max_uses = db.Column(db.Integer, default=1)
    used_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_code():
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    
    def is_expired(self):
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False
    
    def can_be_used(self):
        if self.is_expired():
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_site_settings():
    site_settings = SiteSettings.query.first()
    if not site_settings:
        site_settings = SiteSettings()
        db.session.add(site_settings)
        db.session.commit()
    return dict(site_settings=site_settings)


def generate_token(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)


def serv00_login_and_create_email(prefix, domain, password):
    session_req = requests.Session()
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    login_url = f"https://{SERV00_PANEL}/login/?next=/mail/add"
    email_creation_url = f"https://{SERV00_PANEL}/mail/add"

    try:
        login_page = session_req.get(login_url, headers={"User-Agent": user_agent})
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        login_data = {
            'username': SERV00_USERNAME,
            'password': SERV00_PASSWORD,
            'csrfmiddlewaretoken': csrf_token,
            'next': '/mail/add'
        }
        login_response = session_req.post(login_url, data=login_data, headers={
            "User-Agent": user_agent,
            "Referer": login_url,
            "Content-Type": "application/x-www-form-urlencoded"
        })

        if "Dodaj nowy adres e-mail" in login_response.text or "/mail/add" in login_response.url:
            mail_add_page = session_req.get(email_creation_url, headers={"User-Agent": user_agent})
            soup = BeautifulSoup(mail_add_page.content, 'html.parser')
            new_csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

            full_email = f"{prefix}{domain}"
            email_data = {
                'csrfmiddlewaretoken': new_csrf_token,
                'email': full_email,
                'password1': password,
                'password2': password
            }

            email_creation_response = session_req.post(email_creation_url, data=email_data, headers={
                "User-Agent": user_agent,
                "Referer": email_creation_url,
                "Content-Type": "application/x-www-form-urlencoded"
            })

            if email_creation_response.status_code == 200:
                return {"success": True, "email": full_email}
            else:
                raise Exception("邮箱创建失败")
        else:
            raise Exception("登录失败")
    except Exception as e:
        return {"success": False, "message": str(e)}


def serv00_reset_password(email_address, new_password):
    username_part, domain_part = email_address.split('@', 1)
    
    session_req = requests.Session()
    user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    login_url = f"https://{SERV00_PANEL}/login/?next=/mail"
    mail_list_url = f"https://{SERV00_PANEL}/mail"

    try:
        login_page = session_req.get(login_url, headers={"User-Agent": user_agent})
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        login_data = {
            'username': SERV00_USERNAME,
            'password': SERV00_PASSWORD,
            'csrfmiddlewaretoken': csrf_token,
            'next': '/mail'
        }
        login_response = session_req.post(login_url, data=login_data, headers={
            "User-Agent": user_agent,
            "Referer": login_url,
            "Content-Type": "application/x-www-form-urlencoded"
        })

        domain_page = session_req.get(mail_list_url, headers={"User-Agent": user_agent})
        soup = BeautifulSoup(domain_page.content, 'html.parser')

        domain_row = None
        all_rows = soup.find_all('tr')
        
        for row in all_rows:
            row_text = str(row)
            if domain_part in row_text:
                domain_row = row
                break

        if not domain_row:
            return {"success": False, "message": "未找到该域名"}

        domain_link = domain_row.find('a', href=True)
        if not domain_link:
            return {"success": False, "message": "未找到域名链接"}

        domain_mail_url = f"https://{SERV00_PANEL}{domain_link['href']}"
        mail_page = session_req.get(domain_mail_url, headers={"User-Agent": user_agent})
        soup = BeautifulSoup(mail_page.content, 'html.parser')

        email_row = None
        all_email_rows = soup.find_all('tr')
        
        for row in all_email_rows:
            row_text = str(row)
            if username_part in row_text or email_address in row_text:
                email_row = row
                break

        if not email_row:
            return {"success": False, "message": "未找到该邮箱"}

        password_modal = soup.find('div', id='password_modal_1')
        if not password_modal:
            return {"success": False, "message": "未找到密码模态框"}
        
        password_form = password_modal.find('form')
        if not password_form:
            return {"success": False, "message": "未找到密码表单"}

        form_action = password_form.get('action', '')

        csrf_input = password_form.find('input', {'name': 'csrfmiddlewaretoken'})
        if not csrf_input:
            return {"success": False, "message": "未找到 CSRF token"}
        csrf_token = csrf_input['value']
        
        email_input = password_form.find('input', {'name': 'pass_email'})
        if not email_input:
            return {"success": False, "message": "未找到邮箱输入框"}
        
        password_url = f"https://{SERV00_PANEL}{form_action}"
        
        password_data = {
            'csrfmiddlewaretoken': csrf_token,
            'pass_email': email_address,
            'password1': new_password,
            'password2': new_password
        }

        password_response = session_req.post(password_url, data=password_data, headers={
            "User-Agent": user_agent,
            "Referer": domain_mail_url,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        if "Zmiana hasła zakończona sukcesem" in password_response.text or "Operacja wykonana prawidłowo" in password_response.text:
            return {"success": True}
        else:
            error_messages = [
                "Hasło jest za krótkie",
                "Hasło musi zawierać co najmniej jedną cyfrę",
                "Hasło musi zawierać co najmniej jedną małą literę",
                "Hasło musi zawierać co najmniej jedną dużą literę",
                "Błąd",
                "error"
            ]
            
            found_errors = []
            for err in error_messages:
                if err.lower() in password_response.text.lower():
                    found_errors.append(err)
            
            if found_errors:
                return {"success": False, "message": f"密码重置失败"}
            else:
                return {"success": False, "message": "密码重置失败"}
    except Exception as e:
        return {"success": False, "message": "密码重置失败"}


# 路由
@app.context_processor
def inject_recaptcha_key():
    return dict(recaptcha_site_key=RECAPTCHA_SITE_KEY, recaptcha_api_url=RECAPTCHA_API_URL, recaptcha_enabled=RECAPTCHA_ENABLED)


@app.route('/')
def index():
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    return render_template('index.html', announcements=announcements)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        agree_terms = request.form.get('agree_terms')
        
        if not agree_terms:
            flash('请同意用户协议', 'danger')
            return redirect(url_for('register'))
        
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('请完成人机验证', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))

        allowed_suffixes = [s.suffix for s in AllowedEmailSuffix.query.all()]
        if allowed_suffixes:
            email_lower = email.lower()
            valid = False
            for suffix in allowed_suffixes:
                if email_lower.endswith(suffix.lower()):
                    valid = True
                    break
            if not valid:
                allowed_list = ', '.join(allowed_suffixes)
                flash(f'只允许使用以下邮箱后缀注册：{allowed_list}', 'danger')
                return redirect(url_for('register'))

        site_settings = SiteSettings.query.first()
        default_max_emails = site_settings.default_user_max_emails if site_settings else 2
        user = User(username=username, email=email, is_verified=False, max_emails=default_max_emails)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        token = generate_token()
        verification_token = VerificationToken(
            token=token,
            user_id=user.id,
            token_type='email_verification',
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(verification_token)
        db.session.commit()

        site_settings = SiteSettings.query.first()
        base_url = site_settings.site_url if site_settings else 'http://localhost:5000'
        verify_url = f"{base_url}{url_for('verify_email', token=token)}"
        email_body = f'请点击以下链接验证您的邮箱：\n{verify_url}\n\n该链接24小时内有效。'
        send_email('邮箱验证', [email], email_body)

        flash('注册成功！请检查您的邮箱以完成验证', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/verify-email/<token>')
def verify_email(token):
    verification_token = VerificationToken.query.filter_by(token=token, token_type='email_verification').first()
    if not verification_token or verification_token.expires_at < datetime.utcnow():
        flash('验证链接无效或已过期', 'danger')
        return redirect(url_for('login'))

    user = verification_token.user
    user.is_verified = True
    db.session.delete(verification_token)
    db.session.commit()

    flash('邮箱验证成功！您现在可以登录了', 'success')
    return redirect(url_for('login'))


@app.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('您的邮箱已验证', 'info')
        return redirect(url_for('dashboard'))

    old_token = VerificationToken.query.filter_by(user_id=current_user.id, token_type='email_verification').first()
    if old_token:
        db.session.delete(old_token)

    token = generate_token()
    verification_token = VerificationToken(
        token=token,
        user_id=current_user.id,
        token_type='email_verification',
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.session.add(verification_token)
    db.session.commit()

    site_settings = SiteSettings.query.first()
    base_url = site_settings.site_url if site_settings else 'http://localhost:5000'
    verify_url = f"{base_url}{url_for('verify_email', token=token)}"
    email_body = f'请点击以下链接验证您的邮箱：\n{verify_url}\n\n该链接24小时内有效。'
    send_email('邮箱验证', [current_user.email], email_body)

    flash('验证邮件已重新发送', 'success')
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('请完成人机验证', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if user.is_banned:
                flash('您的账户已被封禁', 'danger')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('请完成人机验证', 'danger')
            return redirect(url_for('forgot_password'))
        
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token()
            verification_token = VerificationToken(
                token=token,
                user_id=user.id,
                token_type='password_reset',
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(verification_token)
            db.session.commit()

            site_settings = SiteSettings.query.first()
            base_url = site_settings.site_url if site_settings else 'http://localhost:5000'
            reset_url = f"{base_url}{url_for('reset_password', token=token)}"
            email_body = f'请点击以下链接重置您的密码：\n{reset_url}\n\n该链接1小时内有效。'
            send_email('密码重置', [email], email_body)

        flash('如果该邮箱已注册，您将收到重置密码的邮件', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    verification_token = VerificationToken.query.filter_by(token=token, token_type='password_reset').first()
    if not verification_token or verification_token.expires_at < datetime.utcnow():
        flash('重置链接无效或已过期', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            flash('请完成人机验证', 'danger')
            return redirect(url_for('reset_password', token=token))

        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('reset_password', token=token))

        user = verification_token.user
        user.set_password(password)
        db.session.delete(verification_token)
        db.session.commit()

        flash('密码重置成功！您现在可以登录了', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not current_user.check_password(old_password):
            flash('原密码错误', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('change_password'))

        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功！', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')


@app.route('/about')
def about():
    about_page = AboutPage.query.first()
    if not about_page:
        about_page = AboutPage()
        db.session.add(about_page)
        db.session.commit()
    return render_template('about.html', about_page=about_page)


@app.route('/tickets')
@login_required
def tickets():
    if current_user.can_access_admin():
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=tickets)


@app.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        ticket = Ticket(title=title, user_id=current_user.id)
        db.session.add(ticket)
        db.session.flush()

        reply = TicketReply(ticket_id=ticket.id, user_id=current_user.id, content=content)
        db.session.add(reply)
        db.session.commit()

        flash('工单创建成功！', 'success')
        return redirect(url_for('tickets'))

    return render_template('create_ticket.html')


@app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not current_user.can_access_admin() and ticket.user_id != current_user.id:
        flash('无权查看此工单', 'danger')
        return redirect(url_for('tickets'))

    if request.method == 'POST':
        content = request.form['content']

        reply = TicketReply(
            ticket_id=ticket.id,
            user_id=current_user.id,
            content=content,
            is_admin=current_user.can_access_admin()
        )
        db.session.add(reply)
        db.session.commit()

        flash('回复成功！', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    return render_template('view_ticket.html', ticket=ticket)


@app.route('/tickets/<int:ticket_id>/close')
@login_required
def close_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not current_user.can_access_admin() and ticket.user_id != current_user.id:
        flash('无权操作此工单', 'danger')
        return redirect(url_for('tickets'))

    ticket.status = 'closed'
    ticket.closed_at = datetime.utcnow()
    db.session.commit()
    flash('工单已关闭', 'success')
    return redirect(url_for('tickets'))


@app.route('/tickets/<int:ticket_id>/open')
@login_required
def open_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not current_user.can_access_admin() and ticket.user_id != current_user.id:
        flash('无权操作此工单', 'danger')
        return redirect(url_for('tickets'))

    ticket.status = 'open'
    ticket.closed_at = None
    db.session.commit()
    flash('工单已重新打开', 'success')
    return redirect(url_for('tickets'))


@app.route('/dashboard')
@login_required
def dashboard():
    domains = Domain.query.filter_by(is_active=True).all()
    emails = RegisteredEmail.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', domains=domains, emails=emails, datetime=datetime)


@app.route('/create-email', methods=['POST'])
@login_required
def create_email():

    if not current_user.is_verified:
        flash('请先验证您的邮箱后再创建邮箱', 'danger')
        return redirect(url_for('dashboard'))

    prefix = request.form['prefix']
    domain_id = request.form['domain_id']
    email_password = request.form['email_password']
    
    password_errors = validate_password(email_password)
    if password_errors:
        for error in password_errors:
            flash(error, 'danger')
        return redirect(url_for('dashboard'))
    
    recaptcha_response = request.form.get('g-recaptcha-response')
    if not verify_recaptcha(recaptcha_response):
        flash('请完成人机验证', 'danger')
        return redirect(url_for('dashboard'))

    site_settings = SiteSettings.query.first()
    if current_user.role == 'user':
        min_length = site_settings.min_user_prefix_length if site_settings else 7
        if len(prefix) < min_length:
            flash(f'普通用户邮箱前缀必须不少于{min_length}个字符', 'danger')
            return redirect(url_for('dashboard'))
    elif current_user.role == 'pro':
        min_length = site_settings.min_pro_prefix_length if site_settings else 3
        if len(prefix) < min_length:
            flash(f'Pro用户邮箱前缀必须不少于{min_length}个字符', 'danger')
            return redirect(url_for('dashboard'))

    if not current_user.can_create_email():
        flash(f'已达到邮箱数量上限（当前: {current_user.get_email_count()}/{current_user.get_max_emails()}）', 'danger')
        return redirect(url_for('dashboard'))
    
    prefix_lower = prefix.lower()
    blacklisted = PrefixBlacklist.query.filter(
        db.or_(
            PrefixBlacklist.prefix == prefix_lower,
            PrefixBlacklist.prefix.like(f'{prefix_lower}%')
        )
    ).first()
    if blacklisted:
        flash(f'邮箱前缀 "{prefix}" 不允许使用，请更换其他前缀', 'danger')
        return redirect(url_for('dashboard'))

    domain = Domain.query.get(domain_id)
    if not domain or not domain.is_active:
        flash('无效的域名', 'danger')
        return redirect(url_for('dashboard'))

    full_email = f"{prefix}{domain.domain}"

    existing_email = RegisteredEmail.query.filter_by(email_address=full_email).first()
    if existing_email:
        if existing_email.is_disabled:
            flash('该邮箱已被管理员禁用', 'danger')
        else:
            flash('该邮箱已被注册', 'danger')
        return redirect(url_for('dashboard'))

    result = serv00_login_and_create_email(prefix, domain.domain, email_password)
    if result['success']:
        new_email = RegisteredEmail(
            email_address=full_email,
            email_password=email_password,
            prefix=prefix,
            domain_id=domain_id,
            user_id=current_user.id
        )
        db.session.add(new_email)
        db.session.commit()
        flash(f'邮箱 {full_email} 创建成功！', 'success')
    else:
        flash(f'邮箱创建失败: {result["message"]}', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/reset-email-password/<int:email_id>', methods=['POST'])
@login_required
def reset_email_password(email_id):
    email = RegisteredEmail.query.get_or_404(email_id)
    if email.user_id != current_user.id:
        flash('无权操作此邮箱', 'danger')
        return redirect(url_for('dashboard'))

    if email.is_disabled:
        flash('该邮箱已被禁用', 'danger')
        return redirect(url_for('dashboard'))

    new_password = request.form['new_password']
    
    password_errors = validate_password(new_password)
    if password_errors:
        for error in password_errors:
            flash(error, 'danger')
        return redirect(url_for('dashboard'))
    
    result = serv00_reset_password(email.email_address, new_password)

    if result['success']:
        email.email_password = new_password
        db.session.commit()
        flash('邮箱密码重置成功！', 'success')
    else:
        flash(f'密码重置失败: {result["message"]}', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/transfer-email/<int:email_id>', methods=['POST'])
@login_required
def transfer_email(email_id):
    email = RegisteredEmail.query.get_or_404(email_id)
    if email.user_id != current_user.id:
        flash('无权操作此邮箱', 'danger')
        return redirect(url_for('dashboard'))

    if email.is_disabled:
        flash('该邮箱已被禁用，无法转移', 'danger')
        return redirect(url_for('dashboard'))
    
    recaptcha_response = request.form.get('g-recaptcha-response')
    if not verify_recaptcha(recaptcha_response):
        flash('请完成人机验证', 'danger')
        return redirect(url_for('dashboard'))
    
    target_uid = request.form.get('target_uid', '').strip()
    if not target_uid:
        flash('请输入目标用户UID', 'danger')
        return redirect(url_for('dashboard'))
    
    target_user = User.query.filter_by(uid=target_uid).first()
    if not target_user:
        flash('目标用户不存在', 'danger')
        return redirect(url_for('dashboard'))
    
    if target_user.id == current_user.id:
        flash('不能转移给自己', 'danger')
        return redirect(url_for('dashboard'))
    
    if not target_user.is_verified:
        flash('目标用户未验证邮箱', 'danger')
        return redirect(url_for('dashboard'))
    
    if not target_user.can_create_email():
        flash('目标用户邮箱配额已满', 'danger')
        return redirect(url_for('dashboard'))
    
    email.user_id = target_user.id
    db.session.commit()
    
    flash(f'邮箱 {email.email_address} 已成功转移给用户 {target_user.username}！', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    user_count = User.query.count()
    email_count = RegisteredEmail.query.count()
    
    expired_tokens_count = VerificationToken.query.filter(VerificationToken.expires_at < datetime.utcnow()).count()
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    closed_tickets_count = Ticket.query.filter(
        Ticket.status == 'closed'
    ).filter(
        (Ticket.closed_at < seven_days_ago) | 
        ((Ticket.closed_at.is_(None)) & (Ticket.created_at < seven_days_ago))
    ).count()
    unverified_users_count = User.query.filter(User.is_verified == False, User.created_at < datetime.utcnow() - timedelta(days=2)).count()
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count, 
                          email_count=email_count,
                          expired_tokens_count=expired_tokens_count,
                          closed_tickets_count=closed_tickets_count,
                          unverified_users_count=unverified_users_count)


def cleanup_expired_tokens():
    expired_tokens = VerificationToken.query.filter(VerificationToken.expires_at < datetime.utcnow()).all()
    count = len(expired_tokens)
    for token in expired_tokens:
        db.session.delete(token)
    db.session.commit()
    return count


def cleanup_closed_tickets():
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    closed_tickets = Ticket.query.filter(
        Ticket.status == 'closed'
    ).filter(
        (Ticket.closed_at < seven_days_ago) | 
        ((Ticket.closed_at.is_(None)) & (Ticket.created_at < seven_days_ago))
    ).all()
    count = len(closed_tickets)
    for ticket in closed_tickets:
        db.session.delete(ticket)
    db.session.commit()
    return count


def cleanup_unverified_users():
    two_days_ago = datetime.utcnow() - timedelta(days=2)
    unverified_users = User.query.filter(User.is_verified == False, User.created_at < two_days_ago).all()
    count = len(unverified_users)
    for user in unverified_users:
        db.session.delete(user)
    db.session.commit()
    return count


@app.route('/admin/cleanup/tokens', methods=['POST'])
@login_required
def admin_cleanup_tokens():
    if not current_user.can_access_admin():
        flash('无权访问管理员页面', 'danger')
        return redirect(url_for('dashboard'))
    
    count = cleanup_expired_tokens()
    flash(f'已清理 {count} 个过期验证令牌', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cleanup/tickets', methods=['POST'])
@login_required
def admin_cleanup_tickets():
    if not current_user.can_access_admin():
        flash('无权访问管理员页面', 'danger')
        return redirect(url_for('dashboard'))
    
    count = cleanup_closed_tickets()
    flash(f'已清理 {count} 个已关闭超过7天的工单', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cleanup/tickets/all', methods=['POST'])
@login_required
def admin_cleanup_all_tickets():
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))
    
    all_closed_tickets = Ticket.query.filter(Ticket.status == 'closed').all()
    count = len(all_closed_tickets)
    for ticket in all_closed_tickets:
        db.session.delete(ticket)
    db.session.commit()
    flash(f'已清理 {count} 个所有已关闭的工单', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cleanup/users', methods=['POST'])
@login_required
def admin_cleanup_users():
    if not current_user.can_access_admin():
        flash('无权访问管理员页面', 'danger')
        return redirect(url_for('dashboard'))
    
    count = cleanup_unverified_users()
    flash(f'已清理 {count} 个未验证超过2天的账户', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cleanup/all', methods=['POST'])
@login_required
def admin_cleanup_all():
    if not current_user.can_access_admin():
        flash('无权访问管理员页面', 'danger')
        return redirect(url_for('dashboard'))
    
    tokens_count = cleanup_expired_tokens()
    tickets_count = cleanup_closed_tickets()
    users_count = cleanup_unverified_users()
    
    flash(f'清理完成：过期令牌 {tokens_count} 个，关闭工单 {tickets_count} 个，未验证账户 {users_count} 个', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            (User.username.contains(search_query)) |
            (User.email.contains(search_query)) |
            (User.uid.contains(search_query))
        ).all()
    else:
        users = User.query.all()
    return render_template('admin/users.html', users=users, search_query=search_query)


@app.route('/admin/users/ban/<int:user_id>')
@login_required
def admin_ban_user(user_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'owner':
        flash('不能封禁Owner', 'danger')
    else:
        user.is_banned = True
        db.session.commit()
        flash('用户已封禁', 'success')

    return redirect(url_for('admin_users'))


@app.route('/admin/users/unban/<int:user_id>')
@login_required
def admin_unban_user(user_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash('用户已解封', 'success')

    return redirect(url_for('admin_users'))


@app.route('/admin/users/delete/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    if user.role == 'owner':
        flash('不能删除Owner', 'danger')
    else:
        RegisteredEmail.query.filter_by(user_id=user_id).delete()
        VerificationToken.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('用户已删除', 'success')

    return redirect(url_for('admin_users'))


@app.route('/admin/domains')
@login_required
def admin_domains():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    domains = Domain.query.all()
    return render_template('admin/domains.html', domains=domains)


@app.route('/admin/domains/add', methods=['POST'])
@login_required
def admin_add_domain():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    domain_name = request.form['domain']
    if Domain.query.filter_by(domain=domain_name).first():
        flash('域名已存在', 'danger')
    else:
        domain = Domain(domain=domain_name)
        db.session.add(domain)
        db.session.commit()
        flash('域名添加成功', 'success')

    return redirect(url_for('admin_domains'))


@app.route('/admin/domains/toggle/<int:domain_id>')
@login_required
def admin_toggle_domain(domain_id):
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    domain = Domain.query.get_or_404(domain_id)
    domain.is_active = not domain.is_active
    db.session.commit()
    flash('域名状态已更新', 'success')

    return redirect(url_for('admin_domains'))


@app.route('/admin/domains/delete/<int:domain_id>')
@login_required
def admin_delete_domain(domain_id):
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    domain = Domain.query.get_or_404(domain_id)
    RegisteredEmail.query.filter_by(domain_id=domain_id).delete()
    db.session.delete(domain)
    db.session.commit()
    flash('域名已删除', 'success')

    return redirect(url_for('admin_domains'))


@app.route('/admin/emails')
@login_required
def admin_emails():
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    if current_user.is_owner():
        emails = RegisteredEmail.query.all()
    else:
        emails = RegisteredEmail.query.join(User).filter(User.role != 'owner').all()
    return render_template('admin/emails.html', emails=emails)


@app.route('/admin/emails/disable/<int:email_id>')
@login_required
def admin_disable_email(email_id):
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    email = RegisteredEmail.query.get_or_404(email_id)
    if not current_user.is_owner() and email.owner.role == 'owner':
        flash('无权操作此邮箱', 'danger')
        return redirect(url_for('admin_emails'))
    email.is_disabled = True
    db.session.commit()
    flash('邮箱已禁用', 'success')

    return redirect(url_for('admin_emails'))


@app.route('/admin/emails/enable/<int:email_id>')
@login_required
def admin_enable_email(email_id):
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    email = RegisteredEmail.query.get_or_404(email_id)
    if not current_user.is_owner() and email.owner.role == 'owner':
        flash('无权操作此邮箱', 'danger')
        return redirect(url_for('admin_emails'))
    email.is_disabled = False
    db.session.commit()
    flash('邮箱已启用', 'success')

    return redirect(url_for('admin_emails'))


@app.route('/admin/emails/delete/<int:email_id>')
@login_required
def admin_delete_email(email_id):
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    email = RegisteredEmail.query.get_or_404(email_id)
    if not current_user.is_owner() and email.owner.role == 'owner':
        flash('无权操作此邮箱', 'danger')
        return redirect(url_for('admin_emails'))
    db.session.delete(email)
    db.session.commit()
    flash('邮箱已删除', 'success')

    return redirect(url_for('admin_emails'))


@app.route('/admin/announcements')
@login_required
def admin_announcements():
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    announcements = Announcement.query.all()
    return render_template('admin/announcements.html', announcements=announcements)


@app.route('/admin/announcements/add', methods=['POST'])
@login_required
def admin_add_announcement():
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    title = request.form['title']
    content = request.form['content']
    announcement = Announcement(title=title, content=content)
    db.session.add(announcement)
    db.session.commit()
    flash('公告添加成功', 'success')

    return redirect(url_for('admin_announcements'))


@app.route('/admin/announcements/toggle/<int:announcement_id>')
@login_required
def admin_toggle_announcement(announcement_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    flash('公告状态已更新', 'success')

    return redirect(url_for('admin_announcements'))


@app.route('/admin/announcements/delete/<int:announcement_id>')
@login_required
def admin_delete_announcement(announcement_id):
    if not current_user.is_owner():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('公告已删除', 'success')

    return redirect(url_for('admin_announcements'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        if 'site_name' in request.form:
            settings.site_name = request.form['site_name']
            settings.site_description = request.form['site_description']
            settings.site_url = request.form['site_url']
            settings.purchase_code_url = request.form.get('purchase_code_url', '')
            settings.tg_group_url = request.form.get('tg_group_url', '')
            settings.default_user_max_emails = int(request.form['default_user_max_emails'])
            settings.default_pro_max_emails = int(request.form['default_pro_max_emails'])
            settings.min_user_prefix_length = int(request.form['min_user_prefix_length'])
            settings.min_pro_prefix_length = int(request.form['min_pro_prefix_length'])
        elif 'smtp_server' in request.form:
            settings.smtp_server = request.form['smtp_server']
            settings.imap_server = request.form['imap_server']
            settings.pop3_server = request.form['pop3_server']
            settings.webmail_url = request.form['webmail_url']
        db.session.commit()
        flash('站点设置已更新', 'success')

    return render_template('admin/settings.html', site_settings=settings)


@app.route('/admin/tickets')
@login_required
def admin_tickets():
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)


@app.route('/admin/about', methods=['GET', 'POST'])
@login_required
def admin_about():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    about_page = AboutPage.query.first()
    if not about_page:
        about_page = AboutPage()
        db.session.add(about_page)
        db.session.commit()

    if request.method == 'POST':
        about_page.content = request.form['content']
        db.session.commit()
        flash('关于页面已更新', 'success')

    return render_template('admin/about.html', about_page=about_page)


@app.route('/admin/agreement', methods=['GET', 'POST'])
@login_required
def admin_agreement():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))

    user_agreement = UserAgreement.query.first()
    if not user_agreement:
        user_agreement = UserAgreement()
        db.session.add(user_agreement)
        db.session.commit()

    if request.method == 'POST':
        user_agreement.content = request.form['content']
        db.session.commit()
        flash('用户协议已更新', 'success')

    return render_template('admin/agreement.html', user_agreement=user_agreement)


@app.route('/agreement')
def agreement():
    user_agreement = UserAgreement.query.first()
    if not user_agreement:
        user_agreement = UserAgreement()
        db.session.add(user_agreement)
        db.session.commit()
    return render_template('agreement.html', user_agreement=user_agreement)


@app.route('/admin/users/change-role/<int:user_id>', methods=['POST'])
@login_required
def admin_change_role(user_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    
    if user.role == 'owner' and not current_user.is_owner():
        flash('无权修改Owner用户组', 'danger')
        return redirect(url_for('admin_users'))

    new_role = request.form['role']
    
    if new_role == 'owner' and not current_user.is_owner():
        flash('无权将用户设为Owner', 'danger')
        return redirect(url_for('admin_users'))

    user.role = new_role
    
    site_settings = SiteSettings.query.first()
    if new_role == 'user':
        user.max_emails = site_settings.default_user_max_emails if site_settings else 2
    elif new_role == 'pro':
        user.max_emails = site_settings.default_pro_max_emails if site_settings else 5
        duration = request.form.get('duration')
        if duration:
            if duration == 'permanent':
                user.is_permanent = True
                user.pro_expires_at = None
            else:
                user.is_permanent = False
                user.pro_expires_at = datetime.utcnow() + timedelta(days=int(duration))
    
    db.session.commit()
    flash('用户组已更新', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/update-max-emails/<int:user_id>', methods=['POST'])
@login_required
def admin_update_max_emails(user_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    
    if user.role == 'owner' and not current_user.is_owner():
        flash('无权修改Owner用户', 'danger')
        return redirect(url_for('admin_users'))

    new_max_emails = request.form.get('max_emails')
    try:
        new_max_emails = int(new_max_emails)
        if new_max_emails < 1:
            flash('邮箱数量必须大于0', 'danger')
        else:
            user.max_emails = new_max_emails
            db.session.commit()
            flash('用户邮箱上限已更新', 'success')
    except ValueError:
        flash('请输入有效的数字', 'danger')

    return redirect(url_for('admin_users'))


@app.route('/admin/codes')
@login_required
def admin_codes():
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    search = request.args.get('search', '')
    query = RedemptionCode.query
    
    if search:
        query = query.filter(RedemptionCode.code.like(f'%{search}%'))
    
    codes = query.order_by(RedemptionCode.created_at.desc()).all()
    return render_template('admin/codes.html', codes=codes, search=search)


@app.route('/admin/codes/create', methods=['GET', 'POST'])
@login_required
def admin_create_code():
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        duration = request.form.get('duration')
        extra_emails = int(request.form.get('extra_emails', 1))
        is_permanent = request.form.get('is_permanent') == 'true'
        custom_code = request.form.get('custom_code', '').strip()
        count = int(request.form.get('count', 1))
        max_uses = int(request.form.get('max_uses', 1))
        expires_days = int(request.form.get('expires_days', 0))

        if count > 1 and custom_code:
            flash('批量生成时不能使用自定义卡密', 'danger')
            return redirect(url_for('admin_create_code'))

        created_codes = []
        for _ in range(count):
            if custom_code:
                code = custom_code
            else:
                code = RedemptionCode.generate_code()
            
            while RedemptionCode.query.filter_by(code=code).first():
                code = RedemptionCode.generate_code()

            redemption_code = RedemptionCode(
                code=code,
                extra_emails=extra_emails,
                is_permanent=is_permanent,
                max_uses=max_uses
            )
            
            if not is_permanent and duration:
                redemption_code.duration_days = int(duration)
            
            if expires_days > 0:
                redemption_code.expires_at = datetime.utcnow() + timedelta(days=expires_days)

            db.session.add(redemption_code)
            created_codes.append(code)

        db.session.commit()
        flash(f'成功创建 {len(created_codes)} 个卡密！', 'success')
        
        if len(created_codes) == 1:
            return redirect(url_for('admin_codes'))
        else:
            return render_template('admin/show_codes.html', codes=created_codes)

    return render_template('admin/create_code.html')


@app.route('/admin/codes/delete/<int:code_id>')
@login_required
def admin_delete_code(code_id):
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))

    code = RedemptionCode.query.get_or_404(code_id)
    db.session.delete(code)
    db.session.commit()
    flash('卡密已删除', 'success')
    return redirect(url_for('admin_codes'))


@app.route('/admin/codes/cleanup')
@login_required
def admin_cleanup_codes():
    if not current_user.can_access_admin():
        flash('无权访问', 'danger')
        return redirect(url_for('dashboard'))
    
    now = datetime.utcnow()
    two_days_ago = now - timedelta(days=2)
    
    deleted_count = 0
    
    expired_codes = RedemptionCode.query.filter(
        RedemptionCode.expires_at < now
    ).all()
    
    for code in expired_codes:
        db.session.delete(code)
        deleted_count += 1
    
    used_old_codes = RedemptionCode.query.filter(
        RedemptionCode.is_used == True,
        RedemptionCode.used_at < two_days_ago
    ).all()
    
    for code in used_old_codes:
        db.session.delete(code)
        deleted_count += 1
    
    db.session.commit()
    flash(f'成功删除 {deleted_count} 个过期或已使用2天以上的卡密', 'success')
    return redirect(url_for('admin_codes'))


@app.route('/admin/prefix-blacklist')
@login_required
def admin_prefix_blacklist():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    blacklist = PrefixBlacklist.query.order_by(PrefixBlacklist.created_at.desc()).all()
    return render_template('admin/prefix_blacklist.html', blacklist=blacklist)


@app.route('/admin/prefix-blacklist/add', methods=['POST'])
@login_required
def admin_add_prefix_blacklist():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    prefix = request.form.get('prefix', '').strip().lower()
    if not prefix:
        flash('请输入前缀', 'danger')
        return redirect(url_for('admin_prefix_blacklist'))
    
    existing = PrefixBlacklist.query.filter_by(prefix=prefix).first()
    if existing:
        flash('该前缀已在黑名单中', 'danger')
        return redirect(url_for('admin_prefix_blacklist'))
    
    blacklist_item = PrefixBlacklist(prefix=prefix)
    db.session.add(blacklist_item)
    db.session.commit()
    
    flash(f'前缀 "{prefix}" 已添加到黑名单', 'success')
    return redirect(url_for('admin_prefix_blacklist'))


@app.route('/admin/prefix-blacklist/delete/<int:item_id>')
@login_required
def admin_delete_prefix_blacklist(item_id):
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    item = PrefixBlacklist.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    flash(f'前缀 "{item.prefix}" 已从黑名单中删除', 'success')
    return redirect(url_for('admin_prefix_blacklist'))


@app.route('/admin/email-suffixes')
@login_required
def admin_email_suffixes():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    suffixes = AllowedEmailSuffix.query.order_by(AllowedEmailSuffix.created_at.desc()).all()
    return render_template('admin/email_suffixes.html', suffixes=suffixes)


@app.route('/admin/email-suffixes/add', methods=['POST'])
@login_required
def admin_add_email_suffix():
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    suffix = request.form.get('suffix', '').strip().lower()
    if not suffix:
        flash('请输入邮箱后缀', 'danger')
        return redirect(url_for('admin_email_suffixes'))
    
    if not suffix.startswith('@'):
        suffix = '@' + suffix
    
    existing = AllowedEmailSuffix.query.filter_by(suffix=suffix).first()
    if existing:
        flash('该邮箱后缀已存在', 'danger')
        return redirect(url_for('admin_email_suffixes'))
    
    suffix_item = AllowedEmailSuffix(suffix=suffix)
    db.session.add(suffix_item)
    db.session.commit()
    
    flash(f'邮箱后缀 "{suffix}" 已添加到允许列表', 'success')
    return redirect(url_for('admin_email_suffixes'))


@app.route('/admin/email-suffixes/delete/<int:item_id>')
@login_required
def admin_delete_email_suffix(item_id):
    if not current_user.is_owner():
        flash('无权访问此页面', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    item = AllowedEmailSuffix.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    flash(f'邮箱后缀 "{item.suffix}" 已从允许列表中删除', 'success')
    return redirect(url_for('admin_email_suffixes'))


@app.route('/redeem-code', methods=['GET', 'POST'])
@login_required
def redeem_code():
    if request.method == 'POST':
        code_str = request.form['code'].strip().upper()
        
        code = RedemptionCode.query.filter_by(code=code_str).first()
        
        if not code:
            flash('卡密无效', 'danger')
            return redirect(url_for('redeem_code'))
        
        if code.is_expired():
            flash('该卡密已过期', 'danger')
            return redirect(url_for('redeem_code'))
        
        if not code.can_be_used():
            flash('该卡密已达到最大使用次数', 'danger')
            return redirect(url_for('redeem_code'))
        
        if code.is_permanent:
            current_user.extra_emails += code.extra_emails
        else:
            if code.duration_days:
                if current_user.temp_expires_at and current_user.temp_expires_at > datetime.utcnow():
                    current_user.temp_extra_emails += code.extra_emails
                    current_user.temp_expires_at = max(current_user.temp_expires_at, datetime.utcnow() + timedelta(days=code.duration_days))
                else:
                    current_user.temp_extra_emails = code.extra_emails
                    current_user.temp_expires_at = datetime.utcnow() + timedelta(days=code.duration_days)
        
        code.used_count += 1
        if code.max_uses > 0 and code.used_count >= code.max_uses:
            code.is_used = True
        code.user_id = current_user.id
        code.used_at = datetime.utcnow()
        
        db.session.commit()
        remaining = code.max_uses - code.used_count if code.max_uses > 0 else '无限'
        flash(f'卡密兑换成功！剩余使用次数: {remaining}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('redeem_code.html')


def init_db():
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('user')]
                new_columns = ['uid', 'role', 'max_emails', 'extra_emails', 'pro_expires_at', 'is_permanent', 'temp_extra_emails', 'temp_expires_at']
                for col in new_columns:
                    if col not in columns:
                        try:
                            with db.engine.connect() as conn:
                                if col == 'uid':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN uid VARCHAR(20)"))
                                elif col == 'role':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                                elif col == 'max_emails':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN max_emails INT DEFAULT 2"))
                                elif col == 'extra_emails':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN extra_emails INT DEFAULT 0"))
                                elif col == 'pro_expires_at':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN pro_expires_at DATETIME"))
                                elif col == 'is_permanent':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN is_permanent BOOLEAN DEFAULT FALSE"))
                                elif col == 'temp_extra_emails':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN temp_extra_emails INT DEFAULT 0"))
                                elif col == 'temp_expires_at':
                                    conn.execute(db.text("ALTER TABLE user ADD COLUMN temp_expires_at DATETIME"))
                                conn.execute(db.text("COMMIT"))
                        except Exception as e:
                            print(f"添加{col}列时出错: {e}")
            
            if 'site_settings' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('site_settings')]
                if 'site_url' not in columns:
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(db.text("ALTER TABLE site_settings ADD COLUMN site_url VARCHAR(200) DEFAULT 'http://localhost:5000'"))
                            conn.execute(db.text("COMMIT"))
                    except Exception as e:
                        print(f"添加site_url列时出错: {e}")
            
            if 'redemption_code' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('redemption_code')]
                new_columns = ['max_uses', 'used_count', 'expires_at']
                for col in new_columns:
                    if col not in columns:
                        try:
                            with db.engine.connect() as conn:
                                if col == 'max_uses':
                                    conn.execute(db.text("ALTER TABLE redemption_code ADD COLUMN max_uses INT DEFAULT 1"))
                                elif col == 'used_count':
                                    conn.execute(db.text("ALTER TABLE redemption_code ADD COLUMN used_count INT DEFAULT 0"))
                                elif col == 'expires_at':
                                    conn.execute(db.text("ALTER TABLE redemption_code ADD COLUMN expires_at DATETIME"))
                                conn.execute(db.text("COMMIT"))
                        except Exception as e:
                            print(f"添加{col}列时出错: {e}")
            
            if 'site_settings' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('site_settings')]
                if 'purchase_code_url' not in columns:
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(db.text("ALTER TABLE site_settings ADD COLUMN purchase_code_url VARCHAR(500) DEFAULT ''"))
                            conn.execute(db.text("COMMIT"))
                    except Exception as e:
                        print(f"添加purchase_code_url列时出错: {e}")
            
            if 'site_settings' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('site_settings')]
                if 'tg_group_url' not in columns:
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(db.text("ALTER TABLE site_settings ADD COLUMN tg_group_url VARCHAR(500) DEFAULT ''"))
                            conn.execute(db.text("COMMIT"))
                    except Exception as e:
                        print(f"添加tg_group_url列时出错: {e}")
            
            db.create_all()
            
            if 'user' in existing_tables:
                try:
                    with db.engine.connect() as conn:
                        result = conn.execute(db.text("SELECT id, uid FROM user WHERE uid IS NULL OR uid = ''"))
                        users_without_uid = result.fetchall()
                        for user in users_without_uid:
                            new_uid = generate_uid()
                            conn.execute(db.text("UPDATE user SET uid = :uid WHERE id = :id"), {'uid': new_uid, 'id': user[0]})
                        conn.execute(db.text("COMMIT"))
                except Exception as e:
                    print(f"为现有用户分配uid时出错: {e}")
        
        except Exception as e:
            print(f"数据库迁移出错: {e}")
        
        try:
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

            if not User.query.filter_by(role='owner').first():
                admin = User(username=admin_username, email=admin_email, is_admin=True, is_verified=True, uid=generate_uid(), role='owner')
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()

            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            for user in User.query.all():
                if not user.uid:
                    user.uid = generate_uid()
                if user.username == admin_username and user.role != 'owner':
                    user.role = 'owner'
                    user.is_admin = True
            db.session.commit()

            if not SiteSettings.query.first():
                settings = SiteSettings()
                db.session.add(settings)
                db.session.commit()

            if not AboutPage.query.first():
                about = AboutPage()
                db.session.add(about)
                db.session.commit()
            
            default_prefixes = [
                'system', 'admin', 'administrator', 'root', 'host',
                'report', 'abuse', 'support', 'help', 'info',
                'contact', 'postmaster', 'webmaster', 'mailer-daemon',
                'noreply', 'no-reply', 'service', 'services',
                'security', 'privacy', 'legal', 'compliance',
                'billing', 'payment', 'sales', 'marketing',
                'press', 'media', 'pr', 'feedback',
                'careers', 'jobs', 'hr', 'recruitment',
                'dev', 'developer', 'api', 'api-admin',
                'test', 'demo', 'example', 'sample',
                'temp', 'tmp', 'guest', 'anonymous',
                'user', 'users', 'member', 'members',
                'customer', 'customers', 'client', 'clients',
                'partner', 'partners', 'vendor', 'vendors',
                'supplier', 'suppliers', 'manager', 'management',
                'ceo', 'cfo', 'cto', 'director',
                'executive', 'lead', 'head', 'owner',
                'founder', 'co-founder', 'chairman', 'board',
                'trustee', 'moderator', 'mod', 'supermod',
                'superuser', 'su', 'sudo', 'wheel',
                'staff', 'team', 'crew', 'office',
                'office@', 'mail', 'mailbox', 'inbox',
                'outbox', 'spam', 'trash', 'archive',
                'draft', 'drafts', 'sent', 'sentmail'
            ]
            
            for prefix in default_prefixes:
                existing = PrefixBlacklist.query.filter_by(prefix=prefix).first()
                if not existing:
                    blacklist_item = PrefixBlacklist(prefix=prefix)
                    db.session.add(blacklist_item)
            
            default_suffixes = [
                '@gmail.com', '@hotmail.com', '@yahoo.com', '@qq.com',
                '@163.com', '@126.com', '@88.com', '@vip.qq.com',
                '@outlook.com', '@icloud.com', '@sina.com', '@sohu.com',
                '@aliyun.com', '@foxmail.com', '@yeah.com', '@me.com', '@mail.com'
            ]
            
            for suffix in default_suffixes:
                existing = AllowedEmailSuffix.query.filter_by(suffix=suffix).first()
                if not existing:
                    suffix_item = AllowedEmailSuffix(suffix=suffix)
                    db.session.add(suffix_item)
            
            db.session.commit()
        except Exception as e:
            print(f"初始化数据时出错: {e}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
