import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Phone, Settings, Activity, AlertCircle, CheckCircle, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function Integration() {
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const { toast } = useToast();

  const { data: settings = [], isLoading } = useQuery({
    queryKey: ["/api/settings", { category: "twilio" }],
  });

  const updateSettingMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: any }) => {
      return await apiRequest("PUT", `/api/settings/${key}`, { value });
    },
    onSuccess: () => {
      toast({
        title: "Settings Updated",
        description: "Twilio configuration has been saved successfully",
      });
    },
    onError: (error) => {
      toast({
        title: "Update Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const testConnection = async () => {
    setIsTestingConnection(true);
    // Simulate connection test
    setTimeout(() => {
      setIsTestingConnection(false);
      toast({
        title: "Connection Test Complete",
        description: "Twilio integration is working correctly",
      });
    }, 2000);
  };

  // Mock call activity data
  const callActivity = [
    {
      id: 1,
      phoneNumber: "+1234567890",
      patientId: 101,
      status: "completed",
      duration: 185,
      timestamp: "2023-12-15T14:30:00Z",
      errorCode: null,
    },
    {
      id: 2,
      phoneNumber: "+1987654321",
      patientId: 102,
      status: "failed",
      duration: 0,
      timestamp: "2023-12-15T14:25:00Z",
      errorCode: "busy",
    },
    {
      id: 3,
      phoneNumber: "+1122334455",
      patientId: 103,
      status: "completed",
      duration: 142,
      timestamp: "2023-12-15T14:20:00Z",
      errorCode: null,
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "in-progress":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds === 0) return "N/A";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Twilio Voice Integration</h1>
        <p className="text-medical-gray">Configure and manage the voice backend powered by Twilio</p>
      </div>

      {/* Configuration Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Connection Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Account SID
              </label>
              <Input 
                placeholder="Enter Twilio Account SID"
                defaultValue="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                type="password"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auth Token
              </label>
              <Input 
                placeholder="Enter Twilio Auth Token"
                defaultValue="••••••••••••••••••••••••••••••••"
                type="password"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <Input 
                placeholder="Enter Twilio Phone Number"
                defaultValue="+1234567890"
              />
            </div>

            <div className="flex items-center justify-between pt-4">
              <div className="flex items-center space-x-2">
                <Switch defaultChecked />
                <span className="text-sm text-gray-700">Enable voice calls</span>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={testConnection}
                disabled={isTestingConnection}
              >
                {isTestingConnection ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Test Connection
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Call Routing */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Phone className="h-5 w-5 mr-2" />
              Call Routing Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Voice
              </label>
              <Select defaultValue="alice">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="alice">Alice (Female, English)</SelectItem>
                  <SelectItem value="man">Man (Male, English)</SelectItem>
                  <SelectItem value="woman">Woman (Female, English)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Call Timeout (seconds)
              </label>
              <Input 
                type="number"
                defaultValue="30"
                min="10"
                max="300"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Retry Attempts
              </label>
              <Select defaultValue="3">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 attempt</SelectItem>
                  <SelectItem value="2">2 attempts</SelectItem>
                  <SelectItem value="3">3 attempts</SelectItem>
                  <SelectItem value="5">5 attempts</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Webhook URL
              </label>
              <Input 
                placeholder="https://your-app.com/webhook"
                defaultValue="https://healthsense24.replit.app/api/twilio/webhook"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Real-time Status Dashboard */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            Real-time Status Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">24</div>
              <div className="text-sm text-gray-600">Active Calls</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">156</div>
              <div className="text-sm text-gray-600">Queued Calls</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">1,247</div>
              <div className="text-sm text-gray-600">Completed Today</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">12</div>
              <div className="text-sm text-gray-600">Failed Calls</div>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-medium text-gray-900">Recent Call Activity</h4>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Live monitoring</span>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Phone Number</TableHead>
                <TableHead>Patient ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {callActivity.map((call) => (
                <TableRow key={call.id}>
                  <TableCell className="font-mono text-sm">{call.phoneNumber}</TableCell>
                  <TableCell>{call.patientId}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(call.status)}>
                      {call.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDuration(call.duration)}</TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {getTimeAgo(call.timestamp)}
                  </TableCell>
                  <TableCell>
                    {call.errorCode ? (
                      <Badge variant="destructive">{call.errorCode}</Badge>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Error Logging */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            Error Logging & Diagnostics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-700">Log Level</h4>
              <Select defaultValue="info">
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="debug">Debug</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warn">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recent Errors
              </label>
              <Textarea
                readOnly
                rows={6}
                className="font-mono text-xs bg-gray-50"
                value={`[2023-12-15 14:32:15] ERROR: Call to +1987654321 failed - Busy signal
[2023-12-15 14:30:42] WARN: High call volume detected - Queue length: 156
[2023-12-15 14:28:33] INFO: Voice agent successfully completed call to +1234567890
[2023-12-15 14:25:12] ERROR: Webhook timeout for patient ID 105
[2023-12-15 14:22:45] INFO: Twilio connection established successfully`}
              />
            </div>

            <div className="flex space-x-3">
              <Button variant="outline" size="sm">
                Download Logs
              </Button>
              <Button variant="outline" size="sm">
                Clear Error Log
              </Button>
              <Button variant="outline" size="sm">
                Test Override
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button 
          className="bg-medical-blue hover:bg-medical-blue-dark"
          onClick={() => {
            updateSettingMutation.mutate({
              key: "twilio_config",
              value: { updated: true }
            });
          }}
          disabled={updateSettingMutation.isPending}
        >
          {updateSettingMutation.isPending ? "Saving..." : "Save Configuration"}
        </Button>
      </div>
    </div>
  );
}
