# frontend-streamlit/app/streamlit_app.py

import streamlit as st
from requests.exceptions import HTTPError
import uuid
import logging

from api_client import go_api, python_rag_api
from api_client.python_rag_api import API_PYTHON_RAG_URL

# --- ページ設定 & 初期化 ---
st.set_page_config(page_title="OpenRAG", layout="wide")
logging.basicConfig(level=logging.INFO)

# --- セッション状態の初期化 ---
def init_session_state():
    defaults = {
        "token": None,
        "user_info": None,
        "workspaces": [],
        "selected_workspace": None,
        "messages": [],
        "mode": None, # "guest" または None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- ゲストページ ---
def guest_page():
    st.session_state.setdefault("guest_id", str(uuid.uuid4()))
    st.session_state.setdefault("messages", [])

    # --- サイドバー ---
    with st.sidebar:
        st.title("🗂️ OpenRAG (ゲスト)")
        st.info("ゲストモードでは、アップロードした資料はセッション終了時に破棄されます。")

        if st.button("ゲストセッションを終了"):
            # セッション状態をクリアして再実行
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()
        
        st.divider()

        # ファイルアップロード
        with st.expander("資料をアップロード", expanded=True):
            uploaded_file = st.file_uploader("PDF, DOCX, TXTファイルをアップロード", type=["pdf", "docx", "txt"], key="guest_uploader")
            if uploaded_file:
                if st.button("ファイルを処理", key="guest_process_button"):
                    with st.spinner("ファイルをアップロード中..."):
                        try:
                            result = python_rag_api.guest_upload_document(
                                guest_id=st.session_state.guest_id,
                                file=uploaded_file
                            )
                            st.success(f"ファイル「{result['filename']}」の処理が完了しました。")
                        except HTTPError as e:
                            try:
                                error_details = e.response.json()
                                error_message = error_details.get("detail", "不明なエラーです。")
                                st.error(f"アップロードに失敗しました: {error_message}")
                            except (ValueError, AttributeError):
                                st.error(f"アップロードに失敗しました: {e.response.text}")
                        except Exception as e:
                            st.error(f"予期せぬエラーが発生しました: {e}")

    # --- メインコンテンツ ---
    st.header("💬 ゲストチャット")
    st.markdown("サイドバーから資料をアップロードして、内容について質問してください。")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("回答を生成中です..."):
                try:
                    response_data = python_rag_api.guest_post_chat_message(guest_id=st.session_state.guest_id, query=prompt)
                    response_text = response_data.get("response", "回答を取得できませんでした。")
                    sources = response_data.get("sources", [])
                    
                    full_response = response_text
                    if sources:
                        sources_str = "\n- ".join(sorted(list(set(sources))))
                        full_response += f"\n\n---\n**参照ソース:**\n- {sources_str}"

                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    error_msg = f"回答の生成中にエラーが発生しました: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# --- 認証ページ ---
def login_page():
    st.title("🚀 OpenRAGへようこそ")
    
    login_tab, register_tab = st.tabs(["ログイン", "新規登録"])

    with login_tab:
        st.header("ログイン")

        if st.button("ゲストとして試す", use_container_width=True, type="secondary"):
            st.session_state.mode = "guest"
            st.rerun()
        st.divider()

        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submitted = st.form_submit_button("ログイン")

            if submitted:
                if not email or not password:
                    st.error("メールアドレスとパスワードを入力してください。")
                    return

                try:
                    with st.spinner("ログイン中..."):
                        login_data = go_api.login(email, password)
                        st.session_state.token = login_data.get("token")
                        st.session_state.user_info = login_data.get("user")
                        st.rerun()
                except HTTPError as e:
                    if e.response.status_code == 401:
                        st.error("メールアドレスまたはパスワードが正しくありません。")
                    else:
                        st.error(f"ログイン中にエラーが発生しました: {e.response.text}")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {e}")

    with register_tab:
        st.header("新規登録")
        with st.form("register_form", clear_on_submit=True):
            username = st.text_input(
                "ユーザー名",
                help="ユーザー名は半角英数字のみ使用できます (例: user123)"
            )
            email_reg = st.text_input("メールアドレス (登録用)")
            password_reg = st.text_input(
                "パスワード (登録用)",
                type="password",
                help="パスワードは8文字以上で設定してください。"
            )
            submitted_reg = st.form_submit_button("登録")

            if submitted_reg:
                if not username or not email_reg or not password_reg:
                    st.warning("すべての項目を入力してください。")
                else:
                    try:
                        with st.spinner("登録処理中..."):
                            # この機能には api_client.py への register 関数の追加が必要です
                            go_api.register(username, email_reg, password_reg)
                        st.success("登録が完了しました。ログインタブからログインしてください。")
                    except HTTPError as e:
                        try:
                            # APIからの詳細なエラーメッセージを抽出しようと試みる
                            error_details = e.response.json()
                            error_message = error_details.get("error", "不明なエラーです。")
                            st.error(f"登録に失敗しました: {error_message}")
                        except ValueError:
                            # JSONの解析に失敗した場合、プレーンテキストを表示
                            st.error(f"登録に失敗しました: {e.response.text}")
                    except Exception as e:
                        st.error(f"予期せぬエラーが発生しました: {e}")

# --- メインページ ---
def main_page():
    # --- サイドバー ---
    with st.sidebar:
        st.title("🗂️ OpenRAG")
        if st.session_state.user_info:
            st.write(f"ようこそ、 **{st.session_state.user_info['username']}** さん")
        
        if st.button("ログアウト"):
            # セッション状態をクリアして再実行
            for key in st.session_state.keys():
                del st.session_state[key]
            init_session_state()
            st.rerun()

        st.divider()

        # --- 新しいワークスペースの作成GUI ---
        with st.expander("新しいワークスペースを作成"):
            with st.form("new_workspace_form", clear_on_submit=True):
                new_workspace_name = st.text_input("ワークスペース名")
                new_system_prompt = st.text_area(
                    "システムプロンプト (オプション)",
                    help="AIに特定の役割や振る舞いをさせたい場合に設定します。例: 「あなたはプロの編集者です。以下の資料に基づき、簡潔に回答してください。」"
                )
                create_submitted = st.form_submit_button("作成")
                if create_submitted:
                    if not new_workspace_name:
                        st.warning("ワークスペース名を入力してください。")
                    else:
                        try:
                            with st.spinner("作成中..."):
                                go_api.create_lecture(
                                    token=st.session_state.token,
                                    name=new_workspace_name,
                                    system_prompt=new_system_prompt
                                )
                            st.success(f"ワークスペース「{new_workspace_name}」を作成しました。")
                            st.rerun() # リストを更新するために再実行
                        except Exception as e:
                            st.error(f"ワークスペースの作成に失敗しました: {e}")
        
        st.divider()

        # ワークスペースの選択
        try:
            st.session_state.workspaces = go_api.get_lectures(st.session_state.token)
        except Exception as e:
            st.error(f"ワークスペース一覧の取得に失敗しました: {e}")
            return
        
        if st.session_state.workspaces:
            workspace_options = {ws['id']: ws['name'] for ws in st.session_state.workspaces}
            selected_id = st.selectbox(
                "ワークスペースを選択してください",
                options=list(workspace_options.keys()),
                format_func=lambda x: workspace_options[x],
                index=0 if not st.session_state.selected_workspace else list(workspace_options.keys()).index(st.session_state.selected_workspace['id'])
            )
            if not st.session_state.selected_workspace or st.session_state.selected_workspace['id'] != selected_id:
                st.session_state.selected_workspace = next((ws for ws in st.session_state.workspaces if ws['id'] == selected_id), None)
                st.session_state.messages = []
                st.rerun()
        else:
            st.warning("利用可能なワークスペースがありません。")
            st.session_state.selected_workspace = None
        
        st.divider()

        # ファイルアップロード
        if st.session_state.selected_workspace:
            with st.expander("資料をアップロード"):
                uploaded_file = st.file_uploader("PDF, DOCX, TXTファイルをアップロード", type=["pdf", "docx", "txt"])
                if uploaded_file:
                    if st.button("ファイルを処理"):
                        with st.spinner(f"「{st.session_state.selected_workspace['name']}」にファイルをアップロード中..."):
                            try:
                                result = python_rag_api.upload_document(
                                    token=st.session_state.token,
                                    lecture_id=st.session_state.selected_workspace['id'],
                                    file=uploaded_file
                                )
                                st.success(f"ファイル「{result['filename']}」の処理が完了しました。")
                            except HTTPError as e:
                                try:
                                    # FastAPI/Pythonバックエンドからの詳細なエラーメッセージを抽出
                                    error_details = e.response.json()
                                    error_message = error_details.get("detail", "不明なエラーです。")
                                    st.error(f"アップロードに失敗しました: {error_message}")
                                except (ValueError, AttributeError):
                                    # JSONの解析に失敗した場合、プレーンテキストを表示
                                    st.error(f"アップロードに失敗しました: {e.response.text}")
                            except Exception as e:
                                st.error(f"予期せぬエラーが発生しました: {e}")
    
    # --- メインコンテンツ ---
    if not st.session_state.selected_workspace:
        st.info("サイドバーからワークスペースを選択してください。")
        return

    st.header(f"💬 {st.session_state.selected_workspace['name']}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("回答を生成中です..."):
                try:
                    response_data = python_rag_api.post_chat_message(
                        token=st.session_state.token,
                        lecture_id=st.session_state.selected_workspace['id'],
                        query=prompt,
                        system_prompt=st.session_state.selected_workspace.get("system_prompt")
                    )
                    
                    response_text = response_data.get("response", "回答を取得できませんでした。")
                    sources = response_data.get("sources", [])
                    
                    full_response = response_text
                    if sources:
                        sources_str = "\n- ".join(sorted(list(set(sources))))
                        full_response += f"\n\n---\n**参照ソース:**\n- {sources_str}"

                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    error_msg = f"回答の生成中にエラーが発生しました: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


# --- メインロジック (ページの切り替え) ---
if st.session_state.get("mode") == "guest":
    guest_page()
elif st.session_state.get("token"):
    main_page()
else:
    login_page()