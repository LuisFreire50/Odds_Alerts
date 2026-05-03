# Odds Alert Monitor — Setup Guide

## 1. Instalação

```bash
pip install -r requirements.txt
streamlit run odds_alert_app.py
```

## 2. Configurar sua API de Odds

Abra `odds_alert_app.py` e localize a função `fetch_odds()`.
Descomente o bloco com a chamada real e adapte para o formato da sua API.

APIs sugeridas:
- **The Odds API** → https://the-odds-api.com  (suporta AH)
- **Betfair Exchange API** → https://developer.betfair.com
- **API-Football** → https://www.api-football.com

O retorno esperado da função é:
```python
{
    "home":        1.85,   # Odd Back Home
    "ah_minus_05": 1.72,   # Odd AH -0.5
    "ah_plus_05":  2.10,   # Odd AH +0.5
}
```

## 3. Configurar Instagram

O app usa o **Instagram Graph API** (Meta for Developers).

Passos:
1. Conta Business ou Creator no Instagram
2. App no Meta for Developers com permissão `instagram_messaging`
3. Gerar Access Token de longa duração
4. Inserir Token e User ID no sidebar do app (nunca no código)

## 4. Lógica de Alertas

| Alerta     | Condição                                              |
|------------|-------------------------------------------------------|
| BACK HOME  | `Odd Home − AH −0.5 ≥ 0.10`                         |
| LAY HOME   | `Odd Home − AH +0.5 ≥ 0.10` **E** `AH +0.5 > AH −0.5` |

O threshold padrão é **0.10 (10 ticks)** e pode ser ajustado no sidebar.

## 5. Modo Simulação

Por padrão, a função `fetch_odds()` gera odds aleatórias para você testar
o fluxo completo sem precisar de API. Remova esse bloco quando integrar a API real.
