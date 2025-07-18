import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/useAuth";
import { Layout } from "@/components/layout/Layout";
import NotFound from "@/pages/not-found";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import Patients from "@/pages/Patients";
import PatientDetail from "@/pages/PatientDetail";
import VoiceReports from "@/pages/VoiceReports";
import Testing from "@/pages/Testing";
import Knowledge from "@/pages/Knowledge";
import Integration from "@/pages/Integration";
import Settings from "@/pages/Settings";
import PatientsTest from "@/components/PatientsTest";

function Router() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-medical-light">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-medical-blue mx-auto mb-4"></div>
          <p className="text-medical-gray">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Switch>
      {!isAuthenticated ? (
        <Route path="/" component={Landing} />
      ) : (
        <>
          <Route path="/">
            <Layout>
              <Dashboard />
            </Layout>
          </Route>
          <Route path="/patients">
            <Layout>
              <Patients />
            </Layout>
          </Route>
          <Route path="/patients-test">
            <Layout>
              <PatientsTest />
            </Layout>
          </Route>
          <Route path="/patients/:id">
            {(params) => (
              <Layout>
                <PatientDetail patientId={parseInt(params.id)} />
              </Layout>
            )}
          </Route>
          <Route path="/voice-reports">
            <Layout>
              <VoiceReports />
            </Layout>
          </Route>
          <Route path="/testing">
            <Layout>
              <Testing />
            </Layout>
          </Route>
          <Route path="/knowledge">
            <Layout>
              <Knowledge />
            </Layout>
          </Route>
          <Route path="/integration">
            <Layout>
              <Integration />
            </Layout>
          </Route>
          <Route path="/settings">
            <Layout>
              <Settings />
            </Layout>
          </Route>
        </>
      )}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
