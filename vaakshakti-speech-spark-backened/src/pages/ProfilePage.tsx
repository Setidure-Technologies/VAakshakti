import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiService, UserStats } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { 
  User, 
  Mail, 
  Calendar, 
  TrendingUp, 
  BarChart3, 
  Award,
  Clock,
  Target,
  Edit,
  Save,
  X
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner'; // Changed to named import

const ProfilePage: React.FC = () => {
  const { currentUser, fetchCurrentUser } = useAuth();
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [formData, setFormData] = useState({
    full_name: currentUser?.full_name || '',
    email: currentUser?.email || ''
  });

  useEffect(() => {
    if (currentUser) {
      setFormData({
        full_name: currentUser.full_name || '',
        email: currentUser.email || ''
      });
    }
  }, [currentUser]);

  useEffect(() => {
    loadUserStats();
  }, []);

  const loadUserStats = async () => {
    try {
      setStatsLoading(true);
      const stats = await apiService.getUserStats(30);
      setUserStats(stats);
    } catch (error) {
      console.error('Error loading user stats:', error);
      toast({
        title: "Error",
        description: "Failed to load user statistics",
        variant: "destructive",
      });
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      await apiService.updateUserProfile(formData);
      await fetchCurrentUser();
      setIsEditing(false);
      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      full_name: currentUser?.full_name || '',
      email: currentUser?.email || ''
    });
    setIsEditing(false);
  };

  const getImprovementBadge = (trend: string) => {
    switch (trend) {
      case 'improving':
        // Using 'default' variant which is often primary/positive.
        // Custom styling can be added by extending badgeVariants if needed.
        return <Badge variant="default">📈 Improving</Badge>;
      case 'declining':
        return <Badge variant="destructive">📉 Needs Focus</Badge>;
      case 'stable':
        return <Badge variant="secondary">📊 Stable</Badge>; // Or another appropriate variant
      default:
        return <Badge variant="outline">📋 No Data</Badge>;
    }
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return 'text-green-600';
    if (rating >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!currentUser) {
    return <LoadingSpinner />;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Profile</h1>
        <p className="text-gray-600">Manage your account and view your progress</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Information */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Profile Information</span>
                {!isEditing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    className="ml-auto"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isEditing ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                      placeholder="Enter your full name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="Enter your email"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      onClick={handleSave}
                      disabled={isLoading}
                      className="flex-1"
                    >
                      {isLoading ? (
                        <LoadingSpinner />
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          Save
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCancel}
                      disabled={isLoading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {currentUser.full_name?.charAt(0) || currentUser.email.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold">{currentUser.full_name || 'No name set'}</p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <Mail className="h-4 w-4 mr-1" />
                        {currentUser.email}
                      </p>
                    </div>
                  </div>
                  <Separator />
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600 flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      Member since {new Date(currentUser.created_at || Date.now()).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-gray-600 flex items-center">
                      <Clock className="h-4 w-4 mr-2" />
                      Last login: {currentUser.last_login ? new Date(currentUser.last_login).toLocaleDateString() : 'Never'}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Statistics */}
        <div className="lg:col-span-2">
          <div className="space-y-6">
            {/* Overview Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Performance Overview (Last 30 Days)</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {statsLoading ? (
                  <div className="flex justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : userStats ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{userStats.total_sessions}</div>
                      <div className="text-sm text-gray-600">Total Sessions</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className={`text-2xl font-bold ${getRatingColor(userStats.average_rating)}`}>
                        {userStats.average_rating.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-600">Average Rating</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {getImprovementBadge(userStats.improvement_trend)}
                      </div>
                      <div className="text-sm text-gray-600">Trend</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No statistics available. Start practicing to see your progress!
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Difficulty Breakdown */}
            {userStats && Object.keys(userStats.difficulty_breakdown).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="h-5 w-5" />
                    <span>Performance by Difficulty</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(userStats.difficulty_breakdown).map(([difficulty, stats]) => (
                      <div key={difficulty} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Badge variant={
                            difficulty.toLowerCase() === 'easy' ? 'default' :
                            difficulty.toLowerCase() === 'medium' ? 'secondary' :
                            difficulty.toLowerCase() === 'hard' ? 'destructive' : 'outline'
                          }>
                            {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                          </Badge>
                          <span className="text-sm text-gray-600">
                            {(stats as any).count} sessions
                          </span>
                        </div>
                        <div className={`font-semibold ${getRatingColor((stats as any).avg_rating)}`}>
                          {((stats as any).avg_rating).toFixed(1)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Sessions */}
            {userStats && userStats.recent_sessions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Award className="h-5 w-5" />
                    <span>Recent Sessions</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {userStats.recent_sessions.slice(0, 5).map((session) => (
                      <div key={session.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium text-sm">{session.topic}</p>
                          <p className="text-xs text-gray-600">
                            {new Date(session.created_at).toLocaleDateString()} • {session.difficulty}
                          </p>
                        </div>
                        <div className={`font-semibold ${getRatingColor(session.rating)}`}>
                          {session.rating.toFixed(1)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Improvement Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5" />
                  <span>Improvement Tips</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-800">Practice Regularly</p>
                    <p className="text-xs text-blue-600">Consistent practice leads to better results. Try to practice at least 3 times a week.</p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-800">Focus on Weak Areas</p>
                    <p className="text-xs text-green-600">Review your feedback and focus on areas that need improvement.</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm font-medium text-purple-800">Challenge Yourself</p>
                    <p className="text-xs text-purple-600">Gradually increase difficulty levels to improve your skills.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;