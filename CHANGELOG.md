# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.3.0] - 2025-01-XX

### Ajouté
- **Nouvelles entités pour une meilleure intégration** :
  - `button.alarme_reset_trigger_count` : Bouton pour réinitialiser le compteur de déclenchements
  - `sensor.alarme_trigger_count` : Capteur affichant le nombre de déclenchements
  - `sensor.alarme_last_triggered_by` : Capteur affichant le dernier capteur déclencheur
  - `sensor.alarme_last_changed_at` : Capteur timestamp du dernier changement d'état
  - `switch.alarme_rearm_after_trigger` : Interrupteur pour activer/désactiver le réarmement automatique
  - `number.alarme_arming_time` : Contrôle du délai d'armement (0-600 secondes)
  - `number.alarme_delay_time` : Contrôle du délai d'entrée (0-600 secondes)
  - `number.alarme_trigger_time` : Contrôle de la durée de déclenchement (0-1800 secondes)

### Modifié
- Les nouvelles entités permettent de contrôler les paramètres de l'alarme sans passer par la configuration
- Toutes les entités sont regroupées sous un même "device" dans Home Assistant
- Le service `reset_trigger_count` est conservé pour compatibilité

### Amélioré
- Traductions françaises et anglaises complètes pour toutes les nouvelles entités
- Les entités se mettent à jour automatiquement quand l'alarme change d'état
- Interface plus intuitive avec des entités visibles et contrôlables

## [1.2.1] - 2025-12-28

### Corrigé
- **Service reset_trigger_count** : Intégré directement dans `__init__.py` pour garantir son chargement
- **Panneau HTML** : Code simplifié et robusté avec meilleure gestion des erreurs
- **Connexion hass** : Amélioration de la détection de l'objet hass depuis l'iframe
- **Logs de débogage** : Ajout de messages console pour faciliter le diagnostic

### Ajouté
- **Guide de dépannage** : Fichier `TROUBLESHOOTING.md` complet avec :
  - Checklist de vérification après installation
  - Solutions aux problèmes courants
  - Commandes utiles pour RPI5
  - Instructions de diagnostic

### Modifié
- Design du panneau simplifié avec emojis au lieu d'icônes MDI
- Meilleure gestion des erreurs dans le panneau
- Messages d'erreur plus explicites

## [1.2.0] - 2025-01-XX

### Ajouté
- **Panneau personnalisé dans la barre latérale** :
  - Nouveau panneau "Alarme" accessible directement depuis la sidebar
  - Interface visuelle avec l'état de l'alarme en temps réel
  - Affichage des statistiques (nombre de déclenchements, dernier capteur déclenché)
  - Liste des capteurs surveillés par mode avec leur état actuel
  - Journal des événements des dernières 24 heures
  - Actions rapides : modifier les paramètres, réinitialiser le compteur, actualiser
  
### Modifié
- Interface améliorée avec design moderne et responsive
- Mise à jour automatique des données toutes les 5 secondes

## [1.1.0] - 2025-01-XX

### Ajouté
- **Attributs enrichis** : 
  - `triggered_count` : Compteur de déclenchements
  - `last_triggered_by` : Dernier capteur ayant déclenché l'alarme
  - `last_changed_at` : Horodatage du dernier changement d'état
  - `last_armed_state` : Dernier état d'armement
  - `monitored_sensors` : Liste des capteurs surveillés par mode

- **Événement personnalisé** : 
  - `alarme_personnalisee.triggered` : Émis lors du déclenchement avec les détails
  
- **Service personnalisé** :
  - `alarme_personnalisee.reset_trigger_count` : Réinitialise le compteur de déclenchements

- **Traductions** :
  - Ajout de la traduction anglaise complète (en.json)
  - Amélioration de la traduction française (fr.json)

- **Documentation** :
  - Fichier `EXAMPLES.md` avec 10 exemples d'automatisations
  - Fichier `services.yaml` pour la documentation des services
  - `CHANGELOG.md` pour suivre les versions

### Modifié
- Mise à jour de la version minimale Home Assistant vers 2024.1.0
- Amélioration du README avec toutes les nouvelles fonctionnalités
- Mise à jour du manifest.json avec les bonnes URLs du projet
- Amélioration de hacs.json pour une meilleure intégration HACS

### Technique
- Ajout de `dt_util` pour la gestion des horodatages
- Meilleure gestion des données dans `hass.data`
- Nettoyage amélioré lors du déchargement de l'intégration

## [1.0.0] - 2024-12-XX

### Ajouté
- Version initiale de l'intégration
- Support des modes Armed Home, Armed Away et Armed Vacation
- Comportement de bascule pour l'armement/désarmement
- Configuration via l'interface utilisateur
- Support du code PIN avec codes séparés pour armement/désarmement
- Code d'urgence avec événement dédié
- Temporisations configurables (armement, entrée, déclenchement)
- Sélection des capteurs par mode
- Option de réarmement automatique après déclenchement
- Compatibilité HACS
