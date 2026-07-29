class AlarmePersonnaliseeCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pin = "";
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: { entity: { domain: "alarm_control_panel" } },
        },
        { name: "name", selector: { text: {} } },
        { name: "show_sensors", selector: { boolean: {} } },
      ],
    };
  }

  static getStubConfig() {
    return {
      entity: "alarm_control_panel.alarme",
      show_sensors: true,
    };
  }

  setConfig(config) {
    if (!config.entity || !config.entity.startsWith("alarm_control_panel.")) {
      throw new Error("Une entité alarm_control_panel est obligatoire.");
    }
    this._config = {
      show_sensors: true,
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config?.show_sensors ? 6 : 4;
  }

  getGridOptions() {
    return {
      columns: 12,
      rows: this._config?.show_sensors ? 6 : 4,
      min_columns: 6,
      min_rows: 3,
    };
  }

  _translations() {
    const french = this._hass?.language?.toLowerCase().startsWith("fr");
    return french
      ? {
          unavailable: "Alarme indisponible",
          disarmed: "Désarmée",
          armed_home: "Armée — Domicile",
          armed_away: "Armée — Absent",
          armed_vacation: "Armée — Vacances",
          arming: "Armement en cours",
          pending: "Délai d'entrée",
          triggered: "Alarme déclenchée",
          home: "Domicile",
          away: "Absent",
          vacation: "Vacances",
          disarm: "Désarmer",
          code: "Code PIN",
          triggers: "Déclenchements",
          lastSensor: "Dernier capteur",
          triggeredBy: "Déclenchement causé par",
          lastChange: "Dernier changement",
          sensors: "Zones surveillées",
          noSensors: "Aucun capteur configuré",
          unavailableSensors: "Protection réduite : capteurs indisponibles",
          bypassedSensors: "Zones contournées jusqu'à leur fermeture",
          serviceError: "La commande d'alarme a échoué",
        }
      : {
          unavailable: "Alarm unavailable",
          disarmed: "Disarmed",
          armed_home: "Armed — Home",
          armed_away: "Armed — Away",
          armed_vacation: "Armed — Vacation",
          arming: "Arming",
          pending: "Entry delay",
          triggered: "Alarm triggered",
          home: "Home",
          away: "Away",
          vacation: "Vacation",
          disarm: "Disarm",
          code: "PIN code",
          triggers: "Triggers",
          lastSensor: "Last sensor",
          triggeredBy: "Triggered by",
          lastChange: "Last change",
          sensors: "Monitored zones",
          noSensors: "No configured sensor",
          unavailableSensors: "Reduced protection: unavailable sensors",
          bypassedSensors: "Zones bypassed until they close",
          serviceError: "Alarm command failed",
        };
  }

  _escape(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  _formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? String(value)
      : new Intl.DateTimeFormat(this._hass?.language || "fr", {
          dateStyle: "short",
          timeStyle: "medium",
        }).format(date);
  }

  _sensorGroups(entity) {
    const monitored = entity.attributes.monitored_sensors || {};
    return [
      ["home", monitored.home || []],
      ["away", monitored.away || []],
      ["vacation", monitored.vacation || []],
    ];
  }

  _sensorStatus(entityId, bypassed = new Set()) {
    if (bypassed.has(entityId)) {
      return "bypassed";
    }
    const state = this._hass?.states?.[entityId];
    if (!state || ["unknown", "unavailable"].includes(state.state)) {
      return "unavailable";
    }
    return state.state === "on" ? "active" : "inactive";
  }

  _renderSensors(entity, text) {
    if (!this._config.show_sensors) return "";
    const groups = this._sensorGroups(entity);
    const hasSensors = groups.some(([, sensors]) => sensors.length);
    if (!hasSensors) {
      return `
        <section class="zones">
          <h3>${text.sensors}</h3>
          <p class="empty">${text.noSensors}</p>
        </section>
      `;
    }

    const bypassed = new Set(entity.attributes.bypassed_sensors || []);
    const content = groups
      .filter(([, sensors]) => sensors.length)
      .map(
        ([mode, sensors]) => `
          <div class="zone-group">
            <h4>${this._escape(text[mode])}</h4>
            ${sensors
              .map((entityId) => {
                const sensor = this._hass?.states?.[entityId];
                const name =
                  sensor?.attributes?.friendly_name || entityId;
                const status = this._sensorStatus(entityId, bypassed);
                return `
                  <div class="zone-row">
                    <span class="status-dot ${status}"></span>
                    <span class="zone-name">${this._escape(name)}</span>
                    <span class="zone-state">${this._escape(
                      sensor?.state || "unavailable",
                    )}</span>
                  </div>
                `;
              })
              .join("")}
          </div>
        `,
      )
      .join("");

    return `
      <section class="zones">
        <h3>${text.sensors}</h3>
        <div class="zone-grid">${content}</div>
      </section>
    `;
  }

  _render() {
    if (!this.shadowRoot || !this._config || !this._hass) return;
    const previousPin = this.shadowRoot.querySelector("#pin")?.value;
    if (previousPin !== undefined) this._pin = previousPin;

    const text = this._translations();
    const entity = this._hass.states[this._config.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="missing">${text.unavailable}: ${this._escape(
            this._config.entity,
          )}</div>
        </ha-card>
      `;
      return;
    }

    const state = entity.state;
    const name =
      this._config.name ||
      entity.attributes.friendly_name ||
      this._config.entity;
    const allSensors = this._sensorGroups(entity).flatMap(([, sensors]) => sensors);
    const unavailable = allSensors.filter(
      (entityId) => this._sensorStatus(entityId) === "unavailable",
    );
    const bypassed = entity.attributes.bypassed_sensors || [];
    const triggeredBy =
      entity.attributes.triggered_by_name ||
      this._hass.states[entity.attributes.triggered_by]?.attributes?.friendly_name ||
      entity.attributes.triggered_by;
    const codeConfigured = Boolean(entity.attributes.code_format);
    const stateClass = state === "triggered" ? "danger" : state;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --alarm-green: var(--success-color, #2e7d32);
          --alarm-orange: var(--warning-color, #ed6c02);
          --alarm-red: var(--error-color, #d32f2f);
          display: block;
        }
        ha-card {
          overflow: hidden;
          color: var(--primary-text-color);
        }
        .header {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px 22px;
          cursor: pointer;
          background:
            radial-gradient(circle at 95% 5%, rgba(255,255,255,.2), transparent 32%),
            var(--primary-color);
          color: var(--text-primary-color, white);
        }
        .shield {
          display: grid;
          width: 50px;
          height: 50px;
          place-items: center;
          border-radius: 16px;
          background: rgba(255,255,255,.18);
        }
        .shield ha-icon { --mdc-icon-size: 30px; }
        .title { min-width: 0; flex: 1; }
        .title h2 {
          overflow: hidden;
          margin: 0 0 4px;
          font-size: 20px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .state {
          font-size: 14px;
          font-weight: 600;
          opacity: .92;
        }
        .state.danger { animation: pulse 1.2s infinite; }
        @keyframes pulse { 50% { opacity: .45; } }
        .warning {
          display: flex;
          gap: 10px;
          align-items: center;
          padding: 12px 20px;
          color: var(--alarm-red);
          background: color-mix(in srgb, var(--alarm-red) 12%, transparent);
          font-weight: 600;
        }
        .warning.bypassed {
          color: var(--alarm-orange);
          background: color-mix(in srgb, var(--alarm-orange) 12%, transparent);
        }
        .trigger-cause {
          display: flex;
          gap: 10px;
          align-items: center;
          padding: 14px 20px;
          color: var(--alarm-orange);
          background: color-mix(in srgb, var(--alarm-orange) 15%, transparent);
          font-weight: 700;
        }
        .trigger-cause.danger {
          color: var(--alarm-red);
          background: color-mix(in srgb, var(--alarm-red) 15%, transparent);
        }
        .controls {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          padding: 18px 20px 10px;
        }
        button {
          display: flex;
          min-height: 64px;
          flex-direction: column;
          gap: 6px;
          align-items: center;
          justify-content: center;
          border: 1px solid var(--divider-color);
          border-radius: 14px;
          color: var(--primary-text-color);
          background: var(--card-background-color);
          cursor: pointer;
          font: inherit;
          transition: transform .15s ease, background .15s ease;
        }
        button:hover { transform: translateY(-2px); }
        button.active {
          border-color: var(--alarm-green);
          color: var(--alarm-green);
          background: color-mix(in srgb, var(--alarm-green) 12%, transparent);
        }
        button.disarm.active {
          color: var(--primary-color);
          border-color: var(--primary-color);
          background: color-mix(in srgb, var(--primary-color) 12%, transparent);
        }
        button ha-icon { --mdc-icon-size: 25px; }
        .pin-row { padding: 6px 20px 14px; }
        .pin-row input {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 13px;
          border: 1px solid var(--divider-color);
          border-radius: 10px;
          color: var(--primary-text-color);
          background: var(--secondary-background-color);
          font: inherit;
        }
        .stats {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1px;
          border-block: 1px solid var(--divider-color);
          background: var(--divider-color);
        }
        .stat {
          padding: 15px;
          text-align: center;
          background: var(--card-background-color);
        }
        .stat strong {
          display: block;
          overflow: hidden;
          margin-bottom: 4px;
          font-size: 16px;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .stat span {
          color: var(--secondary-text-color);
          font-size: 12px;
        }
        .zones { padding: 17px 20px 20px; }
        .zones h3 { margin: 0 0 12px; font-size: 16px; }
        .zone-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
          gap: 12px;
        }
        .zone-group {
          padding: 12px;
          border-radius: 12px;
          background: var(--secondary-background-color);
        }
        .zone-group h4 { margin: 0 0 8px; }
        .zone-row {
          display: grid;
          grid-template-columns: 10px minmax(0, 1fr) auto;
          gap: 8px;
          align-items: center;
          min-height: 28px;
          font-size: 13px;
        }
        .status-dot {
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: var(--alarm-green);
        }
        .status-dot.active { background: var(--alarm-orange); }
        .status-dot.bypassed { background: var(--alarm-orange); }
        .status-dot.unavailable { background: var(--alarm-red); }
        .zone-name {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .zone-state {
          color: var(--secondary-text-color);
          font-size: 11px;
        }
        .empty, .missing {
          padding: 22px;
          color: var(--secondary-text-color);
          text-align: center;
        }
        @media (max-width: 520px) {
          .controls { grid-template-columns: repeat(2, 1fr); }
          .stats { grid-template-columns: 1fr; }
        }
      </style>

      <ha-card>
        <div class="header" id="more-info">
          <div class="shield"><ha-icon icon="mdi:shield-home"></ha-icon></div>
          <div class="title">
            <h2>${this._escape(name)}</h2>
            <div class="state ${this._escape(stateClass)}">
              ${this._escape(text[state] || state)}
            </div>
          </div>
        </div>

        ${
          triggeredBy && ["pending", "triggered"].includes(state)
            ? `<div class="trigger-cause ${state === "triggered" ? "danger" : ""}">
                <ha-icon icon="mdi:motion-sensor"></ha-icon>
                <span>${text.triggeredBy}: ${this._escape(triggeredBy)}</span>
              </div>`
            : ""
        }
        ${
          unavailable.length
            ? `<div class="warning">
                <ha-icon icon="mdi:alert-circle"></ha-icon>
                <span>${text.unavailableSensors}: ${unavailable.length}</span>
              </div>`
            : ""
        }
        ${
          bypassed.length
            ? `<div class="warning bypassed">
                <ha-icon icon="mdi:shield-alert"></ha-icon>
                <span>${text.bypassedSensors}: ${bypassed.length}</span>
              </div>`
            : ""
        }

        <div class="controls">
          <button data-service="alarm_arm_home" class="${
            state === "armed_home" ? "active" : ""
          }">
            <ha-icon icon="mdi:shield-home"></ha-icon><span>${text.home}</span>
          </button>
          <button data-service="alarm_arm_away" class="${
            state === "armed_away" ? "active" : ""
          }">
            <ha-icon icon="mdi:shield-lock"></ha-icon><span>${text.away}</span>
          </button>
          <button data-service="alarm_arm_vacation" class="${
            state === "armed_vacation" ? "active" : ""
          }">
            <ha-icon icon="mdi:shield-airplane"></ha-icon><span>${text.vacation}</span>
          </button>
          <button data-service="alarm_disarm" class="disarm ${
            state === "disarmed" ? "active" : ""
          }">
            <ha-icon icon="mdi:shield-off"></ha-icon><span>${text.disarm}</span>
          </button>
        </div>

        ${
          codeConfigured
            ? `<div class="pin-row">
                <input id="pin" type="password" inputmode="numeric"
                  autocomplete="off" placeholder="${this._escape(text.code)}"
                  value="${this._escape(this._pin)}">
              </div>`
            : ""
        }

        <div class="stats">
          <div class="stat">
            <strong>${Number(entity.attributes.triggered_count || 0)}</strong>
            <span>${text.triggers}</span>
          </div>
          <div class="stat">
            <strong>${this._escape(triggeredBy || "—")}</strong>
            <span>${text.lastSensor}</span>
          </div>
          <div class="stat">
            <strong>${this._escape(
              this._formatDate(entity.attributes.last_changed_at),
            )}</strong>
            <span>${text.lastChange}</span>
          </div>
        </div>

        ${this._renderSensors(entity, text)}
      </ha-card>
    `;

    this.shadowRoot.querySelector("#more-info")?.addEventListener("click", () => {
      const event = new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId: this._config.entity },
      });
      this.dispatchEvent(event);
    });

    this.shadowRoot.querySelector("#pin")?.addEventListener("input", (event) => {
      this._pin = event.target.value;
    });

    this.shadowRoot.querySelectorAll("button[data-service]").forEach((button) => {
      button.addEventListener("click", () =>
        this._callAlarmService(button.dataset.service),
      );
    });
  }

  async _callAlarmService(service) {
    const data = { entity_id: this._config.entity };
    if (this._pin) data.code = this._pin;
    try {
      await this._hass.callService("alarm_control_panel", service, data);
      this._pin = "";
      const input = this.shadowRoot.querySelector("#pin");
      if (input) input.value = "";
    } catch (error) {
      console.error(error);
      alert(`${this._translations().serviceError}: ${error.message || error}`);
    }
  }
}

if (!customElements.get("alarme-personnalisee-card")) {
  customElements.define("alarme-personnalisee-card", AlarmePersonnaliseeCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "alarme-personnalisee-card",
  name: "Alarme Personnalisée",
  preview: true,
  description: "Contrôle moderne de l'alarme et état des zones surveillées.",
  documentationURL:
    "https://github.com/Turiko313/Alarme-home-assistant-#carte-lovelace",
});
