// The PRD sample response (Tokyo sightseeing + dinner).
export const PRD_RESPONSE = {
  status: "success",
  agent_text: "Here is a plan. These are demo records.",
  a2ui_payload: {
    a2ui_surface: "main_view",
    components: [
      {
        id: "attractions_card_list",
        type: "CardList",
        title: "Top Attractions in Tokyo",
        items: [
          { title: "Senso-ji Temple", type: "Culture", rating: "4.8", cost: "Free" },
          { title: "Tokyo Skytree", type: "Views", rating: "4.6", cost: "$25" },
        ],
      },
      {
        id: "dining_card_list",
        type: "CardList",
        title: "Recommended Dining in Tokyo",
        items: [
          { title: "Ichiran Ramen", cuisine: "Ramen", rating: "4.9", price: "$$" },
          { title: "Sukiyabashi Jiro Sushi", cuisine: "Sushi", rating: "4.9", price: "$$$$" },
        ],
      },
    ],
  },
};
