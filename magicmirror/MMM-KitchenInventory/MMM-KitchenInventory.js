Module.register("MMM-KitchenInventory", {
  defaults: {
    apiBaseUrl: "http://localhost:8000",
    updateInterval: 60 * 1000,
    animationSpeed: 400,
    maxItems: 20,
    showLocation: true,
    locations: ["Fridge", "Freezer", "Cupboard"],
  },

  getStyles: function () {
    return ["MMM-KitchenInventory.css"];
  },

  getTranslations: function () {
    return {
      en: "translations/en.json",
    };
  },

  start: function () {
    Log.info("Starting module: " + this.name);
    this.items = [];
    this.loaded = false;
    this.error = null;
    this.sendSocketNotification("INIT", { config: this.config });
    this.scheduleUpdate();
  },

  scheduleUpdate: function () {
    this.sendSocketNotification("FETCH_ITEMS", { config: this.config });
    setInterval(() => {
      this.sendSocketNotification("FETCH_ITEMS", { config: this.config });
    }, this.config.updateInterval);
  },

  socketNotificationReceived: function (notification, payload) {
    switch (notification) {
      case "ITEMS_UPDATED":
        this.items = payload.items;
        this.loaded = true;
        this.error = null;
        this.updateDom(this.config.animationSpeed);
        break;
      case "WS_EVENT":
        this.handleRealtimeEvent(payload);
        break;
      case "ERROR":
        this.error = payload.message;
        this.updateDom(this.config.animationSpeed);
        break;
    }
  },

  handleRealtimeEvent: function (event) {
    Log.info(this.name + " received real-time event: " + event.type);
    // Refetch items on any inventory change
    this.sendSocketNotification("FETCH_ITEMS", { config: this.config });
  },

  getDom: function () {
    var wrapper = document.createElement("div");
    wrapper.className = "kitchen-inventory";

    if (this.error) {
      wrapper.innerHTML = this.renderError();
      return wrapper;
    }

    if (!this.loaded) {
      wrapper.innerHTML = this.renderLoading();
      return wrapper;
    }

    if (this.items.length === 0) {
      wrapper.innerHTML = this.renderEmpty();
      return wrapper;
    }

    wrapper.innerHTML = this.renderInventory();
    return wrapper;
  },

  renderLoading: function () {
    return '<div class="ki-loading">Loading inventory...</div>';
  },

  renderError: function () {
    return '<div class="ki-error">Error: ' + this.error + "</div>";
  },

  renderEmpty: function () {
    return '<div class="ki-empty">No items in inventory</div>';
  },

  renderInventory: function () {
    var html = '<div class="ki-container">';
    var self = this;

    var groupedByLocation = this.groupByLocation(this.items);

    this.config.locations.forEach(function (location) {
      var locationItems = groupedByLocation[location];
      if (!locationItems || locationItems.length === 0) return;

      html += '<div class="ki-location-group">';
      if (self.config.showLocation) {
        html +=
          '<div class="ki-location-header">' +
          self.formatLocationName(location) +
          "</div>";
      }
      html += '<ul class="ki-item-list">';

      locationItems.slice(0, self.config.maxItems).forEach(function (item) {
        html += self.renderItem(item);
      });

      html += "</ul></div>";
    });

    html += "</div>";
    return html;
  },

  renderItem: function (item) {
    var name = item.product_reference
      ? item.product_reference.name
      : "Unknown";
    var qty = item.quantity || 0;
    var unit = item.product_reference ? item.product_reference.unit || "" : "";

    return (
      '<li class="ki-item">' +
      '<span class="ki-item-name">' +
      name +
      "</span>" +
      '<span class="ki-item-qty">' +
      qty +
      (unit ? " " + unit : "") +
      "</span>" +
      "</li>"
    );
  },

  groupByLocation: function (items) {
    var groups = {};
    items.forEach(function (item) {
      var loc = item.location || "Unknown";
      if (!groups[loc]) groups[loc] = [];
      groups[loc].push(item);
    });
    return groups;
  },

  formatLocationName: function (location) {
    return location.charAt(0).toUpperCase() + location.slice(1);
  },
});
