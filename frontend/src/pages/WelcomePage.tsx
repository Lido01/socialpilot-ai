import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTelegram } from '@/context/TelegramContext';
import { useToast } from '@/context/ToastContext';
import { companyService } from '@/api/company.service';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Sparkles, Building2, Send, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';

export const WelcomePage: React.FC = () => {
  const navigate = useNavigate();
  const { isInTelegram, initDataUnsafeUser } = useTelegram();
  const { isAuthenticated, loginWithTelegram, pendingRegistration, activeCompany } = useAuth();
  const { showToast } = useToast();

  const [step, setStep] = useState<'auth' | 'register'>(
    isAuthenticated ? 'register' : 'auth'
  );

  // Form fields matching backend CompanyRegistrationRequestCreate
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [website, setWebsite] = useState('');
  const [country, setCountry] = useState('US');
  const [contactEmail, setContactEmail] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already authenticated and has company or pending request, redirect
  React.useEffect(() => {
    if (activeCompany) {
      navigate('/dashboard', { replace: true });
    } else if (pendingRegistration) {
      navigate('/registration-status', { replace: true });
    }
  }, [activeCompany, pendingRegistration, navigate]);

  const handleAuth = async () => {
    try {
      if (isInTelegram) {
        await loginWithTelegram();
        showToast('Telegram session authenticated!', 'success');
        setStep('register');
      } else {
        // Outside Telegram dev authentication
        showToast('Running in Dev Preview mode. Please connect inside Telegram for production auth.', 'info');
        setStep('register');
      }
    } catch (err: any) {
      showToast(err.message || 'Authentication failed', 'error');
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = 'Company name is required';
    if (country && !/^[A-Z]{2}$/.test(country.toUpperCase())) {
      errs.country = 'Country code must be 2 uppercase letters (e.g. US, GB, DE)';
    }
    if (website && !website.startsWith('http://') && !website.startsWith('https://')) {
      errs.website = 'Website must start with http:// or https://';
    }
    if (contactEmail && !contactEmail.includes('@')) {
      errs.contactEmail = 'Invalid email address';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const payload = {
        name: name.trim(),
        industry: industry.trim() || undefined,
        website: website.trim() || undefined,
        country: country.trim().toUpperCase() || undefined,
        contact_email: contactEmail.trim() || undefined,
      };

      const res = await companyService.registerCompany(payload);
      showToast('Registration request submitted successfully!', 'success');
      navigate('/registration-status', { state: { registration: res } });
    } catch (err: any) {
      if (err.statusCode === 409) {
        showToast('A company or pending request with this name already exists.', 'error');
      } else {
        showToast(err.message || 'Failed to submit registration', 'error');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="py-4 space-y-6 max-w-sm mx-auto">
      {/* Brand Hero */}
      <div className="text-center space-y-3 pt-4">
        <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-purple-500 mx-auto flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
          <Sparkles className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
            SocialPilot AI
          </h1>
          <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
            Multi-tenant AI social media planning, team approvals, and automated Telegram publishing.
          </p>
        </div>
      </div>

      {step === 'auth' ? (
        <Card className="p-6 space-y-5 text-center">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">
              {isInTelegram ? 'Telegram Mini App' : 'Welcome to SocialPilot'}
            </h2>
            <p className="text-xs text-slate-500">
              {isInTelegram
                ? `Logged in as @${initDataUnsafeUser?.username || initDataUnsafeUser?.first_name || 'User'}`
                : 'Authenticate your Telegram account to start managing your channels.'}
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 text-left space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2 text-indigo-700 font-semibold">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Cryptographic Telegram Security</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-500">
              Your identity is verified server-side with HMAC-SHA256 signature using your bot token.
            </p>
          </div>

          <Button
            size="lg"
            onClick={handleAuth}
            icon={<Send className="w-4 h-4" />}
            className="w-full"
          >
            {isInTelegram ? 'Continue with Telegram' : 'Launch Preview / Register'}
          </Button>
        </Card>
      ) : (
        /* Company Registration Form */
        <Card className="p-5 space-y-5">
          <div className="space-y-1 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 text-indigo-600 font-bold text-xs uppercase tracking-wide">
              <Building2 className="w-4 h-4" />
              <span>Workspace Setup</span>
            </div>
            <h2 className="text-base font-bold text-slate-900">Register Your Company</h2>
            <p className="text-xs text-slate-500">
              Create a dedicated workspace. Registrations are reviewed by the Platform Owner before activation.
            </p>
          </div>

          <form onSubmit={handleRegister} className="space-y-3.5">
            <Input
              label="Company Name *"
              placeholder="e.g. Acme Media Corp"
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.name}
              required
            />

            <Input
              label="Industry"
              placeholder="e.g. Technology, E-commerce, Media"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            />

            <Input
              label="Website URL"
              type="url"
              placeholder="https://example.com"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              error={errors.website}
            />

            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-1">
                <Input
                  label="Country"
                  placeholder="US"
                  maxLength={2}
                  value={country}
                  onChange={(e) => setCountry(e.target.value.toUpperCase())}
                  error={errors.country}
                  helperText="ISO code"
                />
              </div>
              <div className="col-span-2">
                <Input
                  label="Contact Email"
                  type="email"
                  placeholder="admin@example.com"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  error={errors.contactEmail}
                />
              </div>
            </div>

            <Button
              type="submit"
              size="lg"
              isLoading={isSubmitting}
              icon={<ArrowRight className="w-4 h-4" />}
              className="mt-3 w-full"
            >
              Submit Registration Request
            </Button>
          </form>
        </Card>
      )}

      {/* Trust Badges */}
      <div className="grid grid-cols-2 gap-2 text-center text-[11px] text-slate-400">
        <div className="flex items-center justify-center gap-1.5 p-2 rounded-xl bg-white/60 border border-slate-100">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Multi-tenant Isolation</span>
        </div>
        <div className="flex items-center justify-center gap-1.5 p-2 rounded-xl bg-white/60 border border-slate-100">
          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-500" />
          <span>Role-Based Access</span>
        </div>
      </div>
    </div>
  );
};
