import React, { useState } from 'react';
import { mockService } from '@/api/mock.service';
import { useToast } from '@/context/ToastContext';
import { TelegramChannel } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import {
  Radio,
  Plus,
  CheckCircle2,
  Info,
  Bot,
} from 'lucide-react';

export const ChannelsPage: React.FC = () => {
  const { showToast } = useToast();

  const [channels, setChannels] = useState<TelegramChannel[]>(() =>
    mockService.getChannels()
  );
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [username, setUsername] = useState('');
  const [chatId, setChatId] = useState('');

  const handleAddChannel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !username.trim()) {
      showToast('Please provide channel title and username', 'warning');
      return;
    }

    const newChan = mockService.addChannel(
      title.trim(),
      username.trim(),
      chatId.trim() || '-1000000000'
    );
    setChannels(mockService.getChannels());
    setShowAddModal(false);
    setTitle('');
    setUsername('');
    setChatId('');
    showToast(`Channel "${newChan.title}" connected successfully!`, 'success');
  };

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Connected Channels</h1>
          <p className="text-xs text-slate-500">
            Publish targets configured for this company workspace
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => setShowAddModal(!showAddModal)}
          icon={<Plus className="w-3.5 h-3.5" />}
        >
          Add Channel
        </Button>
      </div>

      {/* Backend API Notice */}
      <div className="p-3 bg-slate-100 rounded-2xl text-xs text-slate-600 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800">
          <Info className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
          <span>Backend Channel Verification API</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Channel verification requires the Telegram Bot to be an Administrator with <i>Post Messages</i> permission. When backend channel endpoints are finalized, verification happens over the Telegram Bot API.
        </p>
      </div>

      {/* Add Channel Form */}
      {showAddModal && (
        <Card className="p-4 space-y-4 border-indigo-200 bg-indigo-50/20">
          <div className="space-y-1 border-b border-indigo-100 pb-2">
            <h2 className="text-sm font-bold text-slate-900">Connect Telegram Channel</h2>
            <p className="text-xs text-slate-500">
              Ensure your bot is added as Administrator to the target channel first.
            </p>
          </div>

          <form onSubmit={handleAddChannel} className="space-y-3">
            <Input
              label="Channel Display Title *"
              placeholder="e.g. Official Community Channel"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <Input
              label="Channel Username or Link *"
              placeholder="e.g. @socialpilot_ai or t.me/socialpilot_ai"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Input
              label="Telegram Chat ID (Optional)"
              placeholder="e.g. -1001234567890"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              helperText="Bot automatically detects Chat ID if left blank"
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => setShowAddModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" size="sm">
                Verify & Save Channel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Channel List */}
      <div className="space-y-2.5">
        {channels.map((chan) => (
          <Card key={chan.id} className="p-4 space-y-2.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Radio className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{chan.title}</h3>
                  <p className="text-xs text-slate-500 font-mono">{chan.username}</p>
                </div>
              </div>
              <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                <span>Active</span>
              </span>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-50 text-xs text-slate-500">
              <div className="flex items-center gap-1.5 text-[11px]">
                <Bot className="w-3.5 h-3.5 text-indigo-600" />
                <span>Bot Admin Status: <b>Granted</b></span>
              </div>
              <span className="text-[11px] text-slate-400">
                {chan.subscriberCount ? `${chan.subscriberCount.toLocaleString()} subs` : 'Connected'}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Guide Card */}
      <Card className="p-4 space-y-3 bg-slate-50 border-slate-200/60">
        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
          How to connect a new Telegram Channel
        </h4>
        <ol className="text-xs text-slate-600 space-y-2 list-decimal list-inside leading-relaxed">
          <li>Open your Channel in the Telegram app and tap Channel Settings.</li>
          <li>Tap <b>Administrators</b> → <b>Add Administrator</b>.</li>
          <li>Search for your configured bot username and select it.</li>
          <li>Ensure the <b>"Post Messages"</b> permission is enabled.</li>
          <li>Enter the channel username in SocialPilot to complete connection.</li>
        </ol>
      </Card>
    </div>
  );
};
