import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Sparkles } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../components/ui/Toast';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const { success, error: showError } = useToast();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    try {
      await login(values);
      success('Welcome back! Signed in successfully.');
      navigate('/dashboard');
    } catch (err: any) {
      let msg = 'Invalid email or password';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          msg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          msg = err.response.data.detail.map((e: any) => e.msg || e.message).join(', ');
        }
      } else if (err.message === 'Network Error' || !err.response) {
        msg = 'Unable to connect to the backend server. Please check your backend URL or server status.';
      } else if (err.message) {
        msg = err.message;
      }
      showError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoAccount = () => {
    setValue('email', 'admin@dataintel.com');
    setValue('password', 'Password123!');
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Email Address"
        type="email"
        placeholder="you@company.com"
        icon={<Mail className="w-4 h-4" />}
        error={errors.email?.message}
        {...register('email')}
      />

      <Input
        label="Password"
        type="password"
        placeholder="••••••••"
        icon={<Lock className="w-4 h-4" />}
        error={errors.password?.message}
        {...register('password')}
      />

      <Button
        type="submit"
        variant="primary"
        className="w-full mt-2"
        isLoading={isLoading}
      >
        Sign in to Account
      </Button>

      <div className="pt-2 text-center">
        <button
          type="button"
          onClick={fillDemoAccount}
          className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-700 font-medium py-1 px-2.5 rounded-md hover:bg-indigo-50 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Fill Demo Credentials
        </button>
      </div>

      <p className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        Don't have an account?{' '}
        <Link
          to="/register"
          className="font-semibold text-indigo-600 hover:text-indigo-700 underline underline-offset-2"
        >
          Create account
        </Link>
      </p>
    </form>
  );
}
