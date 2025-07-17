import { useQuery } from "@tanstack/react-query";
import { Users, TrendingDown, Mic, Target } from "lucide-react";
import { StatCard } from "@/components/dashboard/StatCard";
import { AlertBanner } from "@/components/dashboard/AlertBanner";
import { PriorityAlerts } from "@/components/dashboard/PriorityAlerts";
import { RecentInteractions } from "@/components/dashboard/RecentInteractions";
import { PatientTable } from "@/components/dashboard/PatientTable";

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["/api/dashboard/stats"],
  });

  const { data: priorityAlerts = [] } = useQuery({
    queryKey: ["/api/dashboard/priority-alerts"],
  });

  const highPriorityCount = priorityAlerts.filter((alert: any) => alert.priority === "high").length;

  return (
    <div className="p-6 space-y-8">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Provider Dashboard</h1>
        <p className="text-medical-gray">Monitor post-surgical patients and voice agent interactions</p>
      </div>

      {/* Alert Banner */}
      {highPriorityCount > 0 && (
        <AlertBanner
          count={highPriorityCount}
          description="High-risk symptoms detected in recent voice check-ins"
          onViewDetails={() => {}}
        />
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Patients"
          value={statsLoading ? "..." : stats?.activePatients || 0}
          change="+12.5%"
          changeType="positive"
          icon={Users}
          iconColor="text-medical-blue"
        />
        <StatCard
          title="30-Day Readmissions"
          value={statsLoading ? "..." : `${stats?.readmissionRate || 0}%`}
          change="-2.1%"
          changeType="positive"
          icon={TrendingDown}
          iconColor="text-red-600"
        />
        <StatCard
          title="Voice Interactions"
          value={statsLoading ? "..." : stats?.voiceInteractions || 0}
          change="+18.2%"
          changeType="positive"
          icon={Mic}
          iconColor="text-medical-green"
        />
        <StatCard
          title="Detection Accuracy"
          value={statsLoading ? "..." : `${stats?.detectionAccuracy || 0}%`}
          change="+1.3%"
          changeType="positive"
          icon={Target}
          iconColor="text-medical-green"
        />
      </div>

      {/* Main Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <PriorityAlerts />
        <RecentInteractions />
      </div>

      {/* Patient Management Table */}
      <PatientTable />
    </div>
  );
}
