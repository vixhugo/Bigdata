import React, { useState, useEffect, useMemo } from 'react';
import { 
  Mail, Plus, Trash2, Eye, CheckCircle2, XCircle, Clock, 
  MoreVertical, Search, Filter, Users, Send, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface Invitation {
  id: number;
  email: string;
  full_name: string | null;
  role_id: number;
  role_name: string | null;
  token: string;
  is_accepted: boolean;
  accepted_at: string | null;
  expires_at: string;
  message: string | null;
  created_at: string;
  updated_at: string | null;
  invited_by_email: string | null;
  invited_by_name: string | null;
}

interface Role {
  id: number;
  name: string;
  display_name: string;
}

interface InvitationFormData {
  email: string;
  full_name: string;
  role_id: number;
  message: string;
  expires_in_days: number;
}

export const InvitationsPage: React.FC = () => {
  const { hasPermission, token } = useAuth();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'accepted' | 'expired'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  
  const [formData, setFormData] = useState<InvitationFormData>({
    email: '',
    full_name: '',
    role_id: 4, // user
    message: '',
    expires_in_days: 7,
  });

  // Cargar invitations y roles
  useEffect(() => {
    fetchInvitations();
    fetchRoles();
  }, []);

  const fetchInvitations = async () => {
    try {
      const response = await fetch('/api/invitations', {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (response.ok) {
        const data = await response.json();
        setInvitations(data.items || []);
      }
    } catch (err) {
      console.error('Error al cargar invitaciones:', err);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/admin/roles', {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (response.ok) {
        const data = await response.json();
        setRoles(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error('Error al cargar roles:', err);
    }
  };

  // Filtrar invitaciones
  const filteredInvitations = useMemo(() => {
    let result = invitations;

    // Filtro de búsqueda
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (inv) =>
          inv.email.toLowerCase().includes(q) ||
          inv.full_name?.toLowerCase().includes(q) ||
          inv.role_name?.toLowerCase().includes(q)
      );
    }

    // Filtro de estado
    if (statusFilter !== 'all') {
      const now = new Date();
      result = result.filter((inv) => {
        if (statusFilter === 'accepted') return inv.is_accepted;
        if (statusFilter === 'expired') return new Date(inv.expires_at) < now;
        return !inv.is_accepted && new Date(inv.expires_at) > now;
      });
    }

    return result;
  }, [invitations, searchQuery, statusFilter]);

  // Crear invitación
  const handleCreateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.email || !formData.role_id) {
      alert('Por favor completa los campos obligatorios.');
      return;
    }

    try {
      const response = await fetch('/api/invitations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setFormData({
          email: '',
          full_name: '',
          role_id: 4,
          message: '',
          expires_in_days: 7,
        });
        setShowCreateModal(false);
        fetchInvitations();
        alert('Invitación creada con éxito.');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Error al crear la invitación.');
      }
    } catch (err) {
      alert('Error al conectar con el servidor.');
    }
  };

  // Revocar invitación
  const handleRevokeInvitation = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres revocar esta invitación?')) return;

    setDeletingId(id);
    try {
      const response = await fetch(`/api/invitations/${id}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });

      if (response.ok) {
        fetchInvitations();
      } else {
        alert('Error al revocar la invitación.');
      }
    } catch (err) {
      alert('Error al conectar con el servidor.');
    } finally {
      setDeletingId(null);
    }
  };

  // Copiar enlace de invitación
  const copyLink = (token: string) => {
    const link = `${window.location.origin}/accept-invitation?token=${token}`;
    navigator.clipboard.writeText(link);
    alert('Enlace copiado al portapapeles.');
  };

  // Formatear fecha
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-PE', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  // Obtener color de estado
  const getStatusColor = (inv: Invitation) => {
    const now = new Date();
    if (inv.is_accepted) return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
    if (new Date(inv.expires_at) < now) return 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20';
    return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
  };

  // Obtener estado label
  const getStatusLabel = (inv: Invitation) => {
    const now = new Date();
    if (inv.is_accepted) return 'Aceptada';
    if (new Date(inv.expires_at) < now) return 'Expirada';
    return 'Pendiente';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Invitaciones
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Gestionar invitaciones de usuarios al sistema
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-xl font-semibold transition-colors shadow-lg shadow-sky-500/20"
        >
          <Plus className="w-5 h-5" />
          <span>Nueva Invitación</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por email, nombre o rol..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
          >
            <option value="all">Todas</option>
            <option value="pending">Pendientes</option>
            <option value="accepted">Aceptadas</option>
            <option value="expired">Expiradas</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Mail className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Total</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{invitations.length}</p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <Clock className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Pendientes</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {filteredInvitations.filter(i => !i.is_accepted && new Date(i.expires_at) > new Date()).length}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <CheckCircle2 className="w-6 h-6 text-emerald-500" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Aceptadas</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {invitations.filter(i => i.is_accepted).length}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/10 rounded-lg">
              <XCircle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Expiradas</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {invitations.filter(i => new Date(i.expires_at) < new Date()).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Invitations Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Email</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Nombre</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Rol</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Expira</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredInvitations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                    <div className="flex flex-col items-center gap-3">
                      <Mail className="w-12 h-12 text-slate-300 dark:text-slate-600" />
                      <p>No hay invitaciones encontradas</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredInvitations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sky-500/10 flex items-center justify-center text-sky-600 dark:text-sky-400 font-semibold">
                          {inv.email[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">{inv.email}</p>
                          {inv.invited_by_email && (
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              Enviada por: {inv.invited_by_email}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-slate-900 dark:text-white">
                        {inv.full_name || '—'}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-500/10 text-sky-600 dark:text-sky-400">
                        {inv.role_name || 'user'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(inv)}`}>
                        {inv.is_accepted ? (
                          <CheckCircle2 className="w-3 h-3 mr-1.5" />
                        ) : new Date(inv.expires_at) < new Date() ? (
                          <XCircle className="w-3 h-3 mr-1.5" />
                        ) : (
                          <Clock className="w-3 h-3 mr-1.5" />
                        )}
                        {getStatusLabel(inv)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-slate-900 dark:text-white">
                        {formatDate(inv.expires_at)}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {new Date(inv.expires_at) > new Date() 
                          ? 'Vigente' 
                          : 'Vencida'}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {!inv.is_accepted && (
                          <>
                            <button
                              onClick={() => copyLink(inv.token)}
                              className="p-2 text-sky-600 dark:text-sky-400 hover:bg-sky-50 dark:hover:bg-sky-500/10 rounded-lg transition-colors"
                              title="Copiar enlace"
                            >
                              <Send className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleRevokeInvitation(inv.id)}
                              disabled={deletingId === inv.id}
                              className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors"
                              title="Revocar"
                            >
                              {deletingId === inv.id ? (
                                <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Invitation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setShowCreateModal(false)} />
          
          <div className="relative bg-white dark:bg-slate-900 rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="px-8 py-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Nueva Invitación
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateInvitation} className="px-8 py-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Email del destinatario *
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="ejemplo@correo.com"
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Nombre completo
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="Nombre y apellidos"
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Rol asignado *
                </label>
                <select
                  value={formData.role_id}
                  onChange={(e) => setFormData({ ...formData, role_id: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
                  required
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.display_name} ({role.name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Mensaje personalizado (opcional)
                </label>
                <textarea
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Escribe un mensaje para el usuario..."
                  rows={3}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Expiración (días) *
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={formData.expires_in_days}
                  onChange={(e) => setFormData({ ...formData, expires_in_days: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
                />
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  La invitación expirará en {formData.expires_in_days} días
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-6 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 font-medium transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-600 text-white font-semibold shadow-lg shadow-sky-500/20 hover:shadow-xl transition-all"
                >
                  Enviar Invitación
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvitationsPage;
