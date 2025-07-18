import {
  pgTable,
  text,
  varchar,
  timestamp,
  jsonb,
  index,
  serial,
  integer,
  boolean,
  date,
  uuid,
} from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// Session storage table (required for Replit Auth)
export const sessions = pgTable(
  "sessions",
  {
    sid: varchar("sid").primaryKey(),
    sess: jsonb("sess").notNull(),
    expire: timestamp("expire").notNull(),
  },
  (table) => [index("IDX_session_expire").on(table.expire)],
);

// User storage table (required for Replit Auth)  
export const users = pgTable("users", {
  id: varchar("id").primaryKey().notNull(),
  email: varchar("email").unique(),
  firstName: varchar("first_name"),
  lastName: varchar("last_name"),
  profileImageUrl: varchar("profile_image_url"),
  role: varchar("role").notNull().default("provider"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Patients table - core entity
export const patients = pgTable("patients", {
  id: serial("id").primaryKey(),
  mrn: varchar("mrn").unique(),
  firstName: varchar("first_name").notNull(),
  lastName: varchar("last_name").notNull(),
  dateOfBirth: date("date_of_birth"),
  phone: varchar("phone"),
  email: varchar("email"),
  address: text("address"),
  emergencyContactName: varchar("emergency_contact_name"),
  emergencyContactPhone: varchar("emergency_contact_phone"),
  emergencyContactRelationship: varchar("emergency_contact_relationship"),
  medicalHistory: text("medical_history"),
  currentMedications: text("current_medications"),
  allergies: text("allergies"),
  insuranceInfo: text("insurance_info"),
  preferredLanguage: varchar("preferred_language").default("en"),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Surgeries table
export const surgeries = pgTable("surgeries", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => patients.id).notNull(),
  procedure: varchar("procedure", { length: 255 }).notNull(),
  surgeonName: varchar("surgeon_name", { length: 255 }).notNull(),
  surgeryDate: date("surgery_date").notNull(),
  dischargeDate: date("discharge_date"),
  expectedRecoveryWeeks: integer("expected_recovery_weeks"),
  specialty: varchar("specialty", { length: 100 }).notNull(),
  notes: text("notes"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Voice Interactions table - for TwiML calls
export const voiceInteractions = pgTable("voice_interactions", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => patients.id).notNull(),
  surgeryId: integer("surgery_id").references(() => surgeries.id).notNull(),
  callDate: timestamp("call_date").notNull(),
  callDuration: integer("call_duration"), // in seconds
  callSid: varchar("call_sid", { length: 255 }).unique(),
  phoneNumber: varchar("phone_number", { length: 20 }),
  callDirection: varchar("call_direction", { length: 20 }),
  callStatus: varchar("call_status", { length: 20 }),
  transcript: text("transcript"),
  intentExtraction: jsonb("intent_extraction"),
  sentimentAnalysis: jsonb("sentiment_analysis"),
  painLevel: integer("pain_level"),
  concerns: text("concerns"),
  followUpRequired: boolean("follow_up_required").default(false),
  followUpNotes: text("follow_up_notes"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Clinical Staff table
export const clinicalStaff = pgTable("clinical_staff", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: varchar("user_id", { length: 255 }),
  name: varchar("name", { length: 255 }).notNull(),
  email: varchar("email", { length: 255 }).notNull().unique(),
  role: varchar("role", { length: 50 }).notNull(),
  specialty: varchar("specialty", { length: 100 }),
  phone: varchar("phone", { length: 20 }),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Simple relationships
export const patientsRelations = relations(patients, ({ many }) => ({
  surgeries: many(surgeries),
  voiceInteractions: many(voiceInteractions),
}));

export const surgeriesRelations = relations(surgeries, ({ one, many }) => ({
  patient: one(patients, {
    fields: [surgeries.patientId],
    references: [patients.id],
  }),
  voiceInteractions: many(voiceInteractions),
}));

export const voiceInteractionsRelations = relations(voiceInteractions, ({ one }) => ({
  patient: one(patients, {
    fields: [voiceInteractions.patientId],
    references: [patients.id],
  }),
  surgery: one(surgeries, {
    fields: [voiceInteractions.surgeryId],
    references: [surgeries.id],
  }),
}));

export const clinicalStaffRelations = relations(clinicalStaff, ({ one }) => ({
  user: one(users, {
    fields: [clinicalStaff.userId],
    references: [users.id],
  }),
}));

export const usersRelations = relations(users, ({ one }) => ({
  clinicalStaff: one(clinicalStaff, {
    fields: [users.id],
    references: [clinicalStaff.userId],
  }),
}));

// Export Zod schemas for validation
export const insertPatientSchema = createInsertSchema(patients);
export const insertSurgerySchema = createInsertSchema(surgeries);
export const insertVoiceInteractionSchema = createInsertSchema(voiceInteractions);
export const insertClinicalStaffSchema = createInsertSchema(clinicalStaff);
export const insertUserSchema = createInsertSchema(users);
export const insertSessionSchema = createInsertSchema(sessions);

// Export types
export type Patient = typeof patients.$inferSelect;
export type Surgery = typeof surgeries.$inferSelect;
export type VoiceInteraction = typeof voiceInteractions.$inferSelect;
export type ClinicalStaff = typeof clinicalStaff.$inferSelect;
export type User = typeof users.$inferSelect;
export type Session = typeof sessions.$inferSelect;

export type NewPatient = typeof patients.$inferInsert;
export type NewSurgery = typeof surgeries.$inferInsert;
export type NewVoiceInteraction = typeof voiceInteractions.$inferInsert;
export type NewClinicalStaff = typeof clinicalStaff.$inferInsert;
export type NewUser = typeof users.$inferInsert;
export type NewSession = typeof sessions.$inferInsert;

// Legacy aliases for compatibility
export type InsertPatient = NewPatient;
export type InsertSurgery = NewSurgery;
export type InsertVoiceInteraction = NewVoiceInteraction;
export type InsertClinicalStaff = NewClinicalStaff;
export type UpsertUser = NewUser;
