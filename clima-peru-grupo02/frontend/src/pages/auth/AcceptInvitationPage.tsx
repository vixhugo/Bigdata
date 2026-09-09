import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface InvitationStatus {
  token: string;
  is_valid: boolean;
  is_expired: boolean;
  is_accepted: boolean;
  email: string;
  full_name: string | null;
  role_id: number;
  role_name: string | null;
  message: string | null;
  expires_at: string;
}

interface AcceptInvitationRequest {
  token: string;
  full_name: string;
  password: string;
  confirm_password: string;
}

export const AcceptInvitationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();

  const [status, setStatus] = useState<'loading' | 'ready' | 'error' | 'success'>('loading');
  const [invitation, setInvitation] = useState<InvitationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Verificar invitación al montar el componente
  useEffect(() => {
    if (!token) {
      setError('No se encontró el token de invitación.');
      setStatus('error');
      return;
    }

    fetchInvitationStatus(token);
  }, [token]);

  const fetchInvitationStatus = async (token: string) => {
    try {
      const response = await fetch(`/api/invitations/verify/${token}`);
      if (response.ok) {
        const data = await response.json();
        setInvitation(data);
        setStatus('ready');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Invitación inválida o expirada.');
        setStatus('error');
      }
    } catch (err) {
      setError('Error al conectar con el servidor. Por favor, intenta de nuevo.');
      setStatus('error');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token || !fullName || !password || !confirmPassword) {
      setError('Por favor, completa todos los campos.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/invitations/accept', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          full_name: fullName,
          password,
          confirm_password: confirmPassword,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Login automático con el token devuelto
        await loginWithToken({
          access_token: data.token,
          token_type: 'bearer',
          expires_in: 3600,
        });
        
        setStatus('success');
        window.history.replaceState({}, document.title, '/');
        setTimeout(() => navigate('/'), 1200);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error al aceptar la invitación.');
        setSubmitting(false);
      }
    } catch (err) {
      setError('Error al conectar con el servidor. Por favor, intenta de nuevo.');
      setSubmitting(false);
    }
  };

  // Pantalla de carga
  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-sky-500" />
          <p className="text-slate-400 text-sm">Verificando invitación...</p>
        </div>
      </div>
    );
  }

  // Pantalla de error
  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-xl border border-slate-200 dark:border-slate-800">
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white text-center">
              Invitación Inválida
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-center">
              {error}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="mt-6 px-6 py-3 bg-sky-500 hover:bg-sky-600 text-white rounded-xl font-semibold transition-colors"
            >
              Volver al Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950 px-4 py-8">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 mx-auto mb-4 rounded-3xl bg-gradient-to-tr from-sky-500 to-indigo-600 p-0.5 shadow-2xl shadow-sky-500/20">
            <div className="w-full h-full bg-white dark:bg-slate-900 rounded-[22px] flex items-center justify-center">
              <ShieldCheck className="w-10 h-10 text-sky-600 dark:text-sky-400" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            ¡Bienvenido a MeteoPerú!
          </h1>
          <p className="text-sky-200/80 text-lg">
            Acepta tu invitación para unirte a nuestra plataforma
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl shadow-sky-500/10 border border-slate-200 dark:border-slate-800 overflow-hidden">
          {/* Status Banner */}
          <div className="bg-gradient-to-r from-sky-500/10 to-indigo-500/10 p-6 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-start gap-3">
              <div className="mt-1">
                <ShieldCheck className="w-5 h-5 text-sky-500" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Invitación válida
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  {invitation?.email && (
                    <span>Para: <strong className="text-sky-500">{invitation.email}</strong></span>
                  )}
                </p>
                {invitation?.role_name && (
                  <p className="text-xs text-indigo-500 mt-1">
                    Rol asignado: <strong>{invitation.role_name}</strong>
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="p-8">
            {status === 'ready' && (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Nombre completo */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Nombre completo
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Ej. Juan Pérez"
                    className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all outline-none placeholder-slate-400"
                    required
                  />
                </div>

                {/* Contraseña */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Contraseña
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all outline-none placeholder-slate-400 pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                    Mínimo 8 caracteres
                  </p>
                </div>

                {/* Confirmar contraseña */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Confirmar contraseña
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all outline-none placeholder-slate-400"
                    required
                  />
                </div>

                {/* Error message */}
                {error && (
                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3 text-red-600 dark:text-red-400 text-sm">
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Submit button */}
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-4 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 text-white rounded-xl font-semibold text-lg shadow-lg shadow-sky-500/20 hover:shadow-xl hover:shadow-sky-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Creando cuenta...
                    </>
                  ) : (
                    <>
                      Aceptar Invitación y Entrar
                      <ShieldCheck className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Success state */}
            {status === 'success' && (
              <div className="text-center py-8">
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-emerald-500/10 flex items-center justify-center">
                  <ShieldCheck className="w-10 h-10 text-emerald-500" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                  ¡Cuenta creada con éxito!
                </h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Redirigiéndote al dashboard...
                </p>
              </div>
            )}
          </div>

          <div className="bg-slate-50 dark:bg-slate-950/50 px-8 py-4 text-center border-t border-slate-100 dark:border-slate-800">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Al aceptar, aceptas nuestros términos y condiciones de uso.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AcceptInvitationPage;
