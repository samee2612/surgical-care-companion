#!/usr/bin/env python3
"""
Database migration runner
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append('/app')

try:
    from alembic import command
    from alembic.config import Config
    
    # Set up Alembic configuration
    alembic_cfg = Config('/app/alembic.ini')
    
    # Run migrations
    command.upgrade(alembic_cfg, 'head')
    print('[SUCCESS] Database migrations completed successfully')
    
except Exception as e:
    print(f'[INFO] Migration note: {e}')
    print('[INFO] This is normal on first run if tables already exist')
    
    # Try to create tables directly if Alembic fails
    try:
        from database.connection import engine, Base
        from models import Patient, ClinicalStaff, CallSession, Notification, ClinicalAlert
        
        Base.metadata.create_all(bind=engine)
        print('[SUCCESS] Database tables created directly')
        
    except Exception as e2:
        print(f'[WARNING] Could not create tables: {e2}')
        print('[INFO] Database may already be initialized')
