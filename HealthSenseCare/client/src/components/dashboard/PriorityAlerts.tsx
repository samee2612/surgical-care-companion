import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Alert {
  id: number;
  patientId: number;
  priority: string;
  title: string;
  description: string;
  riskScore: number;
  createdAt: string;
}

export function PriorityAlerts() {
  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ["/api/dashboard/priority-alerts"],
  });

  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return "bg-red-100 text-red-800";
    if (score >= 60) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const getPriorityIcon = (priority: string) => {
    return priority === "high" ? (
      <AlertTriangle className="h-4 w-4 text-red-600" />
    ) : (
      <CheckCircle className="h-4 w-4 text-yellow-600" />
    );
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  if (isLoading) {
    return (
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>High Priority Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse p-4 bg-gray-50 rounded-lg">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>High Priority Alerts</CardTitle>
        <Button variant="link" className="text-medical-blue">
          View All
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-sm text-gray-500">No high priority alerts at this time</p>
            </div>
          ) : (
            alerts.map((alert: Alert) => (
              <div
                key={alert.id}
                className={`flex items-start space-x-4 p-4 rounded-lg border ${
                  alert.priority === "high" 
                    ? "bg-red-50 border-red-200" 
                    : "bg-yellow-50 border-yellow-200"
                }`}
              >
                <div className="w-10 h-10 bg-opacity-20 rounded-full flex items-center justify-center flex-shrink-0">
                  {getPriorityIcon(alert.priority)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">{alert.title}</p>
                  <p className={`text-sm ${
                    alert.priority === "high" ? "text-red-700" : "text-yellow-700"
                  }`}>
                    Patient ID: {alert.patientId}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  <div className="flex items-center mt-2 space-x-4">
                    <Badge className={getRiskScoreColor(alert.riskScore)}>
                      Risk Score: {alert.riskScore}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {getTimeAgo(alert.createdAt)}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button size="sm" className="bg-medical-blue hover:bg-medical-blue-dark">
                    Contact
                  </Button>
                  <Button size="sm" variant="outline">
                    View
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
