
import React, { useState } from 'react';

interface TopicSelectorProps {
  onTopicChange: (topic: string) => void;
  onDifficultyChange: (difficulty: string) => void;
}

const topics = [
  "HR Interview",
  "Technical Interview",
  "IELTS Speaking",
  "Debate Practice",
  "Extempore Speech",
  "Other"
];

const difficulties = ["Easy", "Medium", "Hard"];

const TopicSelector: React.FC<TopicSelectorProps> = ({ onTopicChange, onDifficultyChange }) => {
  const [customTopic, setCustomTopic] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");

  const handleTopicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const topic = e.target.value;
    setSelectedTopic(topic);
    if (topic !== "Other") {
      onTopicChange(topic);
    } else {
      onTopicChange(customTopic);
    }
  };

  const handleCustomTopicChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomTopic(e.target.value);
    onTopicChange(e.target.value);
  };

  return (
    <div className="flex-grow w-full space-y-4">
      <div>
        <label htmlFor="topicSelector" className="block text-sm font-medium text-gray-700 mb-1">
          Topic
        </label>
        <select
          id="topicSelector"
          onChange={handleTopicChange}
          className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Select a topic...</option>
          {topics.map((topic) => (
            <option key={topic} value={topic}>
              {topic}
            </option>
          ))}
        </select>
      </div>
      {selectedTopic === "Other" && (
        <div>
          <label htmlFor="customTopic" className="block text-sm font-medium text-gray-700 mb-1">
            Custom Topic
          </label>
          <input
            type="text"
            id="customTopic"
            value={customTopic}
            onChange={handleCustomTopicChange}
            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter your custom topic"
          />
        </div>
      )}
      <div>
        <label htmlFor="difficultySelector" className="block text-sm font-medium text-gray-700 mb-1">
          Difficulty
        </label>
        <select
          id="difficultySelector"
          defaultValue="medium"
          onChange={(e) => onDifficultyChange(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          {difficulties.map((level) => (
            <option key={level} value={level.toLowerCase()}>
              {level}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export { TopicSelector };
