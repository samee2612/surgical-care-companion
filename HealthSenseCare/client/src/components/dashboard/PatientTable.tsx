import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, MoreHorizontal } from "lucide-react";
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
  programActive: boolean;
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
    if (score >= 80) return "bg-red-100 text-red-800";
    if (score >= 60) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const getRiskLevel = (score: number) => {
    if (score >= 80) return "High";
    if (score >= 60) return "Medium";
    return "Low";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "alert":
        return "bg-red-100 text-red-800";
      case "monitor":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-green-100 text-green-800";
    }
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
            {patients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  No patients found
                </TableCell>
              </TableRow>
            ) : (
              patients.map((patient: Patient) => (
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
                        <div className="text-sm text-gray-500">MRN: {patient.mrn}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm text-gray-900">Hip Replacement</div>
                      <div className="text-sm text-gray-500">Dr. Anderson</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-gray-900">Day 3</TableCell>
                  <TableCell>
                    <Badge className={getRiskScoreColor(87)}>
                      87 - {getRiskLevel(87)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-gray-500">2 mins ago</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor("alert")}>Alert</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button variant="link" size="sm" className="text-medical-blue">
                        View
                      </Button>
                      <Button variant="link" size="sm" className="text-medical-blue">
                        Call
                      </Button>
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
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        
        {/* Pagination */}
        <div className="px-6 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing <span className="font-medium">1</span> to{" "}
              <span className="font-medium">10</span> of{" "}
              <span className="font-medium">{patients.length}</span> patients
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
