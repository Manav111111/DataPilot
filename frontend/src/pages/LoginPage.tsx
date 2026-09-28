import React from 'react';
import { LoginForm } from '../features/auth/LoginForm';
import { Layers, ShieldCheck, Database, Zap } from 'lucide-react';

export function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-[#f8fafc]">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo and heading */}
        <div className="flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-500/30">
            <Layers className="h-7 w-7" />
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900">
          Sign in to DataIntel
        </h2>
        <p className="mt-1 text-center text-xs sm:text-sm text-slate-500">
          AI-Powered Data Intelligence & Extraction Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-xl shadow-slate-200/50 rounded-2xl border border-slate-200/80">
          <LoginForm />
        </div>

        {/* Feature badges */}
        <div className="mt-8 grid grid-cols-3 gap-2 text-center text-[11px] text-slate-500 font-medium">
          <div className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-100/70">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
            <span>Secure JWT</span>
          </div>
          <div className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-100/70">
            <Database className="w-3.5 h-3.5 text-indigo-600" />
            <span>PostgreSQL</span>
          </div>
          <div className="flex items-center justify-center gap-1.5 p-2 rounded-lg bg-slate-100/70">
            <Zap className="w-3.5 h-3.5 text-indigo-600" />
            <span>FastAPI</span>
          </div>
        </div>
      </div>
    </div>
  );
}
