# Alarme Personnalisée pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Ce composant personnalisé pour Home Assistant vous permet de créer une alarme de sécurité flexible et configurable avec des entités dédiées pour un contrôle total.

## Fonctionnalités

-   **Modes d'alarme multiples :** Prend en charge les modes `À domicile` (armed_home), `Extérieur` (armed_away), et `Vacances` (armed_vacation).
-   **Comportement de bascule :** Activez un mode en cliquant sur son icône. Cliquez à nouveau pour le désactiver. Fini le bouton "Désactiver" !
-   **Désarmement par badges RFID/NFC :** Configurez des badges pour désarmer automatiquement l'alarme sans code PIN.
-   **Entités dédiées** : Contrôlez tous les aspects de l'alarme via des entités natives Home Assistant :
    - **Bouton** : Réinitialiser le compteur de déclenchements
    - **Capteurs** : Nombre de déclenchements, dernier capteur, dernier changement
    - **Interrupteur** : Activer/désactiver le réarmement automatique
    - **Contrôles numériques** : Modifier les délais d'armement, d'entrée et de déclenchement en temps réel
-   **Configuration facile :** Entièrement configurable via l'interface utilisateur de Home Assistant.
-   **Déclencheurs personnalisables :** Définissez les capteurs qui déclencheront l'alarme.
-   **Suivi avancé :** Compteur de déclenchements, dernier capteur déclenché, horodatage des changements.
-   **Événements personnalisés :** Événements pour les déclenchements et les désarmements d'urgence.
-   **Compatibilité HACS :** Installation et mises à jour faciles via le [Home Assistant Community Store (HACS)](https://hacs.xyz/).

## Installation

### Via HACS (Recommandé)

1.  Assurez-vous d'avoir [HACS](https://hacs.xyz/) installé.
2.  Allez dans HACS > Intégrations.
3.  Cliquez sur les trois points en haut à droite et sélectionnez "Référentiels personnalisés".
4.  Entrez l'URL de ce dépôt dans le champ "Dépôt" et sélectionnez "Intégration" dans la catégorie. Cliquez sur "Ajouter".
5.  Le composant "Alarme Personnalisée" devrait maintenant apparaître. Cliquez sur "Installer".
6.  Redémarrez Home Assistant.

### Manuelle

1.  Téléchargez la dernière version depuis la page des [Releases](https://github.com/Turiko313/Alarme-home-assistant-/releases).
2.  Copiez le dossier `custom_components/alarme_personnalisee` dans le répertoire `custom_components` de votre installation Home Assistant.
3.  Redémarrez Home Assistant.

## Configuration

1.  Allez dans **Paramètres** > **Appareils et services**.
2.  Cliquez sur **Ajouter une intégration** et recherchez **Alarme Personnalisée**.
3.  Suivez les instructions à l'écran pour configurer votre alarme :
    *   **Code d'armement/désarmement :** Définissez un code PIN (optionnel).
    *   **Temporisations :** Configurez les délais d'armement, d'entrée et de déclenchement.
    *   **Capteurs :** Sélectionnez les capteurs pour chaque mode d'alarme.
    *   **Badges RFID/NFC :** Configurez des badges pour le désarmement automatique (optionnel).

## Configuration des badges RFID/NFC

L'intégration supporte le désarmement automatique via badges RFID/NFC. Cette fonctionnalité est particulièrement utile pour les membres de la famille qui n'ont pas besoin de se souvenir d'un code PIN.

### Configuration

1.  Allez dans **Paramètres** > **Appareils et services** > **Alarme Personnalisée** > **Configurer**.
2.  Accédez à l'onglet **Badges**.
3.  Ajoutez vos badges un par un :
    *   **Nom du badge :** Un nom convivial (ex: "Badge Papa", "Badge Maman")
    *   **ID du badge :** L'identifiant unique du badge (ex: "AB:CD:EF:12:34:56")
    *   **Lecteur NFC :** Sélectionnez le capteur ou capteur binaire qui détecte les badges

### Lecteurs compatibles

L'intégration fonctionne avec n'importe quel `sensor` ou `binary_sensor` qui renvoie l'ID du badge. Exemples :
-   Lecteurs NFC connectés à Home Assistant
-   Tags NFC lus par l'application mobile Home Assistant
-   Lecteurs RFID intégrés (ESPHome, Tasmota, etc.)

### Fonctionnement

-   Lorsqu'un badge configuré est détecté, l'alarme se désarme automatiquement
-   Fonctionne même si l'alarme est en état `pending` ou `triggered`
-   Un événement `alarme_personnalisee.badge_disarm` est émis à chaque utilisation pour tracer qui a désarmé l'alarme
-   Les logs indiquent quel badge a été utilisé et à quelle heure

## Entités créées

Après l'installation, les entités suivantes seront disponibles :

### Entité principale
- `alarm_control_panel.alarme` - L'entité d'alarme principale

### Capteurs
- `sensor.alarme_trigger_count` - Nombre total de déclenchements
- `sensor.alarme_last_triggered_by` - Nom du dernier capteur ayant déclenché l'alarme
- `sensor.alarme_last_changed_at` - Horodatage du dernier changement d'état

### Contrôles
- `button.alarme_reset_trigger_count` - Réinitialise le compteur de déclenchements
- `switch.alarme_rearm_after_trigger` - Active/désactive le réarmement automatique
- `number.alarme_arming_time` - Contrôle le délai d'armement (0-600s)
- `number.alarme_delay_time` - Contrôle le délai d'entrée (0-600s)
- `number.alarme_trigger_time` - Contrôle la durée de déclenchement (0-1800s)

Toutes ces entités sont regroupées sous le même appareil "Alarme Personnalisée" pour une meilleure organisation.

## Utilisation dans Lovelace

Pour une expérience utilisateur optimale avec des icônes qui changent de couleur et agissent comme des boutons à bascule, nous vous recommandons d'utiliser `custom:button-card`.

**1. Installez `custom:button-card`**

Si ce n'est pas déjà fait, installez `custom:button-card` via HACS.

**2. Exemple de carte Lovelace**

Ajoutez une nouvelle carte "Manuelle" à votre tableau de bord et collez le code YAML suivant :

```yaml
type: vertical-stack
cards:
  - type: custom:button-card
    entity: alarm_control_panel.alarme
    name: 'État de l''alarme'
    show_state: true
  - type: horizontal-stack
    cards:
      - type: custom:button-card
        entity: alarm_control_panel.alarme
        icon: mdi:shield-home
        name: Domicile
        state:
          - value: armed_home
            color: green
            icon: mdi:shield-home
          - value: disarmed
            color: 'off'
            icon: mdi:shield-home-outline
        tap_action:
          action: call-service
          service: alarm_control_panel.alarm_arm_home
          service_data:
            entity_id: alarm_control_panel.alarme
      - type: custom:button-card
        entity: alarm_control_panel.alarme
        icon: mdi:shield-lock
        name: Extérieur
        state:
          - value: armed_away
            color: green
            icon: mdi:shield-lock
          - value: disarmed
            color: 'off'
            icon: mdi:shield-lock-outline
        tap_action:
          action: call-service
          service: alarm_control_panel.alarm_arm_away
          service_data:
            entity_id: alarm_control_panel.alarme
      - type: custom:button-card
        entity: alarm_control_panel.alarme
        icon: mdi:shield-airplane
        name: Vacances
        state:
          - value: armed_vacation
            color: green
            icon: mdi:shield-airplane
          - value: disarmed
            color: 'off'
            icon: mdi:shield-airplane-outline
        tap_action:
          action: call-service
          service: alarm_control_panel.alarm_arm_vacation
          service_data:
            entity_id: alarm_control_panel.alarme
```

**Remarque :** Assurez-vous que `entity: alarm_control_panel.alarme` correspond à l'ID de votre entité d'alarme.

## Attributs et Services

### Attributs

-   `supported_features_list`: Une liste des modes d'armement pris en charge (par exemple, `["ARM_HOME", "ARM_AWAY", "ARM_VACATION"]`). Utile pour les automatisations ou les cartes Lovelace dynamiques.
-   `triggered_count`: Nombre total de fois que l'alarme a été déclenchée.
-   `last_triggered_by`: ID du dernier capteur ayant déclenché l'alarme.
-   `last_changed_at`: Horodatage ISO du dernier changement d'état.
-   `last_armed_state`: Dernier état d'armement avant désarmement.
-   `monitored_sensors`: Liste des capteurs surveillés par mode (away, home, vacation).

### Services

Les services suivants peuvent être appelés dans vos automatisations ou scripts :

-   `alarm_control_panel.alarm_arm_home`
-   `alarm_control_panel.alarm_arm_away`
-   `alarm_control_panel.alarm_arm_vacation`
-   `alarm_control_panel.alarm_disarm`
-   `alarme_personnalisee.reset_trigger_count` - Réinitialise le compteur de déclenchements

Grâce au comportement de bascule, appeler un service d'armement sur un mode déjà actif désarmera l'alarme.

### Événements

L'intégration émet les événements suivants :

-   `alarme_personnalisee.triggered` - Déclenché quand l'alarme se déclenche
  - `entity_id`: ID de l'entité d'alarme
  - `triggered_by`: ID du capteur qui a déclenché l'alarme
  - `timestamp`: Horodatage du déclenchement
  
-   `alarme_personnalisee.urgence` - Déclenché lors d'un désarmement avec le code d'urgence
  - `entity_id`: ID de l'entité d'alarme

-   `alarme_personnalisee.badge_disarm` - Déclenché lors d'un désarmement par badge RFID/NFC
  - `entity_id`: ID de l'entité d'alarme
  - `badge_name`: Nom du badge utilisé
  - `badge_id`: ID du badge utilisé
  - `timestamp`: Horodatage du désarmement

### Exemple d'automatisation

```yaml
automation:
  - alias: "Notification déclenchement alarme"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.triggered
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 Alarme déclenchée!"
          message: "Capteur: {{ trigger.event.data.triggered_by }}"

  - alias: "Notification désarmement par badge"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.badge_disarm
    action:
      - service: notify.mobile_app
        data:
          title: "🔓 Alarme désarmée"
          message: "{{ trigger.event.data.badge_name }} a désarmé l'alarme"
```

---

N'hésitez pas à ouvrir une [issue](https://github.com/Turiko313/Alarme-home-assistant-/issues) si vous rencontrez des problèmes ou avez des suggestions d'amélioration.
