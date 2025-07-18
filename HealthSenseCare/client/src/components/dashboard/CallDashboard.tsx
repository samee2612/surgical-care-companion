import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Phone, MessageCircle, AlertTriangle, Clock, User } from 'lucide-react';

interface Conversation {
  id: string;
  patient_id: string;
  patient_name: string;
  phone_number: string;
  call_status: string;
  call_duration: number;
  intent: string;
  sentiment: string;
  urgency_level: string;
  pain_level: number;
  symptoms: string[];
  concerns: string[];
  actions_required: string[];
  started_at: string;
  ended_at: string;
  transcript: string;
  conversation_json: {
    messages: Array<{
      role: string;
      content: string;
      timestamp: string;
      audio_url?: string;
    }>;
  };
}

const CallDashboard: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await fetch('/api/v1/conversations');
      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      case 'anxious':
        return 'text-orange-600';
      case 'distressed':
        return 'text-red-500';
      default:
        return 'text-gray-600';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Call Dashboard</h1>
        <p className="text-gray-600">Monitor and manage patient voice interactions</p>
      </div>

      <Tabs defaultValue="recent" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="recent">Recent Calls</TabsTrigger>
          <TabsTrigger value="urgent">Urgent Cases</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="recent" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {conversations.map((conversation) => (
              <Card 
                key={conversation.id} 
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedConversation(conversation)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <User className="h-5 w-5" />
                      {conversation.patient_name}
                    </CardTitle>
                    <Badge className={getUrgencyColor(conversation.urgency_level)}>
                      {conversation.urgency_level}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Phone className="h-4 w-4" />
                      {conversation.phone_number}
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="h-4 w-4" />
                      {conversation.call_duration ? formatDuration(conversation.call_duration) : 'In progress'}
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <MessageCircle className="h-4 w-4" />
                      <span className={getSentimentColor(conversation.sentiment)}>
                        {conversation.sentiment}
                      </span>
                    </div>

                    {conversation.pain_level && (
                      <div className="text-sm">
                        <span className="font-medium">Pain Level:</span> {conversation.pain_level}/10
                      </div>
                    )}

                    {conversation.symptoms && conversation.symptoms.length > 0 && (
                      <div className="text-sm">
                        <span className="font-medium">Symptoms:</span> {conversation.symptoms.join(', ')}
                      </div>
                    )}

                    <div className="text-xs text-gray-500 mt-2">
                      {formatDateTime(conversation.started_at)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="urgent" className="space-y-4">
          <div className="grid gap-4">
            {conversations
              .filter(c => c.urgency_level === 'critical' || c.urgency_level === 'high')
              .map((conversation) => (
                <Card key={conversation.id} className="border-l-4 border-red-500">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                        {conversation.patient_name}
                      </CardTitle>
                      <Badge className={getUrgencyColor(conversation.urgency_level)}>
                        {conversation.urgency_level}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        <strong>Intent:</strong> {conversation.intent}
                      </p>
                      
                      {conversation.concerns && conversation.concerns.length > 0 && (
                        <div className="text-sm">
                          <strong>Concerns:</strong>
                          <ul className="list-disc list-inside mt-1">
                            {conversation.concerns.map((concern, index) => (
                              <li key={index} className="text-red-600">{concern}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {conversation.actions_required && conversation.actions_required.length > 0 && (
                        <div className="text-sm">
                          <strong>Actions Required:</strong>
                          <ul className="list-disc list-inside mt-1">
                            {conversation.actions_required.map((action, index) => (
                              <li key={index} className="text-blue-600">{action}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div className="flex justify-between items-center mt-4">
                        <span className="text-xs text-gray-500">
                          {formatDateTime(conversation.started_at)}
                        </span>
                        <Button 
                          size="sm" 
                          onClick={() => setSelectedConversation(conversation)}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{conversations.length}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Urgent Cases</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {conversations.filter(c => c.urgency_level === 'critical' || c.urgency_level === 'high').length}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Avg Pain Level</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {conversations.filter(c => c.pain_level).length > 0 
                    ? (conversations.filter(c => c.pain_level).reduce((acc, c) => acc + c.pain_level, 0) / conversations.filter(c => c.pain_level).length).toFixed(1)
                    : 'N/A'
                  }
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Completed Calls</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {conversations.filter(c => c.call_status === 'completed').length}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Conversation Detail Modal */}
      {selectedConversation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Conversation Details</h2>
              <Button variant="outline" onClick={() => setSelectedConversation(null)}>
                Close
              </Button>
            </div>
            
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold mb-2">Patient Information</h3>
                  <p><strong>Name:</strong> {selectedConversation.patient_name}</p>
                  <p><strong>Phone:</strong> {selectedConversation.phone_number}</p>
                  <p><strong>Started:</strong> {formatDateTime(selectedConversation.started_at)}</p>
                  {selectedConversation.ended_at && (
                    <p><strong>Ended:</strong> {formatDateTime(selectedConversation.ended_at)}</p>
                  )}
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">Analysis</h3>
                  <p><strong>Intent:</strong> {selectedConversation.intent}</p>
                  <p><strong>Sentiment:</strong> <span className={getSentimentColor(selectedConversation.sentiment)}>{selectedConversation.sentiment}</span></p>
                  <p><strong>Urgency:</strong> <Badge className={getUrgencyColor(selectedConversation.urgency_level)}>{selectedConversation.urgency_level}</Badge></p>
                  {selectedConversation.pain_level && (
                    <p><strong>Pain Level:</strong> {selectedConversation.pain_level}/10</p>
                  )}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Conversation Transcript</h3>
                <div className="bg-gray-50 p-4 rounded-lg max-h-60 overflow-y-auto">
                  {selectedConversation.conversation_json?.messages?.map((message, index) => (
                    <div key={index} className="mb-3 p-2 bg-white rounded">
                      <div className="text-sm text-gray-600 mb-1">
                        <strong>{message.role}:</strong> {formatDateTime(message.timestamp)}
                      </div>
                      <div className="text-sm">{message.content}</div>
                    </div>
                  ))}
                </div>
              </div>

              {selectedConversation.transcript && (
                <div>
                  <h3 className="font-semibold mb-2">Full Transcript</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">{selectedConversation.transcript}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CallDashboard;
