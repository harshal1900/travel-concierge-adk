import type { CardItem, CardListComponent, UiComponent } from "@/lib/a2ui";

const VARIANTS = {
  attractions: {
    heading: "Things to do",
    badge: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
    bar: "from-sky-400 to-indigo-500",
    chip: "bg-emerald-50 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200",
  },
  dining: {
    heading: "Where to eat",
    badge: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200",
    bar: "from-amber-400 to-rose-500",
    chip: "bg-violet-50 text-violet-900 dark:bg-violet-950 dark:text-violet-200",
  },
} as const;

function Star() {
  return (
    <svg viewBox="0 0 20 20" className="size-4 fill-amber-400" aria-hidden="true">
      <path d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L10 14.9 4.8 17.7l1-5.9L1.5 7.7l5.9-.8L10 1.5z" />
    </svg>
  );
}

function Card({ item, variant }: { item: CardItem; variant: CardListComponent["variant"] }) {
  const v = VARIANTS[variant];
  return (
    <li className="group relative overflow-hidden rounded-2xl border bg-card p-4 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md focus-within:ring-2 focus-within:ring-ring">
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${v.bar}`} aria-hidden="true" />
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base leading-snug font-semibold">{item.title}</h3>
        {item.label && (
          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${v.badge}`}>{item.label}</span>
        )}
      </div>
      <dl className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <div className="flex items-center gap-1">
          <Star />
          <dt className="sr-only">Rating</dt>
          <dd className="font-medium">{item.rating ?? "Not listed"}</dd>
        </div>
        <div className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 ${v.chip}`}>
          <dt className="text-xs opacity-80">{item.costLabel}</dt>
          <dd className="font-medium">{item.cost ?? "Not listed"}</dd>
        </div>
      </dl>
    </li>
  );
}

export function ComponentRenderer({ components }: { components: UiComponent[] }) {
  return (
    <div className="flex flex-col gap-6">
      {components.map((c) =>
        c.kind === "CardList" ? (
          <section key={c.id} aria-labelledby={`${c.id}-title`}>
            <div className="mb-3 flex items-baseline justify-between gap-2">
              <h2 id={`${c.id}-title`} className="text-lg font-semibold tracking-tight">
                {c.title || VARIANTS[c.variant].heading}
              </h2>
              <span className="text-xs text-muted-foreground">{c.items.length} picks</span>
            </div>
            <ul className="grid gap-3 sm:grid-cols-2">
              {c.items.map((item, i) => (
                <Card key={`${item.title}-${i}`} item={item} variant={c.variant} />
              ))}
            </ul>
          </section>
        ) : (
          <p key={c.id} className="whitespace-pre-wrap">
            {c.content}
          </p>
        ),
      )}
    </div>
  );
}
