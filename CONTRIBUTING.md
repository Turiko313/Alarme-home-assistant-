# Contribuer à Alarme Personnalisée

Merci de votre intérêt pour contribuer à ce projet ! ??

## Comment contribuer

### Rapporter des bugs

Si vous trouvez un bug, veuillez créer une [issue](https://github.com/Turiko313/Alarme-home-assistant-/issues) en incluant :

- Une description claire du problème
- Les étapes pour reproduire le bug
- La version de Home Assistant utilisée
- La version de l'intégration
- Les logs pertinents (si disponibles)

### Suggérer des améliorations

Les suggestions sont les bienvenues ! Créez une issue avec :

- Une description claire de la fonctionnalité souhaitée
- Pourquoi cette fonctionnalité serait utile
- Des exemples d'utilisation si possible

### Soumettre des Pull Requests

1. **Fork** le projet
2. **Créez** une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. **Committez** vos changements (`git commit -m 'Add some AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrez** une Pull Request

### Directives de code

- Suivez le style de code Python PEP 8
- Ajoutez des commentaires pour les sections complexes
- Testez vos modifications avec Home Assistant
- Mettez à jour la documentation si nécessaire

### Tests

Avant de soumettre une PR :

1. Testez l'intégration dans Home Assistant
2. Vérifiez qu'il n'y a pas d'erreurs dans les logs
3. Testez les différents scénarios (armement, désarmement, déclenchement)

## Structure du projet

```
custom_components/alarme_personnalisee/
??? __init__.py              # Initialisation de l'intégration
??? alarm_control_panel.py   # Entité principale de l'alarme
??? config_flow.py           # Configuration UI
??? const.py                 # Constantes
??? services.py              # Services personnalisés
??? manifest.json            # Métadonnées de l'intégration
??? strings.json             # Traductions par défaut
??? services.yaml            # Documentation des services
??? translations/
    ??? en.json              # Traduction anglaise
    ??? fr.json              # Traduction française
```

## Ajouter une traduction

Pour ajouter une nouvelle langue :

1. Créez un nouveau fichier dans `custom_components/alarme_personnalisee/translations/`
2. Nommez-le selon le code de langue (ex: `de.json` pour l'allemand)
3. Copiez la structure de `en.json` ou `fr.json`
4. Traduisez toutes les chaînes

## Questions ?

N'hésitez pas à ouvrir une issue pour toute question !

## Code de conduite

Soyez respectueux et constructif dans vos interactions. Ce projet vise à créer une communauté accueillante pour tous.

---

Merci encore pour votre contribution ! ??
