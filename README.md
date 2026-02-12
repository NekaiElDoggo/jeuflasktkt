Jeu Gacha - prototype

Ce dépôt contient un prototype CLI pour tester la logique gacha (pity system simple).

Exécution rapide (PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt
python gacha_cli.py -n 10
```

Fichiers principaux:
- `gacha_cli.py`: logique gacha et CLI
- `tests/test_gacha.py`: tests unitaires basiques

Prochaine étape: intégrer Flask et persistance SQLite.

