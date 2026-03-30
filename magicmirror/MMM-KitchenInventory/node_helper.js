var NodeHelper = require("node_helper");
var fetch = require("node-fetch");
var WebSocket = require("ws");

module.exports = NodeHelper.create({
  name: "MMM-KitchenInventory",

  start: function () {
    console.log(this.name + ": node_helper started");
    this.ws = null;
    this.wsRetryCount = 0;
    this.maxWsRetries = 10;
    this.wsRetryDelay = 5000;
  },

  socketNotificationReceived: function (notification, payload) {
    switch (notification) {
      case "INIT":
        this.config = payload.config;
        this.connectWebSocket();
        break;
      case "FETCH_ITEMS":
        this.fetchItems(payload.config);
        break;
    }
  },

  fetchItems: async function (config) {
    var self = this;
    var url = config.apiBaseUrl + "/api/v1/items/";

    try {
      var response = await fetch(url);
      if (!response.ok) {
        throw new Error("API responded with status " + response.status);
      }
      var items = await response.json();
      self.sendSocketNotification("ITEMS_UPDATED", { items: items });
    } catch (error) {
      console.error(self.name + ": Failed to fetch items:", error.message);
      self.sendSocketNotification("ERROR", {
        message: "Cannot reach inventory API",
      });
    }
  },

  connectWebSocket: function () {
    var self = this;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    var wsUrl = this.config.apiBaseUrl.replace(/^http/, "ws") + "/ws";
    console.log(this.name + ": Connecting to WebSocket at " + wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.on("open", function () {
        console.log(self.name + ": WebSocket connected");
        self.wsRetryCount = 0;
      });

      this.ws.on("message", function (data) {
        try {
          var event = JSON.parse(data);
          self.sendSocketNotification("WS_EVENT", event);
        } catch (e) {
          console.error(self.name + ": Failed to parse WS message:", e);
        }
      });

      this.ws.on("close", function () {
        console.log(self.name + ": WebSocket closed");
        self.scheduleReconnect();
      });

      this.ws.on("error", function (error) {
        console.error(self.name + ": WebSocket error:", error.message);
      });
    } catch (error) {
      console.error(self.name + ": WebSocket connection failed:", error.message);
      this.scheduleReconnect();
    }
  },

  scheduleReconnect: function () {
    var self = this;

    if (this.wsRetryCount >= this.maxWsRetries) {
      console.error(
        this.name + ": Max WebSocket reconnection attempts reached"
      );
      return;
    }

    this.wsRetryCount++;
    var delay = this.wsRetryDelay * this.wsRetryCount;
    console.log(
      this.name +
        ": Reconnecting WebSocket in " +
        delay / 1000 +
        "s (attempt " +
        this.wsRetryCount +
        "/" +
        this.maxWsRetries +
        ")"
    );

    setTimeout(function () {
      self.connectWebSocket();
    }, delay);
  },

  stop: function () {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  },
});
