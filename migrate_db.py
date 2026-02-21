from app import app, db, UserAgreement
from sqlalchemy import inspect, text

def add_column_if_not_exists(table_name, column_name, column_definition):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    if column_name not in columns:
        with db.engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
            conn.commit()
        print(f"Added column: {table_name}.{column_name}")
    else:
        print(f"Column already exists: {table_name}.{column_name}")

def create_table_if_not_exists(table_name, create_sql):
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if table_name not in tables:
        with db.engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()
        print(f"Created table: {table_name}")
    else:
        print(f"Table already exists: {table_name}")

with app.app_context():
    print("Starting database migration...")
    
    # Add columns to site_settings table
    add_column_if_not_exists('site_settings', 'default_user_max_emails', 'INT DEFAULT 2')
    add_column_if_not_exists('site_settings', 'default_pro_max_emails', 'INT DEFAULT 5')
    add_column_if_not_exists('site_settings', 'min_user_prefix_length', 'INT DEFAULT 7')
    add_column_if_not_exists('site_settings', 'min_pro_prefix_length', 'INT DEFAULT 3')
    
    # Add columns to ticket table
    add_column_if_not_exists('ticket', 'closed_at', 'DATETIME')
    
    # Create user_agreement table if not exists
    create_table_if_not_exists('user_agreement', '''
        CREATE TABLE user_agreement (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            content TEXT,
            updated_at DATETIME
        )
    ''')
    
    # Initialize user agreement if not exists
    agreement = UserAgreement.query.first()
    if not agreement:
        agreement = UserAgreement()
        db.session.add(agreement)
        db.session.commit()
        print("Initialized user agreement")
    
    print("Migration completed successfully!")
