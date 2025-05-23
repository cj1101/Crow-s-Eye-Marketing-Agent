import { useState, useRef, useEffect } from 'react';

interface PromptInputProps {
  placeholder?: string;
  onSubmit: (prompt: string) => void;
  buttonText?: string;
  initialValue?: string;
  isLoading?: boolean;
  className?: string;
  minRows?: number;
  maxRows?: number;
}

const PromptInput: React.FC<PromptInputProps> = ({
  placeholder = 'Enter your prompt...',
  onSubmit,
  buttonText = 'Submit',
  initialValue = '',
  isLoading = false,
  className = '',
  minRows = 2,
  maxRows = 5,
}) => {
  const [prompt, setPrompt] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  useEffect(() => {
    if (textareaRef.current) {
      // Auto-resize the textarea based on content
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const lineHeight = parseInt(getComputedStyle(textareaRef.current).lineHeight);
      const maxHeight = lineHeight * maxRows;
      
      textareaRef.current.style.height = 
        Math.min(Math.max(lineHeight * minRows, scrollHeight), maxHeight) + 'px';
    }
  }, [prompt, minRows, maxRows]);
  
  const handleSubmit = () => {
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim());
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.shiftKey === false) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  return (
    <div className={`flex flex-col ${className}`}>
      <div className="relative">
        <textarea
          ref={textareaRef}
          className="w-full px-4 py-3 rounded-md border border-gray-300 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none resize-none"
          placeholder={placeholder}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={minRows}
          disabled={isLoading}
        />
      </div>
      
      <div className="mt-2 flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={isLoading || !prompt.trim()}
          className={`px-4 py-2 rounded-md text-white font-medium transition ${
            isLoading || !prompt.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700'
          }`}
        >
          {isLoading ? 'Processing...' : buttonText}
        </button>
      </div>
    </div>
  );
};

export default PromptInput; 