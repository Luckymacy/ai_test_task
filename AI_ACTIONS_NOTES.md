# AI Controlled Actions

The Muse Edit Assistant supports controlled AI actions for rental management.

The main goal is to let AI prepare an action without executing it automatically. Every write action requires explicit user confirmation.

The assistant supports two controlled action tools: mark_order_shipped and mark_order_returned.

The mark_order_shipped action is used when the user wants to change a booking from booked to shipped. The mark_order_returned action is used when the user wants to change a booking from shipped to returned.

When the user asks the AI to perform one of these actions, the assistant does not update the database immediately. Instead, it creates a pending_action object with an action_id, order_id, current status, target status, client name and action type.

The pending action is returned to the React interface and displayed in a confirmation card.

The confirmation card shows the booking information and provides two buttons: “Підтвердити” and “Скасувати”.

If the user confirms the action, the frontend sends a request to the confirm endpoint. The backend verifies the current booking status before updating the rental_status field in the orders table.

If the user cancels the action, the booking data is not changed.

The backend uses two endpoints for controlled actions: POST /api/ai/actions/{action_id}/confirm and POST /api/ai/actions/{action_id}/cancel.

Every confirmed, cancelled or failed AI action is written to the ai_action_audit_log table.

The audit log stores the action ID, action type, order ID, action status, details and creation time.

This architecture prevents uncontrolled AI automation because the model cannot directly modify booking data. AI can only prepare an action, while the final decision remains with the user.

Pending actions are currently stored in backend application memory. If the backend restarts before the action is confirmed or cancelled, the pending action is lost.

The controlled action flow was tested in the React interface for both confirmation and cancellation scenarios.