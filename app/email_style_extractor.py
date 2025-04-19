import os
from openai import OpenAI
import streamlit as st
from jinja2 import Environment, FileSystemLoader

# --- 初期設定 -----------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "prompts")), autoescape=False)

st.set_page_config(page_title="Email Stylist", page_icon="📧")

# --- サイドバー ---------------------------------------------------------
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")

# --- 1) スタイル抽出 ----------------------------------------------------
st.title("📧 Email Style Rule Extractor & Writer")
email_src = st.text_area("✉️ メール本文を入力 (まずは分析)", height=250)
extract_btn = st.button("Analyze Style", disabled=not (email_src and api_key))

style_rules = None

if "style_rules" not in st.session_state:
    st.session_state.style_rules = None

if extract_btn:
    with st.spinner("Analyzing style…"):
        tpl = env.get_template("style_rules_prompt.jinja2")
        prompt = tpl.render(email_text=email_src)
        try:
            client = OpenAI(api_key=api_key)
            res = client.chat.completions.create(
                model="gpt-4.1",
                temperature=0.3,
                messages=[
                    {"role": "system", "content": "You are an expert writing-style analyst."},
                    {"role": "user", "content": prompt},
                ],
            )
            style_rules = res.choices[0].message.content
            st.session_state.style_rules = style_rules
            st.subheader("📝 抽出された文体ルール")
            st.markdown(style_rules)
        except Exception as e:
            st.error(e)

# --- 2) 新規メール生成 --------------------------------------------------
if st.session_state.style_rules:
    st.divider()
    st.subheader("✍️ 新しく書きたいメールの要件を入力")
    user_request = st.text_area("どういう内容を書きたいか？", key="request", height=150)
    gen_btn = st.button("Generate Email", disabled=not (user_request and api_key))

    if gen_btn:
        with st.spinner("Generating email…"):
            tpl = env.get_template("email_generate_prompt.jinja2")
            gen_prompt = tpl.render(style_rules=st.session_state.style_rules, user_request=user_request)
            try:
                client = OpenAI(api_key=api_key)
                res = client.chat.completions.create(
                    model="gpt-4.1",
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that writes emails."},
                        {"role": "user", "content": gen_prompt},
                    ],
                )
                email_out = res.choices[0].message.content
                st.subheader("📨 生成されたメール")
                st.markdown(email_out)
                st.download_button("Download .txt", email_out, file_name="generated_email.txt")
            except Exception as e:
                st.error(e)

# --- フッター -----------------------------------------------------------
st.markdown("\n---\nAPI キーはブラウザにのみ保持され、サーバー側には保存されません。")