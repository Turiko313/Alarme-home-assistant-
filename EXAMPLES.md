# Exemples d'automatisations pour Alarme Personnalisée

## 1. Notification lors du déclenchement de l'alarme

```yaml
automation:
  - id: notification_alarme_declenchee
    alias: "Notification - Alarme déclenchée"
    description: "Envoie une notification lorsque l'alarme est déclenchée"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.triggered
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "?? Alarme déclenchée!"
          message: >
            L'alarme a été déclenchée par le capteur: 
            {{ trigger.event.data.triggered_by }}
            à {{ trigger.event.data.timestamp }}
          data:
            priority: high
            ttl: 0
            channel: alarm
```

## 1.5 Notification si l'armement est annulé (NOUVEAU)

```yaml
automation:
  - id: notification_armement_annule
    alias: "Notification - Armement annulé"
    description: "Alerte si un capteur empêche l'armement"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.arming_cancelled
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "?? Armement annulé"
          message: >
            L'armement a été annulé car le capteur {{ trigger.event.data.cancelled_by }} est ouvert.
            Fermez toutes les portes et fenêtres avant d'armer.
          data:
            priority: high
            channel: alarm
```

## 2. Notification lors d'un désarmement d'urgence

```yaml
automation:
  - id: notification_urgence
    alias: "Notification - Code d'urgence utilisé"
    description: "Alerte lorsque le code d'urgence est utilisé"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.urgence
    action:
      - service: notify.famille
        data:
          title: "?? Code d'urgence utilisé!"
          message: "Le code d'urgence a été utilisé pour désarmer l'alarme"
      - service: notify.contacts_urgence
        data:
          message: "Code d'urgence activé à la maison"
```

## 3. Armer automatiquement l'alarme en mode Absent

```yaml
automation:
  - id: armer_alarme_depart
    alias: "Alarme - Armer en partant"
    description: "Arme l'alarme en mode Absent quand tout le monde part"
    trigger:
      - platform: state
        entity_id: zone.home
        to: "0"
    condition:
      - condition: state
        entity_id: alarm_control_panel.alarme
        state: "disarmed"
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.alarme
        data:
          code: "1234"  # Votre code PIN
```

## 4. Désarmer automatiquement au retour

```yaml
automation:
  - id: desarmer_alarme_retour
    alias: "Alarme - Désarmer au retour"
    description: "Désarme l'alarme quand quelqu'un rentre"
    trigger:
      - platform: state
        entity_id: binary_sensor.porte_entree
        to: "on"
    condition:
      - condition: state
        entity_id: alarm_control_panel.alarme
        state: "armed_away"
      - condition: state
        entity_id: person.votre_nom
        state: "home"
    action:
      - service: alarm_control_panel.alarm_disarm
        target:
          entity_id: alarm_control_panel.alarme
        data:
          code: "1234"
```

## 5. Armer en mode Nuit automatiquement

```yaml
automation:
  - id: armer_alarme_nuit
    alias: "Alarme - Mode nuit automatique"
    description: "Arme l'alarme en mode Domicile à 23h"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: state
        entity_id: alarm_control_panel.alarme
        state: "disarmed"
    action:
      - service: alarm_control_panel.alarm_arm_home
        target:
          entity_id: alarm_control_panel.alarme
        data:
          code: "1234"
```

## 6. Statistiques de déclenchements mensuels

```yaml
automation:
  - id: reset_compteur_alarme_mensuel
    alias: "Alarme - Reset compteur mensuel"
    description: "Réinitialise le compteur de déclenchements chaque mois"
    trigger:
      - platform: time
        at: "00:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: alarme_personnalisee.reset_trigger_count
        data:
          entity_id: alarm_control_panel.alarme
```

## 7. Mode Vacances avec calendrier

```yaml
automation:
  - id: mode_vacances_auto
    alias: "Alarme - Mode vacances automatique"
    description: "Active le mode vacances selon le calendrier"
    trigger:
      - platform: state
        entity_id: calendar.vacances
        to: "on"
    action:
      - service: alarm_control_panel.alarm_arm_vacation
        target:
          entity_id: alarm_control_panel.alarme
        data:
          code: "1234"
```

## 8. Alerte si alarme déclenchée plus de X fois

```yaml
automation:
  - id: alerte_declenchements_multiples
    alias: "Alarme - Alerte déclenchements multiples"
    description: "Alerte si l'alarme est déclenchée plus de 3 fois"
    trigger:
      - platform: state
        entity_id: alarm_control_panel.alarme
        to: "triggered"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('alarm_control_panel.alarme', 'triggered_count') | int > 3 }}
    action:
      - service: notify.admin
        data:
          title: "?? Alarme - Multiples déclenchements"
          message: >
            L'alarme a été déclenchée {{ state_attr('alarm_control_panel.alarme', 'triggered_count') }} fois.
            Vérifiez la configuration des capteurs.
```

## 9. Historique des derniers déclenchements

```yaml
# Template sensor pour suivre les déclenchements
template:
  - sensor:
      - name: "Alarme - Dernier déclenchement"
        state: >
          {% if state_attr('alarm_control_panel.alarme', 'last_triggered_by') %}
            {{ state_attr('alarm_control_panel.alarme', 'last_triggered_by') }}
          {% else %}
            Aucun
          {% endif %}
        attributes:
          timestamp: >
            {{ state_attr('alarm_control_panel.alarme', 'last_changed_at') }}
          count: >
            {{ state_attr('alarm_control_panel.alarme', 'triggered_count') }}
```

## 10. Flash des lumières lors du déclenchement

```yaml
automation:
  - id: flash_lumieres_alarme
    alias: "Alarme - Flash lumières"
    description: "Fait clignoter les lumières lors du déclenchement"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.triggered
    action:
      - repeat:
          count: 10
          sequence:
            - service: light.turn_on
              target:
                entity_id: light.toutes_les_lumieres
              data:
                brightness: 255
                rgb_color: [255, 0, 0]
            - delay: "00:00:01"
            - service: light.turn_off
              target:
                entity_id: light.toutes_les_lumieres
            - delay: "00:00:01"
