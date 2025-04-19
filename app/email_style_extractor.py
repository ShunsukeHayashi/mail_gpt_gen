import os
import json
import datetime
from openai import OpenAI
import streamlit as st
from jinja2 import Environment, FileSystemLoader

# --- 初期設定 -----------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "prompts")), autoescape=False)

# カスタムCSS
st.set_page_config(
    page_title="Email Stylist Pro", 
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {color: #000000; font-size: 2.5rem !important; font-weight: 700; margin-bottom: 1rem;}
    .sub-header {color: #333333; font-size: 1.8rem !important; font-weight: 600; margin-top: 1rem;}
    .info-text {font-size: 1.1rem; color: #000000;}
    .highlight {background-color: #f0f0f0; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;}
    .success-box {background-color: #f0f0f0; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #333333;}
    .info-box {background-color: #f5f5f5; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #555555;}
    .btn-custom {background-color: #333333 !important; color: white !important; font-weight: 600 !important;}
    .footer {font-size: 0.8rem; color: #333333; text-align: center; margin-top: 2rem;}
    .card {background-color: #f9f9f9; border-radius: 0.5rem; padding: 1.5rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    code {font-family: 'Courier New', monospace !important;}
    pre {background-color: #f5f5f5; padding: 0.5rem; border-radius: 0.3rem;}
    li {margin-bottom: 0.5rem;}
    textarea, input {font-family: 'Courier New', monospace !important;}
</style>
""", unsafe_allow_html=True)

# --- サイドバー ---------------------------------------------------------
with st.sidebar:
    st.image("https://i.imgur.com/g4B5qHP.png", width=80)
    st.markdown("## 📧 Email Stylist Pro")
    
    # 認証系
    api_key = st.text_input("🔑 OpenAI API Key", type="password")
    
    # モデル選択
    models = ["gpt-4.1", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
    model = st.selectbox("🤖 AIモデル", models, index=0)
    
    # 言語選択
    languages = ["日本語", "English", "简体中文", "한국어"]
    language = st.selectbox("🌐 言語", languages, index=0)
    
    # メールの目的
    email_purposes = [
        "一般的な連絡",
        "お詫び・謝罪",
        "依頼・お願い", 
        "お礼・感謝",
        "案内・招待",
        "報告・進捗共有",
        "質問・確認",
        "スケジュール調整",
        "お祝い・慶事",
        "クレーム対応"
    ]
    purpose = st.selectbox("📋 メールの目的", email_purposes, index=0)
    
    # 拡張設定（折りたたみ可能なUIで）
    with st.expander("⚙️ 詳細設定"):
        temperature = st.slider("創造性 (Temperature)", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        max_tokens = st.slider("最大トークン数", min_value=100, max_value=4000, value=2000, step=100)
    
    # サンプルメール
    with st.expander("📝 サンプルテンプレート"):
        sample_emails = {
            "ビジネスメール (丁寧)": """拝啓

平素より格別のご高配を賜り、厚く御礼申し上げます。
株式会社〇〇の山田太郎でございます。

先日はご多忙の中、弊社製品についてご検討いただき誠にありがとうございました。
ご要望いただいた資料を添付させていただきます。

ご不明な点がございましたら、お気軽にお問い合わせください。
今後とも何卒よろしくお願い申し上げます。

敬具""",
            "カジュアルな連絡": """こんにちは山田さん

先日はありがとうございました！
打ち合わせの件ですが、来週の水曜日15時からでよろしいでしょうか？

ご都合を教えてくださいm(_ _)m
よろしくお願いします！

田中""",
            "お詫びメール": """件名: 【お詫び】納品遅延について

○○様

いつもお世話になっております。
株式会社△△の佐藤でございます。

先日ご注文いただきました商品の納期遅延につきまして、
心よりお詫び申し上げます。

当初の予定では本日お届けの予定でしたが、
生産ラインの一部トラブルにより3営業日ほど遅れる見込みとなりました。

ご迷惑をおかけし大変申し訳ございません。
今後このようなことがないよう、生産体制を見直してまいります。

何卒ご理解いただきますようお願い申し上げます。

株式会社△△
佐藤一郎
TEL: 03-XXXX-XXXX""",
            "お礼メール": """鈴木様

先日はお忙しい中、当社イベントにご参加いただき誠にありがとうございました。
おかげさまで、大盛況のうちに終えることができました。

ご提供いただいたフィードバックは、今後の企画に活かしてまいります。
引き続きご支援いただけますと幸いです。

今後ともどうぞよろしくお願いいたします。

佐々木""",
            "社内連絡 (報告)": """部長

先週依頼いただいた四半期レポートの進捗状況をご報告いたします。

【完了項目】
・売上データの集計
・前年同期との比較分析
・部門別実績まとめ

【作業中】
・グラフ作成と考察（70%完了）
・来期予測（30%完了）

すべて予定通り進んでおり、週末までには完成版をお送りできる見込みです。
何かご質問やご指示がありましたら、お知らせください。

伊藤""",
            "スケジュール調整": """チームのみなさん

来週のプロジェクトミーティングの日程調整をしたいと思います。
下記の候補日時から都合の良い時間をお知らせください。

①月曜日 10:00-11:30
②火曜日 13:00-14:30
③水曜日 15:00-16:30

アジェンダは以下の通りです。
1. 現在の進捗確認（15分）
2. 課題の洗い出しと解決策検討（30分）
3. 次のマイルストーン設定（15分）
4. 質疑応答（15分）

参加できない場合は事前にコメントをいただけると助かります。
よろしくお願いします。

プロジェクトリーダー 小林""",
            "案内・招待": """山本様

来る6月15日(土)に当社創立10周年記念パーティーを開催することとなりました。
日頃お世話になっている山本様にもぜひご出席いただきたく、ご案内申し上げます。

【日時】6月15日(土) 18:00-20:30
【場所】グランドホテル東京 2階「桜の間」
【内容】軽食ビュッフェ、記念スピーチ、アトラクション等

ご多忙中誠に恐縮ですが、6月5日(水)までにご出欠のご連絡をいただけますと幸いです。
お会いできることを心よりお待ちしております。

株式会社○○
イベント担当 高橋
TEL: 03-XXXX-XXXX
Email: event@xxxx.co.jp"""
        }
        
        selected_sample = st.selectbox("サンプル選択", list(sample_emails.keys()))
        if st.button("サンプルを適用"):
            st.session_state.email_input = sample_emails[selected_sample]
            
    # 保存済みスタイル
    with st.expander("💾 保存済みスタイル"):
        if "saved_styles" not in st.session_state:
            st.session_state.saved_styles = {}
            
        if st.session_state.saved_styles:
            selected_style = st.selectbox("保存済みスタイル", list(st.session_state.saved_styles.keys()))
            if st.button("ロード"):
                st.session_state.style_rules = st.session_state.saved_styles[selected_style]
                st.success(f"スタイル '{selected_style}' を読み込みました")

# タブを作成
tab1, tab2 = st.tabs(["📝 スタイル抽出", "✉️ メール生成"])

# --- 1) スタイル抽出タブ ------------------------------------------------
with tab1:
    st.markdown('<h1 class="main-header">📧 メールスタイル抽出</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="info-box">既存のメールから文体ルールを自動抽出します。メール全文を入力してください。</div>', unsafe_allow_html=True)
        # セッション状態がない場合は初期化
        if "email_input" not in st.session_state:
            st.session_state.email_input = ""
        
        email_src = st.text_area(
            "✉️ メール本文", 
            value=st.session_state.email_input,
            height=250,
            key="email_src"
        )
        
        # 分析ボタンの作成（カスタムスタイル適用）
        extract_btn = st.button(
            "🔍 スタイルを分析", 
            disabled=not (email_src and api_key),
            type="primary",
            use_container_width=True
        )
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💡 ヒント")
        st.markdown("""
        - 長文のメールほど特徴を抽出しやすくなります
        - 複数のメールを入力するとより豊かなスタイルが抽出できます
        - 文体の特徴を最もよく表したメールを選びましょう
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown("### 📊 抽出される特徴例")
        st.markdown("""
        - 文末表現のパターン
        - 挨拶や結びの特徴
        - 文の長さや構造
        - 敬語・謙譲語の使用傾向
        - 使用される慣用表現
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # スタイルルール初期化
    if "style_rules" not in st.session_state:
        st.session_state.style_rules = None
    
    # 分析ボタンが押された場合の処理
    if extract_btn:
        with st.spinner("文体を分析中..."):
            tpl = env.get_template("style_rules_prompt.jinja2")
            prompt = tpl.render(email_text=email_src)
            try:
                client = OpenAI(api_key=api_key)
                res = client.chat.completions.create(
                    model=model,
                    temperature=0.3,
                    messages=[
                        {"role": "system", "content": "You are an expert writing-style analyst."},
                        {"role": "user", "content": prompt},
                    ],
                )
                style_rules = res.choices[0].message.content
                st.session_state.style_rules = style_rules
                
                # 分析結果の表示
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown('<h2 class="sub-header">📝 抽出された文体ルール</h2>', unsafe_allow_html=True)
                st.markdown(style_rules)
                
                # スタイル保存機能
                save_name = st.text_input("このスタイルに名前をつけて保存", placeholder="例: ビジネス丁寧スタイル")
                if st.button("保存", key="save_style"):
                    if save_name:
                        if "saved_styles" not in st.session_state:
                            st.session_state.saved_styles = {}
                        st.session_state.saved_styles[save_name] = style_rules
                        st.success(f"'{save_name}'として保存しました！")
                
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- 2) メール生成タブ --------------------------------------------------
with tab2:
    st.markdown('<h1 class="main-header">✍️ メール生成</h1>', unsafe_allow_html=True)
    
    if st.session_state.style_rules:
        st.markdown('<div class="info-box">抽出されたスタイルを使って新しいメールを生成します。書きたい内容を入力してください。</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            user_request = st.text_area(
                "📋 書きたい内容", 
                placeholder="例: 会議の日程変更のお知らせ。水曜から金曜に変更したいです。",
                height=150, 
                key="request"
            )
            
            # 追加オプション
            with st.expander("📌 追加オプション"):
                recipient = st.text_input("宛先 (任意)", placeholder="例: 田中様")
                formality = st.slider("フォーマリティ", 1, 5, 3, 
                               help="1=カジュアル、5=非常に丁寧")
                length = st.radio("メールの長さ", ["短め", "標準", "詳細"], index=1)
            
            # 生成ボタン
            gen_btn = st.button(
                "✨ メールを生成", 
                disabled=not (user_request and api_key),
                type="primary",
                use_container_width=True
            )
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 現在のスタイル")
            # スタイルをコンパクトに表示
            compact_style = st.session_state.style_rules.split('\n')[:5]
            compact_style.append("...")
            st.markdown('\n'.join(compact_style))
            if st.button("スタイルを編集", key="edit_style"):
                st.session_state.style_rules = st.text_area(
                    "スタイルルールを編集", 
                    value=st.session_state.style_rules,
                    height=300
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        if gen_btn:
            with st.spinner("メールを生成中..."):
                tpl = env.get_template("email_generate_prompt.jinja2")
                
                # 追加オプションを含めたプロンプト作成
                additional_info = {
                    "recipient": recipient if 'recipient' in locals() and recipient else "",
                    "formality": formality if 'formality' in locals() else 3,
                    "length": length if 'length' in locals() else "標準",
                    "purpose": purpose
                }
                
                gen_prompt = tpl.render(
                    style_rules=st.session_state.style_rules, 
                    user_request=user_request,
                    additional_info=additional_info
                )
                
                try:
                    client = OpenAI(api_key=api_key)
                    res = client.chat.completions.create(
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that writes emails."},
                            {"role": "user", "content": gen_prompt},
                        ],
                    )
                    email_out = res.choices[0].message.content
                    
                    # 生成されたメールの表示
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown('<h2 class="sub-header">📨 生成されたメール</h2>', unsafe_allow_html=True)
                    
                    # タブでプレーンテキストとプレビュー表示を切り替え
                    email_tab1, email_tab2 = st.tabs(["✉️ テキスト", "👁️ プレビュー"])
                    
                    with email_tab1:
                        st.text_area("", email_out, height=300)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 ダウンロード (.txt)", 
                                email_out, 
                                file_name=f"email_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                use_container_width=True
                            )
                        with col2:
                            st.button(
                                "📋 クリップボードにコピー", 
                                key="copy_btn",
                                use_container_width=True,
                                on_click=lambda: st.write('<script>navigator.clipboard.writeText(`' + email_out.replace('`', '\\`') + '`);</script>', unsafe_allow_html=True)
                            )
                    
                    with email_tab2:
                        st.markdown(f"<div style='background-color: white; padding: 20px; border-radius: 5px; border: 1px solid #ccc;'>{email_out.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                    
                    # 改善提案
                    with st.expander("💡 メール改善のヒント"):
                        st.markdown("""
                        - **主題を明確に:** 最初の段落で目的を明確にしましょう
                        - **簡潔さを心がける:** 不要な説明は省きましょう
                        - **アクションアイテムを明確に:** 相手に何を求めるか明確にしましょう
                        - **締めくくりを丁寧に:** 最後の挨拶は印象を左右します
                        """)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 履歴に保存
                    if "email_history" not in st.session_state:
                        st.session_state.email_history = []
                    
                    st.session_state.email_history.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "request": user_request,
                        "email": email_out
                    })
                    
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
    else:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 💡 まずはスタイルを抽出してください")
        st.markdown("「スタイル抽出」タブで既存のメールからスタイルを抽出すると、そのスタイルに基づいて新しいメールを生成できます。")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 履歴タブ (オプション) ----------------------------------------------
if "email_history" in st.session_state and st.session_state.email_history:
    with st.expander("📚 履歴"):
        for i, item in enumerate(reversed(st.session_state.email_history)):
            st.markdown(f"**{item['timestamp']}**")
            st.markdown(f"要件: {item['request'][:50]}...")
            if st.button(f"表示する #{i+1}", key=f"show_history_{i}"):
                st.text_area(f"生成履歴 #{i+1}", item['email'], height=200)
            st.divider()

# --- フッター -----------------------------------------------------------
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("---")
st.markdown("📧 Email Stylist Pro - API キーはブラウザにのみ保持され、サーバー側には保存されません。")
st.markdown('</div>', unsafe_allow_html=True)