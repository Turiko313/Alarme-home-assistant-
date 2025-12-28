# Guide de dépannage - Alarme Personnalisée

## ?? Vérifications après le redémarrage de Home Assistant

### 1. Vérifier que l'intégration est chargée

Allez dans **Paramètres** > **Appareils et services** et vérifiez que "Alarme Personnalisée" apparaît dans la liste.

### 2. Vérifier l'entité de l'alarme

Allez dans **Outils de développement** > **États** et recherchez `alarm_control_panel.alarme`

L'entité devrait afficher :
- **État** : `disarmed`, `armed_home`, `armed_away`, etc.
- **Attributs** :
  - `triggered_count`
  - `last_triggered_by`
  - `last_changed_at`
  - `monitored_sensors`

### 3. Vérifier les logs

Allez dans **Paramètres** > **Système** > **Journaux** et recherchez "alarme" ou "Alarme Personnalisée"

**Logs attendus :**
```
[custom_components.alarme_personnalisee] Setting up...
[custom_components.alarme_personnalisee.alarm_control_panel] Alarm panel initialized
```

**Logs d'erreur à surveiller :**
- `Error loading panel` ? Problème avec le panneau HTML
- `Entity not found` ? Problème avec l'entité alarme
- `Service not registered` ? Problème avec le service reset

### 4. Vérifier le panneau dans la sidebar

Le panneau "Alarme" (icône ???) devrait apparaître dans la barre latérale gauche.

**Si le panneau n'apparaît pas :**
1. Effacez le cache du navigateur (Ctrl+Shift+Delete)
2. Rechargez la page (Ctrl+F5)
3. Vérifiez les logs de Home Assistant
4. Vérifiez que le fichier `panel.html` existe dans `custom_components/alarme_personnalisee/`

### 5. Tester le panneau

Une fois dans le panneau :
1. Vérifiez que l'état de l'alarme s'affiche
2. Vérifiez que les statistiques sont visibles
3. Ouvrez la console du navigateur (F12) pour voir les logs JavaScript

**Messages de débogage dans la console :**
```
[Alarme Panel] DOM loaded, initializing...
[Alarme Panel] Attempting to connect to Home Assistant...
[Alarme Panel] Connection established!
[Alarme Panel] Entity state: disarmed
```

### 6. Tester le service reset_trigger_count

Dans **Outils de développement** > **Services**, appelez :
- **Service** : `alarme_personnalisee.reset_trigger_count`
- **Données** :
```yaml
entity_id: alarm_control_panel.alarme
```

Cliquez sur "Appeler le service". Le compteur devrait passer à 0.

## ? Problèmes courants et solutions

### Problème : "Entité alarme introuvable"

**Solution :**
1. Vérifiez que l'intégration est bien configurée
2. Redémarrez Home Assistant
3. Vérifiez le nom de l'entité dans États (peut-être `alarm_control_panel.alarme_personnalisee`)
4. Si le nom est différent, modifiez `ALARM_ENTITY_ID` dans `panel.html`

### Problème : Le panneau reste sur "Chargement..."

**Solution :**
1. Ouvrez la console du navigateur (F12)
2. Regardez les messages d'erreur
3. Vérifiez que le fichier panel.html se charge bien (onglet Network)
4. Essayez de rafraîchir plusieurs fois

### Problème : "Service alarme_personnalisee.reset_trigger_count not found"

**Solution :**
1. Vérifiez dans **Outils de développement** > **Services** que le service existe
2. Redémarrez Home Assistant
3. Vérifiez les logs pour voir si le service a été enregistré

### Problème : Les capteurs ne s'affichent pas

**Solution :**
1. Allez dans **Paramètres** > **Appareils et services** > **Alarme Personnalisée**
2. Cliquez sur "Configurer"
3. Ajoutez des capteurs pour au moins un mode (Domicile, Absent, ou Vacances)
4. Sauvegardez et actualisez le panneau

## ?? Checklist de diagnostic

- [ ] L'intégration apparaît dans Paramètres > Appareils et services
- [ ] L'entité `alarm_control_panel.alarme` existe dans États
- [ ] Aucune erreur dans les logs de Home Assistant
- [ ] Le panneau "Alarme" apparaît dans la sidebar
- [ ] Le panneau affiche l'état de l'alarme
- [ ] Les capteurs sont configurés
- [ ] Les capteurs s'affichent dans le panneau
- [ ] Le service `reset_trigger_count` est disponible
- [ ] Les logs d'événements se chargent

## ?? Commandes utiles

### Redémarrer Home Assistant
```bash
# Via l'interface : Paramètres > Système > Redémarrer
# Ou via CLI sur le RPI5 :
ha core restart
```

### Voir les logs en temps réel
```bash
ha core logs --follow
```

### Recharger les intégrations personnalisées
Dans Home Assistant :
1. Allez dans **Outils de développement**
2. Onglet **YAML**
3. Cliquez sur "Recharger les intégrations personnalisées" (si disponible)

Sinon, redémarrez complètement Home Assistant.

## ?? Besoin d'aide ?

Si vous rencontrez toujours des problèmes :

1. **Activez le mode debug** dans `configuration.yaml` :
```yaml
logger:
  default: info
  logs:
    custom_components.alarme_personnalisee: debug
```

2. **Redémarrez** Home Assistant

3. **Récupérez les logs** et partagez-les pour analyse

4. **Vérifiez la version** de Home Assistant :
   - Minimum requis : 2024.1.0
   - Recommandé : Dernière version stable
