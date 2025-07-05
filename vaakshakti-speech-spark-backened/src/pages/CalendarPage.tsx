import React, { useState, useEffect } from 'react';
import { apiService, BookingSlot } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { 
  Calendar, 
  Clock, 
  Plus, 
  Edit, 
  Trash2, 
  CheckCircle,
  XCircle,
  AlertCircle,
  Users
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner'; // Changed to named import

const CalendarPage: React.FC = () => {
  const { toast } = useToast();
  const [bookings, setBookings] = useState<BookingSlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [editingBooking, setEditingBooking] = useState<BookingSlot | null>(null);
  const [formData, setFormData] = useState({
    scheduled_time: '',
    duration_minutes: 30,
    session_type: '',
    topic: '',
    notes: ''
  });

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      setIsLoading(true);
      const userBookings = await apiService.getUserBookings();
      setBookings(userBookings);
    } catch (error) {
      console.error('Error loading bookings:', error);
      toast({
        title: "Error",
        description: "Failed to load bookings",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.scheduled_time || !formData.session_type) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    try {
      if (editingBooking) {
        await apiService.updateBooking(editingBooking.id, formData);
        toast({
          title: "Success",
          description: "Booking updated successfully",
        });
      } else {
        await apiService.createBooking(formData);
        toast({
          title: "Success",
          description: "Booking created successfully",
        });
      }
      
      resetForm();
      loadBookings();
    } catch (error) {
      console.error('Error saving booking:', error);
      toast({
        title: "Error",
        description: "Failed to save booking",
        variant: "destructive",
      });
    }
  };

  const handleEdit = (booking: BookingSlot) => {
    setEditingBooking(booking);
    setFormData({
      scheduled_time: new Date(booking.scheduled_time).toISOString().slice(0, 16),
      duration_minutes: booking.duration_minutes,
      session_type: booking.session_type,
      topic: booking.topic || '',
      notes: booking.notes || ''
    });
    setShowBookingForm(true);
  };

  const handleCancel = async (bookingId: number) => {
    try {
      await apiService.cancelBooking(bookingId);
      toast({
        title: "Success",
        description: "Booking cancelled successfully",
      });
      loadBookings();
    } catch (error) {
      console.error('Error cancelling booking:', error);
      toast({
        title: "Error",
        description: "Failed to cancel booking",
        variant: "destructive",
      });
    }
  };

  const resetForm = () => {
    setFormData({
      scheduled_time: '',
      duration_minutes: 30,
      session_type: '',
      topic: '',
      notes: ''
    });
    setShowBookingForm(false);
    setEditingBooking(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'no_show':
        return <AlertCircle className="h-4 w-4 text-orange-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'no_show': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSessionTypeColor = (type: string) => {
    switch (type) {
      case 'practice': return 'bg-blue-100 text-blue-800';
      case 'interview': return 'bg-purple-100 text-purple-800';
      case 'evaluation': return 'bg-green-100 text-green-800';
      case 'consultation': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const upcomingBookings = bookings.filter(booking => 
    new Date(booking.scheduled_time) > new Date() && booking.status === 'scheduled'
  );

  const pastBookings = bookings.filter(booking => 
    new Date(booking.scheduled_time) <= new Date() || booking.status !== 'scheduled'
  );

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center space-x-2">
              <Calendar className="h-8 w-8" />
              <span>Session Calendar</span>
            </h1>
            <p className="text-gray-600">Schedule and manage your practice sessions</p>
          </div>
          <Button 
            onClick={() => setShowBookingForm(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Book Session
          </Button>
        </div>
      </div>

      {/* Booking Form */}
      {showBookingForm && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>
              {editingBooking ? 'Edit Booking' : 'Book New Session'}
            </CardTitle>
            <CardDescription>
              Schedule a practice session, interview, or consultation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="scheduled_time">Date & Time *</Label>
                  <Input
                    id="scheduled_time"
                    type="datetime-local"
                    value={formData.scheduled_time}
                    onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                    min={new Date().toISOString().slice(0, 16)}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="duration_minutes">Duration (minutes)</Label>
                  <Select 
                    value={formData.duration_minutes.toString()} 
                    onValueChange={(value) => setFormData({ ...formData, duration_minutes: parseInt(value) })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="45">45 minutes</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                      <SelectItem value="90">1.5 hours</SelectItem>
                      <SelectItem value="120">2 hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="session_type">Session Type *</Label>
                  <Select 
                    value={formData.session_type} 
                    onValueChange={(value) => setFormData({ ...formData, session_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select session type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="practice">Practice Session</SelectItem>
                      <SelectItem value="interview">Mock Interview</SelectItem>
                      <SelectItem value="evaluation">Skill Evaluation</SelectItem>
                      <SelectItem value="consultation">Consultation</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="topic">Topic (Optional)</Label>
                  <Input
                    id="topic"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    placeholder="e.g., Business Communication, Academic Discussion"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Notes (Optional)</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Any specific requirements or notes for this session"
                  rows={3}
                />
              </div>

              <div className="flex space-x-2">
                <Button type="submit">
                  {editingBooking ? 'Update Booking' : 'Book Session'}
                </Button>
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Upcoming Bookings */}
          <div>
            <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
              <Clock className="h-6 w-6" />
              <span>Upcoming Sessions</span>
              {upcomingBookings.length > 0 && (
                <Badge variant="secondary">{upcomingBookings.length}</Badge>
              )}
            </h2>
            
            {upcomingBookings.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-600 mb-2">No Upcoming Sessions</h3>
                  <p className="text-gray-500 mb-4">
                    You don't have any scheduled sessions. Book a session to get started!
                  </p>
                  <Button onClick={() => setShowBookingForm(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Book Your First Session
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {upcomingBookings.map((booking) => (
                  <Card key={booking.id} className="hover:shadow-lg transition-shadow duration-300">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg flex items-center space-x-2">
                            {getStatusIcon(booking.status)}
                            <span>{booking.session_type.charAt(0).toUpperCase() + booking.session_type.slice(1)}</span>
                          </CardTitle>
                          <CardDescription>
                            {new Date(booking.scheduled_time).toLocaleString()}
                          </CardDescription>
                        </div>
                        <Badge className={getSessionTypeColor(booking.session_type)}>
                          {booking.duration_minutes}min
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {booking.topic && (
                          <p className="text-sm"><strong>Topic:</strong> {booking.topic}</p>
                        )}
                        {booking.notes && (
                          <p className="text-sm text-gray-600">{booking.notes}</p>
                        )}
                        
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(booking.status)}>
                            {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                          </Badge>
                        </div>
                        
                        <div className="flex space-x-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleEdit(booking)}
                          >
                            <Edit className="h-3 w-3 mr-1" />
                            Edit
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleCancel(booking.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-3 w-3 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Past Bookings */}
          {pastBookings.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
                <Users className="h-6 w-6" />
                <span>Past Sessions</span>
                <Badge variant="secondary">{pastBookings.length}</Badge>
              </h2>
              
              <div className="space-y-3">
                {pastBookings.slice(0, 10).map((booking) => (
                  <Card key={booking.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          {getStatusIcon(booking.status)}
                          <div>
                            <h3 className="font-semibold">
                              {booking.session_type.charAt(0).toUpperCase() + booking.session_type.slice(1)}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {new Date(booking.scheduled_time).toLocaleString()}
                            </p>
                            {booking.topic && (
                              <p className="text-sm text-gray-500">{booking.topic}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(booking.status)}>
                            {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                          </Badge>
                          <Badge variant="outline">
                            {booking.duration_minutes}min
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CalendarPage;