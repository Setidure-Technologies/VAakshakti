import React from 'react';
import { PracticeSessionRead } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Star, FileText, CheckCircle, Mic, BookOpen } from 'lucide-react';

const FeedbackCard: React.FC<{ title: string; content: string | null | undefined; icon: React.ReactNode; }> = ({ title, content, icon }) => {
  if (!content) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center space-x-3">
                {icon}
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-gray-500">Not available.</p>
            </CardContent>
        </Card>
    );
  }
  return (
    <Card>
        <CardHeader className="flex flex-row items-center space-x-3">
            {icon}
            <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
            <p className="text-gray-800 whitespace-pre-wrap">{content}</p>
        </CardContent>
    </Card>
  );
};

interface EvaluationResultsProps {
  session: PracticeSessionRead;
}

const EvaluationResults: React.FC<EvaluationResultsProps> = ({ session }) => {
  if (!session) {
    return (
        <div className="text-center p-4">
            <p className="text-gray-500">No session data available.</p>
        </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn p-4">
      {/* Summary Card */}
      <Card className="bg-gradient-to-r from-purple-100 to-pink-100">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Star className="text-yellow-500" />
            <span>Overall Rating: {session.rating.toFixed(1)} / 5.0</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-800 leading-relaxed">
            {session.final_feedback || "Your evaluation is complete. Please review the detailed feedback in the sections below."}
          </p>
        </CardContent>
      </Card>

      {/* Transcription and Ideal Answer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <FeedbackCard title="Your Transcription" content={session.transcript} icon={<FileText />} />
        <FeedbackCard title="Ideal Answer" content={session.ideal_answer} icon={<CheckCircle />} />
      </div>

      {/* Detailed Feedback Sections */}
      <div className="space-y-6">
        <FeedbackCard 
          title="Content Feedback" 
          content={session.content_feedback} 
          icon={<BookOpen />} 
        />
        <FeedbackCard 
          title="Pronunciation & Fluency Feedback" 
          content={session.pronunciation_feedback} 
          icon={<Mic />} 
        />
      </div>
    </div>
  );
};

export { EvaluationResults };
