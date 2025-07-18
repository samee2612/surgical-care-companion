import { PatientProfile } from "@/components/patients/PatientProfile";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";

interface PatientDetailProps {
  patientId: number;
}

export default function PatientDetail({ patientId }: PatientDetailProps) {
  return (
    <div className="min-h-screen bg-medical-light">
      {/* Back Navigation */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <Link href="/patients">
          <Button variant="ghost" className="flex items-center text-medical-blue">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>

      {/* Patient Profile Content */}
      <PatientProfile patientId={patientId} />
    </div>
  );
}
