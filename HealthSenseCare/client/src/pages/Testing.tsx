import { TestingInterface } from "@/components/voice/TestingInterface";

export default function Testing() {
  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Voice Agent Testing Interface</h1>
        <p className="text-medical-gray">Test and validate voice agent behavior with simulated patient interactions</p>
      </div>

      <TestingInterface />
    </div>
  );
}
