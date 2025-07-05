import React, { useState, useEffect } from 'react';
import { apiService, PracticeSessionRead } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { History, Eye, RefreshCw, MessageSquare, Calendar } from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { EvaluationResults } from '@/components/EvaluationResults'; // Import the results component

const HistoryPage: React.FC = () => {
  const { toast } = useToast();
  const [sessions, setSessions] = useState<PracticeSessionRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<PracticeSessionRead | null>(null);

  const loadHistory = async () => {
    try {
      setIsLoading(true);
      const history = await apiService.getUserHistory();
      setSessions(history);
    } catch (error) {
      console.error('Error loading history:', error);
      toast({
        title: "Error",
        description: "Failed to load session history.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center space-x-2">
            <History className="h-8 w-8" />
            <span>Session History</span>
          </h1>
          <p className="text-gray-600">View your past practice sessions.</p>
        </div>
        <Button onClick={loadHistory} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : sessions.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No History Found</h3>
            <p className="text-gray-500">You haven't completed any practice sessions yet.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sessions.map((session) => (
            <Card key={session.id} className="hover:shadow-lg transition-shadow duration-300">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg mb-2">{session.topic}</CardTitle>
                  <Badge variant={session.rating >= 4 ? "default" : session.rating >= 2.5 ? "secondary" : "destructive"}>
                    Rating: {session.rating.toFixed(1)}/5.0
                  </Badge>
                </div>
                <CardDescription className="text-sm line-clamp-2">{session.question}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    {new Date(session.created_at).toLocaleDateString()}
                  </div>
                  <Button onClick={() => setSelectedSession(session)} variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {selectedSession && (
         <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
           <Card className="max-w-4xl w-full max-h-[90vh] flex flex-col">
             <CardHeader className="flex flex-row items-center justify-between">
               <CardTitle>Evaluation Results</CardTitle>
               <Button variant="ghost" size="icon" onClick={() => setSelectedSession(null)}>✕</Button>
             </CardHeader>
             <CardContent className="overflow-y-auto">
               <EvaluationResults session={selectedSession} />
             </CardContent>
           </Card>
         </div>
      )}
    </div>
  );
};

export default HistoryPage;