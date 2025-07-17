import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, FileText, Book, Brain, HelpCircle, Settings, ChevronRight } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const categories = [
  { id: "clinical", name: "Clinical Guidelines", icon: FileText, active: true },
  { id: "patient-education", name: "Patient Education", icon: Book, active: false },
  { id: "technical", name: "Technical Docs", icon: Settings, active: false },
  { id: "faq", name: "FAQ", icon: HelpCircle, active: false },
  { id: "ai-models", name: "AI Risk Models", icon: Brain, active: false },
];

const specialties = [
  {
    id: "orthopedic",
    title: "Orthopedic Surgery",
    description: "Post-operative monitoring protocols for joint replacement, fracture repair, and arthroscopic procedures",
    documents: 12,
    updated: "2 days ago",
    icon: "🦴",
  },
  {
    id: "cardiac",
    title: "Cardiac Surgery",
    description: "Cardiac recovery monitoring, complication detection, and patient education protocols",
    documents: 8,
    updated: "1 week ago",
    icon: "❤️",
  },
  {
    id: "general",
    title: "General Surgery",
    description: "Guidelines for appendectomy, cholecystectomy, hernia repair, and other common procedures",
    documents: 15,
    updated: "3 days ago",
    icon: "🔪",
  },
  {
    id: "neurosurgery",
    title: "Neurosurgery",
    description: "Neurological assessment protocols and post-operative monitoring guidelines",
    documents: 6,
    updated: "5 days ago",
    icon: "🧠",
  },
];

const recentUpdates = [
  {
    title: "Post-Hip Replacement Monitoring Protocol v2.1",
    description: "Updated pain assessment criteria and mobility guidelines",
    date: "Dec 13, 2023",
    type: "New Version",
    color: "bg-green-100 text-green-600",
  },
  {
    title: "AI Risk Scoring Model Update",
    description: "Enhanced algorithm for cardiac surgery patients",
    date: "Dec 11, 2023",
    type: "Model Update",
    color: "bg-blue-100 text-blue-600",
  },
  {
    title: "Patient Education: Wound Care",
    description: "New multimedia content for surgical site care",
    date: "Dec 10, 2023",
    type: "Content Update",
    color: "bg-yellow-100 text-yellow-600",
  },
];

export function KnowledgeBase() {
  const [activeCategory, setActiveCategory] = useState("clinical");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: articles = [] } = useQuery({
    queryKey: ["/api/knowledge", { category: activeCategory }],
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Navigation Categories */}
      <div className="lg:col-span-1">
        <Card>
          <CardHeader>
            <CardTitle>Categories</CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <nav className="space-y-1">
              {categories.map((category) => {
                const Icon = category.icon;
                const isActive = activeCategory === category.id;
                
                return (
                  <button
                    key={category.id}
                    onClick={() => setActiveCategory(category.id)}
                    className={`w-full text-left flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? "bg-medical-blue text-white"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="text-sm">{category.name}</span>
                  </button>
                );
              })}
            </nav>
          </CardContent>
        </Card>
      </div>

      {/* Content Area */}
      <div className="lg:col-span-3 space-y-6">
        {/* Search Bar */}
        <Card>
          <CardContent className="p-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search knowledge base..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 text-sm"
              />
            </div>
          </CardContent>
        </Card>

        {/* Clinical Guidelines Content */}
        {activeCategory === "clinical" && (
          <div className="space-y-6">
            {/* Surgical Specialties */}
            <Card>
              <CardHeader>
                <CardTitle>Clinical Guidelines by Specialty</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {specialties.map((specialty) => (
                    <div
                      key={specialty.id}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-start space-x-3">
                        <div className="text-2xl">{specialty.icon}</div>
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900 mb-1">
                            {specialty.title}
                          </h4>
                          <p className="text-sm text-gray-600 mb-2">
                            {specialty.description}
                          </p>
                          <div className="flex items-center space-x-2 text-xs">
                            <span className="text-medical-blue font-medium">
                              {specialty.documents} documents
                            </span>
                            <span className="text-gray-400">•</span>
                            <span className="text-gray-500">
                              Updated {specialty.updated}
                            </span>
                          </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recently Updated */}
            <Card>
              <CardHeader>
                <CardTitle>Recently Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentUpdates.map((update, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${update.color}`}>
                        <FileText className="h-4 w-4" />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {update.title}
                        </h4>
                        <p className="text-sm text-gray-600">{update.description}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-gray-500">{update.date}</span>
                        <Badge className={`mt-1 text-xs ${update.color}`}>
                          {update.type}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Other category content would go here */}
        {activeCategory !== "clinical" && (
          <Card>
            <CardContent className="p-8 text-center">
              <div className="text-gray-400 mb-4">
                <Book className="h-12 w-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {categories.find(c => c.id === activeCategory)?.name} Content
              </h3>
              <p className="text-gray-600 mb-4">
                Content for this category is being developed and will be available soon.
              </p>
              <Button variant="outline">Request Content</Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
