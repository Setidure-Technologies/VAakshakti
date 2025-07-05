import React, { useState, useRef } from "react";
import { useToast } from "@/hooks/use-toast";

interface AudioRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const { toast } = useToast();

  const startRecording = async () => {
    setAudioBlob(null); // Reset previous recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const newAudioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(newAudioBlob);
        stream.getTracks().forEach(track => track.stop());
        // Automatically call the completion handler
        onRecordingComplete(newAudioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      toast({
        title: "Recording started",
        description: "Speak clearly into your microphone.",
      });
    } catch (error) {
      console.error("Error starting recording:", error);
      toast({
        title: "Microphone Error",
        description: "Please allow microphone access to record your answer.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast({
        title: "Recording stopped",
        description: "Your answer has been recorded and is being processed.",
      });
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-100 to-indigo-100 rounded-xl p-6 shadow-lg border border-blue-200 animate-fadeIn">
      <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
        🎙️ Record Your Answer
      </h3>
      
      <div className="flex flex-col items-center space-y-4">
        <div className="flex gap-4">
          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={isRecording}
              className="bg-red-500 hover:bg-red-600 text-white font-semibold py-3 px-6 rounded-full transition-all duration-300 transform hover:scale-105 flex items-center gap-2 shadow-lg disabled:bg-red-300"
            >
              🔴 Start Recording
            </button>
          ) : (
            <button
              onClick={stopRecording}
              disabled={!isRecording}
              className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-full transition-all duration-300 transform hover:scale-105 flex items-center gap-2 shadow-lg animate-pulse disabled:bg-gray-400"
            >
              ⏹️ Stop Recording
            </button>
          )}
        </div>

        {isRecording && (
          <div className="flex items-center gap-2 text-red-600 animate-pulse">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-ping"></div>
            <span className="font-medium">Recording in progress...</span>
          </div>
        )}

        {audioBlob && !isRecording && (
          <div className="text-green-600 font-medium mt-4">
            ✅ Recording complete. Uploading for evaluation...
          </div>
        )}
      </div>
    </div>
  );
};

export { AudioRecorder };
