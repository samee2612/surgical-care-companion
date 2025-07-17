# HealthSense24 Surgical Care Voice Agent System

## Overview

HealthSense24 is a comprehensive web application designed to support surgical care teams and patients through a voice-enabled platform. The system provides post-surgical patient monitoring via automated voice check-ins, risk assessment, and real-time alert management for healthcare providers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modern full-stack architecture with clear separation between client and server components:

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for development and building
- **Routing**: Wouter for client-side routing
- **State Management**: TanStack Query (React Query) for server state management
- **UI Framework**: Shadcn/ui components built on Radix UI primitives
- **Styling**: Tailwind CSS with custom medical-themed color variables
- **Form Handling**: React Hook Form with Zod validation

### Backend Architecture
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js for REST API
- **Database ORM**: Drizzle ORM with PostgreSQL dialect
- **Database Provider**: Neon Database (serverless PostgreSQL)
- **Authentication**: Replit Auth with OpenID Connect
- **Session Management**: Express sessions with PostgreSQL session store

## Key Components

### 1. Authentication & User Management
- **Implementation**: Replit Auth integration with OIDC
- **Session Storage**: PostgreSQL-backed sessions with connect-pg-simple
- **User Roles**: Provider, Administrator, Patient with role-based access control
- **Security**: HIPAA-compliant design with secure session handling

### 2. Database Schema
- **Users**: Core user management with role-based access
- **Patients**: Comprehensive patient profiles with medical record numbers
- **Surgeries**: Surgery tracking with procedure details and recovery protocols
- **Voice Interactions**: Call logs with transcripts, risk scores, and status tracking
- **Alerts**: Priority-based alert system for patient monitoring
- **Knowledge Articles**: Clinical guidelines and patient education content
- **System Settings**: Configurable application parameters

### 3. Voice Integration System
- **Provider**: Twilio for voice communication
- **Features**: Automated voice check-ins, symptom detection, risk scoring
- **Monitoring**: Call success tracking, transcript analysis, escalation protocols

### 4. Dashboard & Monitoring
- **Provider Dashboard**: Real-time patient monitoring, alert management, statistics
- **Patient Management**: Comprehensive patient profiles, surgery history, interaction logs
- **Voice Reports**: Detailed interaction analysis with filtering and export capabilities
- **Testing Interface**: Sandbox environment for voice agent simulation

### 5. Knowledge Management
- **Clinical Guidelines**: Specialty-specific protocols and procedures
- **Patient Education**: Recovery information and care instructions
- **Technical Documentation**: System administration and API documentation

## Data Flow

1. **Patient Enrollment**: Patients are registered with demographic and surgical details
2. **Voice Check-ins**: Automated calls collect symptom data and patient responses
3. **Risk Assessment**: AI-powered analysis generates risk scores and flags concerning symptoms
4. **Alert Generation**: High-risk situations trigger immediate alerts to care teams
5. **Provider Response**: Healthcare teams review alerts and take appropriate action
6. **Knowledge Integration**: Clinical guidelines inform risk thresholds and protocols

## External Dependencies

### Core Dependencies
- **@neondatabase/serverless**: PostgreSQL database connectivity
- **drizzle-orm**: Database ORM and query builder
- **express**: Web server framework
- **@tanstack/react-query**: Client-side data fetching and caching
- **react-hook-form**: Form state management and validation
- **zod**: Schema validation

### UI Dependencies
- **@radix-ui/react-***: Accessible UI component primitives
- **tailwindcss**: Utility-first CSS framework
- **class-variance-authority**: Component variant management
- **cmdk**: Command palette and search functionality

### Authentication & Security
- **openid-client**: OIDC authentication
- **passport**: Authentication middleware
- **express-session**: Session management
- **connect-pg-simple**: PostgreSQL session storage

## Deployment Strategy

### Development Environment
- **Hot Reload**: Vite development server with React Fast Refresh
- **Database**: Neon serverless PostgreSQL with connection pooling
- **Environment Variables**: DATABASE_URL, SESSION_SECRET, REPLIT_DOMAINS
- **Development Tools**: TypeScript checking, ESBuild bundling

### Production Build
- **Frontend**: Vite build to static assets in dist/public
- **Backend**: ESBuild bundle for Node.js deployment
- **Database Migrations**: Drizzle Kit for schema management
- **Session Storage**: PostgreSQL sessions table for scalability

### Key Architectural Decisions

1. **Serverless Database**: Chosen Neon for automatic scaling and reduced operational overhead
2. **Monorepo Structure**: Shared schema and types between client/server for type safety
3. **Component Library**: Shadcn/ui for consistent, accessible UI components
4. **Authentication Strategy**: Replit Auth for simplified user management in development
5. **Real-time Monitoring**: React Query for automatic data synchronization and caching
6. **Medical Compliance**: HIPAA-focused design with secure data handling practices

The system prioritizes security, scalability, and user experience while maintaining compliance with healthcare data protection requirements. The modular architecture allows for easy extension of voice capabilities and integration with additional healthcare systems.