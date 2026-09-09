import React, { useState, ReactNode } from 'react';
import {
  LayoutDashboard, Users, Shield, ClipboardList, LogOut,
  Menu, X, ChevronRight, Bell, UserCircle2, Settings,
  ShieldCheck, Activity, Mail,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export type AdminTab = 'dashboard' | 'members' | 'roles' | 'audit' | 'profile' | 'invitations';

interface AdminLayoutProps {
  children: ReactNode;
  activeTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
  onBackToApp: () => void;
}

interface NavItem {
  id: AdminTab;
  label: string;
  icon: React.FC<{ className?: string }>;
  permission?: string;
  badge?: number;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({
  children, activeTab, onTabChange, onBackToApp,
}) => {
  const { user, logout, hasPermission, isSuperAdmin } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems: NavItem[] = [
    { id: 'dashboard',  label: 'Dashboard',   icon: LayoutDashboard, permission: undefined },
    { id: 'members',    label: 'Miembros',     icon: Users,           permission: 'users:view' },
    { id: 'roles',      label: 'Roles y Permisos', icon: Shield,      permission: 'roles:view' },
    { id: 'audit',      label: 'Auditoría',    icon: ClipboardList,   permission: 'audit:view' },
    { id: 'invitations', label: 'Invitaciones', icon: Mail,           permission: 'roles:view' },
    { id: 'profile',    label: 'Mi Perfil',    icon: UserCircle2,     permission: undefined },
  ];

  const visibleItems = navItems.filter(item =>
    !item.permission || hasPermission(item.permission) || isSuperAdmin()
  );

  const primaryRole = user?.roles[0];

  const roleColors: Record<string, string> = {
    super_admin: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    admin:       'bg-sky-500/20 text-sky-300 border-sky-500/30',
    supervisor:  'bg-amber-500/20 text-amber-300 border-amber-500/30',
    user:        'bg-slate-500/20 text-slate-300 border-slate-500/30',
  };
  const roleColor = primaryRole ? (roleColors[primaryRole.name] ?? roleColors.user) : roleColors.user;

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-3 cursor-pointer" onClick={onBackToApp}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-red-600 to-sky-500 p-0.5 shrink-0">
            <div className="w-full h-full bg-slate-900 rounded-[10px] flex items-center justify-center">
              <span className="text-sm font-black text-white">PE</span>
            </div>
          </div>
          <div>
            <div className="text-sm font-bold text-white">
              METEO<span className="text-sky-400">PERÚ</span>
            </div>
            <div className="text-[10px] text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-2.5 h-2.5 text-sky-500" />
              Panel de Administración
            </div>
          </div>
        </div>
      </div>

      {/* User info */}
      <div className="px-4 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {user?.full_name?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-white truncate">{user?.full_name}</div>
            <div className="text-xs text-slate-400 truncate">{user?.email}</div>
          </div>
        </div>
        {primaryRole && (
          <div className={`mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${roleColor}`}>
            <Activity className="w-2.5 h-2.5" />
            {primaryRole.display_name}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => { onTabChange(item.id); setSidebarOpen(false); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-500'}`} />
              <span className="flex-1 text-left">{item.label}</span>
              {isActive && <ChevronRight className="w-3 h-3 opacity-60" />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-4 space-y-1 border-t border-slate-800 pt-3">
        <button
          onClick={onBackToApp}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        >
          <Settings className="w-4 h-4 text-slate-500" />
          Volver a MeteoPerú
        </button>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar desktop */}
      <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 bg-slate-900 border-r border-slate-800">
        <SidebarContent />
      </aside>

      {/* Sidebar mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col w-64 bg-slate-900 border-r border-slate-800
          transform transition-transform duration-200 lg:hidden
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <SidebarContent />
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 flex items-center gap-4 px-6
          bg-slate-900/80 backdrop-blur border-b border-slate-800">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm flex-1">
            <span className="text-slate-500">Admin</span>
            <ChevronRight className="w-3 h-3 text-slate-600" />
            <span className="text-white font-medium capitalize">
              {visibleItems.find(i => i.id === activeTab)?.label ?? activeTab}
            </span>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <button className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors relative">
              <Bell className="w-4 h-4" />
            </button>
            <button
              onClick={() => onTabChange('profile')}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs">
                {user?.full_name?.charAt(0).toUpperCase() ?? 'U'}
              </div>
              <span className="text-sm text-slate-300 hidden sm:inline">{user?.full_name?.split(' ')[0]}</span>
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
