import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  iconColor?: string;
}

export function StatCard({ 
  title, 
  value, 
  change, 
  changeType = "neutral", 
  icon: Icon,
  iconColor = "text-medical-blue"
}: StatCardProps) {
  const getChangeColor = () => {
    switch (changeType) {
      case "positive":
        return "text-medical-green";
      case "negative":
        return "text-red-600";
      default:
        return "text-medical-gray";
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-medical-gray">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
          <div className={`w-12 h-12 bg-opacity-10 rounded-lg flex items-center justify-center ${iconColor.includes('blue') ? 'bg-medical-blue' : iconColor.includes('green') ? 'bg-medical-green' : 'bg-red-100'}`}>
            <Icon className={`h-6 w-6 ${iconColor}`} />
          </div>
        </div>
        {change && (
          <div className="mt-4">
            <span className={`text-sm font-medium ${getChangeColor()}`}>{change}</span>
            <span className="text-medical-gray text-sm ml-1">from last month</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
