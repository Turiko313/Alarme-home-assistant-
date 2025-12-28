# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

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
