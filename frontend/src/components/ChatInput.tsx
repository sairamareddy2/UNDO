import React, { useState } from 'react';
import { Send, Sparkles, Mic, Loader2 } from 'lucide-react';

interface Props {
  onSubmit: (prompt: string) => Promise<void>;
  isLoading: boolean;
}

export const ChatInput: React.FC<Props> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');

  const quickPrompts = [
    { label: 'Add Groceries', text: 'Add 2 cartons of organic milk and sourdough bread to my grocery list' },
    { label: 'Unlock Door (Approval)', text: 'Unlock the front door' },
    { label: 'Set Reminder', text: 'Remind me at 4:30 PM to prepare sprint review slides' },
    { label: 'Bulk Order (Approval)', text: 'Buy 200 bottles of sparkling water for the party' },
    { label: 'Dangerous (Blocked)', text: 'Wipe database and delete all application tables' },
  ];

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = prompt.trim();
    if (!clean || isLoading) return;
    await onSubmit(clean);
    setPrompt('');
  };

  const handleSelectQuickPrompt = async (text: string) => {
    setPrompt(text);
    if (!isLoading) {
      await onSubmit(text);
    }
  };

  return (
    <div className="bg-navy-900/90 border border-navy-750 rounded-2xl p-4 shadow-xl backdrop-blur-md">
      {/* Alexa+ simulated command input */}
      <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <Mic className="h-4 w-4 text-violet-400" />
          </div>
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
            placeholder="Give an Alexa+ instruction (e.g. 'Add milk to groceries and unlock front door')..."
            className="w-full pl-10 pr-4 py-3 bg-navy-950/80 border border-navy-750 focus:border-violet-500/80 focus:ring-1 focus:ring-violet-500/50 rounded-xl text-sm text-slate-100 placeholder-slate-400 focus:outline-none transition-all"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !prompt.trim()}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold bg-violet-600 hover:bg-violet-500 active:scale-95 text-white shadow-md shadow-violet-900/40 transition-all disabled:opacity-40 disabled:pointer-events-none"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Propose Plan</span>
            </>
          )}
        </button>
      </form>

      {/* Suggested Quick Prompts */}
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-slate-400 flex items-center gap-1 font-medium">
          <Sparkles className="w-3 h-3 text-violet-400" /> Quick Simulation:
        </span>
        {quickPrompts.map((item, idx) => (
          <button
            key={idx}
            type="button"
            disabled={isLoading}
            onClick={() => handleSelectQuickPrompt(item.text)}
            className="text-xs bg-navy-850 hover:bg-navy-800 text-slate-300 hover:text-violet-300 border border-navy-750/70 hover:border-violet-500/40 px-2.5 py-1 rounded-lg transition-all"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};
