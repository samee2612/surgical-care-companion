import {
  users,
  patients,
  surgeries,
  voiceInteractions,
  alerts,
  knowledgeArticles,
  systemSettings,
  testSimulations,
  type User,
  type UpsertUser,
  type Patient,
  type InsertPatient,
  type Surgery,
  type InsertSurgery,
  type VoiceInteraction,
  type InsertVoiceInteraction,
  type Alert,
  type InsertAlert,
  type KnowledgeArticle,
  type InsertKnowledgeArticle,
  type SystemSetting,
  type TestSimulation,
  type InsertTestSimulation,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, and, or, sql, count, ilike } from "drizzle-orm";

export interface IStorage {
  // User operations (required for Replit Auth)
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Patient operations
  getPatients(limit?: number, offset?: number, search?: string): Promise<Patient[]>;
  getPatient(id: number): Promise<Patient | undefined>;
  createPatient(patient: InsertPatient): Promise<Patient>;
  updatePatient(id: number, patient: Partial<InsertPatient>): Promise<Patient>;
  
  // Surgery operations
  getSurgeriesForPatient(patientId: number): Promise<Surgery[]>;
  createSurgery(surgery: InsertSurgery): Promise<Surgery>;
  
  // Voice Interaction operations
  getVoiceInteractionsForPatient(patientId: number, limit?: number): Promise<VoiceInteraction[]>;
  getRecentVoiceInteractions(limit?: number): Promise<VoiceInteraction[]>;
  createVoiceInteraction(interaction: InsertVoiceInteraction): Promise<VoiceInteraction>;
  
  // Alert operations
  getActiveAlerts(limit?: number): Promise<Alert[]>;
  getPriorityAlerts(priority: string, limit?: number): Promise<Alert[]>;
  getAlertsForPatient(patientId: number): Promise<Alert[]>;
  createAlert(alert: InsertAlert): Promise<Alert>;
  updateAlert(id: number, alert: Partial<InsertAlert>): Promise<Alert>;
  
  // Knowledge Base operations
  getKnowledgeArticles(category?: string, specialty?: string): Promise<KnowledgeArticle[]>;
  searchKnowledgeArticles(query: string): Promise<KnowledgeArticle[]>;
  createKnowledgeArticle(article: InsertKnowledgeArticle): Promise<KnowledgeArticle>;
  
  // System Settings operations
  getSystemSettings(category?: string): Promise<SystemSetting[]>;
  updateSystemSetting(key: string, value: any, updatedBy: string): Promise<SystemSetting>;
  
  // Test Simulation operations
  getTestSimulations(testerId?: string, limit?: number): Promise<TestSimulation[]>;
  createTestSimulation(simulation: InsertTestSimulation): Promise<TestSimulation>;
  
  // Dashboard statistics
  getDashboardStats(): Promise<{
    activePatients: number;
    readmissionRate: number;
    voiceInteractions: number;
    detectionAccuracy: number;
  }>;
}

export class DatabaseStorage implements IStorage {
  // User operations (required for Replit Auth)
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async upsertUser(userData: UpsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(userData)
      .onConflictDoUpdate({
        target: users.id,
        set: {
          ...userData,
          updatedAt: new Date(),
        },
      })
      .returning();
    return user;
  }

  // Patient operations
  async getPatients(limit = 50, offset = 0, search?: string): Promise<Patient[]> {
    let query = db.select().from(patients);
    
    if (search) {
      query = query.where(
        or(
          ilike(patients.firstName, `%${search}%`),
          ilike(patients.lastName, `%${search}%`),
          ilike(patients.mrn, `%${search}%`)
        )
      ) as any;
    }
    
    return await query.orderBy(desc(patients.updatedAt)).limit(limit).offset(offset);
  }

  async getPatient(id: number): Promise<Patient | undefined> {
    const [patient] = await db.select().from(patients).where(eq(patients.id, id));
    return patient;
  }

  async createPatient(patient: InsertPatient): Promise<Patient> {
    const [newPatient] = await db.insert(patients).values(patient).returning();
    return newPatient;
  }

  async updatePatient(id: number, patient: Partial<InsertPatient>): Promise<Patient> {
    const [updatedPatient] = await db
      .update(patients)
      .set({ ...patient, updatedAt: new Date() })
      .where(eq(patients.id, id))
      .returning();
    return updatedPatient;
  }

  // Surgery operations
  async getSurgeriesForPatient(patientId: number): Promise<Surgery[]> {
    return await db
      .select()
      .from(surgeries)
      .where(eq(surgeries.patientId, patientId))
      .orderBy(desc(surgeries.surgeryDate));
  }

  async createSurgery(surgery: InsertSurgery): Promise<Surgery> {
    const [newSurgery] = await db.insert(surgeries).values(surgery).returning();
    return newSurgery;
  }

  // Voice Interaction operations
  async getVoiceInteractionsForPatient(patientId: number, limit = 10): Promise<VoiceInteraction[]> {
    return await db
      .select()
      .from(voiceInteractions)
      .where(eq(voiceInteractions.patientId, patientId))
      .orderBy(desc(voiceInteractions.callDate))
      .limit(limit);
  }

  async getRecentVoiceInteractions(limit = 10): Promise<VoiceInteraction[]> {
    return await db
      .select()
      .from(voiceInteractions)
      .orderBy(desc(voiceInteractions.callDate))
      .limit(limit);
  }

  async createVoiceInteraction(interaction: InsertVoiceInteraction): Promise<VoiceInteraction> {
    const [newInteraction] = await db.insert(voiceInteractions).values(interaction).returning();
    return newInteraction;
  }

  // Alert operations
  async getActiveAlerts(limit = 20): Promise<Alert[]> {
    return await db
      .select()
      .from(alerts)
      .where(eq(alerts.status, "active"))
      .orderBy(desc(alerts.createdAt))
      .limit(limit);
  }

  async getPriorityAlerts(priority: string, limit = 10): Promise<Alert[]> {
    return await db
      .select()
      .from(alerts)
      .where(and(eq(alerts.priority, priority), eq(alerts.status, "active")))
      .orderBy(desc(alerts.createdAt))
      .limit(limit);
  }

  async getAlertsForPatient(patientId: number): Promise<Alert[]> {
    return await db
      .select()
      .from(alerts)
      .where(eq(alerts.patientId, patientId))
      .orderBy(desc(alerts.createdAt));
  }

  async createAlert(alert: InsertAlert): Promise<Alert> {
    const [newAlert] = await db.insert(alerts).values(alert).returning();
    return newAlert;
  }

  async updateAlert(id: number, alert: Partial<InsertAlert>): Promise<Alert> {
    const [updatedAlert] = await db
      .update(alerts)
      .set({ ...alert, updatedAt: new Date() })
      .where(eq(alerts.id, id))
      .returning();
    return updatedAlert;
  }

  // Knowledge Base operations
  async getKnowledgeArticles(category?: string, specialty?: string): Promise<KnowledgeArticle[]> {
    let query = db.select().from(knowledgeArticles).where(eq(knowledgeArticles.published, true));
    
    if (category) {
      query = query.where(eq(knowledgeArticles.category, category)) as any;
    }
    
    if (specialty) {
      query = query.where(eq(knowledgeArticles.specialty, specialty)) as any;
    }
    
    return await query.orderBy(desc(knowledgeArticles.updatedAt));
  }

  async searchKnowledgeArticles(query: string): Promise<KnowledgeArticle[]> {
    return await db
      .select()
      .from(knowledgeArticles)
      .where(
        and(
          eq(knowledgeArticles.published, true),
          or(
            ilike(knowledgeArticles.title, `%${query}%`),
            ilike(knowledgeArticles.content, `%${query}%`)
          )
        )
      )
      .orderBy(desc(knowledgeArticles.updatedAt));
  }

  async createKnowledgeArticle(article: InsertKnowledgeArticle): Promise<KnowledgeArticle> {
    const [newArticle] = await db.insert(knowledgeArticles).values(article).returning();
    return newArticle;
  }

  // System Settings operations
  async getSystemSettings(category?: string): Promise<SystemSetting[]> {
    let query = db.select().from(systemSettings);
    
    if (category) {
      query = query.where(eq(systemSettings.category, category)) as any;
    }
    
    return await query.orderBy(systemSettings.key);
  }

  async updateSystemSetting(key: string, value: any, updatedBy: string): Promise<SystemSetting> {
    const [setting] = await db
      .insert(systemSettings)
      .values({ key, value, updatedBy, updatedAt: new Date() })
      .onConflictDoUpdate({
        target: systemSettings.key,
        set: { value, updatedBy, updatedAt: new Date() },
      })
      .returning();
    return setting;
  }

  // Test Simulation operations
  async getTestSimulations(testerId?: string, limit = 20): Promise<TestSimulation[]> {
    let query = db.select().from(testSimulations);
    
    if (testerId) {
      query = query.where(eq(testSimulations.testerId, testerId)) as any;
    }
    
    return await query.orderBy(desc(testSimulations.createdAt)).limit(limit);
  }

  async createTestSimulation(simulation: InsertTestSimulation): Promise<TestSimulation> {
    const [newSimulation] = await db.insert(testSimulations).values(simulation).returning();
    return newSimulation;
  }

  // Dashboard statistics
  async getDashboardStats(): Promise<{
    activePatients: number;
    readmissionRate: number;
    voiceInteractions: number;
    detectionAccuracy: number;
  }> {
    // Active patients count
    const [{ count: activePatients }] = await db
      .select({ count: count() })
      .from(patients)
      .where(eq(patients.programActive, true));

    // Voice interactions count (last 7 days)
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    const [{ count: recentInteractions }] = await db
      .select({ count: count() })
      .from(voiceInteractions)
      .where(sql`${voiceInteractions.callDate} > ${weekAgo}`);

    // For now, return static values for readmission rate and detection accuracy
    // These would be calculated from actual data in a real implementation
    return {
      activePatients: activePatients || 0,
      readmissionRate: 8.2,
      voiceInteractions: recentInteractions || 0,
      detectionAccuracy: 94.7,
    };
  }
}

export const storage = new DatabaseStorage();
