// A quiet section divider under page titles and between sections. (Formerly the
// dendrite-pulse signature motif; stripped to a plain hairline in the minimalist
// redesign. The API + test id are unchanged so all callers keep working.)

interface DendriteRuleProps {
  /** Retained for API compatibility; the rule no longer animates. */
  pulse?: boolean;
  className?: string;
}

export default function DendriteRule({ className = '' }: DendriteRuleProps) {
  return <div className={`dendrite ${className}`} aria-hidden="true" data-testid="dendrite-rule" />;
}
