import { cn } from "@/lib/utils";
import { 
  BarChart3, 
  Users, 
  Mic, 
  FlaskConical, 
  BookOpen, 
  Phone, 
  Settings 
} from "lucide-react";
import { Link, useLocation } from "wouter";

const navigation = [
  { name: "Provider Dashboard", href: "/", icon: BarChart3 },
  { name: "Patient Management", href: "/patients", icon: Users },
  { name: "Voice Interactions", href: "/voice-reports", icon: Mic },
  { name: "Voice Agent Testing", href: "/testing", icon: FlaskConical },
  { name: "Knowledge Base", href: "/knowledge", icon: BookOpen },
  { name: "Twilio Integration", href: "/integration", icon: Phone },
  { name: "System Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [location] = useLocation();

  return (
    <div className="w-64 bg-white shadow-sm border-r border-gray-200">
      <div className="p-6">
        <nav className="space-y-1">
          {navigation.map((item) => {
            const isActive = location === item.href;
            const Icon = item.icon;
            
            return (
              <Link key={item.name} href={item.href}>
                <a
                  className={cn(
                    isActive
                      ? "bg-medical-blue text-white"
                      : "text-gray-700 hover:bg-gray-50",
                    "group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors"
                  )}
                >
                  <Icon
                    className={cn(
                      isActive ? "text-white" : "text-gray-400 group-hover:text-gray-500",
                      "mr-3 h-5 w-5 flex-shrink-0"
                    )}
                  />
                  {item.name}
                </a>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
