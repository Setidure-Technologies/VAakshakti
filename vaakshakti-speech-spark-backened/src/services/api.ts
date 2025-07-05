// API Base URL - Vite will proxy requests starting with /api/v1
const API_BASE_URL = "/api/v1";

const getToken = (): string | null => {
  return localStorage.getItem("accessToken");
};

const getRefreshToken = (): string | null => {
  return localStorage.getItem("refreshToken");
};

// --- Request Headers ---
const getAuthHeaders = () => {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

const getAuthHeadersFormData = () => {
  const token = getToken();
  return {
    ...(token && { Authorization: `Bearer ${token}` }),
    // Content-Type is set automatically by FormData
  };
};

// --- Centralized Fetch with Auth and Refresh Logic ---
let isRefreshing = false;
// Queue for requests that failed due to 401 while token is being refreshed
type FailedRequest = {
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
  url: string;
  options: RequestInit;
};
let failedQueue: FailedRequest[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      // Update token for the retried request
      if (prom.options.headers && token) {
        (prom.options.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
      }
      // Retry the original request
      fetch(prom.url, prom.options).then(response => {
        // If retry is successful, resolve with the new response
        // If retry also fails (e.g. 401 again, or other error), reject
        if (response.ok) {
          prom.resolve(response);
        } else {
          // If retry fails, reject with an error indicating retry failure
           response.json().catch(() => ({ detail: response.statusText }))
           .then(errorData => prom.reject(new Error(`Request failed after refresh: ${errorData.detail || response.statusText} (Status: ${response.status})`)));
        }
      }).catch(prom.reject);
    }
  });
  failedQueue = [];
};

const internalLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    // Here, you might want to redirect to login or use a global state update
    // For simplicity, we're just clearing tokens. AuthContext should react to this.
    console.warn("Internal logout triggered due to token refresh failure.");
    // Attempt to navigate to login page, if window is available (client-side)
    if (typeof window !== 'undefined') {
        window.location.href = '/login';
    }
};

const fetchWithAuth = async (url: string, options: RequestInit): Promise<Response> => {
  let currentToken = getToken();
  // Ensure options.headers exists before trying to set Authorization
  if (!options.headers) {
    options.headers = {};
  }
  if (currentToken) {
    (options.headers as Record<string, string>)['Authorization'] = `Bearer ${currentToken}`;
  }

  let response = await fetch(url, options);

  if (response.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const newTokens = await apiService.refreshToken(); // Call the refreshToken method of apiService
        isRefreshing = false;
        if (newTokens && newTokens.access_token) {
          processQueue(null, newTokens.access_token);
          // Retry the original request with the new token in headers
          if (options.headers) { // Headers should exist now
            (options.headers as Record<string, string>)['Authorization'] = `Bearer ${newTokens.access_token}`;
          }
          return fetch(url, options);
        } else {
          // Refresh failed or no new token
          internalLogout(); // Perform local logout
          processQueue(new Error("Session expired. Please log in again."), null);
          throw new Error("Session expired. Please log in again.");
        }
      } catch (refreshError: any) {
        isRefreshing = false;
        internalLogout(); // Perform local logout on refresh error
        processQueue(refreshError, null);
        throw refreshError;
      }
    } else {
      // Add to queue if refresh is already in progress
      return new Promise<Response>((resolve, reject) => {
        failedQueue.push({ resolve, reject, url, options });
      });
    }
  }
  return response;
};


// --- Response Interfaces (matching FastAPI Pydantic models) ---
export interface QuestionResponse {
  question: string;
  ideal_answer: string;
}

export interface SpeechEvaluationResponse {
  transcript: string;
  grammar_feedback: string;
  pronunciation_feedback: string;
  content_evaluation: string;
  rating: number;
}

export interface InterviewQuestionsResponse {
  interview_questions: string;
}

export interface UserRead {
  id: number;
  email: string;
  full_name?: string | null; // Match Optional[str]
  bio?: string | null; // Added
  avatar_url?: string | null; // Added
  created_at: string; // Assuming datetime is serialized as string
  last_login?: string | null; // Added, assuming datetime is serialized as string
  is_active: boolean; // Added
}

export interface PracticeSessionRead {
  id: number;
  parent_task_id: string;
  topic: string;
  difficulty: string;
  question: string;
  ideal_answer: string;
  transcript: string;
  grammar_feedback?: string | null;
  pronunciation_feedback?: string | null;
  content_evaluation?: string | null;
  audio_features?: string | null;
  linguistic_features?: string | null;
  sentiment_analysis?: string | null;
  emotion_analysis?: string | null;
  rating: number;
  created_at: string;
  user_id: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  refresh_token: string; // Added refresh_token
}

// Matches the ComponentStatusDetail Pydantic model in main.py
export interface ComponentStatusDetail {
  component_id: number;
  component_type: string;
  status: string;
  status_message?: string | null;
  result?: any | null; // The result can be any object
  error_message?: string | null;
  updated_at: string; // datetime serialized as string
}

// Matches the updated TaskStatusResponse Pydantic model in main.py
export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: number;
  status_message?: string | null;
  result?: any | null; // Parent task's result
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  components: ComponentStatusDetail[]; // The array of component results
}

export interface SpeechEvaluationTaskResponse {
  task_id: string;
  message: string;
}

export interface BookingSlot {
  id: number;
  scheduled_time: string;
  duration_minutes: number;
  session_type: string;
  status: string;
  topic?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface UserStats {
  total_sessions: number;
  average_rating: number;
  improvement_trend: string;
  recent_sessions: PracticeSessionRead[];
  difficulty_breakdown: Record<string, any>;
}

// --- API Service ---
export const apiService = {
  // --- Question Generation ---
  async generateQuestion(topic: string, difficulty: string, model: string = "mistral:latest"): Promise<QuestionResponse> {
    const response = await fetchWithAuth(`${API_BASE_URL}/questions/generate`, {
      method: 'POST',
      headers: getAuthHeaders(), // getAuthHeaders will be overridden by fetchWithAuth if token changes
      body: JSON.stringify({ topic, difficulty, model }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to generate question: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Speech Evaluation ---
  async evaluateSpeech(
    audioBlob: Blob,
    topic: string,
    question: string,
    ideal_answer: string,
    difficulty: string,
    model: string = "mistral:latest"
  ): Promise<SpeechEvaluationTaskResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');
    formData.append('topic', topic);
    formData.append('question', question);
    formData.append('ideal_answer', ideal_answer);
    formData.append('difficulty', difficulty);
    formData.append('model', model);

    const response = await fetchWithAuth(`${API_BASE_URL}/speech/evaluate`, {
      method: 'POST',
      headers: getAuthHeadersFormData(), // getAuthHeadersFormData will be overridden by fetchWithAuth if token changes
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to start speech evaluation: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Synchronous Speech Evaluation (for backward compatibility) ---
  async evaluateSpeechSync(
    audioBlob: Blob,
    question: string,
    ideal_answer: string,
    difficulty: string,
    model: string = "mistral:latest"
  ): Promise<SpeechEvaluationResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.wav');
    formData.append('question', question);
    formData.append('ideal_answer', ideal_answer);
    formData.append('difficulty', difficulty);
    formData.append('model', model);

    const response = await fetchWithAuth(`${API_BASE_URL}/speech/evaluate-sync`, {
      method: 'POST',
      headers: getAuthHeadersFormData(),
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to evaluate speech: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Task Status ---
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await fetchWithAuth(`${API_BASE_URL}/tasks/${taskId}/status`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get task status: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async getUserTasks(): Promise<TaskStatusResponse[]> {
    const response = await fetchWithAuth(`${API_BASE_URL}/users/me/tasks`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get user tasks: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Interview Question Generation ---
  async generateInterviewQuestions(
    topic: string,
    personality_traits: string,
    technical_skills: string,
    model: string = "mistral:latest"
  ): Promise<InterviewQuestionsResponse> {
    const response = await fetchWithAuth(`${API_BASE_URL}/interviews/generate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ topic, personality_traits, technical_skills, model }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to generate interview questions: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- User Authentication ---
  // Register and Login don't use fetchWithAuth as they don't require prior auth
  async registerUser(email: string, password: string, fullName?: string): Promise<UserRead> {
    const response = await fetch(`${API_BASE_URL}/users/register`, {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Registration failed: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async loginUser(email: string, password: string): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', email); // FastAPI's OAuth2PasswordRequestForm expects 'username'
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Login failed: ${errorData.detail || response.statusText}`);
    }
    const tokenData = await response.json();
    if (tokenData.access_token && tokenData.refresh_token) {
      localStorage.setItem("accessToken", tokenData.access_token);
      localStorage.setItem("refreshToken", tokenData.refresh_token);
    }
    return tokenData;
  },

  async refreshToken(): Promise<TokenResponse | null> {
    const currentRefreshToken = getRefreshToken();
    if (!currentRefreshToken) {
      internalLogout(); // No refresh token, perform local logout
      return null;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/token/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: currentRefreshToken }),
      });

      if (!response.ok) {
        internalLogout(); // Refresh failed, perform local logout
        return null;
      }

      const newTokens = await response.json();
      if (newTokens.access_token && newTokens.refresh_token) {
        localStorage.setItem("accessToken", newTokens.access_token);
        localStorage.setItem("refreshToken", newTokens.refresh_token);
        return newTokens;
      } else {
        internalLogout(); // Invalid new tokens, perform local logout
        return null;
      }
    } catch (error) {
      console.error("Error refreshing token:", error);
      internalLogout(); // Error during refresh, perform local logout
      return null;
    }
  },

  async logoutUser(): Promise<void> {
    try {
      const token = getToken();
      if (token) {
        // Use fetch directly to avoid potential loop with fetchWithAuth if logout itself fails with 401
        await fetch(`${API_BASE_URL}/logout`, {
          method: 'POST',
          headers: getAuthHeaders(),
        });
      }
    } catch (error) {
      console.error("Error during backend logout call:", error);
    } finally {
      internalLogout(); // Always perform local logout
    }
  },

  async getCurrentUser(): Promise<UserRead> {
    const response = await fetchWithAuth(`${API_BASE_URL}/users/me`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get current user: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- User History ---
  async getUserHistory(): Promise<PracticeSessionRead[]> {
    const response = await fetchWithAuth(`${API_BASE_URL}/users/me/history`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get user history: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- User Profile Management ---
  async updateUserProfile(profileData: { full_name?: string; email?: string; bio?: string; avatar_url?: string }): Promise<UserRead> {
    const response = await fetchWithAuth(`${API_BASE_URL}/users/me`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(profileData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to update profile: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async getUserStats(days: number = 30): Promise<UserStats> {
    const response = await fetchWithAuth(`${API_BASE_URL}/users/me/stats?days=${days}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get user stats: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Booking System ---
  async createBooking(bookingData: {
    scheduled_time: string;
    duration_minutes?: number;
    session_type: string;
    topic?: string;
    notes?: string;
  }): Promise<BookingSlot> {
    const response = await fetchWithAuth(`${API_BASE_URL}/bookings`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(bookingData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to create booking: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async getUserBookings(statusFilter?: string): Promise<BookingSlot[]> {
    const url = statusFilter
      ? `${API_BASE_URL}/bookings?status_filter=${statusFilter}`
      : `${API_BASE_URL}/bookings`;

    const response = await fetchWithAuth(url, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get bookings: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async updateBooking(bookingId: number, updateData: {
    scheduled_time?: string;
    duration_minutes?: number;
    session_type?: string;
    status?: string;
    topic?: string;
    notes?: string;
  }): Promise<BookingSlot> {
    const response = await fetchWithAuth(`${API_BASE_URL}/bookings/${bookingId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updateData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to update booking: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  async cancelBooking(bookingId: number): Promise<{ message: string }> {
    const response = await fetchWithAuth(`${API_BASE_URL}/bookings/${bookingId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to cancel booking: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  },

  // --- Session Analysis ---
  async getSessionAnalysis(sessionId: number): Promise<any> {
    const response = await fetchWithAuth(`${API_BASE_URL}/sessions/${sessionId}/analysis`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(`Failed to get session analysis: ${errorData.detail || response.statusText}`);
    }
    return response.json();
  }
};
