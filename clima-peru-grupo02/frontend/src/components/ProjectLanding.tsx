import React from 'react';
import {
  ArrowUpRight,
  BarChart3,
  CloudSun,
  Database,
  LockKeyhole,
  Network,
  Sparkles,
} from 'lucide-react';

interface ProjectLandingProps {
  onOpenMeteoPeru: () => void;
}

interface ProjectCard {
  eyebrow: string;
  title: string;
  description: string;
  icon: React.ElementType;
  accent: string;
  active?: boolean;
}

const projects: ProjectCard[] = [
  {
    eyebrow: 'Proyecto MeteoPerú',
    title: 'MeteoPerú Pro',
    description: 'Monitoreo del clima en tiempo real para el Perú: pronósticos, mapas, alertas y reportes oficiales.',
    icon: CloudSun,
    accent: 'from-sky-400 to-rose-400',
    active: true,
  },
  {
    eyebrow: 'Proyecto institucional',
    title: 'Proyecto 01',
    description: 'Nuevo módulo institucional en etapa de planificación. Se habilitará próximamente.',
    icon: Network,
    accent: 'from-emerald-300 to-cyan-400',
  },
  {
    eyebrow: 'Proyecto institucional',
    title: 'Proyecto 02',
    description: 'Nuevo módulo institucional en etapa de planificación. Se habilitará próximamente.',
    icon: BarChart3,
    accent: 'from-violet-300 to-fuchsia-400',
  },
  {
    eyebrow: 'Proyecto institucional',
    title: 'Proyecto 03',
    description: 'Nuevo módulo institucional en etapa de planificación. Se habilitará próximamente.',
    icon: Database,
    accent: 'from-orange-300 to-rose-400',
  },
];

export const ProjectLanding: React.FC<ProjectLandingProps> = ({ onOpenMeteoPeru }) => (
  <main className="min-h-screen overflow-hidden bg-[#080d1a] px-5 py-10 text-white sm:px-8 lg:px-12">
    <div className="pointer-events-none fixed inset-0 opacity-70" aria-hidden="true">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_8%,rgba(14,165,233,0.18),transparent_28%),radial-gradient(circle_at_90%_20%,rgba(244,63,94,0.12),transparent_25%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.045)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.045)_1px,transparent_1px)] bg-[size:52px_52px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />
    </div>

    <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col">
      <header className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/15 bg-white/10 shadow-2xl shadow-sky-950/40 backdrop-blur">
            <Sparkles className="h-5 w-5 text-sky-300" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.28em] text-sky-200/70">Portal institucional</p>
            <p className="text-sm font-semibold text-white/90">Centro de proyectos</p>
          </div>
        </div>
        <span className="hidden rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-[11px] font-medium text-slate-400 sm:block">
          Grupo 02 · 2026
        </span>
      </header>

      <section className="mx-auto w-full max-w-6xl flex-1 py-16 sm:py-20 lg:py-24">
        <div className="max-w-3xl animate-[fade-in_700ms_ease-out_both]">
          <p className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.3em] text-sky-300">
            <span className="h-px w-8 bg-sky-400" />
            Aplicaciones institucionales
          </p>
          <h1 className="max-w-4xl text-4xl font-black leading-[1.05] tracking-tight text-white sm:text-6xl lg:text-7xl">
            Centro de Proyectos <span className="text-sky-300">&</span>{' '}
            <span className="bg-gradient-to-r from-sky-300 via-white to-rose-300 bg-clip-text text-transparent">Aplicaciones</span>
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">
            Selecciona un proyecto para ingresar. Los sistemas en desarrollo se encuentran marcados como «Próximamente».
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {projects.map((project, index) => {
            const Icon = project.icon;
            const content = (
              <>
                <div className="flex items-start justify-between gap-3">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${project.accent} p-px shadow-lg`}>
                    <div className="flex h-full w-full items-center justify-center rounded-[15px] bg-[#101a2d]">
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                  </div>
                  <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide ${project.active ? 'border-rose-300/30 bg-rose-300/15 text-rose-200' : 'border-amber-300/25 bg-amber-300/10 text-amber-200'}`}>
                    {project.active ? 'Disponible' : 'Próximamente'}
                  </span>
                </div>
                <div className="mt-8">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">{project.eyebrow}</p>
                  <h2 className="mt-2 text-xl font-extrabold tracking-tight text-white">{project.title}</h2>
                  <p className="mt-4 text-sm leading-6 text-slate-400">{project.description}</p>
                </div>
                <div className="mt-8 flex items-center gap-2 text-sm font-semibold">
                  {project.active ? (
                    <><span className="text-sky-300">Ingresar al proyecto</span><ArrowUpRight className="h-4 w-4 text-sky-300" /></>
                  ) : (
                    <><LockKeyhole className="h-4 w-4 text-slate-500" /><span className="text-slate-500">Disponible próximamente</span></>
                  )}
                </div>
              </>
            );

            return project.active ? (
              <button
                key={project.title}
                type="button"
                onClick={onOpenMeteoPeru}
                className="group min-h-[315px] rounded-[26px] border border-sky-300/50 bg-gradient-to-br from-sky-400/20 via-white/[0.06] to-rose-300/10 p-6 text-left shadow-[0_20px_70px_rgba(14,165,233,0.14)] transition duration-300 hover:-translate-y-1 hover:border-sky-200 hover:shadow-[0_24px_80px_rgba(14,165,233,0.24)] focus:outline-none focus:ring-2 focus:ring-sky-300/80 animate-[fade-in_700ms_ease-out_150ms_both]"
              >
                {content}
              </button>
            ) : (
              <div
                key={project.title}
                aria-disabled="true"
                className="min-h-[315px] cursor-not-allowed rounded-[26px] border border-white/10 bg-white/[0.035] p-6 opacity-80 animate-[fade-in_700ms_ease-out_300ms_both]"
                style={{ animationDelay: `${150 + index * 90}ms` }}
              >
                {content}
              </div>
            );
          })}
        </div>
      </section>

      <footer className="flex flex-col gap-2 border-t border-white/10 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <span>© 2026 Centro de Proyectos & Aplicaciones Institucionales</span>
        <span>Acceso seguro · Plataforma en evolución</span>
      </footer>
    </div>
  </main>
);
