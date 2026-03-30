/* MagicMirror² configuration for Kitchen Inventory
 *
 * apiBaseUrl uses the Docker service name "api" — works in both local Docker
 * Compose and Unraid stacks since all services share the same Docker network.
 *
 * If you run MagicMirror outside Docker (e.g. bare Node.js on your Mac),
 * change apiBaseUrl to "http://localhost:8000".
 */
var config = {
  address: "0.0.0.0", // Listen on all interfaces so the browser preview works
  port: 8080,
  basePath: "/",
  ipWhitelist: [], // Empty = allow all (fine for local/LAN use)
  useHttps: false,
  language: "en",
  locale: "en-US",
  logLevel: ["INFO", "LOG", "WARN", "ERROR"],
  timeFormat: 24,
  units: "metric",

  modules: [
    {
      module: "alert",
    },
    {
      module: "MMM-KitchenInventory",
      position: "top_left",
      config: {
        apiBaseUrl: "http://api:8000",
        updateInterval: 60 * 1000,
        animationSpeed: 400,
        maxItems: 20,
        showLocation: true,
        locations: ["Fridge", "Freezer", "Cupboard"],
      },
    },
  ],
};

/*************** DO NOT EDIT THE LINE BELOW ***************/
if (typeof module !== "undefined") {
  module.exports = config;
}
