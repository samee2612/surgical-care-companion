import { KnowledgeBase } from "@/components/knowledge/KnowledgeBase";

export default function Knowledge() {
  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-medical-gray">Clinical guidelines, patient education, and system documentation</p>
      </div>

      <KnowledgeBase />
    </div>
  );
}
