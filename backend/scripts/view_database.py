#!/usr/bin/env python3
"""
Database Viewer Script
Quick view of database contents for monitoring API interactions
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import SessionLocal
from models import Patient, ClinicalStaff, CallSession
from datetime import datetime
import json

def view_database():
    """Display all database contents in a readable format"""
    
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🏥 TKA VOICE AGENT DATABASE CONTENTS")
        print("=" * 80)
        
        # Clinical Staff
        print("\n👨‍⚕️ CLINICAL STAFF:")
        print("-" * 40)
        staff = db.query(ClinicalStaff).all()
        if staff:
            for s in staff:
                print(f"  • {s.name} ({s.role}) - {s.email}")
        else:
            print("  No clinical staff found")
        
        # Patients
        print("\n👤 PATIENTS:")
        print("-" * 40)
        patients = db.query(Patient).all()
        if patients:
            for p in patients:
                print(f"  • {p.name}")
                print(f"    📞 Primary: {p.primary_phone_number}")
                if p.secondary_phone_number is not None:
                    print(f"    📞 Secondary: {p.secondary_phone_number}")
                print(f"    📅 Surgery: {p.surgery_date.strftime('%Y-%m-%d') if p.surgery_date is not None else 'Not set'}")
                print(f"    📊 Status: {p.surgery_readiness_status}")
                print(f"    🎯 Compliance: {p.overall_compliance_score}%")
                print(f"    🆔 ID: {p.id}")
                print()
        else:
            print("  No patients found")
        
        # Call Sessions
        print("\n📞 CALL SESSIONS:")
        print("-" * 40)
        calls = db.query(CallSession).order_by(CallSession.scheduled_date).all()
        if calls:
            for c in calls:
                patient = db.query(Patient).filter(Patient.id == c.patient_id).first()
                patient_name = patient.name if patient else "Unknown"
                
                print(f"  • {patient_name} - {c.call_type}")
                print(f"    📅 Scheduled: {c.scheduled_date.strftime('%Y-%m-%d %H:%M') if c.scheduled_date is not None else 'Not set'}")
                print(f"    📊 Status: {c.call_status}")
                print(f"    🏥 Surgery Type: {c.surgery_type}")
                print(f"    📈 Stage: {c.stage}")
                print(f"    📍 Days from surgery: {c.days_from_surgery}")
                if c.compliance_score is not None:
                    print(f"    🎯 Compliance: {c.compliance_score}")
                if c.agent_notes is not None:
                    print(f"    📝 Notes: {c.agent_notes}")
                print(f"    🆔 ID: {c.id}")
                print()
        else:
            print("  No call sessions found")
        
        print("=" * 80)
        print(f"📊 SUMMARY: {len(staff)} staff, {len(patients)} patients, {len(calls)} calls")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error viewing database: {e}")
    finally:
        db.close()

def monitor_mode():
    """Simple monitoring mode - shows database contents every few seconds"""
    import time
    
    print("🔄 MONITORING MODE - Press Ctrl+C to stop")
    print("Database contents will refresh every 5 seconds...\n")
    
    try:
        while True:
            # Clear screen (works on most terminals)
            print("\033[2J\033[H")
            view_database()
            print("\n⏰ Refreshing in 5 seconds... (Ctrl+C to stop)")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_mode()
    else:
        view_database() 