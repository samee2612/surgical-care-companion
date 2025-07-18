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
  decimal,
  date,
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
  role: varchar("role").notNull().default("provider"), // provider, admin, patient
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Patients table
export const patients = pgTable("patients", {
  id: serial("id").primaryKey(),
  mrn: varchar("mrn").notNull().unique(),
  firstName: varchar("first_name").notNull(),
  lastName: varchar("last_name").notNull(),
  dateOfBirth: date("date_of_birth").notNull(),
  phone: varchar("phone"),
  email: varchar("email"),
  emergencyContactName: varchar("emergency_contact_name"),
  emergencyContactPhone: varchar("emergency_contact_phone"),
  voiceConsentGiven: boolean("voice_consent_given").default(false),
  dataConsentGiven: boolean("data_consent_given").default(false),
  programActive: boolean("program_active").default(true),
  enrollmentDate: timestamp("enrollment_date").defaultNow(),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Surgeries table
export const surgeries = pgTable("surgeries", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => patients.id).notNull(),
  procedure: varchar("procedure").notNull(),
  surgeonName: varchar("surgeon_name").notNull(),
  surgeryDate: date("surgery_date").notNull(),
  dischargeDate: date("discharge_date"),
  expectedRecoveryWeeks: integer("expected_recovery_weeks"),
  specialty: varchar("specialty").notNull(), // orthopedic, cardiac, general, neuro
  notes: text("notes"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Voice Interactions table
export const voiceInteractions = pgTable("voice_interactions", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => patients.id).notNull(),
  surgeryId: integer("surgery_id").references(() => surgeries.id).notNull(),
  callDate: timestamp("call_date").notNull(),
  duration: integer("duration"), // in seconds
  transcript: text("transcript"),
  symptoms: jsonb("symptoms"), // array of detected symptoms
  painLevel: integer("pain_level"), // 1-10 scale
  riskScore: decimal("risk_score", { precision: 5, scale: 2 }),
  status: varchar("status").notNull(), // completed, failed, escalated, normal
  escalated: boolean("escalated").default(false),
  escalationReason: text("escalation_reason"),
  aiAnalysis: jsonb("ai_analysis"),
  callSuccessful: boolean("call_successful").default(true),
  createdAt: timestamp("created_at").defaultNow(),
});

// Alerts table
export const alerts = pgTable("alerts", {
  id: serial("id").primaryKey(),
  patientId: integer("patient_id").references(() => patients.id).notNull(),
  voiceInteractionId: integer("voice_interaction_id").references(() => voiceInteractions.id),
  priority: varchar("priority").notNull(), // high, medium, low
  status: varchar("status").notNull().default("active"), // active, resolved, dismissed
  title: varchar("title").notNull(),
  description: text("description"),
  riskScore: decimal("risk_score", { precision: 5, scale: 2 }),
  assignedProviderId: varchar("assigned_provider_id").references(() => users.id),
  resolvedAt: timestamp("resolved_at"),
  resolvedBy: varchar("resolved_by").references(() => users.id),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Knowledge Base Articles table
export const knowledgeArticles = pgTable("knowledge_articles", {
  id: serial("id").primaryKey(),
  title: varchar("title").notNull(),
  content: text("content").notNull(),
  category: varchar("category").notNull(), // clinical, patient-education, technical, faq, ai-models
  specialty: varchar("specialty"), // orthopedic, cardiac, general, neuro
  tags: jsonb("tags"), // array of tags
  authorId: varchar("author_id").references(() => users.id),
  published: boolean("published").default(false),
  readingLevel: varchar("reading_level"), // elementary, middle, high
  language: varchar("language").default("en"),
  version: varchar("version").default("1.0"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// System Settings table
export const systemSettings = pgTable("system_settings", {
  id: serial("id").primaryKey(),
  key: varchar("key").notNull().unique(),
  value: jsonb("value"),
  description: text("description"),
  category: varchar("category").notNull(), // alerts, twilio, billing, ai
  updatedBy: varchar("updated_by").references(() => users.id),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Test Simulations table
export const testSimulations = pgTable("test_simulations", {
  id: serial("id").primaryKey(),
  testerId: varchar("tester_id").references(() => users.id).notNull(),
  patientProfile: varchar("patient_profile").notNull(),
  injectedSymptoms: jsonb("injected_symptoms"),
  customSymptoms: text("custom_symptoms"),
  resultingRiskScore: decimal("resulting_risk_score", { precision: 5, scale: 2 }),
  aiDecision: varchar("ai_decision").notNull(),
  transcript: text("transcript"),
  detectedSymptoms: jsonb("detected_symptoms"),
  escalationTriggered: boolean("escalation_triggered").default(false),
  createdAt: timestamp("created_at").defaultNow(),
});

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  assignedAlerts: many(alerts, { relationName: "assignedProvider" }),
  resolvedAlerts: many(alerts, { relationName: "resolvedBy" }),
  knowledgeArticles: many(knowledgeArticles),
  testSimulations: many(testSimulations),
}));

export const patientsRelations = relations(patients, ({ many }) => ({
  surgeries: many(surgeries),
  voiceInteractions: many(voiceInteractions),
  alerts: many(alerts),
}));

export const surgeriesRelations = relations(surgeries, ({ one, many }) => ({
  patient: one(patients, {
    fields: [surgeries.patientId],
    references: [patients.id],
  }),
  voiceInteractions: many(voiceInteractions),
}));

export const voiceInteractionsRelations = relations(voiceInteractions, ({ one, many }) => ({
  patient: one(patients, {
    fields: [voiceInteractions.patientId],
    references: [patients.id],
  }),
  surgery: one(surgeries, {
    fields: [voiceInteractions.surgeryId],
    references: [surgeries.id],
  }),
  alerts: many(alerts),
}));

export const alertsRelations = relations(alerts, ({ one }) => ({
  patient: one(patients, {
    fields: [alerts.patientId],
    references: [patients.id],
  }),
  voiceInteraction: one(voiceInteractions, {
    fields: [alerts.voiceInteractionId],
    references: [voiceInteractions.id],
  }),
  assignedProvider: one(users, {
    fields: [alerts.assignedProviderId],
    references: [users.id],
    relationName: "assignedProvider",
  }),
  resolvedByUser: one(users, {
    fields: [alerts.resolvedBy],
    references: [users.id],
    relationName: "resolvedBy",
  }),
}));

// Insert schemas
export const insertUserSchema = createInsertSchema(users).omit({
  createdAt: true,
  updatedAt: true,
});

export const insertPatientSchema = createInsertSchema(patients).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertSurgerySchema = createInsertSchema(surgeries).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertVoiceInteractionSchema = createInsertSchema(voiceInteractions).omit({
  id: true,
  createdAt: true,
});

export const insertAlertSchema = createInsertSchema(alerts).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertKnowledgeArticleSchema = createInsertSchema(knowledgeArticles).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertTestSimulationSchema = createInsertSchema(testSimulations).omit({
  id: true,
  createdAt: true,
});

// Types
export type UpsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Patient = typeof patients.$inferSelect;
export type InsertPatient = z.infer<typeof insertPatientSchema>;
export type Surgery = typeof surgeries.$inferSelect;
export type InsertSurgery = z.infer<typeof insertSurgerySchema>;
export type VoiceInteraction = typeof voiceInteractions.$inferSelect;
export type InsertVoiceInteraction = z.infer<typeof insertVoiceInteractionSchema>;
export type Alert = typeof alerts.$inferSelect;
export type InsertAlert = z.infer<typeof insertAlertSchema>;
export type KnowledgeArticle = typeof knowledgeArticles.$inferSelect;
export type InsertKnowledgeArticle = z.infer<typeof insertKnowledgeArticleSchema>;
export type SystemSetting = typeof systemSettings.$inferSelect;
export type TestSimulation = typeof testSimulations.$inferSelect;
export type InsertTestSimulation = z.infer<typeof insertTestSimulationSchema>;
