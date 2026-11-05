import json, os
import streamlit as st
from paypal_helper import create_order, authorize_order, capture_payment, void_payment
from ai_judge import judge_work

FILE = "deals.json"
URL = "http://localhost:8501"

def load():
    return json.load(open(FILE)) if os.path.exists(FILE) else {}

def save(d):
    json.dump(d, open(FILE, "w"), indent=2)

st.title("🔒 TrustHold")
st.caption("Pay only when the work is proven. (PayPal sandbox, fake money)")
deals = load()

# Client came back from PayPal after approving: hold the money
token = st.query_params.get("token")
if token in deals and deals[token]["status"] == "created":
    deals[token]["auth_id"] = authorize_order(token)
    deals[token]["status"] = "held"
    save(deals)
    st.success("PayPal is now HOLDING the money. Go to tab 2.")

t1, t2, t3 = st.tabs(["1. Create deal", "2. Deliver work", "3. Decide"])

with t1:
    brief = st.text_area("Brief (what do you need?)")
    amount = st.number_input("Amount (USD)", min_value=1.0, value=10.0)
    if st.button("Create deal") and brief:
        order_id, link = create_order(amount, brief[:120], URL)
        deals[order_id] = {"brief": brief, "amount": amount, "status": "created"}
        save(deals)
        st.link_button("Approve on PayPal", link)

with t2:
    held = [k for k, v in deals.items() if v["status"] == "held"]
    if held:
        k = st.selectbox("Deal", held)
        st.write(deals[k]["brief"])
        work = st.text_area("Paste your work")
        if st.button("Submit to AI judge") and work:
            try:
                with st.spinner("AI judge is checking the work..."):
                    verdict = judge_work(deals[k]["brief"], work)
                deals[k]["work"] = work
                deals[k]["verdict"] = verdict
                deals[k]["status"] = "reviewed"
                save(deals)
                st.success("Submitted. Go to tab 3.")
            except Exception as e:
                st.warning(str(e))
    else:
        st.info("No held deals yet.")

with t3:
    review = [k for k, v in deals.items() if v["status"] == "reviewed"]
    if review:
        k = st.selectbox("Deal to review", review)
        d = deals[k]
        st.write("Brief:", d["brief"])
        st.code(d["work"])
        for i in d["verdict"]["checklist"]:
            st.write("✅" if i["met"] else "❌", i["requirement"], "-", i["note"])
        st.info(f"AI recommends: {d['verdict']['decision']}. {d['verdict']['summary']}")
        if st.button("Release payment"):
            capture_payment(d["auth_id"])
            d["status"] = "paid"
            save(deals)
            st.success("Money RELEASED to the freelancer.")
        if st.button("Cancel hold"):
            void_payment(d["auth_id"])
            d["status"] = "cancelled"
            save(deals)
            st.success("Hold CANCELLED. The client keeps their money.")
    else:
        st.info("Nothing to review yet.")