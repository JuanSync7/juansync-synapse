// A single artifact row in a list: mono+green slug, description, layer + status
// badges, domain. Links to the detail page. See DESIGN.md (slugs are the
// framework's atoms — always mono + green-tinted).
import { Link } from 'react-router-dom';
import type { Artifact } from '../../../shared/types';
import LayerBadge from './LayerBadge';
import StatusChip from './StatusChip';

interface ArtifactCardProps {
  artifact: Artifact;
  /** Index used to stagger the fade-rise on mount. */
  index?: number;
}

export default function ArtifactCard({ artifact, index = 0 }: ArtifactCardProps) {
  return (
    <li
      className="fade-rise h-full"
      style={{ animationDelay: `${Math.min(index, 20) * 35}ms` }}
    >
      <Link
        to={`/artifact/${artifact.class}/${artifact.slug}`}
        className="group flex h-full flex-col rounded-xl border border-line bg-surface px-4 py-3.5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-synapse/40 hover:shadow"
      >
        <span className="break-words font-mono text-sm font-medium text-synapse group-hover:underline">
          {artifact.slug}
        </span>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <LayerBadge layer={artifact.layer} />
          <StatusChip status={artifact.status} />
        </div>
        {artifact.description && (
          <p className="mt-2.5 line-clamp-3 text-sm leading-relaxed text-muted">
            {artifact.description}
          </p>
        )}
        {artifact.domain && (
          <p className="mt-auto pt-3 font-mono text-xs text-muted/70">{artifact.domain}</p>
        )}
      </Link>
    </li>
  );
}
