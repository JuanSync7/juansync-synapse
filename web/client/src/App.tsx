import { useEffect, useState } from 'react';
import { NavLink, Outlet, Route, Routes } from 'react-router-dom';
import type { ArtifactClass, Counts } from '../../shared/types';
import { listArtifacts } from './api/client';
import ArtifactDetail from './pages/ArtifactDetail';
import ArtifactList from './pages/ArtifactList';
import Brainstorm from './pages/Brainstorm';
import CreatorRun from './pages/CreatorRun';
import Framework from './pages/Framework';
import Landing from './pages/Landing';
import Memos from './pages/Memos';
import Registry from './pages/Registry';
import Scripts from './pages/Scripts';
import Taxonomy from './pages/Taxonomy';

// Nav, grouped into sections. [route, label, optional artifact-class for the count].
type NavItem = readonly [string, string, ArtifactClass?];
const NAV_GROUPS: ReadonlyArray<{ heading: string | null; items: ReadonlyArray<NavItem> }> = [
  { heading: null, items: [['/', 'Overview']] },
  {
    heading: 'Library',
    items: [
      ['/skills', 'Skills', 'skill'],
      ['/agents', 'Agents', 'agent'],
      ['/protocols', 'Protocols', 'protocol'],
      ['/tools', 'Tools', 'tool'],
      ['/pathways', 'Pathways', 'pathway'],
    ],
  },
  {
    heading: 'Catalog',
    items: [
      ['/registry', 'Registry'],
      ['/taxonomy', 'Taxonomy'],
      ['/framework', 'Framework'],
    ],
  },
  {
    heading: 'Operate',
    items: [
      ['/memos', 'Memos'],
      ['/brainstorm', 'Brainstorm'],
      ['/runs', 'Runs'],
      ['/scripts', 'Scripts'],
    ],
  },
];

function Shell() {
  const [counts, setCounts] = useState<Counts | null>(null);

  useEffect(() => {
    let cancelled = false;
    listArtifacts()
      .then((res) => {
        if (!cancelled) setCounts(res.counts);
      })
      .catch(() => {
        // Nav counts are an enhancement; absence is fine.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen bg-ink text-text">
      <nav
        aria-label="Primary"
        className="sticky top-0 h-screen w-60 shrink-0 overflow-y-auto border-r border-line bg-surface px-4 py-6"
      >
        <NavLink to="/" end className="mb-7 flex items-center gap-2 px-2">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-synapse text-sm font-semibold text-white">
            S
          </span>
          <span className="text-base font-semibold tracking-tight text-text">Synapse</span>
        </NavLink>

        {NAV_GROUPS.map((group) => (
          <div key={group.heading ?? 'root'} className="mb-5">
            {group.heading && (
              <p className="mb-1.5 px-2 text-[0.68rem] font-semibold uppercase tracking-wider text-muted/70">
                {group.heading}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map(([to, label, cls]) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center justify-between rounded-md px-2 py-1.5 text-sm transition-colors ${
                        isActive
                          ? 'bg-synapse/10 font-medium text-synapse'
                          : 'text-muted hover:bg-line/50 hover:text-text'
                      }`
                    }
                  >
                    <span>{label}</span>
                    {cls && counts && (
                      <span className="font-mono text-xs text-muted/70">{counts[cls]}</span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      {/* Full-width content area (capped on ultra-wide displays). Reading-centric
          pages re-constrain themselves (Landing/ArtifactList/ArtifactDetail);
          split-nav and table/grid pages (Registry, Taxonomy, …) fill the width. */}
      <main className="mx-auto w-full max-w-[100rem] px-10 py-12">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Landing />} />
        <Route path="skills" element={<ArtifactList cls="skill" />} />
        <Route path="agents" element={<ArtifactList cls="agent" />} />
        <Route path="protocols" element={<ArtifactList cls="protocol" />} />
        <Route path="tools" element={<ArtifactList cls="tool" />} />
        <Route path="pathways" element={<ArtifactList cls="pathway" />} />
        <Route path="registry" element={<Registry />} />
        <Route path="taxonomy" element={<Taxonomy />} />
        <Route path="framework" element={<Framework />} />
        <Route path="memos" element={<Memos />} />
        <Route path="brainstorm" element={<Brainstorm />} />
        <Route path="runs" element={<CreatorRun />} />
        <Route path="runs/:id" element={<CreatorRun />} />
        <Route path="scripts" element={<Scripts />} />
        <Route path="artifact/:cls/:slug" element={<ArtifactDetail />} />
      </Route>
    </Routes>
  );
}
