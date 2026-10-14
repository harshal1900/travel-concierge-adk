import type { UiComponent } from "@/lib/a2ui";

export function ComponentRenderer({ components }: { components: UiComponent[] }) {
  return (
    <div className="flex flex-col gap-4">
      {components.map((c) =>
        c.kind === "CardList" ? (
          <section key={c.id} aria-labelledby={`${c.id}-title`}>
            {c.title && (
              <h2 id={`${c.id}-title`} className="mb-2 text-base font-semibold">
                {c.title}
              </h2>
            )}
            <ul className="grid gap-2 sm:grid-cols-2">
              {c.items.map((item, i) => (
                <li key={`${item.title}-${i}`} className="rounded-lg border bg-card p-3">
                  <p className="font-medium">{item.title}</p>
                  {item.label && <p className="text-sm text-muted-foreground">{item.label}</p>}
                  <p className="mt-1 text-sm">
                    <span>Rating: {item.rating ?? "Not listed"}</span>
                    <span aria-hidden="true"> · </span>
                    <span>
                      {item.costLabel}: {item.cost ?? "Not listed"}
                    </span>
                  </p>
                </li>
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
