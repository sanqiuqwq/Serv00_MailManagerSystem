from app import app, db
from sqlalchemy import text

def update_database():
    with app.app_context():
        print("正在检查并更新数据库...")
        
        try:
            with db.engine.connect() as conn:
                # 检查并添加 smtp_server 列
                try:
                    conn.execute(text("SELECT smtp_server FROM site_settings LIMIT 1"))
                    print("✓ smtp_server 列已存在")
                except:
                    conn.execute(text("ALTER TABLE site_settings ADD COLUMN smtp_server VARCHAR(200) DEFAULT 'smtp.example.com'"))
                    conn.execute(text("COMMIT"))
                    print("✓ 已添加 smtp_server 列")
                
                # 检查并添加 imap_server 列
                try:
                    conn.execute(text("SELECT imap_server FROM site_settings LIMIT 1"))
                    print("✓ imap_server 列已存在")
                except:
                    conn.execute(text("ALTER TABLE site_settings ADD COLUMN imap_server VARCHAR(200) DEFAULT 'imap.example.com'"))
                    conn.execute(text("COMMIT"))
                    print("✓ 已添加 imap_server 列")
                
                # 检查并添加 pop3_server 列
                try:
                    conn.execute(text("SELECT pop3_server FROM site_settings LIMIT 1"))
                    print("✓ pop3_server 列已存在")
                except:
                    conn.execute(text("ALTER TABLE site_settings ADD COLUMN pop3_server VARCHAR(200) DEFAULT 'pop3.example.com'"))
                    conn.execute(text("COMMIT"))
                    print("✓ 已添加 pop3_server 列")
                
                # 检查并添加 webmail_url 列
                try:
                    conn.execute(text("SELECT webmail_url FROM site_settings LIMIT 1"))
                    print("✓ webmail_url 列已存在")
                except:
                    conn.execute(text("ALTER TABLE site_settings ADD COLUMN webmail_url VARCHAR(500) DEFAULT 'https://mail.example.com'"))
                    conn.execute(text("COMMIT"))
                    print("✓ 已添加 webmail_url 列")
                
                # 检查并添加 nodeloc_id 列
                try:
                    conn.execute(text("SELECT nodeloc_id FROM user LIMIT 1"))
                    print("✓ nodeloc_id 列已存在")
                except:
                    conn.execute(text("ALTER TABLE user ADD COLUMN nodeloc_id INT UNIQUE"))
                    conn.execute(text("COMMIT"))
                    print("✓ 已添加 nodeloc_id 列")
            
            print("\n========================================")
            print("数据库更新完成！")
            print("========================================")
            
        except Exception as e:
            print(f"\n错误: {e}")
            print("\n请确保数据库连接正常，并且表 site_settings 已存在。")

if __name__ == '__main__':
    update_database()
