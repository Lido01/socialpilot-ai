import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { mockService } from '@/api/mock.service';
import { AICaptionPrompt, AICaptionResult } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import {
  Sparkles,
  AlertTriangle,
  Copy,
  Check,
  ArrowRight,
  Sliders,
  Smile,
  Hash,
} from 'lucide-react';

interface AICaptionPageProps {
  onUseCaption?: (caption: string) => void;
}

export const AICaptionPage: React.FC<AICaptionPageProps> = ({ onUseCaption }) => {
  const { isDevMockMode, toggleDevMockMode } = useAuth();
  const { showToast } = useToast();

  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState<AICaptionPrompt['tone']>('engaging');
  const [targetAudience, setTargetAudience] = useState('');
  const [includeEmojis, setIncludeEmojis] = useState(true);
  const [includeHashtags, setIncludeHashtags] = useState(true);

  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<AICaptionResult | null>(null);
  const [copied, setCopied] = useState(false);

  const tones: Array<{ id: AICaptionPrompt['tone']; label: string }> = [
    { id: 'engaging', label: '🔥 Engaging' },
    { id: 'professional', label: '💼 Professional' },
    { id: 'casual', label: '☕ Casual' },
    { id: 'promotional', label: '⚡ Promotional' },
    { id: 'educational', label: '📚 Educational' },
  ];

  const handleGenerate = () => {
    if (!topic.trim()) {
      showToast('Please enter a topic or key idea', 'warning');
      return;
    }

    if (!isDevMockMode) {
      showToast(
        'Backend AI generation endpoint is pending deployment. Please enable Dev Mock Mode to test generation UI.',
        'info'
      );
      return;
    }

    setIsGenerating(true);
    setTimeout(() => {
      const result = mockService.generateAICaption({
        topic: topic.trim(),
        tone,
        targetAudience: targetAudience.trim() || undefined,
        includeEmojis,
        includeHashtags,
      });

      setGeneratedResult(result);
      setIsGenerating(false);
      showToast('Caption generated in preview mode!', 'success');
    }, 600);
  };

  const handleCopy = () => {
    if (!generatedResult) return;
    navigator.clipboard.writeText(generatedResult.caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showToast('Copied to clipboard!', 'success');
  };

  return (
    <div className="space-y-4">
      {/* Backend API status notice */}
      <div className="p-3.5 bg-amber-50 rounded-2xl border border-amber-200/70 text-xs text-amber-900 space-y-1.5">
        <div className="flex items-center gap-1.5 font-bold text-amber-800">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Backend Endpoint Status</span>
        </div>
        <p className="text-[11px] leading-relaxed text-amber-700">
          The FastAPI backend has Gemini configuration in <code>.env</code>, but the public REST endpoint (<code>/api/v1/companies/&#123;id&#125;/ai/generate</code>) is not yet wired to the router.
        </p>
        {!isDevMockMode ? (
          <button
            onClick={() => toggleDevMockMode(true)}
            className="text-[11px] font-bold underline text-amber-900 hover:text-amber-950 block pt-0.5"
          >
            Enable Dev Mock Mode to preview AI prompt UI & output →
          </button>
        ) : (
          <span className="inline-block bg-amber-200/70 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full">
            Simulated Preview Active
          </span>
        )}
      </div>

      <Card className="p-4 space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-800">Prompt & Audience</h2>
            <p className="text-[11px] text-slate-500">Fine-tune tone and target readers</p>
          </div>
        </div>

        <Input
          label="Topic / Announcement *"
          placeholder="e.g. Major app update with dark mode and faster publishing..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
        />

        {/* Tone Selection */}
        <div className="space-y-1.5 text-left">
          <label className="block text-xs font-semibold text-slate-700 flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <span>Tone of Voice</span>
          </label>
          <div className="flex flex-wrap gap-1.5">
            {tones.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTone(t.id)}
                className={`text-xs px-2.5 py-1.5 rounded-xl border transition-all ${
                  tone === t.id
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-700 font-bold'
                    : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <Input
          label="Target Audience (Optional)"
          placeholder="e.g. Telegram group members, crypto investors, tech enthusiasts"
          value={targetAudience}
          onChange={(e) => setTargetAudience(e.target.value)}
        />

        {/* Options Toggles */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            type="button"
            onClick={() => setIncludeEmojis(!includeEmojis)}
            className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
              includeEmojis
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                : 'bg-slate-50 border-slate-200 text-slate-500'
            }`}
          >
            <Smile className="w-3.5 h-3.5" />
            <span>Emojis {includeEmojis ? 'ON' : 'OFF'}</span>
          </button>

          <button
            type="button"
            onClick={() => setIncludeHashtags(!includeHashtags)}
            className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
              includeHashtags
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                : 'bg-slate-50 border-slate-200 text-slate-500'
            }`}
          >
            <Hash className="w-3.5 h-3.5" />
            <span>Hashtags {includeHashtags ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        <Button
          size="lg"
          onClick={handleGenerate}
          isLoading={isGenerating}
          icon={<Sparkles className="w-4 h-4" />}
          className="w-full mt-2"
        >
          Generate Caption
        </Button>
      </Card>

      {/* Generated Result Preview */}
      {generatedResult && (
        <Card className="p-4 space-y-3 border-indigo-100 bg-gradient-to-b from-indigo-50/30 to-white">
          <div className="flex items-center justify-between border-b border-indigo-100/60 pb-2">
            <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Generated Caption
            </span>
            <span className="text-[10px] font-mono bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">
              {generatedResult.caption.length} chars
            </span>
          </div>

          <div className="p-3 bg-white rounded-xl border border-indigo-100 text-xs text-slate-800 whitespace-pre-line leading-relaxed">
            {generatedResult.caption}
          </div>

          {generatedResult.mockNote && (
            <p className="text-[10px] text-amber-700 italic">
              *{generatedResult.mockNote}
            </p>
          )}

          <div className="grid grid-cols-2 gap-2 pt-1">
            <Button
              size="sm"
              variant="outline"
              onClick={handleCopy}
              icon={copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            >
              {copied ? 'Copied!' : 'Copy'}
            </Button>
            {onUseCaption && (
              <Button
                size="sm"
                onClick={() => onUseCaption(generatedResult.caption)}
                icon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                Use in Editor
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
