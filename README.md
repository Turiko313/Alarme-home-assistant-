# Alarme Personnalisée pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Ce composant personnalisé pour Home Assistant vous permet de créer une alarme de sécurité flexible et configurable.

## Fonctionnalités

-   **Modes d'alarme multiples :** Prend en charge les modes `À domicile` (armed_home), `Extérieur` (armed_away), et `Vacances` (armed_vacation).
-   **Comportement de bascule :** Activez un mode en cliquant sur son icône. Cliquez à nouveau pour le désactiver. Fini le bouton "Désactiver" !
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

1.  Téléchargez la dernière version depuis la page des [Releases](https://github.com/votre-utilisateur/votre-repo/releases).
2.  Copiez le dossier `custom_components/alarme_personnalisee` dans le répertoire `custom_components` de votre installation Home Assistant.
3.  Redémarrez Home Assistant.

## Configuration

1.  Allez dans **Paramètres** > **Appareils et services**.
2.  Cliquez sur **Ajouter une intégration** et recherchez **Alarme Personnalisée**.
3.  Suivez les instructions à l'écran pour configurer votre alarme :
    *   **Code d'armement/désarmement :** Définissez un code PIN (optionnel).
    *   **Temporisations :** Configurez les délais d'armement, d'entrée et de déclenchement.
    *   **Capteurs :** Sélectionnez les capteurs pour chaque mode d'alarme.

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
```

---

N'hésitez pas à ouvrir une [issue](https://github.com/votre-utilisateur/votre-repo/issues) si vous rencontrez des problèmes ou avez des suggestions d'amélioration.
