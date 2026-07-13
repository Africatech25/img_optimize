# DRX — Système Multi-Agents

> Autorité absolue : LAGOYE Hans (L8)

## Architecture du système

DRX est un système multi-agents d'ingénierie logicielle à orchestration hiérarchique.
L'agent principal `drx` orchestre tous les sous-agents ci-dessous.

| Agent | Rôle | Fichier |
|---|---|---|
| `drx` | Orchestrateur principal | `.opencode/agents/drx.md` |
| `drx-arch` | Architecture & patterns | `.opencode/agents/drx-arch.md` |
| `drx-code` | Production de code | `.opencode/agents/drx-code.md` |
| `drx-design` | UI/UX & direction artistique | `.opencode/agents/drx-design.md` |
| `drx-sec` | Sécurité offensive & audit | `.opencode/agents/drx-sec.md` |
| `drx-test` | Tests & couverture qualité | `.opencode/agents/drx-test.md` |
| `drx-perf` | Performance & profiling | `.opencode/agents/drx-perf.md` |
| `drx-api` | Contrats API REST/GraphQL | `.opencode/agents/drx-api.md` |
| `drx-data` | Modélisation & migrations data | `.opencode/agents/drx-data.md` |
| `drx-deploy` | CI/CD & déploiement | `.opencode/agents/drx-deploy.md` |
| `drx-doc` | Documentation technique | `.opencode/agents/drx-doc.md` |
| `drx-infra` | Infrastructure & IaC | `.opencode/agents/drx-infra.md` |
| `drx-mobile` | Mobile React Native / PWA | `.opencode/agents/drx-mobile.md` |
| `drx-monitor` | Observabilité & alerting | `.opencode/agents/drx-monitor.md` |
| `drx-seo` | SEO technique & on-page | `.opencode/agents/drx-seo.md` |
| `drx-drawio-merise` | Diagrammes MERISE Draw.io | `.opencode/agents/drx-drawio-merise.md` |
| `drx-drawio-uml` | Diagrammes UML Draw.io | `.opencode/agents/drx-drawio-uml.md` |

---

## Utilisation dans OpenCode CLI

```bash
# Activer l'orchestrateur principal
/agent drx

# Activer un sous-agent directement
/agent drx-code
/agent drx-design
/agent drx-sec

# Charger un skill manuellement
/context .opencode/skills/drx-code/SKILL.md
```

## Mémoire et propositions

- `.opencode/drx-memory.md` — Décisions passées, contexte projet persistant
- `.opencode/drx-proposals.md` — Propositions d'amélioration du système DRX
