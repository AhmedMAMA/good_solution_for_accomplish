# Rapport journalier — 17 juin 2026

## Objectif de la journée

Aujourd’hui, le travail a porté sur deux sujets principaux :

1. Vérifier l’évolution de l’entraînement du modèle d’intelligence artificielle.
2. Comprendre comment récupérer la vidéo de la caméra du drone sur la Raspberry Pi.

L’objectif final est de permettre au système de lire la vidéo de la caméra du drone afin de faire de la détection d’objets.

---

## 1. Vérification de l’entraînement du modèle IA

Un entraînement du modèle IA avait été lancé la veille. Aujourd’hui, les résultats obtenus ont été analysés afin de voir si le modèle apprenait correctement.

Le modèle sert à détecter des objets sur des images ou sur une vidéo.

![Image des résultats de prédiction du modèle entraîné](<WhatsApp Image 2026-06-17 at 15.51.29.jpeg>)

Les premiers résultats montrent que le modèle arrive déjà à détecter certains objets, mais les performances ne sont pas encore parfaites.

Deux valeurs importantes ont été regardées :

* la **précision**, qui indique si les objets détectés par le modèle sont corrects ;
* la **mAP50**, qui donne une idée plus générale de la qualité des détections du modèle.

La mAP50 ne veut pas dire que le modèle est exact à 61 %. Elle sert plutôt à mesurer globalement si le modèle détecte bien les objets sur les images de test.

Après analyse, des réglages ont été modifiés afin d’améliorer l’entraînement. Les nouveaux résultats montrent une amélioration, mais l’entraînement est encore en cours. Il faudra donc attendre la fin de l’entraînement pour confirmer les performances finales.

---

## 2. Travail sur la connexion entre la Raspberry Pi et la caméra

La deuxième partie de la journée a porté sur la connexion entre la Raspberry Pi et la caméra du drone.

La Raspberry Pi doit récupérer la vidéo de la caméra pour pouvoir ensuite appliquer le modèle IA dessus.

Le problème rencontré est que la Raspberry Pi et la caméra ne sont pas au départ sur le même réseau.

La Raspberry Pi était connectée au réseau classique de la box, par exemple :

```text
192.168.1.x
```

Alors que la caméra du drone utilise un autre réseau, par exemple :

```text
192.168.144.x
```

Cela signifie que les deux appareils ne peuvent pas communiquer directement tant qu’ils ne sont pas reliés au même réseau.

---

## 3. Test avec un téléphone comme caméra

Pour mieux comprendre le problème, un téléphone a été utilisé comme caméra de test.

Une application a été installée sur le téléphone pour transformer sa caméra en caméra réseau. Cela a permis de créer un flux vidéo, comme celui que l’on veut récupérer plus tard depuis la vraie caméra du drone.

Ce test a permis de comprendre une chose importante :

> Pour lire une vidéo venant d’une caméra réseau, l’ordinateur ou la Raspberry Pi doit pouvoir atteindre cette caméra sur le réseau.

Autrement dit, il ne suffit pas d’écrire une adresse IP sur la Raspberry Pi. Il faut aussi que la Raspberry Pi soit réellement connectée au même réseau que la caméra.

---

## 4. Problème rencontré avec les adresses IP

Plusieurs essais ont été faits pour ajouter manuellement une adresse IP à la Raspberry Pi.

Cependant, ces essais n’ont pas fonctionné au début, car la Raspberry Pi n’était pas réellement connectée au réseau de la caméra.

Un exemple d’erreur obtenu est le suivant :

```bash
Destination Host Unreachable
```

Cela signifie que la machine ne trouve pas l’appareil qu’elle essaie de contacter.

Le problème ne venait donc pas du pare-feu, mais du fait que les appareils n’étaient pas correctement reliés au même réseau.

---

## 5. Test avec le câble Ethernet

Pour vérifier la solution, un câble Ethernet a été branché entre la GCS et la Raspberry Pi.

La GCS est la station de contrôle utilisée pour piloter ou surveiller le drone.

Après avoir branché le câble, la Raspberry Pi a reçu une adresse dans le même réseau que la caméra :

```text
192.168.144.x
```

Cela montre que la Raspberry Pi peut bien rejoindre le réseau de la caméra lorsqu’elle est connectée correctement.

En même temps, la Raspberry Pi gardait aussi sa connexion Wi-Fi au réseau classique :

```text
192.168.1.x
```

Cela donne donc deux connexions différentes :

```text
Wi-Fi     → pour accéder à la Raspberry Pi depuis le PC
Ethernet → pour accéder au réseau de la caméra
```

Ce test a permis de valider que la solution fonctionne au sol.

---

## 6. Problème pour l’utilisation dans le drone

Même si le test avec le câble Ethernet fonctionne au sol, il ne peut pas être utilisé tel quel dans le drone.

En vol, il n’est pas possible d’avoir un câble Ethernet entre la Raspberry Pi embarquée dans le drone et la GCS au sol.

Il faut donc trouver une solution directement à bord du drone.

La caméra du drone est reliée au module vidéo appelé **Air Unit**. Ce module transmet ensuite la vidéo vers la station au sol.

Le but est donc de permettre à la Raspberry Pi de récupérer la vidéo directement à bord, sans ajouter trop de poids.

---

## 7. Recherche d’une solution légère

Dans un drone, le poids est très important. Chaque composant ajouté peut réduire l’autonomie ou perturber le vol.

L’ajout d’un switch Ethernet classique pourrait permettre de connecter à la fois :

```text
la caméra
l’Air Unit
la Raspberry Pi
```

Mais cette solution ajoute du poids, des câbles et de l’encombrement.

Une solution plus légère a donc été recherchée. Une piste intéressante est l’utilisation d’un petit hub Ethernet SIYI compatible avec les systèmes HM30/MK32.

Ce type de composant pourrait permettre de connecter la caméra, l’Air Unit et la Raspberry Pi sans utiliser un gros switch RJ45 classique.

L’idée serait d’avoir une architecture comme ceci :

```text
Caméra du drone
       |
Petit hub Ethernet SIYI
       |
       |---- Air Unit
       |
       |---- Raspberry Pi
```

Ainsi, la caméra pourrait continuer à envoyer la vidéo vers la GCS, tout en permettant à la Raspberry Pi de récupérer le flux vidéo pour faire le traitement IA.

---

## Conclusion

La journée a permis de mieux comprendre deux points importants du projet.

Premièrement, les résultats de l’entraînement IA ont été analysés. Le modèle arrive déjà à détecter certains objets, mais il doit encore être amélioré.

Deuxièmement, le problème de connexion entre la Raspberry Pi et la caméra a été étudié. Les tests ont montré que la Raspberry Pi doit être réellement connectée au réseau de la caméra pour pouvoir lire son flux vidéo.

Le test avec le câble Ethernet a confirmé que la Raspberry Pi peut accéder au réseau de la caméra lorsqu’elle est branchée correctement.

Cependant, pour une utilisation dans le drone, il faut trouver une solution légère, car l’ajout de câbles, d’un switch ou de composants supplémentaires augmente le poids.

La piste la plus intéressante est donc d’utiliser une solution compacte, comme un hub Ethernet SIYI, afin de permettre à la Raspberry Pi de récupérer la vidéo sans trop alourdir le drone.

## Prochaines étapes

Les prochaines étapes seront :

1. Tester la lecture du flux vidéo de la caméra depuis la Raspberry Pi.
2. Identifier l’adresse exacte de la caméra sur le réseau.
3. Vérifier si la Raspberry Pi peut ouvrir le flux vidéo avec un logiciel comme VLC, ffplay ou OpenCV.
4. Étudier l’utilisation d’un petit hub Ethernet SIYI.
5. Décider si le traitement IA doit être fait à bord du drone ou sur le PC au sol.
