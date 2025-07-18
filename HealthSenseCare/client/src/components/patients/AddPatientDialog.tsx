import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X, User, Phone, Mail, Calendar, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

interface AddPatientDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface PatientFormData {
  mrn: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  phone?: string;
  email?: string;
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  voiceConsentGiven: boolean;
  dataConsentGiven: boolean;
  programActive: boolean;
}

export function AddPatientDialog({ open, onOpenChange }: AddPatientDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState<PatientFormData>({
    mrn: "",
    firstName: "",
    lastName: "",
    dateOfBirth: "",
    phone: "",
    email: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    voiceConsentGiven: false,
    dataConsentGiven: false,
    programActive: true,
  });

  const createPatientMutation = useMutation({
    mutationFn: async (data: PatientFormData) => {
      const response = await apiRequest("POST", "/api/patients", data);
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/patients"] });
      toast({
        title: "Patient Added",
        description: "New patient has been successfully added to the system.",
      });
      onOpenChange(false);
      resetForm();
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to add patient. Please try again.",
        variant: "destructive",
      });
    },
  });

  const resetForm = () => {
    setFormData({
      mrn: "",
      firstName: "",
      lastName: "",
      dateOfBirth: "",
      phone: "",
      email: "",
      emergencyContactName: "",
      emergencyContactPhone: "",
      voiceConsentGiven: false,
      dataConsentGiven: false,
      programActive: true,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.mrn || !formData.firstName || !formData.lastName || !formData.dateOfBirth) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields (MRN, Name, Date of Birth).",
        variant: "destructive",
      });
      return;
    }

    // MRN uniqueness check (basic format validation)
    if (formData.mrn.length < 6) {
      toast({
        title: "Invalid MRN",
        description: "MRN must be at least 6 characters long.",
        variant: "destructive",
      });
      return;
    }

    createPatientMutation.mutate(formData);
  };

  const generateMRN = () => {
    const prefix = "MRN";
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    setFormData(prev => ({ ...prev, mrn: `${prefix}${timestamp}${random}` }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-medical-blue" />
            Add New Patient
          </DialogTitle>
          <DialogDescription>
            Enter patient information to enroll them in the surgical care monitoring program.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <User className="h-4 w-4" />
              Basic Information
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="mrn">Medical Record Number (MRN) *</Label>
                <div className="flex gap-2">
                  <Input
                    id="mrn"
                    value={formData.mrn}
                    onChange={(e) => setFormData(prev => ({ ...prev, mrn: e.target.value }))}
                    placeholder="e.g., MRN001234567"
                    required
                  />
                  <Button type="button" variant="outline" onClick={generateMRN}>
                    Generate
                  </Button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="dateOfBirth">Date of Birth *</Label>
                <Input
                  id="dateOfBirth"
                  type="date"
                  value={formData.dateOfBirth}
                  onChange={(e) => setFormData(prev => ({ ...prev, dateOfBirth: e.target.value }))}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First Name *</Label>
                <Input
                  id="firstName"
                  value={formData.firstName}
                  onChange={(e) => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
                  placeholder="Enter first name"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="lastName">Last Name *</Label>
                <Input
                  id="lastName"
                  value={formData.lastName}
                  onChange={(e) => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
                  placeholder="Enter last name"
                  required
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <Phone className="h-4 w-4" />
              Contact Information
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="+1-555-0123"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="patient@example.com"
                />
              </div>
            </div>
          </div>

          {/* Emergency Contact */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Emergency Contact</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="emergencyContactName">Contact Name</Label>
                <Input
                  id="emergencyContactName"
                  value={formData.emergencyContactName}
                  onChange={(e) => setFormData(prev => ({ ...prev, emergencyContactName: e.target.value }))}
                  placeholder="Emergency contact full name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="emergencyContactPhone">Contact Phone</Label>
                <Input
                  id="emergencyContactPhone"
                  type="tel"
                  value={formData.emergencyContactPhone}
                  onChange={(e) => setFormData(prev => ({ ...prev, emergencyContactPhone: e.target.value }))}
                  placeholder="+1-555-0124"
                />
              </div>
            </div>
          </div>

          {/* Consent and Program Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Program Settings</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="voiceConsentGiven">Voice Monitoring Consent</Label>
                  <p className="text-sm text-gray-500">
                    Patient consents to automated voice check-ins
                  </p>
                </div>
                <Switch
                  id="voiceConsentGiven"
                  checked={formData.voiceConsentGiven}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, voiceConsentGiven: checked }))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="dataConsentGiven">Data Collection Consent</Label>
                  <p className="text-sm text-gray-500">
                    Patient consents to data collection and analysis
                  </p>
                </div>
                <Switch
                  id="dataConsentGiven"
                  checked={formData.dataConsentGiven}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, dataConsentGiven: checked }))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="programActive">Program Active</Label>
                  <p className="text-sm text-gray-500">
                    Enroll patient in active monitoring program
                  </p>
                </div>
                <Switch
                  id="programActive"
                  checked={formData.programActive}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, programActive: checked }))}
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createPatientMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-medical-blue hover:bg-medical-blue-dark"
              disabled={createPatientMutation.isPending}
            >
              {createPatientMutation.isPending ? "Adding Patient..." : "Add Patient"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
