import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Settings as SettingsIcon, Users, Bell, CreditCard, Database, Upload, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const [riskThresholds, setRiskThresholds] = useState({
    high: [80],
    medium: [50],
    low: [20],
  });
  const { toast } = useToast();

  const { data: settings = [], isLoading } = useQuery({
    queryKey: ["/api/settings"],
  });

  const updateSettingMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: any }) => {
      return await apiRequest("PUT", `/api/settings/${key}`, { value });
    },
    onSuccess: () => {
      toast({
        title: "Settings Updated",
        description: "Your changes have been saved successfully",
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

  // Mock user management data
  const users = [
    {
      id: "1",
      name: "Dr. Sarah Johnson",
      email: "sarah.johnson@hospital.com",
      role: "provider",
      lastActive: "2023-12-15T14:30:00Z",
      status: "active",
    },
    {
      id: "2",
      name: "John Admin",
      email: "john.admin@hospital.com",
      role: "admin",
      lastActive: "2023-12-15T12:15:00Z",
      status: "active",
    },
    {
      id: "3",
      name: "Maria Rodriguez",
      email: "maria.r@email.com",
      role: "patient",
      lastActive: "2023-12-15T10:45:00Z",
      status: "active",
    },
  ];

  // Mock system logs
  const systemLogs = [
    {
      id: 1,
      timestamp: "2023-12-15T14:32:15Z",
      action: "User Login",
      user: "Dr. Sarah Johnson",
      details: "Successful login from IP 192.168.1.100",
      level: "info",
    },
    {
      id: 2,
      timestamp: "2023-12-15T14:30:42Z",
      action: "Alert Created",
      user: "System",
      details: "High-risk alert generated for Patient ID 101",
      level: "warning",
    },
    {
      id: 3,
      timestamp: "2023-12-15T14:28:33Z",
      action: "Settings Updated",
      user: "John Admin",
      details: "Risk threshold settings modified",
      level: "info",
    },
  ];

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-purple-100 text-purple-800";
      case "provider":
        return "bg-blue-100 text-blue-800";
      case "patient":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "bg-red-100 text-red-800";
      case "warning":
        return "bg-yellow-100 text-yellow-800";
      case "info":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
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
        <h1 className="text-2xl font-bold text-gray-900">System Settings & Admin Tools</h1>
        <p className="text-medical-gray">Manage system configuration, users, and monitoring</p>
      </div>

      <Tabs defaultValue="users" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="alerts">Alert Settings</TabsTrigger>
          <TabsTrigger value="billing">Billing Config</TabsTrigger>
          <TabsTrigger value="system">System Monitor</TabsTrigger>
          <TabsTrigger value="content">Content Management</TabsTrigger>
        </TabsList>

        {/* User Management */}
        <TabsContent value="users" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
            <Button className="bg-medical-blue hover:bg-medical-blue-dark">
              <Users className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>User Accounts</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Last Active</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Badge className={getRoleColor(user.role)}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {getTimeAgo(user.lastActive)}
                      </TableCell>
                      <TableCell>
                        <Badge className="bg-green-100 text-green-800">
                          {user.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="link" size="sm">Edit</Button>
                          <Button variant="link" size="sm" className="text-red-600">
                            Deactivate
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Access Level Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Provider Access</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Patient Dashboard</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Voice Reports</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Testing Interface</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Admin Access</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">User Management</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">System Settings</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Billing Config</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900">Patient Access</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Recovery Portal</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Education Content</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Messaging</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alert Settings */}
        <TabsContent value="alerts" className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Alert Configuration</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Score Thresholds</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    High Risk (Currently: {riskThresholds.high[0]})
                  </label>
                  <Slider
                    value={riskThresholds.high}
                    onValueChange={(value) => setRiskThresholds(prev => ({ ...prev, high: value }))}
                    max={100}
                    min={60}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>60</span>
                    <span>100</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Medium Risk (Currently: {riskThresholds.medium[0]})
                  </label>
                  <Slider
                    value={riskThresholds.medium}
                    onValueChange={(value) => setRiskThresholds(prev => ({ ...prev, medium: value }))}
                    max={79}
                    min={20}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>20</span>
                    <span>79</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Low Risk (Currently: {riskThresholds.low[0]})
                  </label>
                  <Slider
                    value={riskThresholds.low}
                    onValueChange={(value) => setRiskThresholds(prev => ({ ...prev, low: value }))}
                    max={49}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0</span>
                    <span>49</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Surgery-Specific Thresholds</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Orthopedic Surgery
                  </label>
                  <Select defaultValue="standard">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard Thresholds</SelectItem>
                      <SelectItem value="elevated">Elevated Monitoring</SelectItem>
                      <SelectItem value="custom">Custom Configuration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cardiac Surgery
                  </label>
                  <Select defaultValue="elevated">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard Thresholds</SelectItem>
                      <SelectItem value="elevated">Elevated Monitoring</SelectItem>
                      <SelectItem value="custom">Custom Configuration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    General Surgery
                  </label>
                  <Select defaultValue="standard">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard Thresholds</SelectItem>
                      <SelectItem value="elevated">Elevated Monitoring</SelectItem>
                      <SelectItem value="custom">Custom Configuration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Neurosurgery
                  </label>
                  <Select defaultValue="elevated">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard Thresholds</SelectItem>
                      <SelectItem value="elevated">Elevated Monitoring</SelectItem>
                      <SelectItem value="custom">Custom Configuration</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Billing Configuration */}
        <TabsContent value="billing" className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Billing Configuration</h2>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCard className="h-5 w-5 mr-2" />
                CPT Code Management
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Remote Patient Monitoring (RPM)</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Setup & Patient Education
                      </label>
                      <Input defaultValue="99453" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Device Supply
                      </label>
                      <Input defaultValue="99454" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Data Collection (16+ days)
                      </label>
                      <Input defaultValue="99457" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Data Analysis & Report
                      </label>
                      <Input defaultValue="99458" placeholder="CPT Code" />
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Remote Therapeutic Monitoring (RTM)</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Setup & Patient Education
                      </label>
                      <Input defaultValue="98975" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Device Supply
                      </label>
                      <Input defaultValue="98976" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Data Collection (16+ days)
                      </label>
                      <Input defaultValue="98977" placeholder="CPT Code" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Data Analysis & Report
                      </label>
                      <Input defaultValue="98980" placeholder="CPT Code" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">Automatic Billing Integration</h4>
                    <p className="text-sm text-gray-600">Automatically generate billing codes based on patient interactions</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Monitor */}
        <TabsContent value="system" className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">System Monitoring</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">99.8%</div>
                <div className="text-sm text-gray-600">System Uptime</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">2.3GB</div>
                <div className="text-sm text-gray-600">Database Size</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">147ms</div>
                <div className="text-sm text-gray-600">Avg Response</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-orange-600">1,247</div>
                <div className="text-sm text-gray-600">Active Sessions</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="h-5 w-5 mr-2" />
                System Activity Logs
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>Level</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {systemLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-sm font-mono">
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-medium">{log.action}</TableCell>
                      <TableCell>{log.user}</TableCell>
                      <TableCell className="text-sm text-gray-600">{log.details}</TableCell>
                      <TableCell>
                        <Badge className={getLogLevelColor(log.level)}>
                          {log.level}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <div className="flex space-x-3">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Logs
            </Button>
            <Button variant="outline">
              <Database className="h-4 w-4 mr-2" />
              Database Backup
            </Button>
            <Button variant="outline">
              Clear Logs
            </Button>
          </div>
        </TabsContent>

        {/* Content Management */}
        <TabsContent value="content" className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Content Management</h2>

          <Card>
            <CardHeader>
              <CardTitle>Educational Content Upload</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Type
                  </label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select content type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="patient-education">Patient Education</SelectItem>
                      <SelectItem value="clinical-guidelines">Clinical Guidelines</SelectItem>
                      <SelectItem value="training-materials">Training Materials</SelectItem>
                      <SelectItem value="faq">FAQ</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Surgery Specialty
                  </label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select specialty" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="orthopedic">Orthopedic</SelectItem>
                      <SelectItem value="cardiac">Cardiac</SelectItem>
                      <SelectItem value="general">General Surgery</SelectItem>
                      <SelectItem value="neurosurgery">Neurosurgery</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Title
                </label>
                <Input placeholder="Enter content title" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Description
                </label>
                <Textarea 
                  placeholder="Enter content description"
                  rows={4}
                />
              </div>

              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-sm text-gray-600 mb-2">
                  Drag and drop files here, or click to select
                </p>
                <p className="text-xs text-gray-500">
                  Supports: PDF, DOC, MP4, images (max 50MB per file)
                </p>
                <Button variant="outline" className="mt-4">
                  Choose Files
                </Button>
              </div>

              <div className="flex space-x-3">
                <Button className="bg-medical-blue hover:bg-medical-blue-dark">
                  Upload Content
                </Button>
                <Button variant="outline">
                  Preview
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Save All Changes */}
      <div className="flex justify-end pt-6 border-t border-gray-200">
        <Button 
          className="bg-medical-blue hover:bg-medical-blue-dark"
          onClick={() => {
            updateSettingMutation.mutate({
              key: "system_settings",
              value: { updated: new Date().toISOString() }
            });
          }}
          disabled={updateSettingMutation.isPending}
        >
          {updateSettingMutation.isPending ? "Saving..." : "Save All Changes"}
        </Button>
      </div>
    </div>
  );
}
