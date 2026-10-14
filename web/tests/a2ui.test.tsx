import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComponentRenderer } from "@/components/ComponentRenderer";
import { parseComponents } from "@/lib/a2ui";
import { PRD_RESPONSE } from "./fixtures";

describe("parseComponents", () => {
  it("parses both CardList variants from the PRD sample", () => {
    const parsed = parseComponents(PRD_RESPONSE.a2ui_payload);
    expect(parsed.map((c) => c.id)).toEqual(["attractions_card_list", "dining_card_list"]);
    expect(parsed[0]).toMatchObject({ items: [{ title: "Senso-ji Temple", label: "Culture", rating: "4.8", cost: "Free", costLabel: "Cost" }, expect.anything()] });
    expect(parsed[1]).toMatchObject({ items: [{ title: "Ichiran Ramen", label: "Ramen", cost: "$$", costLabel: "Price" }, expect.anything()] });
  });

  it("parses a TextCard fallback", () => {
    const parsed = parseComponents({ components: [{ id: "fallback_text_card", type: "TextCard", content: "Hi" }] });
    expect(parsed).toEqual([{ kind: "TextCard", id: "fallback_text_card", content: "Hi" }]);
  });

  it("ignores unknown and malformed components without throwing", () => {
    const parsed = parseComponents({
      components: [null, 5, "x", { type: "Carousel", id: "c" }, { type: "CardList", id: "a", items: "no" }, { type: "CardList", id: "b", items: [{ nope: 1 }] }],
    });
    expect(parsed).toEqual([]);
    expect(parseComponents(undefined)).toEqual([]);
    expect(parseComponents({ components: "x" })).toEqual([]);
  });

  it("tolerates missing optional values and numeric ratings", () => {
    const [list] = parseComponents({ components: [{ type: "CardList", id: "a", title: "T", items: [{ title: "Only title" }, { title: "N", rating: 4.5 }] }] });
    expect(list).toMatchObject({ items: [{ title: "Only title" }, { title: "N", rating: "4.5" }] });
  });
});

describe("ComponentRenderer", () => {
  it("renders both card lists with their fields", () => {
    render(<ComponentRenderer components={parseComponents(PRD_RESPONSE.a2ui_payload)} />);
    expect(screen.getByRole("heading", { name: "Top Attractions in Tokyo" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recommended Dining in Tokyo" })).toBeInTheDocument();
    expect(screen.getByText("Senso-ji Temple")).toBeInTheDocument();
    expect(screen.getByText("Sukiyabashi Jiro Sushi")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(4);
    expect(screen.getByText("Cost: Free")).toBeInTheDocument();
    expect(screen.getByText("Price: $$")).toBeInTheDocument();
  });

  it("renders only dining when only dining is returned", () => {
    const dining = parseComponents({ components: [PRD_RESPONSE.a2ui_payload.components[1]] });
    render(<ComponentRenderer components={dining} />);
    expect(screen.queryByText("Top Attractions in Tokyo")).not.toBeInTheDocument();
    expect(screen.getByText("Ichiran Ramen")).toBeInTheDocument();
  });

  it("shows 'Not listed' for missing values and renders text as text, not HTML", () => {
    render(
      <ComponentRenderer
        components={parseComponents({
          components: [
            { type: "CardList", id: "a", title: "T", items: [{ title: "<b>x</b>" }] },
            { type: "TextCard", id: "t", content: "<img src=x onerror=alert(1)>" },
          ],
        })}
      />,
    );
    expect(screen.getByText("<b>x</b>")).toBeInTheDocument();
    expect(screen.getByText("Rating: Not listed", { exact: false })).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });
});
