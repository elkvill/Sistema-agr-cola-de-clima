import streamlit as st
from dominio.puertos import ServicioChatIA


def procesar_chat(prompt, r, servicio_ia: ServicioChatIA):
    st.session_state.chat_historial.append(
        {"role": "user", "content": prompt}
    )
    if st.session_state.modo_offline:
        st.session_state.chat_historial.append(
            {"role": "assistant", "content": "Chat no disponible en modo offline."}
        )
    else:
        try:
            resp = servicio_ia.chat(
                prompt, r.datos.actual.temperatura,
                r.datos.actual.humedad, r.datos.actual.precipitacion
            )
            st.session_state.chat_historial.append(
                {"role": "assistant", "content": resp}
            )
        except Exception as e:
            st.session_state.chat_historial.append(
                {"role": "assistant", "content": f"Error: {e}"}
            )


def renderizar_chat(servicio_ia: ServicioChatIA, r):
    st.markdown("### Asesoría Inteligente")
    with st.expander("Abrir Chat Experto Nicaragua", expanded=True):
        for idx, msg in enumerate(st.session_state.chat_historial):
            bg_color = "#e8f5e9" if msg["role"] == "user" else "#ffffff"
            border_color = "#c8e6c9" if msg["role"] == "user" else "#e0e0e0"
            with st.container():
                estilo_div = (
                    f"background-color: {bg_color}; "
                    f"border: 1px solid {border_color}; "
                    "padding: 10px; border-radius: 8px; "
                    "margin-bottom: 8px; width: 100%; "
                    "box-sizing: border-box;"
                )
                emisor = "Tú" if msg["role"] == "user" else "Asistente"
                st.markdown(
                    f'<div style="{estilo_div}">'
                    f'<strong>{emisor}:</strong><br>{msg["content"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        with st.form(key="chat_form", clear_on_submit=True):
            prompt = st.text_input("¿Dudas sobre tu cultivo o el clima?", key="input_chat_text")
            enviar = st.form_submit_button("Enviar", use_container_width=True)
            if enviar and prompt:
                procesar_chat(prompt, r, servicio_ia)
                st.rerun()
