import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import { formatDate } from '../lib/utils';
import { User, Mail, Shield, Key, LogOut, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const profileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  password: z
    .string()
    .optional()
    .refine((val) => !val || val.length >= 8, {
      message: 'New password must be at least 8 characters if provided',
    }),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export function SettingsPage() {
  const { user, updateProfile, logout } = useAuth();
  const { success, error: showError } = useToast();
  const navigate = useNavigate();
  const [isUpdating, setIsUpdating] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || '',
      password: '',
    },
  });

  const onSubmit = async (values: ProfileFormValues) => {
    setIsUpdating(true);
    try {
      await updateProfile({
        name: values.name,
        password: values.password || undefined,
      });
      success('Profile updated successfully!');
    } catch (err: any) {
      showError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
          Account Settings
        </h2>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
          Manage your personal profile, credentials and security preferences.
        </p>
      </div>

      {/* Profile Details Card */}
      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle>Personal Information</CardTitle>
          <CardDescription>
            Update your account display name and password.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
            <Input
              label="Full Name"
              icon={<User className="w-4 h-4" />}
              error={errors.name?.message}
              {...register('name')}
            />

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Email Address (Read-Only)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="flex h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 py-2 text-sm text-slate-500 cursor-not-allowed"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Your email is used for login and cannot be altered.
              </p>
            </div>

            <Input
              label="New Password (Optional)"
              type="password"
              placeholder="Leave blank to keep current password"
              icon={<Key className="w-4 h-4" />}
              error={errors.password?.message}
              {...register('password')}
            />

            <div className="pt-2">
              <Button type="submit" variant="primary" isLoading={isUpdating}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Account Metadata & Security Card */}
      <Card>
        <CardHeader className="border-b border-slate-100">
          <CardTitle>Account Security & Metadata</CardTitle>
          <CardDescription>System identifiers and session status.</CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Account ID</span>
              <span className="font-mono font-semibold text-slate-800 break-all">
                {user?.id}
              </span>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
              <span className="text-slate-400 block mb-0.5">Member Since</span>
              <span className="font-semibold text-slate-800">
                {formatDate(user?.created_at)}
              </span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">Sign Out</p>
              <p className="text-xs text-slate-500">
                End your current session across this browser.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-1.5 text-rose-500" />
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
