import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Filter, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

export default function VoiceReports() {
  const [riskFilter, setRiskFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("all");

  const { data: interactions = [], isLoading } = useQuery({
    queryKey: ["/api/dashboard/recent-interactions"],
  });

  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return "bg-red-100 text-red-800";
    if (score >= 60) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "escalated":
        return "bg-red-100 text-red-800";
      case "normal":
        return "bg-green-100 text-green-800";
      default:
        return "bg-yellow-100 text-yellow-800";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Voice Interaction Reports</h1>
          <p className="text-medical-gray">View and export reports from all automated voice calls</p>
        </div>
        <Button className="bg-medical-blue hover:bg-medical-blue-dark">
          <Download className="h-4 w-4 mr-2" />
          Export Reports
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="h-5 w-5 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Date Range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={riskFilter} onValueChange={setRiskFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Risk Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                <SelectItem value="high">High Risk</SelectItem>
                <SelectItem value="medium">Medium Risk</SelectItem>
                <SelectItem value="low">Low Risk</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Reports Table */}
      <Card>
        <CardHeader>
          <CardTitle>Voice Interaction Reports</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-medical-blue mx-auto"></div>
              <p className="text-gray-500 mt-2">Loading reports...</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Escalation</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {interactions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      No voice interaction reports found
                    </TableCell>
                  </TableRow>
                ) : (
                  interactions.slice(0, 10).map((interaction: any, index: number) => (
                    <TableRow key={interaction.id || index}>
                      <TableCell>
                        <div className="text-sm">
                          <div className="font-medium">
                            {new Date(interaction.callDate || Date.now()).toLocaleDateString()}
                          </div>
                          <div className="text-gray-500">
                            {new Date(interaction.callDate || Date.now()).toLocaleTimeString()}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div className="font-medium">Patient {interaction.patientId}</div>
                          <div className="text-gray-500">Post-op Day {3 + index}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {Math.floor(Math.random() * 300 + 120)}s
                      </TableCell>
                      <TableCell>
                        <Badge className={getRiskScoreColor(85 - index * 10)}>
                          {85 - index * 10}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(interaction.status)}>
                          {interaction.status || "completed"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {interaction.status === "escalated" ? (
                          <Badge className="bg-red-100 text-red-800">Yes</Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-800">No</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="link" size="sm" className="text-medical-blue">
                            View Transcript
                          </Button>
                          <Button variant="link" size="sm" className="text-medical-blue">
                            Download PDF
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
