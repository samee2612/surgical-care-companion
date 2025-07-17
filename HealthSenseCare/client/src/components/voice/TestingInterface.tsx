import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Play, AlertTriangle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
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
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface TestResult {
  riskScore: number;
  aiDecision: string;
  transcript: string;
  detectedSymptoms: string[];
  escalationTriggered: boolean;
}

export function TestingInterface() {
  const [patientProfile, setPatientProfile] = useState("hip-replacement-day3");
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [customSymptoms, setCustomSymptoms] = useState("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const { toast } = useToast();

  const symptoms = [
    "Severe pain (8-10/10)",
    "Shortness of breath",
    "Fever (>101°F)",
    "Surgical site swelling",
    "Nausea/vomiting",
  ];

  const { data: testHistory = [] } = useQuery({
    queryKey: ["/api/test-simulations"],
  });

  const simulationMutation = useMutation({
    mutationFn: async (data: any) => {
      return await apiRequest("POST", "/api/test-simulations", data);
    },
    onSuccess: () => {
      toast({
        title: "Test Simulation Complete",
        description: "Simulation results generated successfully",
      });
    },
    onError: (error) => {
      toast({
        title: "Simulation Failed",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const handleSymptomChange = (symptom: string, checked: boolean) => {
    if (checked) {
      setSelectedSymptoms([...selectedSymptoms, symptom]);
    } else {
      setSelectedSymptoms(selectedSymptoms.filter(s => s !== symptom));
    }
  };

  const runSimulation = () => {
    // Generate mock test result
    const riskScore = selectedSymptoms.length > 2 ? Math.floor(Math.random() * 20 + 80) : 
                     selectedSymptoms.length > 0 ? Math.floor(Math.random() * 30 + 50) :
                     Math.floor(Math.random() * 30 + 20);
    
    const escalationTriggered = riskScore > 75;
    
    const mockResult: TestResult = {
      riskScore,
      aiDecision: escalationTriggered ? "Immediate Escalation Required" : 
                  riskScore > 50 ? "Monitor Closely" : "Continue Normal Care",
      transcript: `Agent: "Hello, this is your HealthSense24 check-in. How are you feeling today on a scale of 1 to 10?"\n\nPatient: "${selectedSymptoms.length > 0 ? 'I\'m really struggling. The pain is about a 9 and I\'m having trouble breathing.' : 'I\'m feeling much better today, maybe a 3 out of 10 for pain.'}"\n\nAgent: "${escalationTriggered ? 'I understand this is concerning. I\'m going to connect you with your care team immediately.' : 'That sounds like you\'re making good progress in your recovery.'}"`,
      detectedSymptoms: selectedSymptoms,
      escalationTriggered,
    };

    setTestResult(mockResult);

    // Submit to backend
    simulationMutation.mutate({
      patientProfile,
      injectedSymptoms: selectedSymptoms,
      customSymptoms,
      resultingRiskScore: riskScore,
      aiDecision: mockResult.aiDecision,
      transcript: mockResult.transcript,
      detectedSymptoms: selectedSymptoms,
      escalationTriggered,
    });
  };

  return (
    <div className="space-y-8">
      {/* Test Configuration and Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Test Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Patient Profile
              </label>
              <Select value={patientProfile} onValueChange={setPatientProfile}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hip-replacement-day3">Post-Hip Replacement - Day 3</SelectItem>
                  <SelectItem value="appendectomy-day7">Post-Appendectomy - Day 7</SelectItem>
                  <SelectItem value="cardiac-surgery-day1">Post-Cardiac Surgery - Day 1</SelectItem>
                  <SelectItem value="knee-surgery-day14">Post-Knee Surgery - Day 14</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Symptoms to Inject
              </label>
              <div className="space-y-2">
                {symptoms.map((symptom) => (
                  <div key={symptom} className="flex items-center space-x-2">
                    <Checkbox
                      id={symptom}
                      checked={selectedSymptoms.includes(symptom)}
                      onCheckedChange={(checked) => 
                        handleSymptomChange(symptom, checked as boolean)
                      }
                    />
                    <label
                      htmlFor={symptom}
                      className="text-sm text-gray-700 cursor-pointer"
                    >
                      {symptom}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Symptoms
              </label>
              <Textarea
                placeholder="Describe additional symptoms or patient responses..."
                value={customSymptoms}
                onChange={(e) => setCustomSymptoms(e.target.value)}
                rows={3}
              />
            </div>

            <Button 
              onClick={runSimulation}
              disabled={simulationMutation.isPending}
              className="w-full bg-medical-blue hover:bg-medical-blue-dark"
            >
              <Play className="h-4 w-4 mr-2" />
              {simulationMutation.isPending ? "Running Simulation..." : "Start Simulation"}
            </Button>
          </CardContent>
        </Card>

        {/* Test Results */}
        <Card>
          <CardHeader>
            <CardTitle>Test Results</CardTitle>
          </CardHeader>
          <CardContent>
            {!testResult ? (
              <div className="text-center py-8 text-gray-500">
                <Play className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Run a simulation to see results</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Risk Score */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Risk Score Calculated</span>
                    <span className={`text-lg font-bold ${
                      testResult.riskScore >= 80 ? "text-red-600" :
                      testResult.riskScore >= 60 ? "text-yellow-600" : "text-green-600"
                    }`}>
                      {testResult.riskScore}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        testResult.riskScore >= 80 ? "bg-red-600" :
                        testResult.riskScore >= 60 ? "bg-yellow-600" : "bg-green-600"
                      }`}
                      style={{ width: `${testResult.riskScore}%` }}
                    ></div>
                  </div>
                </div>

                {/* AI Decision */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">AI Decision</h4>
                  <div className={`rounded-lg p-3 border ${
                    testResult.escalationTriggered ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200"
                  }`}>
                    <div className="flex items-center">
                      {testResult.escalationTriggered ? (
                        <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      )}
                      <span className={`text-sm font-medium ${
                        testResult.escalationTriggered ? "text-red-800" : "text-green-800"
                      }`}>
                        {testResult.aiDecision}
                      </span>
                    </div>
                    <p className={`text-sm mt-1 ${
                      testResult.escalationTriggered ? "text-red-700" : "text-green-700"
                    }`}>
                      {testResult.escalationTriggered 
                        ? "Patient reports severe symptoms. Provider notification sent immediately."
                        : "Patient is recovering normally. Continuing regular monitoring schedule."
                      }
                    </p>
                  </div>
                </div>

                {/* Voice Transcript */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Voice Transcript</h4>
                  <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-line">
                    {testResult.transcript}
                  </div>
                </div>

                {/* Detected Symptoms */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Symptoms Detected</h4>
                  <div className="space-y-2">
                    {testResult.detectedSymptoms.length === 0 ? (
                      <p className="text-sm text-gray-500">No concerning symptoms detected</p>
                    ) : (
                      testResult.detectedSymptoms.map((symptom, index) => (
                        <Badge key={index} variant="destructive" className="mr-2">
                          {symptom}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Test History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Test Simulations</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Test Date</TableHead>
                <TableHead>Patient Profile</TableHead>
                <TableHead>Symptoms</TableHead>
                <TableHead>Risk Score</TableHead>
                <TableHead>AI Decision</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testHistory.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No test simulations found
                  </TableCell>
                </TableRow>
              ) : (
                testHistory.slice(0, 5).map((test: any) => (
                  <TableRow key={test.id}>
                    <TableCell className="text-sm">
                      {new Date(test.createdAt).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm">{test.patientProfile}</TableCell>
                    <TableCell className="text-sm">
                      {test.injectedSymptoms?.join(", ") || "None"}
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        test.resultingRiskScore >= 80 ? "bg-red-100 text-red-800" :
                        test.resultingRiskScore >= 60 ? "bg-yellow-100 text-yellow-800" :
                        "bg-green-100 text-green-800"
                      }>
                        {test.resultingRiskScore}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={
                        test.escalationTriggered ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"
                      }>
                        {test.escalationTriggered ? "Escalate" : "Monitor"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button variant="link" size="sm" className="text-medical-blue">
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
