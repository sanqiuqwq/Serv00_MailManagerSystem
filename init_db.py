from app import app, db
from datetime import datetime
from sqlalchemy import text

def init_database():
    with app.app_context():
        print("正在创建所有数据表...")
        db.create_all()
        print("✓ 数据表创建完成")
        
        print("\n正在检查并更新数据库结构...")
        
        try:
            with db.engine.connect() as conn:
                # 检查并添加 nodeloc_id 列（如果不存在）
                try:
                    conn.execute(text("SELECT nodeloc_id FROM user LIMIT 1"))
                    print("✓ nodeloc_id 列已存在")
                except:
                    try:
                        conn.execute(text("ALTER TABLE user ADD COLUMN nodeloc_id BIGINT UNIQUE"))
                        conn.execute(text("COMMIT"))
                        print("✓ 已添加 nodeloc_id 列")
                    except Exception as e:
                        print(f"  nodeloc_id 列添加跳过: {e}")
                
                # 检查并添加 telegram_id 列（如果不存在）
                try:
                    conn.execute(text("SELECT telegram_id FROM user LIMIT 1"))
                    print("✓ telegram_id 列已存在")
                except:
                    try:
                        conn.execute(text("ALTER TABLE user ADD COLUMN telegram_id BIGINT UNIQUE"))
                        conn.execute(text("COMMIT"))
                        print("✓ 已添加 telegram_id 列")
                    except Exception as e:
                        print(f"  telegram_id 列添加跳过: {e}")
        
        except Exception as e:
            print(f"  数据库结构检查跳过: {e}")
        
        print("\n正在初始化默认数据...")
        
        from app import User, SiteSettings, UserAgreement, AboutPage, PrefixBlacklist, AllowedEmailSuffix
        
        # 初始化站点设置
        if not SiteSettings.query.first():
            settings = SiteSettings()
            db.session.add(settings)
            db.session.commit()
            print("✓ 站点设置初始化完成")
        else:
            print("✓ 站点设置已存在")
        
        # 初始化用户协议
        if not UserAgreement.query.first():
            agreement = UserAgreement()
            db.session.add(agreement)
            db.session.commit()
            print("✓ 用户协议初始化完成")
        else:
            print("✓ 用户协议已存在")
        
        # 初始化关于页面
        if not AboutPage.query.first():
            about = AboutPage()
            db.session.add(about)
            db.session.commit()
            print("✓ 关于页面初始化完成")
        else:
            print("✓ 关于页面已存在")
        
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
        added_count = 0
        for prefix in default_prefixes:
            if prefix not in existing_prefixes:
                p = PrefixBlacklist(prefix=prefix)
                db.session.add(p)
                added_count += 1
        db.session.commit()
        print(f"✓ 邮箱前缀黑名单初始化完成（新增 {added_count} 个）")
        
        # 初始化允许的邮箱后缀
        default_suffixes = [
            '@gmail.com', '@hotmail.com', '@yahoo.com', '@qq.com',
            '@163.com', '@126.com', '@88.com', '@vip.qq.com',
            '@outlook.com', '@icloud.com', '@sina.com', '@sohu.com',
            '@aliyun.com', '@foxmail.com', '@yeah.com', '@me.com', '@mail.com'
        ]
        
        existing_suffixes = [s.suffix for s in AllowedEmailSuffix.query.all()]
        added_suffix_count = 0
        for suffix in default_suffixes:
            if suffix not in existing_suffixes:
                s = AllowedEmailSuffix(suffix=suffix)
                db.session.add(s)
                added_suffix_count += 1
        db.session.commit()
        print(f"✓ 允许的邮箱后缀初始化完成（新增 {added_suffix_count} 个）")
        
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
        else:
            print(f"✓ Owner账户已存在")
        
        print("\n========================================")
        print("数据库初始化完成！")
        print("========================================")

if __name__ == '__main__':
    init_database()
