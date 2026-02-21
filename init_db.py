from app import app, db
from datetime import datetime

def init_database():
    with app.app_context():
        print("正在创建所有数据表...")
        db.create_all()
        print("✓ 数据表创建完成")
        
        print("\n正在初始化默认数据...")
        
        from app import User, SiteSettings, UserAgreement, AboutPage, PrefixBlacklist, AllowedEmailSuffix
        
        # 初始化站点设置
        if not SiteSettings.query.first():
            settings = SiteSettings()
            db.session.add(settings)
            db.session.commit()
            print("✓ 站点设置初始化完成")
        
        # 初始化用户协议
        if not UserAgreement.query.first():
            agreement = UserAgreement()
            db.session.add(agreement)
            db.session.commit()
            print("✓ 用户协议初始化完成")
        
        # 初始化关于页面
        if not AboutPage.query.first():
            about = AboutPage()
            db.session.add(about)
            db.session.commit()
            print("✓ 关于页面初始化完成")
        
        # 初始化邮箱前缀黑名单
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
        
        existing_prefixes = [p.prefix for p in PrefixBlacklist.query.all()]
        for prefix in default_prefixes:
            if prefix not in existing_prefixes:
                p = PrefixBlacklist(prefix=prefix)
                db.session.add(p)
        db.session.commit()
        print(f"✓ 邮箱前缀黑名单初始化完成（共 {len(default_prefixes)} 个）")
        
        # 初始化允许的邮箱后缀
        default_suffixes = [
            '@gmail.com', '@hotmail.com', '@yahoo.com', '@qq.com',
            '@163.com', '@126.com', '@88.com', '@vip.qq.com',
            '@outlook.com', '@icloud.com', '@sina.com', '@sohu.com',
            '@aliyun.com', '@foxmail.com', '@yeah.com', '@me.com', '@mail.com'
        ]
        
        existing_suffixes = [s.suffix for s in AllowedEmailSuffix.query.all()]
        for suffix in default_suffixes:
            if suffix not in existing_suffixes:
                s = AllowedEmailSuffix(suffix=suffix)
                db.session.add(s)
        db.session.commit()
        print(f"✓ 允许的邮箱后缀初始化完成（共 {len(default_suffixes)} 个）")
        
        # 初始化默认Owner账户
        import os
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if not User.query.filter_by(role='owner').first():
            from app import generate_uid
            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True,
                is_verified=True,
                uid=generate_uid(),
                role='owner'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✓ 默认Owner账户创建成功")
            print(f"  用户名: {admin_username}")
            print(f"  密码: {admin_password}")
            print(f"  邮箱: {admin_email}")
        
        print("\n========================================")
        print("数据库初始化完成！")
        print("========================================")

if __name__ == '__main__':
    init_database()
