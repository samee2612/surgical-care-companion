import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface AlertBannerProps {
  count: number;
  description: string;
  onViewDetails?: () => void;
}

export function AlertBanner({ count, description, onViewDetails }: AlertBannerProps) {
  return (
    <Alert className="bg-red-50 border-red-200 mb-6">
      <AlertTriangle className="h-4 w-4 text-red-500" />
      <AlertDescription className="flex items-center justify-between w-full">
        <div>
          <h3 className="text-sm font-medium text-red-800">
            {count} Patient{count !== 1 ? 's' : ''} Require{count === 1 ? 's' : ''} Immediate Attention
          </h3>
          <p className="text-sm text-red-700">{description}</p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          className="bg-red-100 text-red-800 border-red-200 hover:bg-red-200"
          onClick={onViewDetails}
        >
          View Details
        </Button>
      </AlertDescription>
    </Alert>
  );
}
