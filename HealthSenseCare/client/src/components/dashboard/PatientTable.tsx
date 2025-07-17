import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, MoreHorizontal, Phone, Eye } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Patient {
  id: number;
  mrn: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  phone?: string;
  email?: string;
  programActive: boolean;
  enrollmentDate: string;
  // Related data that might come from joins
  surgeries?: Array<{
    id: number;
    procedure: string;
    surgeonName: string;
    surgeryDate: string;
    specialty: string;
  }>;
  alerts?: Array<{
    id: number;
    priority: string;
    status: string;
  }>;
  voiceInteractions?: Array<{
    id: number;
    callDate: string;
    riskScore: string;
    status: string;
  }>;
}

export function PatientTable() {
  const [search, setSearch] = useState("");
  const [procedureFilter, setProcedureFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");

  const { data: patients = [], isLoading } = useQuery({
    queryKey: ["/api/patients", { search, limit: 50 }],
  });

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName[0]}${lastName[0]}`.toUpperCase();
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 7) return "bg-red-100 text-red-800";
    if (score >= 4) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const getRiskLevel = (score: number) => {
    if (score >= 7) return "High";
    if (score >= 4) return "Medium";
    return "Low";
  };

  const getStatusColor = (active: boolean, hasAlerts?: boolean) => {
    if (!active) return "bg-gray-100 text-gray-800";
    if (hasAlerts) return "bg-red-100 text-red-800";
    return "bg-green-100 text-green-800";
  };

  const getStatusText = (active: boolean, hasAlerts?: boolean) => {
    if (!active) return "Inactive";
    if (hasAlerts) return "Alert";
    return "Active";
  };

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const getPostOpDay = (surgeryDate?: string) => {
    if (!surgeryDate) return "N/A";
    const today = new Date();
    const surgery = new Date(surgeryDate);
    const diffTime = Math.abs(today.getTime() - surgery.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `Day ${diffDays}`;
  };

  const getLatestRiskScore = (interactions?: Patient['voiceInteractions']) => {
    if (!interactions || interactions.length === 0) return null;
    const latest = interactions.sort((a, b) => 
      new Date(b.callDate).getTime() - new Date(a.callDate).getTime()
    )[0];
    return parseFloat(latest.riskScore);
  };

  const getLastContact = (interactions?: Patient['voiceInteractions']) => {
    if (!interactions || interactions.length === 0) return "No contact";
    const latest = interactions.sort((a, b) => 
      new Date(b.callDate).getTime() - new Date(a.callDate).getTime()
    )[0];
    
    const contactDate = new Date(latest.callDate);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - contactDate.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Patient Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse">
            <div className="h-10 bg-gray-200 rounded mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-gray-100 rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Patient Management</CardTitle>
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search patients..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 w-64"
              />
            </div>
            <Select value={procedureFilter} onValueChange={setProcedureFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Procedures" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Procedures</SelectItem>
                <SelectItem value="hip">Hip Replacement</SelectItem>
                <SelectItem value="knee">Knee Surgery</SelectItem>
                <SelectItem value="cardiac">Cardiac</SelectItem>
                <SelectItem value="general">General Surgery</SelectItem>
              </SelectContent>
            </Select>
            <Select value={riskFilter} onValueChange={setRiskFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All Risk Levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                <SelectItem value="high">High Risk</SelectItem>
                <SelectItem value="medium">Medium Risk</SelectItem>
                <SelectItem value="low">Low Risk</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>Procedure</TableHead>
              <TableHead>Post-Op Day</TableHead>
              <TableHead>Risk Score</TableHead>
              <TableHead>Last Contact</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(patients as Patient[]).length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  No patients found
                </TableCell>
              </TableRow>
            ) : (
              (patients as Patient[]).map((patient: Patient) => {
                const latestRiskScore = getLatestRiskScore(patient.voiceInteractions);
                const hasActiveAlerts = patient.alerts?.some(alert => alert.status === 'active');
                const latestSurgery = patient.surgeries?.[0];
                
                return (
                  <TableRow key={patient.id} className="hover:bg-gray-50">
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <Avatar>
                          <AvatarFallback className="bg-medical-blue bg-opacity-10 text-medical-blue">
                            {getInitials(patient.firstName, patient.lastName)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium text-gray-900">
                            {patient.firstName} {patient.lastName}
                          </div>
                          <div className="text-sm text-gray-500">
                            MRN: {patient.mrn} • Age: {calculateAge(patient.dateOfBirth)}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm text-gray-900">
                          {latestSurgery?.procedure || "No surgery recorded"}
                        </div>
                        <div className="text-sm text-gray-500">
                          {latestSurgery?.surgeonName || "N/A"}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-900">
                      {getPostOpDay(latestSurgery?.surgeryDate)}
                    </TableCell>
                    <TableCell>
                      {latestRiskScore !== null ? (
                        <Badge className={getRiskScoreColor(latestRiskScore)}>
                          {latestRiskScore.toFixed(1)} - {getRiskLevel(latestRiskScore)}
                        </Badge>
                      ) : (
                        <span className="text-sm text-gray-500">No data</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {getLastContact(patient.voiceInteractions)}
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(patient.programActive, hasActiveAlerts)}>
                        {getStatusText(patient.programActive, hasActiveAlerts)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="sm" className="text-medical-blue hover:text-medical-blue-dark">
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                        {patient.phone && (
                          <Button variant="ghost" size="sm" className="text-medical-blue hover:text-medical-blue-dark">
                            <Phone className="h-4 w-4 mr-1" />
                            Call
                          </Button>
                        )}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem>Edit Profile</DropdownMenuItem>
                            <DropdownMenuItem>View History</DropdownMenuItem>
                            <DropdownMenuItem>Send Message</DropdownMenuItem>
                            <DropdownMenuItem>Add Surgery</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
        
        {/* Pagination */}
        <div className="px-6 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">1</span> to{" "}
              <span className="font-medium">{Math.min(10, (patients as Patient[]).length)}</span> of{" "}
              <span className="font-medium">{(patients as Patient[]).length}</span> patients
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                Previous
              </Button>
              <Button variant="outline" size="sm" className="bg-medical-blue text-white">
                1
              </Button>
              <Button variant="outline" size="sm">
                2
              </Button>
              <Button variant="outline" size="sm">
                3
              </Button>
              <Button variant="outline" size="sm">
                Next
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
