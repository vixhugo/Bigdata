import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';

// ── Páginas de autenticación ─────────────────────────────────────────────────
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { AcceptInvitationPage } from './pages/auth/AcceptInvitationPage';

// ── Layout y páginas de administración ───────────────────────────────────────
import { AdminLayout, AdminTab } from './components/admin/AdminLayout';
import { DashboardPage } from './pages/admin/DashboardPage';
import { MembersPage } from './pages/admin/MembersPage';
import { RolesPage } from './pages/admin/RolesPage';
import { AuditPage } from './pages/admin/AuditPage';
import { ProfilePage } from './pages/admin/ProfilePage';
import { InvitationsPage } from './pages/admin/InvitationsPage';

// ── Componentes de la app meteorológica ──────────────────────────────────────
import { Navbar } from './components/Navbar';
import { CurrentWeatherHero } from './components/CurrentWeatherHero';
import { MetricCardsGrid } from './components/MetricCardsGrid';
import { HourlyForecast } from './components/HourlyForecast';
import { DailyForecast } from './components/DailyForecast';
import { WeatherCharts } from './components/WeatherCharts';
import { PeruMap } from './components/PeruMap';
import { CityComparison } from './components/CityComparison';
import { ClimateAnalysis } from './components/ClimateAnalysis';
import { WeatherAlerts } from './components/WeatherAlerts';
import { RankingsSection } from './components/RankingsSection';
import { CsvImporter } from './components/CsvImporter';
import { SkeletonLoader } from './components/SkeletonLoader';
import { Footer } from './components/Footer';
import { Spinner } from './components/admin/ui';
import PDFPreview from './components/PDFPreview';
import { ProjectLanding } from './components/ProjectLanding';

import { City, FullForecastResponse, DepartmentWeatherSummary, AlertsResponse } from './types/weather';
import { weatherApi } from './services/api';
import { usePdfExport } from './hooks/usePdfExport';
import { buildForecastReport } from './services/reportBuilders';
import { AlertCircle, Sparkles } from 'lucide-react';

// ─── Tipos de vista de la app ─────────────────────────────────────────────────
type AuthPage = 'login' | 'register' | 'forgot-password';
type AppView = 'landing' | 'auth' | 'app' | 'admin';

// ─── Pantalla de carga inicial ────────────────────────────────────────────────
const SplashScreen: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-950">
    <div className="flex flex-col items-center gap-4">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-red-600 to-sky-500 p-0.5">
        <div className="w-full h-full bg-slate-900 rounded-[15px] flex items-center justify-center">
          <span className="text-2xl font-black text-white">PE</span>
        </div>
      </div>
      <Spinner size="md" />
      <p className="text-slate-400 text-sm">Cargando MeteoPerú...</p>
    </div>
  </div>
);

// ─── Controlador de routing basado en estado de auth ─────────────────────────
const AppRouter: React.FC = () => {
  const { status, isAdmin, isSuperAdmin } = useAuth();
  const { isGenerating: isPdfGenerating, generate: generatePdf } = usePdfExport();

  const [view, setView] = useState<AppView>('landing');
  const [authPage, setAuthPage] = useState<AuthPage>('login');
  const [adminTab, setAdminTab] = useState<AdminTab>('dashboard');

  // Estado del tema
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('meteoperu_theme');
    return saved === 'light' ? 'light' : 'dark';
  });

  // Estado meteorológico
  const [cities, setCities] = useState<City[]>([]);
  const [selectedCity, setSelectedCity] = useState<City | null>(null);
  const [forecast, setForecast] = useState<FullForecastResponse | null>(null);
  const [departmentsSummary, setDepartmentsSummary] = useState<DepartmentWeatherSummary[]>([]);
  const [alertsSummary, setAlertsSummary] = useState<AlertsResponse | null>(null);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estado para vista previa de PDF
  const [showPdfPreview, setShowPdfPreview] = useState<boolean>(false);
  const [pdfOptions, setPdfOptions] = useState<any>(null);

  // Sincronizar tema
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.classList.toggle('light', theme === 'light');
    localStorage.setItem('meteoperu_theme', theme);
  }, [theme]);

  // Cargar ciudades
  useEffect(() => {
    weatherApi.getCities().then((list) => {
      setCities(list);
      const lima = list.find(c => c.name === 'Lima') || list[0];
      if (lima) setSelectedCity(lima);
    }).catch(() => {
      setError('No se pudo conectar con el servidor meteorológico.');
      setIsLoading(false);
    });
  }, []);

  // Cargar resumen nacional
  const loadGlobalOverview = useCallback(async () => {
    try {
      const [ov, al] = await Promise.all([weatherApi.getOverview(), weatherApi.getAlerts()]);
      setDepartmentsSummary(ov);
      setAlertsSummary(al);
    } catch {}
  }, []);

  useEffect(() => { loadGlobalOverview(); }, [loadGlobalOverview]);

  // Cargar pronóstico de ciudad
  const loadCityWeather = useCallback(async (city: City, refreshing = false) => {
    if (refreshing) setIsRefreshing(true); else setIsLoading(true);
    setError(null);
    try {
      setForecast(await weatherApi.getForecast(city.id));
    } catch {
      setError(`Error al consultar datos de ${city.name}. Intente de nuevo.`);
    } finally { setIsLoading(false); setIsRefreshing(false); }
  }, []);

  useEffect(() => {
    if (selectedCity) loadCityWeather(selectedCity);
  }, [selectedCity, loadCityWeather]);

  // Navegar desde páginas de auth
  const handleAuthNavigate = (page: 'login' | 'register' | 'forgot-password' | 'app' | 'admin') => {
    if (page === 'app')   { setView('app'); return; }
    if (page === 'admin') { setView('admin'); return; }
    setView('auth');
    setAuthPage(page as AuthPage);
  };

  const handleSelectCityByName = (cityName: string) => {
    const found = cities.find(c => c.name.toLowerCase() === cityName.toLowerCase());
    if (found) { setSelectedCity(found); setActiveTab('dashboard'); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  };

  const handleLocateUser = () => {
    if (!navigator.geolocation) { alert('La geolocalización no está soportada.'); return; }
    setIsRefreshing(true);
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude, longitude } }) => {
        try {
          const data = await weatherApi.getForecast(undefined, latitude, longitude);
          setForecast(data);
          setSelectedCity({ id: 0, department_id: 0, name: data.current.city_name || 'Mi Ubicación', latitude, longitude, altitude: 0, is_featured: false, is_capital: false, department_name: data.current.department_name || 'Perú', region_natural: 'Costa' });
          setActiveTab('dashboard');
        } catch { alert('Error al consultar el clima de sus coordenadas.'); }
        finally { setIsRefreshing(false); }
      },
      (err) => { setIsRefreshing(false); alert('No se pudo acceder a su ubicación: ' + err.message); },
      { timeout: 10000 }
    );
  };

  const featuredQuickCities = ['Lima', 'Arequipa', 'Cusco', 'Piura', 'Trujillo', 'Chiclayo', 'Iquitos', 'Huancayo', 'Puno', 'Tacna', 'Chimbote'];

  // ── Pantalla de carga del auth ─────────────────────────────────────────────
  if (status === 'loading') return <SplashScreen />;

  const invitationToken = new URLSearchParams(window.location.search).get('token');

  if (invitationToken) {
    return <AcceptInvitationPage />;
  }

  if (view === 'landing') {
    return <ProjectLanding onOpenMeteoPeru={() => setView('app')} />;
  }

  // ── Vista de autenticación (solo cuando el usuario quiere iniciar sesión) ───
  if (view === 'auth') {
    if (authPage === 'register')       return <RegisterPage onNavigate={handleAuthNavigate} />;
    if (authPage === 'forgot-password') return <ForgotPasswordPage onNavigate={handleAuthNavigate} />;
    return <LoginPage onNavigate={handleAuthNavigate} />;
  }

  // ── Vista admin ────────────────────────────────────────────────────────────
  if (view === 'admin') {
    if (!isAdmin() && !isSuperAdmin()) { setView('app'); return null; }
    return (
      <AdminLayout activeTab={adminTab} onTabChange={setAdminTab} onBackToApp={() => setView('app')}>
        {adminTab === 'dashboard' && <DashboardPage />}
        {adminTab === 'members'   && <MembersPage />}
        {adminTab === 'roles'     && <RolesPage />}
        {adminTab === 'audit'     && <AuditPage />}
        {adminTab === 'profile'   && <ProfilePage />}
        {adminTab === 'invitations' && <InvitationsPage />}
      </AdminLayout>
    );
  }

  // ── Vista meteorológica principal ──────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col bg-slate-100 text-slate-800 dark:bg-slate-950 dark:text-slate-100 selection:bg-sky-500 selection:text-white transition-colors duration-300">
      <Navbar
        cities={cities}
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
        onRefresh={() => { if (selectedCity) { loadCityWeather(selectedCity, true); loadGlobalOverview(); } }}
        isRefreshing={isRefreshing || isPdfGenerating}
        onLocateUser={handleLocateUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        alertsCount={alertsSummary ? alertsSummary.danger_count + alertsSummary.warning_count : 0}
        onExportForecast={async () => {
            if (!forecast) return;
            const opts = buildForecastReport(
              forecast.current,
              forecast.hourly,
              forecast.daily,
            );
            setPdfOptions(opts);
            setShowPdfPreview(true);
          }}
        theme={theme}
        onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
        onOpenAdmin={() => setView('admin')}
        onOpenAuth={() => { setView('auth'); setAuthPage('login'); }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Acceso rápido */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
          <span className="text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px] shrink-0 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
            Acceso Rápido:
          </span>
          {featuredQuickCities.map((cName) => {
            const isCurrent = selectedCity?.name === cName;
            return (
              <button key={cName} onClick={() => handleSelectCityByName(cName)}
                className={`px-3 py-1 rounded-full whitespace-nowrap transition-all font-medium ${
                  isCurrent
                    ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20 font-bold'
                    : 'bg-white/90 hover:bg-slate-200/80 text-slate-700 border border-slate-200/80 shadow-sm dark:bg-slate-900/80 dark:hover:bg-slate-800 dark:text-slate-300 dark:border-slate-800'
                }`}>
                {cName}
              </button>
            );
          })}
        </div>

        {/* Error banner */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-between gap-3 text-red-600 dark:text-red-300 text-xs">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => { if (selectedCity) loadCityWeather(selectedCity, true); }}
              className="px-3 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-700 dark:text-red-200 font-semibold transition-colors">
              Reintentar
            </button>
          </div>
        )}

        {/* Vistas de la app meteorológica */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {isLoading || !forecast ? <SkeletonLoader /> : (
              <>
                <CurrentWeatherHero weather={forecast.current} />
                <MetricCardsGrid weather={forecast.current} />
                <HourlyForecast hourly={forecast.hourly} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <WeatherCharts hourly={forecast.hourly} theme={theme} />
                  <DailyForecast daily={forecast.daily} />
                </div>
              </>
            )}
          </div>
        )}
        {activeTab === 'map' && <PeruMap departmentsSummary={departmentsSummary} onSelectCityByName={handleSelectCityByName} selectedCity={selectedCity} theme={theme} />}
        {activeTab === 'compare' && <CityComparison cities={cities} />}
        {activeTab === 'analysis' && <ClimateAnalysis cities={cities} selectedCity={selectedCity} />}
        {activeTab === 'alerts' && <WeatherAlerts selectedCity={selectedCity} onSelectCityByName={handleSelectCityByName} />}
        {activeTab === 'rankings' && <RankingsSection onSelectCityByName={handleSelectCityByName} />}
        {activeTab === 'csv' && <CsvImporter theme={theme} />}
      </main>

      <Footer />
      
      {/* Vista previa de PDF */}
      {showPdfPreview && pdfOptions && (
        <PDFPreview
          options={pdfOptions}
          onCancel={() => {
            setShowPdfPreview(false);
            setPdfOptions(null);
          }}
          onDownload={async () => {
            await generatePdf(pdfOptions);
            setShowPdfPreview(false);
            setPdfOptions(null);
          }}
        />
      )}
    </div>
  );
};

// ─── Componente raíz con AuthProvider ────────────────────────────────────────
export const App: React.FC = () => (
  <AuthProvider>
    <AppRouter />
  </AuthProvider>
);

export default App;
