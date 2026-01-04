/* global Office */

Office.onReady(() => {
  // Commands will be registered here in the future
});

// Function that is called when the add-in needs to provide a command handler
function action(event: Office.AddinCommands.Event) {
  const message: Office.NotificationMessageDetails = {
    type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
    message: "Mantle command executed",
    icon: "Icon.80x80",
    persistent: true,
  };

  // Complete the event
  event.completed();
}

// Register the function
Office.actions.associate("action", action);

