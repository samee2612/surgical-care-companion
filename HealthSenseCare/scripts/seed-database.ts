#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from '../shared/schema';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
});

const db = drizzle(pool, { schema });

async function seedDatabase() {
  console.log('🌱 Starting database seeding...');

  try {
    // Seed Users (Healthcare Providers)
    console.log('👥 Creating users...');
    const users = await db.insert(schema.users).values([
      {
        id: 'dr-johnson-001',
        email: 'dr.johnson@hospital.com',
        firstName: 'Sarah',
        lastName: 'Johnson',
        role: 'provider',
      },
      {
        id: 'dr-smith-002',
        email: 'dr.smith@hospital.com',
        firstName: 'Michael',
        lastName: 'Smith',
        role: 'provider',
      },
      {
        id: 'admin-001',
        email: 'admin@hospital.com',
        firstName: 'Lisa',
        lastName: 'Chen',
        role: 'admin',
      },
    ]).returning();

    // Seed Patients
    console.log('🏥 Creating patients...');
    const patients = await db.insert(schema.patients).values([
      {
        mrn: 'MRN001001',
        firstName: 'Robert',
        lastName: 'Thompson',
        dateOfBirth: '1965-03-15',
        phone: '+1-555-0101',
        email: 'r.thompson@email.com',
        emergencyContactName: 'Mary Thompson',
        emergencyContactPhone: '+1-555-0102',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001002',
        firstName: 'Jennifer',
        lastName: 'Davis',
        dateOfBirth: '1972-08-22',
        phone: '+1-555-0103',
        email: 'j.davis@email.com',
        emergencyContactName: 'David Davis',
        emergencyContactPhone: '+1-555-0104',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001003',
        firstName: 'James',
        lastName: 'Wilson',
        dateOfBirth: '1958-12-08',
        phone: '+1-555-0105',
        email: 'j.wilson@email.com',
        emergencyContactName: 'Patricia Wilson',
        emergencyContactPhone: '+1-555-0106',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001004',
        firstName: 'Maria',
        lastName: 'Rodriguez',
        dateOfBirth: '1970-05-18',
        phone: '+1-555-0107',
        email: 'm.rodriguez@email.com',
        emergencyContactName: 'Carlos Rodriguez',
        emergencyContactPhone: '+1-555-0108',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001005',
        firstName: 'William',
        lastName: 'Brown',
        dateOfBirth: '1963-11-30',
        phone: '+1-555-0109',
        email: 'w.brown@email.com',
        emergencyContactName: 'Susan Brown',
        emergencyContactPhone: '+1-555-0110',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001006',
        firstName: 'Elizabeth',
        lastName: 'Miller',
        dateOfBirth: '1975-07-14',
        phone: '+1-555-0111',
        email: 'e.miller@email.com',
        emergencyContactName: 'John Miller',
        emergencyContactPhone: '+1-555-0112',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001007',
        firstName: 'David',
        lastName: 'Anderson',
        dateOfBirth: '1968-02-25',
        phone: '+1-555-0113',
        email: 'd.anderson@email.com',
        emergencyContactName: 'Linda Anderson',
        emergencyContactPhone: '+1-555-0114',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001008',
        firstName: 'Linda',
        lastName: 'Taylor',
        dateOfBirth: '1964-09-12',
        phone: '+1-555-0115',
        email: 'l.taylor@email.com',
        emergencyContactName: 'Robert Taylor',
        emergencyContactPhone: '+1-555-0116',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001009',
        firstName: 'Charles',
        lastName: 'Moore',
        dateOfBirth: '1961-04-06',
        phone: '+1-555-0117',
        email: 'c.moore@email.com',
        emergencyContactName: 'Helen Moore',
        emergencyContactPhone: '+1-555-0118',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
      {
        mrn: 'MRN001010',
        firstName: 'Nancy',
        lastName: 'Jackson',
        dateOfBirth: '1969-10-28',
        phone: '+1-555-0119',
        email: 'n.jackson@email.com',
        emergencyContactName: 'Mark Jackson',
        emergencyContactPhone: '+1-555-0120',
        voiceConsentGiven: true,
        dataConsentGiven: true,
        programActive: true,
      },
    ]).returning();

    // Seed Surgeries
    console.log('🔪 Creating surgeries...');
    const surgeries = await db.insert(schema.surgeries).values([
      {
        patientId: patients[0].id,
        procedure: 'Total Knee Replacement',
        surgeonName: 'Dr. Sarah Johnson',
        surgeryDate: '2024-12-15',
        dischargeDate: '2024-12-17',
        expectedRecoveryWeeks: 12,
        specialty: 'orthopedic',
        notes: 'Left knee replacement due to severe osteoarthritis. Patient responding well to initial recovery protocol.',
      },
      {
        patientId: patients[1].id,
        procedure: 'Coronary Artery Bypass Graft (CABG)',
        surgeonName: 'Dr. Michael Smith',
        surgeryDate: '2024-12-10',
        dischargeDate: '2024-12-14',
        expectedRecoveryWeeks: 8,
        specialty: 'cardiac',
        notes: 'Triple vessel bypass. Excellent surgical outcome. Patient stable and progressing well.',
      },
      {
        patientId: patients[2].id,
        procedure: 'Hip Replacement',
        surgeonName: 'Dr. Sarah Johnson',
        surgeryDate: '2024-12-12',
        dischargeDate: '2024-12-15',
        expectedRecoveryWeeks: 10,
        specialty: 'orthopedic',
        notes: 'Right hip replacement. Minimally invasive approach used. Good range of motion achieved.',
      },
      {
        patientId: patients[3].id,
        procedure: 'Cholecystectomy (Laparoscopic)',
        surgeonName: 'Dr. Michael Smith',
        surgeryDate: '2024-12-18',
        dischargeDate: '2024-12-19',
        expectedRecoveryWeeks: 2,
        specialty: 'general',
        notes: 'Routine laparoscopic gallbladder removal. No complications. Early mobilization encouraged.',
      },
      {
        patientId: patients[4].id,
        procedure: 'Rotator Cuff Repair',
        surgeonName: 'Dr. Sarah Johnson',
        surgeryDate: '2024-12-20',
        dischargeDate: '2024-12-21',
        expectedRecoveryWeeks: 16,
        specialty: 'orthopedic',
        notes: 'Arthroscopic repair of full-thickness rotator cuff tear. Physical therapy protocol initiated.',
      },
      {
        patientId: patients[5].id,
        procedure: 'Appendectomy',
        surgeonName: 'Dr. Michael Smith',
        surgeryDate: '2024-12-22',
        dischargeDate: '2024-12-23',
        expectedRecoveryWeeks: 1,
        specialty: 'general',
        notes: 'Emergency appendectomy for acute appendicitis. Uncomplicated recovery expected.',
      },
      {
        patientId: patients[6].id,
        procedure: 'Spinal Fusion (L4-L5)',
        surgeonName: 'Dr. Sarah Johnson',
        surgeryDate: '2024-12-14',
        dischargeDate: '2024-12-18',
        expectedRecoveryWeeks: 20,
        specialty: 'orthopedic',
        notes: 'Posterior lumbar interbody fusion. Hardware placement successful. Strict lifting restrictions.',
      },
      {
        patientId: patients[7].id,
        procedure: 'Hernia Repair (Inguinal)',
        surgeonName: 'Dr. Michael Smith',
        surgeryDate: '2024-12-25',
        dischargeDate: '2024-12-25',
        expectedRecoveryWeeks: 3,
        specialty: 'general',
        notes: 'Mesh repair of right inguinal hernia. Outpatient procedure. Return to normal activities in 2-3 weeks.',
      },
      {
        patientId: patients[8].id,
        procedure: 'Cataract Surgery',
        surgeonName: 'Dr. Sarah Johnson',
        surgeryDate: '2024-12-28',
        dischargeDate: '2024-12-28',
        expectedRecoveryWeeks: 2,
        specialty: 'ophthalmology',
        notes: 'Right eye cataract extraction with IOL implantation. Vision improvement expected.',
      },
      {
        patientId: patients[9].id,
        procedure: 'Mastectomy (Partial)',
        surgeonName: 'Dr. Michael Smith',
        surgeryDate: '2024-12-30',
        dischargeDate: '2025-01-02',
        expectedRecoveryWeeks: 6,
        specialty: 'oncology',
        notes: 'Lumpectomy with sentinel lymph node biopsy. Clear margins achieved. Oncology follow-up scheduled.',
      },
    ]).returning();

    // Seed Voice Interactions
    console.log('🗣️ Creating voice interactions...');
    const voiceInteractions = await db.insert(schema.voiceInteractions).values([
      {
        patientId: patients[0].id,
        surgeryId: surgeries[0].id,
        callDate: new Date('2024-12-18T10:00:00Z'),
        duration: 420,
        transcript: "Hi Robert, this is your automated care assistant. How are you feeling today? I'm doing much better, thank you. The pain in my knee is manageable with the medication. I've been doing my physical therapy exercises as prescribed. That's great to hear! On a scale of 1 to 10, how would you rate your pain today? I'd say it's about a 4. Are you experiencing any swelling, redness, or unusual warmth around the surgical site? No, everything looks normal to me.",
        symptoms: JSON.stringify(['moderate_pain', 'medication_compliance', 'physical_therapy_compliance']),
        painLevel: 4,
        riskScore: '2.1',
        status: 'normal',
        escalated: false,
        aiAnalysis: JSON.stringify({
          sentiment: 'positive',
          compliance: 'high',
          concerns: 'none',
          recommendations: ['continue_current_plan', 'monitor_pain_levels']
        }),
        callSuccessful: true,
      },
      {
        patientId: patients[1].id,
        surgeryId: surgeries[1].id,
        callDate: new Date('2024-12-16T14:30:00Z'),
        duration: 380,
        transcript: "Hello Jennifer, how has your recovery been going since your cardiac surgery? I've been following all the instructions. I'm walking a little each day and taking my medications. Good! Any chest pain or shortness of breath? I do feel a bit short of breath when I walk up stairs, but the doctor said that's normal. On a scale of 1 to 10, how would you rate any discomfort? Maybe a 3. I'm feeling stronger each day.",
        symptoms: JSON.stringify(['mild_shortness_of_breath', 'medication_compliance', 'activity_compliance']),
        painLevel: 3,
        riskScore: '1.8',
        status: 'normal',
        escalated: false,
        aiAnalysis: JSON.stringify({
          sentiment: 'positive',
          compliance: 'high',
          concerns: 'mild_dyspnea_expected',
          recommendations: ['continue_gradual_activity_increase']
        }),
        callSuccessful: true,
      },
      {
        patientId: patients[2].id,
        surgeryId: surgeries[2].id,
        callDate: new Date('2024-12-17T09:15:00Z'),
        duration: 290,
        transcript: "Hi James, how are you managing after your hip replacement? The pain is quite severe today, probably an 8 out of 10. I'm having trouble walking even with the walker. The surgical site looks a bit red and feels warm. I'm concerned something might be wrong.",
        symptoms: JSON.stringify(['severe_pain', 'mobility_issues', 'surgical_site_redness', 'warmth_at_site']),
        painLevel: 8,
        riskScore: '7.2',
        status: 'escalated',
        escalated: true,
        escalationReason: 'High pain level combined with signs of potential infection (redness, warmth at surgical site)',
        aiAnalysis: JSON.stringify({
          sentiment: 'concerned',
          compliance: 'unknown',
          concerns: 'possible_infection',
          recommendations: ['immediate_medical_evaluation', 'contact_surgeon']
        }),
        callSuccessful: true,
      },
      {
        patientId: patients[3].id,
        surgeryId: surgeries[3].id,
        callDate: new Date('2024-12-20T16:45:00Z'),
        duration: 180,
        transcript: "Hello Maria, how are you feeling after your gallbladder surgery? I'm doing really well! The pain is minimal, maybe a 2. I'm able to eat small meals without any nausea. The incision sites look good - no redness or drainage. I've been walking around the house as instructed.",
        symptoms: JSON.stringify(['minimal_pain', 'good_appetite', 'no_nausea', 'activity_compliance']),
        painLevel: 2,
        riskScore: '0.8',
        status: 'normal',
        escalated: false,
        aiAnalysis: JSON.stringify({
          sentiment: 'very_positive',
          compliance: 'high',
          concerns: 'none',
          recommendations: ['continue_current_plan', 'gradual_activity_increase']
        }),
        callSuccessful: true,
      },
      {
        patientId: patients[4].id,
        surgeryId: surgeries[4].id,
        callDate: new Date('2024-12-23T11:20:00Z'),
        duration: 340,
        transcript: "Hi William, how is your shoulder recovery progressing? It's been challenging. The pain is about a 6, and I'm having trouble sleeping because I can't find a comfortable position. I'm doing the pendulum exercises, but the range of motion exercises are quite painful.",
        symptoms: JSON.stringify(['moderate_to_severe_pain', 'sleep_disturbance', 'limited_rom', 'exercise_compliance']),
        painLevel: 6,
        riskScore: '3.4',
        status: 'normal',
        escalated: false,
        aiAnalysis: JSON.stringify({
          sentiment: 'frustrated_but_compliant',
          compliance: 'moderate',
          concerns: 'expected_recovery_challenges',
          recommendations: ['pain_management_review', 'sleep_positioning_education']
        }),
        callSuccessful: true,
      },
    ]).returning();

    // Seed Alerts
    console.log('🚨 Creating alerts...');
    await db.insert(schema.alerts).values([
      {
        patientId: patients[2].id,
        voiceInteractionId: voiceInteractions[2].id,
        priority: 'high',
        title: 'Possible Surgical Site Infection',
        description: 'Patient reports severe pain (8/10), redness, and warmth at hip replacement surgical site. Requires immediate medical evaluation.',
        riskScore: '7.2',
        assignedProviderId: users[0].id,
        status: 'active',
      },
      {
        patientId: patients[0].id,
        voiceInteractionId: voiceInteractions[0].id,
        priority: 'low',
        title: 'Routine Recovery Check',
        description: 'Patient recovering well from knee replacement. Pain well controlled at 4/10. High compliance with therapy.',
        riskScore: '2.1',
        assignedProviderId: users[0].id,
        status: 'resolved',
        resolvedAt: new Date('2024-12-18T15:00:00Z'),
        resolvedBy: users[0].id,
      },
      {
        patientId: patients[4].id,
        voiceInteractionId: voiceInteractions[4].id,
        priority: 'medium',
        title: 'Sleep Disturbance Post-Surgery',
        description: 'Patient experiencing sleep difficulties due to shoulder positioning. May need additional pain management or sleep aids.',
        riskScore: '3.4',
        assignedProviderId: users[0].id,
        status: 'active',
      },
    ]);

    // Seed Knowledge Articles
    console.log('📚 Creating knowledge articles...');
    await db.insert(schema.knowledgeArticles).values([
      {
        title: 'Post-Operative Pain Management Guidelines',
        content: 'Comprehensive guidelines for managing post-operative pain across different surgical specialties. Includes medication protocols, non-pharmacological interventions, and escalation criteria.',
        category: 'clinical',
        specialty: 'general',
        tags: JSON.stringify(['pain_management', 'post_operative', 'guidelines', 'medication']),
        authorId: users[0].id,
        published: true,
        readingLevel: 'high',
      },
      {
        title: 'Understanding Your Knee Replacement Recovery',
        content: 'Patient education guide covering what to expect during knee replacement recovery, exercise protocols, warning signs, and timeline for return to activities.',
        category: 'patient-education',
        specialty: 'orthopedic',
        tags: JSON.stringify(['knee_replacement', 'recovery', 'patient_education', 'exercises']),
        authorId: users[1].id,
        published: true,
        readingLevel: 'middle',
      },
      {
        title: 'Cardiac Surgery Recovery Best Practices',
        content: 'Evidence-based practices for optimal cardiac surgery recovery including activity progression, medication compliance, and lifestyle modifications.',
        category: 'clinical',
        specialty: 'cardiac',
        tags: JSON.stringify(['cardiac_surgery', 'recovery', 'best_practices', 'lifestyle']),
        authorId: users[1].id,
        published: true,
        readingLevel: 'high',
      },
    ]);

    // Seed System Settings
    console.log('⚙️ Creating system settings...');
    await db.insert(schema.systemSettings).values([
      {
        key: 'alert_escalation_threshold',
        value: JSON.stringify({ high: 7.0, medium: 4.0, low: 2.0 }),
        description: 'Risk score thresholds for automatic alert escalation',
        category: 'alerts',
        updatedBy: users[2].id,
      },
      {
        key: 'call_frequency_settings',
        value: JSON.stringify({ 
          high_risk: 'daily', 
          medium_risk: 'every_2_days', 
          low_risk: 'weekly' 
        }),
        description: 'Automated call frequency based on patient risk level',
        category: 'ai',
        updatedBy: users[2].id,
      },
      {
        key: 'twilio_configuration',
        value: JSON.stringify({ 
          account_sid: 'TWILIO_ACCOUNT_SID', 
          auth_token: 'TWILIO_AUTH_TOKEN',
          phone_number: '+1-555-VOICE-AI'
        }),
        description: 'Twilio API configuration for voice calls',
        category: 'twilio',
        updatedBy: users[2].id,
      },
    ]);

    console.log('✅ Database seeding completed successfully!');
    console.log(`📊 Created:`);
    console.log(`   - ${users.length} healthcare providers`);
    console.log(`   - ${patients.length} patients`);
    console.log(`   - ${surgeries.length} surgeries`);
    console.log(`   - ${voiceInteractions.length} voice interactions`);
    console.log(`   - 3 alerts`);
    console.log(`   - 3 knowledge articles`);
    console.log(`   - 3 system settings`);

  } catch (error) {
    console.error('❌ Error seeding database:', error);
    throw error;
  } finally {
    await pool.end();
  }
}

// Run the seeding if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  seedDatabase()
    .then(() => {
      console.log('🎉 Seeding completed!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Seeding failed:', error);
      process.exit(1);
    });
}
