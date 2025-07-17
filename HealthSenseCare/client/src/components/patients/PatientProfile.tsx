import { useQuery } from "@tanstack/react-query";
import { Phone, Edit, Calendar, MapPin, User, Shield, Heart, AlertTriangle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

interface PatientProfileProps {
  patientId: number;
}

export function PatientProfile({ patientId }: PatientProfileProps) {
  const { data: patient, isLoading: patientLoading } = useQuery({
    queryKey: ["/api/patients", patientId],
  });

  const { data: surgeries = [], isLoading: surgeriesLoading } = useQuery({
    queryKey: ["/api/patients", patientId, "surgeries"],
  });

  const { data: voiceInteractions = [], isLoading: interactionsLoading } = useQuery({
    queryKey: ["/api/patients", patientId, "voice-interactions"],
  });

  const { data: alerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ["/api/patients", patientId, "alerts"],
  });

  if (patientLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-6">
              <div className="h-64 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
            <div className="lg:col-span-2 space-y-6">
              <div className="h-48 bg-gray-200 rounded"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Patient Not Found</h3>
            <p className="text-gray-600">The requested patient could not be found.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName[0]}${lastName[0]}`.toUpperCase();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateAge = (dateOfBirth: string) => {
    const birth = new Date(dateOfBirth);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  const getPostOpDay = (surgeryDate: string) => {
    const surgery = new Date(surgeryDate);
    const today = new Date();
    const diffTime = Math.abs(today.getTime() - surgery.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getInteractionStatusIcon = (status: string, callSuccessful: boolean) => {
    if (!callSuccessful) return <AlertTriangle className="h-4 w-4 text-red-500" />;
    if (status === "escalated") return <AlertTriangle className="h-4 w-4 text-red-500" />;
    if (status === "normal") return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  };

  const getInteractionStatusColor = (status: string, callSuccessful: boolean) => {
    if (!callSuccessful) return "border-red-200 bg-red-50";
    if (status === "escalated") return "border-red-200 bg-red-50";
    if (status === "normal") return "border-green-200 bg-green-50";
    return "border-yellow-200 bg-yellow-50";
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

  // Mock current risk assessment (would be calculated from latest voice interaction)
  const currentRiskScore = 87;
  const currentSurgery = surgeries[0]; // Most recent surgery

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patient Profile</h1>
          <p className="text-medical-gray">
            {patient.firstName} {patient.lastName} • MRN: {patient.mrn}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button className="bg-medical-blue hover:bg-medical-blue-dark">
            <Phone className="h-4 w-4 mr-2" />
            Call Patient
          </Button>
          <Button variant="outline">
            <Edit className="h-4 w-4 mr-2" />
            Edit Profile
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Information Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Patient Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-center mb-4">
                <Avatar className="w-20 h-20">
                  <AvatarFallback className="bg-medical-blue bg-opacity-10 text-medical-blue text-2xl font-bold">
                    {getInitials(patient.firstName, patient.lastName)}
                  </AvatarFallback>
                </Avatar>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-500">Full Name</label>
                  <p className="text-sm text-gray-900">{patient.firstName} {patient.lastName}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Date of Birth</label>
                  <p className="text-sm text-gray-900">
                    {formatDate(patient.dateOfBirth)} ({calculateAge(patient.dateOfBirth)} years)
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Phone</label>
                  <p className="text-sm text-gray-900">{patient.phone || "Not provided"}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Email</label>
                  <p className="text-sm text-gray-900">{patient.email || "Not provided"}</p>
                </div>
                <Separator />
                <div>
                  <label className="text-sm font-medium text-gray-500">Emergency Contact</label>
                  <p className="text-sm text-gray-900">{patient.emergencyContactName || "Not provided"}</p>
                  {patient.emergencyContactPhone && (
                    <p className="text-sm text-gray-500">{patient.emergencyContactPhone}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Consent & Enrollment */}
          <Card>
            <CardHeader>
              <CardTitle>Consent & Enrollment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Voice Monitoring</span>
                <Badge className={patient.voiceConsentGiven ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                  {patient.voiceConsentGiven ? "Consented" : "Not Consented"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Data Sharing</span>
                <Badge className={patient.dataConsentGiven ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                  {patient.dataConsentGiven ? "Approved" : "Not Approved"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Program Enrollment</span>
                <Badge className={patient.programActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                  {patient.programActive ? "Active" : "Inactive"}
                </Badge>
              </div>
              <Separator />
              <div className="pt-2">
                <p className="text-xs text-gray-500">
                  Enrolled: {patient.enrollmentDate ? formatDate(patient.enrollmentDate) : "Not enrolled"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Surgery Details */}
          {currentSurgery && (
            <Card>
              <CardHeader>
                <CardTitle>Current Surgery Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Procedure</label>
                    <p className="text-sm text-gray-900 font-medium">{currentSurgery.procedure}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Surgery Date</label>
                    <p className="text-sm text-gray-900">{formatDate(currentSurgery.surgeryDate)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Surgeon</label>
                    <p className="text-sm text-gray-900">{currentSurgery.surgeonName}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Post-Op Day</label>
                    <p className="text-sm text-gray-900 font-medium">
                      Day {getPostOpDay(currentSurgery.surgeryDate)}
                    </p>
                  </div>
                  {currentSurgery.dischargeDate && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Discharge Date</label>
                      <p className="text-sm text-gray-900">{formatDate(currentSurgery.dischargeDate)}</p>
                    </div>
                  )}
                  {currentSurgery.expectedRecoveryWeeks && (
                    <div>
                      <label className="text-sm font-medium text-gray-500">Expected Recovery</label>
                      <p className="text-sm text-gray-900">{currentSurgery.expectedRecoveryWeeks} weeks</p>
                    </div>
                  )}
                </div>
                {currentSurgery.notes && (
                  <div className="mt-4">
                    <label className="text-sm font-medium text-gray-500">Notes</label>
                    <p className="text-sm text-gray-700 mt-1">{currentSurgery.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Current Risk Assessment */}
          <Card>
            <CardHeader>
              <CardTitle>Current Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-2xl font-bold text-red-600">{currentRiskScore}</h4>
                  <p className="text-sm text-gray-500">Risk Score</p>
                </div>
                <div className="text-right">
                  <Badge className="bg-red-100 text-red-800">High Risk</Badge>
                  <p className="text-xs text-gray-500 mt-1">Updated 2 minutes ago</p>
                </div>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="bg-red-600 h-3 rounded-full" 
                  style={{ width: `${currentRiskScore}%` }}
                ></div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Risk Factors</h5>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Severe pain reported (9/10)</li>
                    <li>• Difficulty breathing</li>
                    <li>• Surgical site swelling</li>
                    <li>• Age factor ({calculateAge(patient.dateOfBirth)} years)</li>
                  </ul>
                </div>
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h5>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Immediate provider contact</li>
                    <li>• Consider emergency evaluation</li>
                    <li>• Monitor respiratory status</li>
                    <li>• Pain management review</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Voice Interaction History */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Voice Interaction History</CardTitle>
                <Button variant="link" className="text-medical-blue">
                  View All Transcripts
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {interactionsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse p-4 bg-gray-50 rounded-lg">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  ))}
                </div>
              ) : voiceInteractions.length === 0 ? (
                <div className="text-center py-8">
                  <Mic className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-sm text-gray-500">No voice interactions found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {voiceInteractions.map((interaction: any) => (
                    <div
                      key={interaction.id}
                      className={`border rounded-lg p-4 ${getInteractionStatusColor(interaction.status, interaction.callSuccessful)}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            {getInteractionStatusIcon(interaction.status, interaction.callSuccessful)}
                            <span className="text-sm font-medium">
                              {!interaction.callSuccessful ? "Call Failed" :
                               interaction.status === "escalated" ? "High Priority Alert" :
                               interaction.status === "normal" ? "Normal Check-in" : "Moderate Concern"}
                            </span>
                            <span className="text-xs text-gray-500">
                              {getTimeAgo(interaction.callDate)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 mb-2">
                            {!interaction.callSuccessful ? "Patient unreachable. Failed to establish connection." :
                             interaction.status === "escalated" ? "Patient reported severe symptoms requiring immediate attention." :
                             interaction.status === "normal" ? "Patient feeling well, recovery progressing normally." :
                             "Patient reported moderate symptoms, monitoring recommended."}
                          </p>
                          <div className="flex items-center space-x-4">
                            {interaction.riskScore && (
                              <span className="text-xs font-medium text-gray-600">
                                Risk Score: {Math.round(parseFloat(interaction.riskScore))}
                              </span>
                            )}
                            <span className="text-xs text-gray-600">
                              Duration: {interaction.duration ? `${Math.floor(interaction.duration / 60)}:${(interaction.duration % 60).toString().padStart(2, '0')}` : "N/A"}
                            </span>
                          </div>
                        </div>
                        <Button variant="link" size="sm" className="text-medical-blue">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
