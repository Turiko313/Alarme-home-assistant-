import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";

const ICONS = {
  disarmed: "mdi:shield-off",
  arming: "mdi:shield-sync",
  pending: "mdi:shield-sync",
  armed_home: "mdi:shield-home",
  armed_away: "mdi:shield-lock",
  armed_vacation: "mdi:shield-airplane",
  triggered: "mdi:shield-alert",
};

const ARM_ACTIONS = ["arm_home", "arm_away", "arm_vacation"];

class AlarmePanel extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
    };
  }

  _getAlarmEntity(hass) {
    const states = hass.states;
    for (const entityId in states) {
      if (entityId.startsWith("alarm_control_panel.alarme")) {
        return states[entityId];
      }
    }
    return null;
  }

  _callService(service, data = {}) {
    const alarmEntity = this._getAlarmEntity(this.hass);
    if (!alarmEntity) return;

    this.hass.callService("alarm_control_panel", service, {
      entity_id: alarmEntity.entity_id,
      ...data,
    });
  }

  _handleArm(e) {
    const mode = e.currentTarget.dataset.mode;
    this._callService(`alarm_${mode}`);
  }

  _handleDisarm() {
    const alarmEntity = this._getAlarmEntity(this.hass);
    if (!alarmEntity) return;

    const code = alarmEntity.attributes.code_format ? prompt("Enter PIN Code:") : "";
    if (code === null) return; // User cancelled prompt

    this._callService("alarm_disarm", { code });
  }

  render() {
    const alarmEntity = this._getAlarmEntity(this.hass);

    if (!alarmEntity) {
      return html`
        <ha-card header="Alarme">
          <div class="card-content">Alarm entity not found.</div>
        </ha-card>
      `;
    }

    const state = alarmEntity.state;
    const icon = ICONS[state] || "mdi:shield";

    return html`
      <ha-card>
        <div class="header">
          <ha-icon .icon=${icon}></ha-icon>
          <div class="status">${state.replace("_", " ")}</div>
        </div>

        <div class="actions">
          ${ARM_ACTIONS.map(
            (mode) => html`
              <mwc-button
                .disabled=${state !== "disarmed"}
                @click=${this._handleArm}
                data-mode=${mode}
              >
                ${mode.replace("arm_", "")}
              </mwc-button>
            `
          )}
          <mwc-button
            unelevated
            .disabled=${state === "disarmed"}
            @click=${this._handleDisarm}
          >
            Disarm
          </mwc-button>
        </div>
      </ha-card>
    `;
  }

  static get styles() {
    return css`
      ha-card {
        max-width: 400px;
        margin: 24px auto;
        padding: 16px;
        text-align: center;
      }
      .header {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 24px;
      }
      ha-icon {
        --mdc-icon-size: 64px;
        margin-bottom: 16px;
        color: var(--primary-color);
      }
      .status {
        font-size: 24px;
        text-transform: capitalize;
        font-weight: 500;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px;
      }
      mwc-button {
        --mdc-theme-primary: var(--primary-color);
      }
    `;
  }
}

customElements.define("alarme-panel", AlarmePanel);
