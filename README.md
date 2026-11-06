# 🔒 TrustHold

**Pay only when the work is proven.**

TrustHold helps freelancers and clients pay each other safely. The client's money is held in PayPal, the freelancer delivers, an AI referee checks the work against the brief, and the client decides whether to release or cancel.

## The problem
Clients fear paying first and getting nothing. Freelancers fear working first and never getting paid.

## How it works
1. **Client creates a deal** with a brief and an amount. PayPal **authorizes** the payment (holds the money, does not take it).
2. **Freelancer delivers** the work.
3. **AI judge** compares the work with the brief and shows a requirement-by-requirement checklist with a recommendation.
4. **Client decides.** Release = PayPal **capture** (freelancer is paid). Cancel = PayPal **void** (client keeps the money).

The AI only recommends. The human always has the final say.

## PayPal features used
Orders API with `intent: AUTHORIZE`, Authorize, Capture and Void (PayPal **sandbox**, fake money only).

## AI tools used
- **Gemini API** (free tier) is the main AI judge.
- **OpenRouter** (free model) is the automatic backup if Gemini is busy or out of quota.
- **Claude** was used as a coding assistant (see "How this was built").

## Run it yourself (all free)
1. Install Python 3.10 or newer.
2. Clone this repo and open a terminal in its folder.
3. `pip3 install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill it in:
   - Create a free account at developer.paypal.com. Make sure **Sandbox** is selected.
   - Create **two US sandbox accounts**: one Business (freelancer), one Personal (client).
   - In **Apps & Credentials**, create a Merchant app and copy the Client ID and Secret into `.env`.
   - Get a free Gemini key at aistudio.google.com for `GEMINI_API_KEY`.
   - Optional backup AI: a free OpenRouter key, with `BACKUP_MODEL` set to a `:free` model name.
5. `streamlit run app.py`. It opens at http://localhost:8501 (the port must be 8501).
6. In the app, approve the PayPal payment with your **sandbox Personal** account (use an Incognito window).

## How this was built
I chose the idea, designed the hold-then-release flow, and tested every path. I used Claude as a coding assistant to write and explain the code while I learned it. Gemini and OpenRouter models power the AI judge inside the app.

## Known limitations (this is a prototype)
I built TrustHold to prove the core idea, and I found these limits while testing:

- **Client can read the work, then cancel.** The client and freelancer share one screen, and the client sees the delivered work before deciding. A dishonest client could copy it and cancel the hold.
- **The AI can be wrong.** It only recommends, and a human always decides. There is no dispute reviewer yet.
- **No separate logins.** One person plays both roles in the demo.
- **Authorization holds expire.** PayPal holds expire after a limited time, and there is no automatic release yet.
- **Text only.** The work is pasted text, with no file uploads.

## Roadmap
1. Lock the delivered work until payment is released.
2. Separate client and freelancer logins.
3. A dispute step with a real reviewer when the client and AI disagree.
4. Automatic release before the hold expires, when the AI says the work matches.
5. File uploads and milestone payments.

## Demo video
(add the YouTube link here)

## License
MIT