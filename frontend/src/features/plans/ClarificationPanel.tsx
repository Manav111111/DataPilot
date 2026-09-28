import React, { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';
import { HelpCircle, Sparkles, Send } from 'lucide-react';

interface ClarificationPanelProps {
  questions: string[];
  onSubmitAnswers: (answers: Record<string, string>) => Promise<void>;
  isLoading?: boolean;
}

export function ClarificationPanel({
  questions,
  onSubmitAnswers,
  isLoading = false,
}: ClarificationPanelProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleAnswerChange = (questionIndex: number, text: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questions[questionIndex]]: text,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmitAnswers(answers);
  };

  return (
    <div className="p-5 rounded-xl border border-amber-200 bg-amber-50/50 space-y-4">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-amber-100 text-amber-700 flex-shrink-0">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-amber-950">
            Clarification Needed from AI Planner
          </h4>
          <p className="text-xs text-amber-800 mt-0.5">
            The planning agent needs a few additional specifics to generate an accurate schema and search strategy.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {questions.map((q, idx) => (
          <div key={idx} className="p-3 rounded-lg bg-white border border-amber-200/80 space-y-1.5">
            <label className="text-xs font-semibold text-slate-800 block">
              {idx + 1}. {q}
            </label>
            <textarea
              rows={2}
              placeholder="Type your answer or preference here..."
              value={answers[q] || ''}
              onChange={(e) => handleAnswerChange(idx, e.target.value)}
              className="w-full rounded-md border border-slate-200 p-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        ))}

        <div className="flex justify-end pt-1">
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={isLoading}
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            Regenerate Plan with Answers
          </Button>
        </div>
      </form>
    </div>
  );
}
