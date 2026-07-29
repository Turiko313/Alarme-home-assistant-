# Alarme Personnalisée pour Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

Ce composant personnalisé pour Home Assistant vous permet de créer une alarme de sécurité flexible et configurable avec des entités dédiées pour un contrôle total.

## Fonctionnalités

-   **Modes d'alarme multiples :** Prend en charge les modes `À domicile` (armed_home), `Extérieur` (armed_away), et `Vacances` (armed_vacation).
-   **Commandes idempotentes :** Répéter une commande d'armement déjà active ne désarme jamais l'alarme par accident.
-   **Désarmement par badges RFID/NFC :** Configurez des badges pour désarmer automatiquement l'alarme sans code PIN.
-   **Entités dédiées** : Contrôlez tous les aspects de l'alarme via des entités natives Home Assistant :
    - **Bouton** : Réinitialiser le compteur de déclenchements
    - **Capteurs** : Nombre de déclenchements, dernier capteur, dernier changement
    - **Interrupteur** : Activer/désactiver le réarmement automatique
    - **Contrôles numériques** : Modifier les délais d'armement, d'entrée et de déclenchement en temps réel
-   **Configuration facile :** Entièrement configurable via l'interface utilisateur de Home Assistant.
-   **Déclencheurs personnalisables :** Définissez les capteurs qui déclencheront l'alarme.
-   **Suivi avancé :** Compteur de déclenchements, dernier capteur déclenché, horodatage des changements.
-   **Restauration après redémarrage :** Le mode armé et le compteur de déclenchements sont restaurés automatiquement.
-   **Surveillance de disponibilité :** Une alerte Repairs apparaît si une zone ou un lecteur de badge est absent, inconnu ou indisponible.
-   **Armement avec zone ouverte :** L'alarme s'arme quand même, signale les zones ouvertes ou inconnues et les réintègre automatiquement après leur fermeture.
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
    *   **Lecteur NFC :** Sélectionnez le capteur ou capteur binaire qui détecte les badges.
    *   **Valeur attendue :** Saisissez exactement la valeur renvoyée par le lecteur pour ce badge (ex: `AB:CD:EF:12:34:56`). Pour un capteur binaire dédié, utilisez `on`.

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

L'intégration fournit désormais sa propre carte moderne, sans dépendance à `button-card`.

### 1. Enregistrer la ressource

Dans **Paramètres > Tableaux de bord > Ressources**, ajoutez :

- URL : `/alarme_personnalisee/alarme-personnalisee-card.js?v=1.6.2`
- Type : **Module JavaScript**

Rechargez ensuite complètement le navigateur. Lors d'une future mise à jour, adaptez le numéro après `?v=` pour éviter de conserver une ancienne version en cache.

### 2. Ajouter la carte

La carte **Alarme Personnalisée** apparaît dans le sélecteur de cartes. Elle peut également être ajoutée manuellement :

```yaml
type: custom:alarme-personnalisee-card
entity: alarm_control_panel.alarme
name: Alarme maison
show_sensors: true
```

Elle fournit :

- les commandes Domicile, Absent, Vacances et Désarmer ;
- un champ PIN qui n'enregistre pas le code dans le tableau de bord ;
- le compteur, le dernier déclencheur et le dernier changement ;
- l'état de chaque zone, les capteurs indisponibles et les zones temporairement contournées ;
- une mise en page compatible avec les vues Sections et les appareils mobiles.

## Attributs et Services

### Attributs

-   `supported_features_list`: Une liste des modes d'armement pris en charge (par exemple, `["ARM_HOME", "ARM_AWAY", "ARM_VACATION"]`). Utile pour les automatisations ou les cartes Lovelace dynamiques.
-   `triggered_count`: Nombre total de fois que l'alarme a été déclenchée.
-   `last_triggered_by`: ID du dernier capteur ayant déclenché l'alarme.
-   `triggered_by_name`: Nom convivial du dernier capteur ayant déclenché l'alarme.
-   `last_changed_at`: Horodatage ISO du dernier changement d'état.
-   `last_armed_state`: Dernier état d'armement avant désarmement.
-   `monitored_sensors`: Liste des capteurs surveillés par mode (away, home, vacation).
-   `bypassed_sensors`: Zones temporairement ignorées jusqu'à leur prochain état fermé (`off`).

### Services

Les services suivants peuvent être appelés dans vos automatisations ou scripts :

-   `alarm_control_panel.alarm_arm_home`
-   `alarm_control_panel.alarm_arm_away`
-   `alarm_control_panel.alarm_arm_vacation`
-   `alarm_control_panel.alarm_disarm`
-   `alarme_personnalisee.reset_trigger_count` - Réinitialise le compteur de déclenchements

Les commandes d'armement sont idempotentes : appeler à nouveau le même service ne désarme pas l'alarme.

Si une zone du mode demandé est déjà ouverte, inconnue, indisponible ou absente, l'armement continue. La zone apparaît dans `bypassed_sensors` et dans **Paramètres > Système > Réparations**. Dès qu'elle transmet `off`, elle est automatiquement réintégrée : son prochain passage à `on` lance normalement le délai d'entrée.

Quand l'alarme passe réellement à l'état `triggered`, une notification persistante apparaît automatiquement dans Home Assistant avec le nom convivial et l'identifiant du capteur responsable. Une nouvelle occurrence met à jour cette notification au lieu d'en accumuler plusieurs. L'événement ci-dessous reste disponible pour envoyer la même information vers un téléphone ou une personne précise.

### Événements

L'intégration émet les événements suivants :

-   `alarme_personnalisee.triggered` - Déclenché quand l'alarme se déclenche
  - `entity_id`: ID de l'entité d'alarme
  - `triggered_by`: ID du capteur qui a déclenché l'alarme
  - `triggered_by_name`: Nom convivial du capteur qui a déclenché l'alarme
  - `timestamp`: Horodatage du déclenchement
  
-   `alarme_personnalisee.urgence` - Déclenché lors d'un désarmement avec le code d'urgence
  - `entity_id`: ID de l'entité d'alarme

-   `alarme_personnalisee.badge_disarm` - Déclenché lors d'un désarmement par badge RFID/NFC
  - `entity_id`: ID de l'entité d'alarme
  - `badge_name`: Nom du badge utilisé
  - `badge_entity`: Entité du lecteur utilisée
  - `badge_value`: Valeur du badge reconnue
  - `timestamp`: Horodatage du désarmement

-   `alarme_personnalisee.sensor_availability_changed` - Émis lorsque la disponibilité des zones ou lecteurs change
  - `entity_id`: ID de l'entité d'alarme
  - `available`: `true` quand tous les capteurs sont disponibles
  - `unavailable_sensors`: Liste des entités indisponibles
  - `timestamp`: Horodatage du changement

-   `alarme_personnalisee.bypassed_sensors_changed` - Émis lorsque la liste des zones temporairement contournées change
  - `entity_id`: ID de l'entité d'alarme
  - `bypassed_sensors`: Liste des zones encore contournées
  - `sensor_states`: État observé lors de leur contournement
  - `timestamp`: Horodatage du changement

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
          message: >-
            Déclenchement causé par
            {{ trigger.event.data.triggered_by_name }}
            ({{ trigger.event.data.triggered_by }})

  - alias: "Notification désarmement par badge"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.badge_disarm
    action:
      - service: notify.mobile_app
        data:
          title: "🔓 Alarme désarmée"
          message: "{{ trigger.event.data.badge_name }} a désarmé l'alarme"

  - alias: "Alerte capteurs d'alarme indisponibles"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.sensor_availability_changed
    condition:
      - condition: template
        value_template: "{{ not trigger.event.data.available }}"
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "⚠️ Protection de l'alarme réduite"
          message: >-
            Capteurs indisponibles :
            {{ trigger.event.data.unavailable_sensors | join(', ') }}

  - alias: "Alerte zones contournées à l'armement"
    trigger:
      - platform: event
        event_type: alarme_personnalisee.bypassed_sensors_changed
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.bypassed_sensors | count > 0 }}"
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "⚠️ Alarme armée avec une zone ouverte"
          message: >-
            Zones temporairement contournées :
            {{ trigger.event.data.bypassed_sensors | join(', ') }}
```

---

N'hésitez pas à ouvrir une [issue](https://github.com/Turiko313/Alarme-home-assistant-/issues) si vous rencontrez des problèmes ou avez des suggestions d'amélioration.
