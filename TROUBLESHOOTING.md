# Guide de dépannage — Alarme Personnalisée

## Vérifications rapides

1. Dans **Paramètres > Appareils et services**, vérifiez que l'intégration est chargée.
2. Dans **Outils de développement > États**, recherchez l'entité `alarm_control_panel` portant le nom choisi lors de l'installation.
3. Vérifiez que les capteurs configurés sont des `binary_sensor` et passent bien à `on` lorsqu'ils s'activent.
4. Dans **Paramètres > Système > Journaux**, recherchez `alarme_personnalisee`.

L'identifiant de l'entité dépend du nom choisi et peut avoir été modifié par l'utilisateur. Ne supposez donc pas qu'il s'agit toujours de `alarm_control_panel.alarme`.

## Une zone est ouverte au moment de l'armement

- L'alarme s'arme quand même et place temporairement toute zone ouverte, inconnue ou indisponible dans l'attribut `bypassed_sensors`.
- Une alerte apparaît dans **Paramètres > Système > Réparations** et l'événement `alarme_personnalisee.bypassed_sensors_changed` permet d'envoyer une notification personnelle.
- Dès que la zone indique `off`, elle est réintégrée automatiquement. Son prochain passage à `on` déclenchera normalement l'alarme.

## L'alarme reste désarmée après une commande

- Si un code d'armement est exigé, vérifiez le code transmis.
- Une alarme en attente (`pending`) ou déclenchée (`triggered`) doit d'abord être désarmée.

## Un capteur ne déclenche pas l'alarme

- Vérifiez qu'il est affecté au mode actuellement armé.
- Vérifiez que son état actif est exactement `on`.
- Consultez **Paramètres > Système > Réparations** : l'intégration y signale les entités absentes, inconnues ou indisponibles.
- Après une modification des options, confirmez que l'intégration ne signale aucune erreur dans les journaux.

## Un badge ne désarme pas l'alarme

- Pour un lecteur de type `sensor`, la valeur configurée doit correspondre exactement à son état.
- Pour un `binary_sensor` dédié à un badge, utilisez la valeur `on`.
- Un badge n'est pris en compte que pendant l'armement, lorsque l'alarme est armée, en attente ou déclenchée.

## Réinitialiser le compteur

Utilisez le bouton de réinitialisation créé avec l'alarme, ou l'action :

```yaml
action: alarme_personnalisee.reset_trigger_count
data:
  entity_id: alarm_control_panel.votre_alarme
```

## Activer les journaux de diagnostic

Ajoutez temporairement ceci dans `configuration.yaml`, puis redémarrez Home Assistant :

```yaml
logger:
  default: info
  logs:
    custom_components.alarme_personnalisee: debug
```

Version minimale requise : Home Assistant 2025.11.
