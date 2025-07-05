import React, { useState, useEffect, useRef } from 'react';
import { apiService, QuestionResponse, TaskStatusResponse, PracticeSessionRead } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { TopicSelector } from '@/components/TopicSelector';
import { QuestionDisplay } from '@/components/QuestionDisplay';
import { AudioRecorder } from '@/components/AudioRecorder';
import { EvaluationResults } from '@/components/EvaluationResults';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Terminal, RefreshCw, CheckCircle, XCircle, Loader } from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';

type EvaluationState = 'idle' | 'generating' | 'ready' | 'recording' | 'uploading' | 'polling' | 'completed' | 'error';

const Index: React.FC = () => {
  const { toast } = useToast();
  const [evaluationState, setEvaluationState] = useState<EvaluationState>('idle');
  const [topic, setTopic] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('medium');
  const [question, setQuestion] = useState<string>('');
  const [idealAnswer, setIdealAnswer] = useState<string>('');
  const [customQuestion, setCustomQuestion] = useState<string>('');
  const [useCustomQuestion, setUseCustomQuestion] = useState<boolean>(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [pollingError, setPollingError] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [finalSession, setFinalSession] = useState<PracticeSessionRead | null>(null);
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const handleGetQuestion = async () => {
    if (!topic) {
      toast({ title: "Topic Required", description: "Please select a topic first.", variant: "destructive" });
      return;
    }
    setEvaluationState('generating');
    setFinalSession(null);
    setTaskStatus(null);
    setTaskId(null);
    try {
      const response: QuestionResponse = await apiService.generateQuestion(topic, difficulty);
      setQuestion(response.question);
      setIdealAnswer(response.ideal_answer);
      setEvaluationState('ready');
    } catch (error) {
      console.error('Error generating question:', error);
      toast({ title: "Error", description: "Failed to generate a question.", variant: "destructive" });
      setEvaluationState('error');
    }
  };

  const handleRecordingComplete = async (audioBlob: Blob) => {
    setEvaluationState('uploading');
    const finalQuestion = useCustomQuestion ? customQuestion : question;
    // When using a custom question, the ideal answer is unknown.
    const finalIdealAnswer = useCustomQuestion ? "" : idealAnswer;

    try {
      const response = await apiService.evaluateSpeech(audioBlob, topic, finalQuestion, finalIdealAnswer, difficulty);
      setTaskId(response.task_id);
      setEvaluationState('polling');
    } catch (error) {
      console.error('Error starting evaluation:', error);
      toast({ title: "Upload Failed", description: "Could not start the evaluation.", variant: "destructive" });
      setEvaluationState('error');
    }
  };

  const pollTaskStatus = async () => {
    if (!taskId) return;

    try {
      const status = await apiService.getTaskStatus(taskId);
      setTaskStatus(status);

      if (status.status === 'completed') {
        setEvaluationState('completed');
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
        
        // The result of the parent task should now contain the ID of the PracticeSession
        const sessionId = status.result?.practice_session_id;
        if (sessionId) {
          // Fetch the final, consolidated session data
          const sessionData = await apiService.getSessionAnalysis(sessionId);
          setFinalSession(sessionData);
        } else {
            throw new Error("Task completed but session ID was not found in the result.");
        }

      } else if (status.status === 'failed') {
        setEvaluationState('error');
        setPollingError(status.error_message || "An unknown error occurred during processing.");
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
      }
    } catch (error) {
      console.error('Error polling task status:', error);
      setEvaluationState('error');
      setPollingError("Failed to get task status. Please check your connection.");
      if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
    }
  };

  useEffect(() => {
    if (evaluationState === 'polling' && taskId) {
      pollingIntervalRef.current = setInterval(pollTaskStatus, 3000);
    }
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [evaluationState, taskId]);

  const resetState = () => {
    setEvaluationState('idle');
    setTopic('');
    setQuestion('');
    setIdealAnswer('');
    setTaskId(null);
    setTaskStatus(null);
    setFinalSession(null);
    setPollingError(null);
  };

  const renderPollingStatus = () => {
    if (!taskStatus) return <LoadingSpinner />;
    
    const completedCount = taskStatus.components.filter(c => c.status === 'completed').length;
    const totalCount = taskStatus.components.length;

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Loader className="animate-spin" />
          <p className="font-semibold">Processing your speech... ({taskStatus.progress}%)</p>
        </div>
        <p className="text-sm text-gray-600">{taskStatus.status_message}</p>
        <div className="space-y-2">
          {taskStatus.components.map(comp => (
            <div key={comp.component_id} className="flex items-center justify-between text-sm p-2 bg-gray-100 rounded-md">
              <span>{comp.component_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
              {comp.status === 'completed' && <CheckCircle className="text-green-500" />}
              {comp.status === 'failed' && <XCircle className="text-red-500" />}
              {(comp.status === 'pending' || comp.status === 'processing') && <Loader size={16} className="animate-spin" />}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-4xl font-bold text-center mb-2">Practice Arena</h1>
      <p className="text-center text-gray-600 mb-8">Select a topic, get a question, and start your practice session.</p>

      <Card className="mb-8">
        <CardContent className="p-6">
          {evaluationState === 'idle' && (
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <TopicSelector onTopicChange={setTopic} onDifficultyChange={setDifficulty} />
              <Button onClick={handleGetQuestion} disabled={!topic}>Get Question</Button>
            </div>
          )}
          {evaluationState === 'generating' && <LoadingSpinner text="Generating question..." />}
          {(evaluationState === 'ready' || evaluationState === 'recording') && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Your Question</h2>
                <Button variant="link" onClick={() => setUseCustomQuestion(!useCustomQuestion)}>
                  {useCustomQuestion ? 'Use Generated Question' : 'Write Your Own Question'}
                </Button>
              </div>
              {useCustomQuestion ? (
                <textarea
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter your custom question here..."
                  rows={4}
                />
              ) : (
                <QuestionDisplay question={question} />
              )}
              <AudioRecorder onRecordingComplete={handleRecordingComplete} />
            </div>
          )}
          {(evaluationState === 'uploading' || evaluationState === 'polling') && (
            <div className="p-6 text-center">
              {renderPollingStatus()}
            </div>
          )}
          {evaluationState === 'completed' && finalSession && (
            <div>
              <EvaluationResults session={finalSession} />
              <Button onClick={resetState} className="mt-6 w-full">Start New Session</Button>
            </div>
          )}
          {evaluationState === 'error' && (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>An Error Occurred</AlertTitle>
              <AlertDescription>{pollingError || "Something went wrong. Please try again."}</AlertDescription>
              <Button onClick={resetState} variant="outline" className="mt-4">Try Again</Button>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Index;
