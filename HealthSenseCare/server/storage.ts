import {
  users,
  patients,
  surgeries,
  voiceInteractions,
  clinicalStaff,
  sessions,
  type User,
  type NewUser,
  type UpsertUser,
  type Patient,
  type NewPatient,
  type InsertPatient,
  type Surgery,
  type NewSurgery,
  type InsertSurgery,
  type VoiceInteraction,
  type NewVoiceInteraction,
  type InsertVoiceInteraction,
  type ClinicalStaff,
  type NewClinicalStaff,
  type InsertClinicalStaff,
  type Session,
  type NewSession,
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
  
  // Clinical Staff operations
  getClinicalStaff(): Promise<ClinicalStaff[]>;
  getClinicalStaffById(id: string): Promise<ClinicalStaff | undefined>;
  createClinicalStaff(staff: InsertClinicalStaff): Promise<ClinicalStaff>;
  
  // Dashboard statistics
  getDashboardStats(): Promise<{
    totalPatients: number;
    totalSurgeries: number;
    recentCalls: number;
    activeCases: number;
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
      );
    }
    
    return await query.orderBy(desc(patients.createdAt)).limit(limit).offset(offset);
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

  // Clinical Staff operations
  async getClinicalStaff(): Promise<ClinicalStaff[]> {
    return await db
      .select()
      .from(clinicalStaff)
      .where(eq(clinicalStaff.isActive, true))
      .orderBy(desc(clinicalStaff.createdAt));
  }

  async getClinicalStaffById(id: string): Promise<ClinicalStaff | undefined> {
    const [staff] = await db.select().from(clinicalStaff).where(eq(clinicalStaff.id, id));
    return staff;
  }

  async createClinicalStaff(staff: InsertClinicalStaff): Promise<ClinicalStaff> {
    const [newStaff] = await db.insert(clinicalStaff).values(staff).returning();
    return newStaff;
  }

  // Dashboard statistics
  async getDashboardStats(): Promise<{
    totalPatients: number;
    totalSurgeries: number;
    recentCalls: number;
    activeCases: number;
  }> {
    const [patientCount] = await db.select({ count: count() }).from(patients);
    const [surgeryCount] = await db.select({ count: count() }).from(surgeries);
    const [callCount] = await db.select({ count: count() }).from(voiceInteractions);
    const [activeCount] = await db.select({ count: count() }).from(patients).where(eq(patients.isActive, true));

    return {
      totalPatients: patientCount.count,
      totalSurgeries: surgeryCount.count,
      recentCalls: callCount.count,
      activeCases: activeCount.count,
    };
  }
}

export const storage = new DatabaseStorage();
