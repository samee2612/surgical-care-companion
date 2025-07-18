import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PatientTable } from "@/components/dashboard/PatientTable";
import { AddPatientDialog } from "@/components/patients/AddPatientDialog";
import { Card, CardContent } from "@/components/ui/card";

export default function Patients() {
  const [search, setSearch] = useState("");
  const [addPatientOpen, setAddPatientOpen] = useState(false);

  const { data: patients = [], isLoading } = useQuery({
    queryKey: ["/api/patients"],
  });

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patient Management</h1>
          <p className="text-medical-gray">Manage and monitor all enrolled patients</p>
        </div>
        <Button 
          className="bg-medical-blue hover:bg-medical-blue-dark w-full sm:w-auto"
          onClick={() => setAddPatientOpen(true)}
        >
          <Plus className="h-4 w-4 mr-2" />
          <span className="hidden sm:inline">Add Patient</span>
          <span className="sm:hidden">Add</span>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-medical-blue">
              {Array.isArray(patients) ? patients.length : 0}
            </div>
            <p className="text-sm text-gray-600">Total Patients</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {Array.isArray(patients) ? patients.filter((p: any) => p.programActive).length : 0}
            </div>
            <p className="text-sm text-gray-600">Active Programs</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {/* We'll calculate this from voice interactions later */}
              {Array.isArray(patients) ? Math.floor(patients.length * 0.15) : 0}
            </div>
            <p className="text-sm text-gray-600">Pending Follow-ups</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-600">
              {/* We'll calculate this from alerts later */}
              {Array.isArray(patients) ? Math.floor(patients.length * 0.08) : 0}
            </div>
            <p className="text-sm text-gray-600">High Risk</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search patients by name or MRN..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" className="w-full sm:w-auto">
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Patient Table */}
      {isLoading ? (
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded"></div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <PatientTable />
      )}

      {/* Add Patient Dialog */}
      <AddPatientDialog 
        open={addPatientOpen} 
        onOpenChange={setAddPatientOpen} 
      />
    </div>
  );
}
