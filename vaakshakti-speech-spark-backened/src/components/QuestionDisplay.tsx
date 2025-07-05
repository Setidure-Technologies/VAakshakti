
interface QuestionDisplayProps {
  question: string;
}

const QuestionDisplay = ({ question }: QuestionDisplayProps) => {
  return (
    <div className="bg-gradient-to-r from-blue-100 to-indigo-100 rounded-xl p-6 shadow-lg 
                    border border-blue-200 animate-fadeIn">
      <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
        💭 Your Question
      </h3>
      <div id="questionBox" className="bg-white/80 p-4 rounded-lg border border-blue-200">
        <p className="text-gray-800 text-lg leading-relaxed">{question}</p>
      </div>
    </div>
  );
};

export { QuestionDisplay };
