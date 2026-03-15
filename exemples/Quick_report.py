from epitools import epi
import webbrowser, os

# Modèle SEIR
model  = epi.seir(N=1_000_000, I0=10, E0=50,
                  beta=0.35, sigma=1/5.2, gamma=1/14)
result = model.run()

# Graphe  une seule fois
result.plot().show()

# Risk ratio
rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
print(rr)

# Rapport  sauvegarde ET ouvre dans le navigateur
report = epi.report(result, title="SEIR  Burkina Faso")
path   = report.save_html("rapport.html")
webbrowser.open(f"file:///{os.path.abspath(path)}")