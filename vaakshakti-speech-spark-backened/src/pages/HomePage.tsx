import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Mic, 
  Brain, 
  BarChart3, 
  Calendar, 
  Users, 
  BookOpen, 
  Zap, 
  Shield,
  Clock,
  TrendingUp,
  Heart,
  Volume2
} from 'lucide-react';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: <Mic className="h-6 w-6" />,
      title: "Speech Analysis",
      description: "Advanced speech-to-text with pronunciation feedback and fluency assessment."
    },
    {
      icon: <Brain className="h-6 w-6" />,
      title: "AI-Powered Evaluation",
      description: "Comprehensive language analysis using state-of-the-art AI models."
    },
    {
      icon: <Heart className="h-6 w-6" />,
      title: "Emotion Detection",
      description: "Analyze emotional tone and sentiment in your speech patterns."
    },
    {
      icon: <Volume2 className="h-6 w-6" />,
      title: "Prosodic Analysis",
      description: "Detailed analysis of pitch, intonation, rhythm, and speaking rate."
    },
    {
      icon: <BarChart3 className="h-6 w-6" />,
      title: "Progress Tracking",
      description: "Monitor your improvement with detailed analytics and insights."
    },
    {
      icon: <Calendar className="h-6 w-6" />,
      title: "Session Booking",
      description: "Schedule practice sessions and track your learning journey."
    }
  ];

  const howItWorks = [
    {
      step: "1",
      title: "Choose Your Topic",
      description: "Select from various topics and difficulty levels to match your learning goals."
    },
    {
      step: "2",
      title: "Record Your Response",
      description: "Answer the generated question by recording your speech using our intuitive interface."
    },
    {
      step: "3",
      title: "Get AI Analysis",
      description: "Receive comprehensive feedback on grammar, pronunciation, content, and emotional tone."
    },
    {
      step: "4",
      title: "Track Progress",
      description: "Monitor your improvement over time with detailed analytics and personalized insights."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full">
              <Mic className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-6">
            VaakShakti AI
          </h1>
          <p className="text-xl text-gray-600 mb-4 max-w-3xl mx-auto">
            Holistic Language Assistant Platform
          </p>
          <p className="text-lg text-gray-500 mb-8 max-w-4xl mx-auto">
            Master your communication skills with AI-powered speech analysis, emotion detection, 
            and comprehensive language evaluation. Get real-time feedback on pronunciation, 
            grammar, fluency, and emotional intelligence.
          </p>
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <Badge variant="secondary" className="px-4 py-2">
              <Zap className="h-4 w-4 mr-2" />
              Real-time Analysis
            </Badge>
            <Badge variant="secondary" className="px-4 py-2">
              <Shield className="h-4 w-4 mr-2" />
              Secure & Private
            </Badge>
            <Badge variant="secondary" className="px-4 py-2">
              <Users className="h-4 w-4 mr-2" />
              Multi-user Support
            </Badge>
            <Badge variant="secondary" className="px-4 py-2">
              <Clock className="h-4 w-4 mr-2" />
              24/7 Available
            </Badge>
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/practice">
              <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                Start Practicing
              </Button>
            </Link>
            <Link to="/register">
              <Button size="lg" variant="outline">
                Create Account
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {howItWorks.map((step, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow duration-300">
                <CardHeader>
                  <div className="mx-auto w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg mb-4">
                    {step.step}
                  </div>
                  <CardTitle className="text-lg">{step.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-600">
                    {step.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <Separator className="my-16" />

        {/* Documentation Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Platform Documentation</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Getting Started */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BookOpen className="h-5 w-5" />
                  <span>Getting Started</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">1. Create Your Account</h4>
                  <p className="text-gray-600 text-sm">
                    Sign up with your email to access all features and track your progress.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">2. Choose Practice Mode</h4>
                  <p className="text-gray-600 text-sm">
                    Select from various topics like business communication, academic discussions, or casual conversations.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">3. Set Difficulty Level</h4>
                  <p className="text-gray-600 text-sm">
                    Choose Easy, Medium, or Hard based on your current proficiency level.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Analysis Features */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>Analysis Features</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Speech-to-Text</h4>
                  <p className="text-gray-600 text-sm">
                    Advanced ASR technology converts your speech to text with high accuracy.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Grammar & Pronunciation</h4>
                  <p className="text-gray-600 text-sm">
                    Get detailed feedback on grammar mistakes and pronunciation issues.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Emotion & Sentiment</h4>
                  <p className="text-gray-600 text-sm">
                    Understand the emotional tone and sentiment of your speech patterns.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Booking System */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5" />
                  <span>Session Booking</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Schedule Sessions</h4>
                  <p className="text-gray-600 text-sm">
                    Book practice sessions, interviews, or consultation slots at your convenience.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Session Types</h4>
                  <p className="text-gray-600 text-sm">
                    Choose from Practice, Interview, Evaluation, or Consultation sessions.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Reminders</h4>
                  <p className="text-gray-600 text-sm">
                    Get notifications and reminders for your upcoming sessions.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Progress Tracking */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5" />
                  <span>Progress Tracking</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Performance Analytics</h4>
                  <p className="text-gray-600 text-sm">
                    View detailed statistics on your speaking performance and improvement trends.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Session History</h4>
                  <p className="text-gray-600 text-sm">
                    Access all your past sessions with detailed analysis and feedback.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Personalized Insights</h4>
                  <p className="text-gray-600 text-sm">
                    Get AI-powered recommendations for improving your communication skills.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Technical Features */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Technical Capabilities</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle>Language Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Real-time speech-to-text conversion</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Grammar and syntax analysis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Pronunciation assessment</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Fluency and coherence evaluation</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Vocabulary complexity analysis</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Advanced Features</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Emotion recognition from speech</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Sentiment analysis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Prosodic feature extraction</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Background task processing</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Multi-user concurrent support</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to Improve Your Communication?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of users who are already enhancing their language skills with VaakShakti AI.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register">
              <Button size="lg" variant="secondary">
                Get Started Free
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;