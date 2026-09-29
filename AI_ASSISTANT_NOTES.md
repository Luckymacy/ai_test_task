# AI Assistant with Memory and Tools

The Muse Edit Assistant is an AI helper for a clothing rental studio. The assistant can answer questions about planned shipments, expected returns and the current financial summary. It uses read-only tools and does not modify database data.

The assistant works through the POST /api/ai/chat endpoint. Each conversation uses a thread_id. If the same thread_id is sent again, the assistant receives the previous messages from that conversation and can keep short-term context. The memory is stored in application memory, is limited to the last 10 messages and resets when the backend server restarts.

The assistant uses three read-only tools. The get_planned_shipments tool returns active bookings with rental_status = booked and a planned shipping date. It is used for questions such as which bookings need to be shipped, which shipments are planned, or what needs to be sent soon. The get_expected_returns tool returns bookings with rental_status = shipped and an expected return date. It is used for questions about which bookings are expected back, which items should be returned, or which returns are planned. The get_financial_summary tool returns total income, total expenses and the current balance of the studio.

Each tool call is logged in the backend. The logs show which tool was selected by the AI and what result it returned. This helps verify that the assistant uses the correct read-only tool for each request.

The React admin interface contains The Muse Edit Assistant chat. The user can send custom questions, use quick actions, keep conversation context through thread_id and start a new conversation. Quick actions include “Що треба відправити?”, “Що чекаємо назад?” and “Який баланс?”.

The assistant was tested with planned shipment and expected return scenarios using data from the orders table.
All tools are read-only. The assistant does not update or delete database records, does not change financial data and does not invent clients, dates, amounts or statuses.

The main limitation is that short-term memory is stored only in backend memory. If the backend server restarts, the conversation memory is lost. The assistant only works with data that is available through the configured tools.