import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { z } from "zod";
import {
  insertPatientSchema,
  insertSurgerySchema,
  insertVoiceInteractionSchema,
  insertAlertSchema,
  insertKnowledgeArticleSchema,
  insertTestSimulationSchema,
} from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // Development auth bypass
  const devAuthMiddleware = (req: any, res: any, next: any) => {
    if (process.env.DISABLE_AUTH === 'true') {
      req.user = { 
        claims: { sub: 'dev-user-123' },
        email: 'dev@example.com',
        firstName: 'Dev',
        lastName: 'User'
      };
    }
    next();
  };

  // Helper function to choose auth middleware
  const authMiddleware = process.env.DISABLE_AUTH === 'true' ? devAuthMiddleware : isAuthenticated;

  // Auth middleware
  if (process.env.DISABLE_AUTH !== 'true') {
    await setupAuth(app);
  } else {
    app.use(devAuthMiddleware);
  }

  // Auth routes
  app.get('/api/auth/user', authMiddleware, async (req: any, res) => {
    try {
      if (process.env.DISABLE_AUTH === 'true') {
        // Return mock user for development
        res.json({
          id: 'dev-user-123',
          email: 'dev@example.com',
          firstName: 'Dev',
          lastName: 'User',
          profileImageUrl: null
        });
        return;
      }
      
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // Dashboard routes
  app.get('/api/dashboard/stats', authMiddleware, async (req, res) => {
    try {
      const stats = await storage.getDashboardStats();
      res.json(stats);
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
      res.status(500).json({ message: "Failed to fetch dashboard statistics" });
    }
  });

  app.get('/api/dashboard/priority-alerts', isAuthenticated, async (req, res) => {
    try {
      const alerts = await storage.getPriorityAlerts('high', 10);
      res.json(alerts);
    } catch (error) {
      console.error("Error fetching priority alerts:", error);
      res.status(500).json({ message: "Failed to fetch priority alerts" });
    }
  });

  app.get('/api/dashboard/recent-interactions', isAuthenticated, async (req, res) => {
    try {
      const interactions = await storage.getRecentVoiceInteractions(10);
      res.json(interactions);
    } catch (error) {
      console.error("Error fetching recent interactions:", error);
      res.status(500).json({ message: "Failed to fetch recent interactions" });
    }
  });

  // Patient routes
  app.get('/api/patients', isAuthenticated, async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const offset = parseInt(req.query.offset as string) || 0;
      const search = req.query.search as string;
      
      const patients = await storage.getPatients(limit, offset, search);
      res.json(patients);
    } catch (error) {
      console.error("Error fetching patients:", error);
      res.status(500).json({ message: "Failed to fetch patients" });
    }
  });

  app.get('/api/patients/:id', isAuthenticated, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const patient = await storage.getPatient(id);
      
      if (!patient) {
        return res.status(404).json({ message: "Patient not found" });
      }
      
      res.json(patient);
    } catch (error) {
      console.error("Error fetching patient:", error);
      res.status(500).json({ message: "Failed to fetch patient" });
    }
  });

  app.post('/api/patients', isAuthenticated, async (req, res) => {
    try {
      const patientData = insertPatientSchema.parse(req.body);
      const patient = await storage.createPatient(patientData);
      res.status(201).json(patient);
    } catch (error) {
      console.error("Error creating patient:", error);
      res.status(400).json({ message: "Invalid patient data" });
    }
  });

  app.put('/api/patients/:id', isAuthenticated, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const updateData = insertPatientSchema.partial().parse(req.body);
      const patient = await storage.updatePatient(id, updateData);
      res.json(patient);
    } catch (error) {
      console.error("Error updating patient:", error);
      res.status(400).json({ message: "Invalid patient data" });
    }
  });

  // Surgery routes
  app.get('/api/patients/:id/surgeries', isAuthenticated, async (req, res) => {
    try {
      const patientId = parseInt(req.params.id);
      const surgeries = await storage.getSurgeriesForPatient(patientId);
      res.json(surgeries);
    } catch (error) {
      console.error("Error fetching surgeries:", error);
      res.status(500).json({ message: "Failed to fetch surgeries" });
    }
  });

  app.post('/api/surgeries', isAuthenticated, async (req, res) => {
    try {
      const surgeryData = insertSurgerySchema.parse(req.body);
      const surgery = await storage.createSurgery(surgeryData);
      res.status(201).json(surgery);
    } catch (error) {
      console.error("Error creating surgery:", error);
      res.status(400).json({ message: "Invalid surgery data" });
    }
  });

  // Voice Interaction routes
  app.get('/api/patients/:id/voice-interactions', isAuthenticated, async (req, res) => {
    try {
      const patientId = parseInt(req.params.id);
      const limit = parseInt(req.query.limit as string) || 10;
      const interactions = await storage.getVoiceInteractionsForPatient(patientId, limit);
      res.json(interactions);
    } catch (error) {
      console.error("Error fetching voice interactions:", error);
      res.status(500).json({ message: "Failed to fetch voice interactions" });
    }
  });

  app.post('/api/voice-interactions', isAuthenticated, async (req, res) => {
    try {
      const interactionData = insertVoiceInteractionSchema.parse(req.body);
      const interaction = await storage.createVoiceInteraction(interactionData);
      res.status(201).json(interaction);
    } catch (error) {
      console.error("Error creating voice interaction:", error);
      res.status(400).json({ message: "Invalid voice interaction data" });
    }
  });

  // Alert routes
  app.get('/api/alerts', isAuthenticated, async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 20;
      const alerts = await storage.getActiveAlerts(limit);
      res.json(alerts);
    } catch (error) {
      console.error("Error fetching alerts:", error);
      res.status(500).json({ message: "Failed to fetch alerts" });
    }
  });

  app.get('/api/patients/:id/alerts', isAuthenticated, async (req, res) => {
    try {
      const patientId = parseInt(req.params.id);
      const alerts = await storage.getAlertsForPatient(patientId);
      res.json(alerts);
    } catch (error) {
      console.error("Error fetching patient alerts:", error);
      res.status(500).json({ message: "Failed to fetch patient alerts" });
    }
  });

  app.post('/api/alerts', isAuthenticated, async (req, res) => {
    try {
      const alertData = insertAlertSchema.parse(req.body);
      const alert = await storage.createAlert(alertData);
      res.status(201).json(alert);
    } catch (error) {
      console.error("Error creating alert:", error);
      res.status(400).json({ message: "Invalid alert data" });
    }
  });

  app.put('/api/alerts/:id', isAuthenticated, async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const updateData = insertAlertSchema.partial().parse(req.body);
      const alert = await storage.updateAlert(id, updateData);
      res.json(alert);
    } catch (error) {
      console.error("Error updating alert:", error);
      res.status(400).json({ message: "Invalid alert data" });
    }
  });

  // Knowledge Base routes
  app.get('/api/knowledge', isAuthenticated, async (req, res) => {
    try {
      const category = req.query.category as string;
      const specialty = req.query.specialty as string;
      const articles = await storage.getKnowledgeArticles(category, specialty);
      res.json(articles);
    } catch (error) {
      console.error("Error fetching knowledge articles:", error);
      res.status(500).json({ message: "Failed to fetch knowledge articles" });
    }
  });

  app.get('/api/knowledge/search', isAuthenticated, async (req, res) => {
    try {
      const query = req.query.q as string;
      if (!query) {
        return res.status(400).json({ message: "Search query is required" });
      }
      const articles = await storage.searchKnowledgeArticles(query);
      res.json(articles);
    } catch (error) {
      console.error("Error searching knowledge articles:", error);
      res.status(500).json({ message: "Failed to search knowledge articles" });
    }
  });

  app.post('/api/knowledge', isAuthenticated, async (req, res) => {
    try {
      const articleData = insertKnowledgeArticleSchema.parse(req.body);
      const article = await storage.createKnowledgeArticle(articleData);
      res.status(201).json(article);
    } catch (error) {
      console.error("Error creating knowledge article:", error);
      res.status(400).json({ message: "Invalid knowledge article data" });
    }
  });

  // Test Simulation routes
  app.get('/api/test-simulations', isAuthenticated, async (req, res) => {
    try {
      const testerId = req.query.testerId as string;
      const limit = parseInt(req.query.limit as string) || 20;
      const simulations = await storage.getTestSimulations(testerId, limit);
      res.json(simulations);
    } catch (error) {
      console.error("Error fetching test simulations:", error);
      res.status(500).json({ message: "Failed to fetch test simulations" });
    }
  });

  app.post('/api/test-simulations', isAuthenticated, async (req, res) => {
    try {
      const simulationData = insertTestSimulationSchema.parse(req.body);
      const simulation = await storage.createTestSimulation(simulationData);
      res.status(201).json(simulation);
    } catch (error) {
      console.error("Error creating test simulation:", error);
      res.status(400).json({ message: "Invalid test simulation data" });
    }
  });

  // System Settings routes
  app.get('/api/settings', isAuthenticated, async (req, res) => {
    try {
      const category = req.query.category as string;
      const settings = await storage.getSystemSettings(category);
      res.json(settings);
    } catch (error) {
      console.error("Error fetching system settings:", error);
      res.status(500).json({ message: "Failed to fetch system settings" });
    }
  });

  app.put('/api/settings/:key', isAuthenticated, async (req, res) => {
    try {
      const key = req.params.key;
      const { value } = req.body;
      const userId = req.user?.claims?.sub;
      
      if (!userId) {
        return res.status(401).json({ message: "User not authenticated" });
      }
      
      const setting = await storage.updateSystemSetting(key, value, userId);
      res.json(setting);
    } catch (error) {
      console.error("Error updating system setting:", error);
      res.status(400).json({ message: "Invalid setting data" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
