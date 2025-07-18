import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface VoiceInteraction {
  id: number;
  patientId: number;
  callDate: string;
  status: string;
  callSuccessful: boolean;
}

export function RecentInteractions() {
  const { data: interactions = [], isLoading } = useQuery({
    queryKey: ["/api/dashboard/recent-interactions"],
  });

  const getStatusColor = (status: string, callSuccessful: boolean) => {
    if (!callSuccessful) return "bg-red-500";
    if (status === "escalated") return "bg-red-500";
    if (status === "normal") return "bg-medical-green";
    return "bg-yellow-500";
  };

  const getStatusText = (status: string, callSuccessful: boolean) => {
    if (!callSuccessful) return "Call failed • Patient unreachable";
    if (status === "escalated") return "Escalated • High priority";
    if (status === "normal") return "Check-in completed • Normal recovery";
    return "Moderate concern • Follow-up needed";
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    return `${Math.floor(diffInMinutes / 60)}h ago`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Voice Interactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse flex items-center space-x-3">
                <div className="w-2 h-2 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="h-3 bg-gray-200 rounded w-12"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Voice Interactions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {interactions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">No recent interactions</p>
            </div>
          ) : (
            interactions.map((interaction: VoiceInteraction) => (
              <div key={interaction.id} className="flex items-center space-x-3">
                <div 
                  className={`w-2 h-2 rounded-full ${getStatusColor(interaction.status, interaction.callSuccessful)}`}
                ></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    Patient {interaction.patientId}
                  </p>
                  <p className="text-xs text-medical-gray">
                    {getStatusText(interaction.status, interaction.callSuccessful)}
                  </p>
                </div>
                <span className="text-xs text-medical-gray">
                  {getTimeAgo(interaction.callDate)}
                </span>
              </div>
            ))
          )}
        </div>
        <Button variant="link" className="w-full mt-4 text-sm text-medical-blue">
          View All Interactions
        </Button>
      </CardContent>
    </Card>
  );
}
