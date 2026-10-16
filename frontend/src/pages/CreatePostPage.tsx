import React, { useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { mockService } from '@/api/mock.service';
import { LocalMediaItem } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Textarea } from '@/components/common/Textarea';
import {
  ImagePlus,
  Sparkles,
  X,
  Send,
  Save,
  CheckCircle,
  Radio,
} from 'lucide-react';
import { AICaptionPage } from './AICaptionPage';

export const CreatePostPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') === 'ai' ? 'ai' : 'editor';

  const { role, user } = useAuth();
  const { showToast } = useToast();

  const [caption, setCaption] = useState('');
  const [mediaList, setMediaList] = useState<LocalMediaItem[]>([]);
  const [selectedChannels, setSelectedChannels] = useState<string[]>(['chan-1']);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const channels = mockService.getChannels();
  const maxChars = mediaList.length > 0 ? 1024 : 4096;

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newItems: LocalMediaItem[] = [];
    Array.from(files).forEach((file, index) => {
      if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
        showToast(`Skipped ${file.name}: only images and videos supported`, 'warning');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        showToast(`Skipped ${file.name}: exceeds 10MB limit`, 'warning');
        return;
      }

      const previewUrl = URL.createObjectURL(file);
      newItems.push({
        id: `media-${Date.now()}-${index}`,
        file,
        previewUrl,
        name: file.name,
        size: file.size,
        type: file.type,
        order: mediaList.length + index,
      });
    });

    setMediaList((prev) => [...prev, ...newItems]);
    if (fileInputRef.current) fileInputRef.current.value = '';
    showToast(`${newItems.length} media item(s) selected`, 'info');
  };

  const removeMedia = (id: string) => {
    setMediaList((prev) => prev.filter((m) => m.id !== id));
  };

  const toggleChannel = (channelId: string) => {
    setSelectedChannels((prev) =>
      prev.includes(channelId)
        ? prev.filter((id) => id !== channelId)
        : [...prev, channelId]
    );
  };

  const handleApplyAICaption = (newCaption: string) => {
    setCaption(newCaption);
    setSearchParams({ tab: 'editor' });
    showToast('AI caption applied to post editor!', 'success');
  };

  const handleSubmit = (action: 'draft' | 'in_review' | 'publish') => {
    if (!caption.trim() && mediaList.length === 0) {
      showToast('Please enter a caption or add media to create a post', 'warning');
      return;
    }

    if (selectedChannels.length === 0) {
      showToast('Please select at least one Telegram channel to publish to', 'warning');
      return;
    }

    setIsSubmitting(true);
    try {
      mockService.savePost({
        companyId: 'company-active',
        caption: caption.trim(),
        status: action === 'publish' ? 'published' : action,
        media: mediaList,
        channelIds: selectedChannels,
        authorId: user?.id || 'u-local',
        authorName: user?.displayName || 'Creator',
        publishedAt: action === 'publish' ? new Date().toISOString() : undefined,
      });

      showToast(
        action === 'draft'
          ? 'Post saved as draft'
          : action === 'in_review'
          ? 'Post submitted for admin review!'
          : 'Post published to channels!',
        'success'
      );

      navigate('/drafts');
    } catch (err: any) {
      showToast(err.message || 'Failed to save post', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4 pb-8">
      {/* Tab Switcher: Editor vs AI Generator */}
      <div className="flex bg-slate-200/70 p-1 rounded-2xl">
        <button
          onClick={() => setSearchParams({ tab: 'editor' })}
          className={`flex-1 py-2 text-xs font-bold rounded-xl transition-all ${
            activeTab === 'editor'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Post Editor
        </button>
        <button
          onClick={() => setSearchParams({ tab: 'ai' })}
          className={`flex-1 py-2 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition-all ${
            activeTab === 'ai'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>AI Caption Generator</span>
        </button>
      </div>

      {activeTab === 'ai' ? (
        <AICaptionPage onUseCaption={handleApplyAICaption} />
      ) : (
        /* Standard Post Editor */
        <div className="space-y-4">
          <Card className="p-4 space-y-4">
            {/* Target Channel Selector */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-indigo-600" />
                <span>Target Channels</span>
              </label>

              <div className="flex flex-wrap gap-1.5">
                {channels.map((chan) => {
                  const isSelected = selectedChannels.includes(chan.id);
                  return (
                    <button
                      key={chan.id}
                      type="button"
                      onClick={() => toggleChannel(chan.id)}
                      className={`text-xs px-2.5 py-1.5 rounded-xl border transition-all flex items-center gap-1.5 ${
                        isSelected
                          ? 'bg-indigo-50 border-indigo-200 text-indigo-700 font-semibold'
                          : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      <span>{chan.title}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Caption Textarea */}
            <Textarea
              label="Caption"
              placeholder="What would you like to share with your Telegram audience? Use #hashtags or @mentions..."
              rows={5}
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              charCount={{ current: caption.length, max: maxChars }}
              helperText={
                mediaList.length > 0
                  ? 'Telegram limits photo/video captions to 1,024 characters.'
                  : 'Plain text messages support up to 4,096 characters.'
              }
            />

            {/* Media Upload and Preview Grid */}
            <div className="space-y-2.5 pt-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                  <ImagePlus className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Attached Media ({mediaList.length})</span>
                </label>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                >
                  + Add Images/Video
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,video/mp4"
                onChange={handleFileSelect}
                className="hidden"
              />

              {mediaList.length === 0 ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-200 hover:border-indigo-300 rounded-2xl p-5 text-center cursor-pointer transition-colors space-y-1.5 bg-slate-50/50"
                >
                  <ImagePlus className="w-6 h-6 text-slate-400 mx-auto" />
                  <div className="text-xs font-semibold text-slate-700">
                    Tap to upload images from your device
                  </div>
                  <p className="text-[10px] text-slate-400">
                    JPG, PNG, WebP or MP4 up to 10MB
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {mediaList.map((m, idx) => (
                    <div
                      key={m.id}
                      className="relative rounded-xl overflow-hidden aspect-square border border-slate-200 group bg-slate-100"
                    >
                      <img
                        src={m.previewUrl}
                        alt={m.name}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-1 left-1 bg-black/60 text-white text-[9px] px-1 py-0.5 rounded font-mono">
                        #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeMedia(m.id)}
                        className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 text-white flex items-center justify-center hover:bg-rose-600 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="aspect-square rounded-xl border border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-500 hover:text-indigo-600 hover:border-indigo-300 bg-slate-50 transition-colors"
                  >
                    <ImagePlus className="w-4 h-4 mb-0.5" />
                    <span className="text-[10px] font-medium">+ Add</span>
                  </button>
                </div>
              )}
            </div>
          </Card>

          {/* Action Button Controls */}
          <div className="space-y-2">
            {role === 'content_owner' ? (
              <Button
                size="lg"
                onClick={() => handleSubmit('in_review')}
                isLoading={isSubmitting}
                icon={<CheckCircle className="w-4 h-4" />}
                className="w-full"
              >
                Submit for Approval
              </Button>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Button
                  size="md"
                  onClick={() => handleSubmit('in_review')}
                  isLoading={isSubmitting}
                  icon={<CheckCircle className="w-4 h-4" />}
                  variant="secondary"
                >
                  Send to Queue
                </Button>
                <Button
                  size="md"
                  onClick={() => handleSubmit('publish')}
                  isLoading={isSubmitting}
                  icon={<Send className="w-4 h-4" />}
                >
                  Publish Now
                </Button>
              </div>
            )}

            <Button
              size="md"
              variant="outline"
              onClick={() => handleSubmit('draft')}
              isLoading={isSubmitting}
              icon={<Save className="w-4 h-4" />}
              className="w-full"
            >
              Save as Draft
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
