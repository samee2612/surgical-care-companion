import { Heart, Shield, Users, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-medical-light to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <Heart className="h-12 w-12 text-medical-blue mr-4" />
            <h1 className="text-4xl font-bold text-gray-900">HealthSense24</h1>
          </div>
          <p className="text-xl text-medical-gray mb-8">
            Surgical Care Voice Agent System
          </p>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-8">
            Advanced AI-powered voice monitoring for post-surgical patients. 
            Ensure better outcomes through continuous care and early intervention.
          </p>
          <Button 
            size="lg" 
            className="bg-medical-blue hover:bg-medical-blue-dark text-white px-8 py-3"
            onClick={() => window.location.href = "/api/login"}
          >
            Access Platform
          </Button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-medical-blue bg-opacity-10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Users className="h-6 w-6 text-medical-blue" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Patient Monitoring</h3>
              <p className="text-sm text-gray-600">
                Real-time voice check-ins with AI-powered symptom detection
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-medical-green bg-opacity-10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Activity className="h-6 w-6 text-medical-green" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Risk Assessment</h3>
              <p className="text-sm text-gray-600">
                Advanced algorithms for early complication detection
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-medical-blue bg-opacity-10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Heart className="h-6 w-6 text-medical-blue" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Provider Dashboard</h3>
              <p className="text-sm text-gray-600">
                Comprehensive analytics and alert management system
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6 text-center">
              <div className="w-12 h-12 bg-medical-green bg-opacity-10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Shield className="h-6 w-6 text-medical-green" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">HIPAA Compliant</h3>
              <p className="text-sm text-gray-600">
                Secure, encrypted platform meeting healthcare standards
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Benefits */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Improving Patient Outcomes Through Technology
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-medical-blue mb-2">30%</div>
              <div className="text-sm text-gray-600">Reduction in readmissions</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-medical-green mb-2">24/7</div>
              <div className="text-sm text-gray-600">Patient monitoring</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-medical-blue mb-2">95%</div>
              <div className="text-sm text-gray-600">Detection accuracy</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-16 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            © 2023 HealthSense24. HIPAA Compliant Healthcare Technology.
          </p>
        </div>
      </div>
    </div>
  );
}
