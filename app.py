"""The VC Brain — Dashboard (Streamlit).

Ejecutar con:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from vcbrain.config import settings
from vcbrain.connect import generate_outreach
from vcbrain.pipeline import run_pipeline

st.set_page_config(
    page_title="The VC Brain",
    page_icon="🧠",
    layout="wide",
)

# ---------- Encabezado ----------
st.title("🧠 The VC Brain")
st.caption(
    "Aprobación instantánea de fundadores early-stage — "
    "Scout → Judge → Score → Connect · Maschmeyer Group"
)

# ---------- Validación de entorno ----------
missing = settings.validate()
if missing:
    st.error(
        "Faltan variables de entorno en `.env`: **"
        + ", ".join(missing)
        + "**. Copia `.env.example` a `.env` y rellena tus claves."
    )
    st.stop()

# ---------- Sidebar: configuración ----------
with st.sidebar:
    st.header("⚙️ Configuración")
    st.markdown(f"**Motor cognitivo:** `{settings.llm_provider}`")
    st.markdown(f"**Modelo:** `{settings.openai_model}`")
    max_results = st.slider("Resultados Tavily por consulta", 3, 15, settings.tavily_max_results)

# ---------- Barra de búsqueda ----------
col_query, col_btn = st.columns([5, 1])
with col_query:
    query = st.text_input(
        "Sector o tecnología",
        placeholder="p. ej. AI agents infrastructure, climate tech, dev tools…",
        label_visibility="collapsed",
    )
with col_btn:
    run = st.button("🚀 Ejecutar", type="primary", use_container_width=True)

# ---------- Ejecución del pipeline ----------
if run and query.strip():
    with st.spinner("Scout: rastreando señales en la web (Tavily)…"):
        result = run_pipeline(query.strip(), max_results=max_results)
    st.session_state["result"] = result
elif run:
    st.warning("Escribe un sector o tecnología antes de ejecutar.")

result = st.session_state.get("result")

if result:
    for err in result.errors:
        st.error(err)

    if result.founders:
        st.success(
            f"**{len(result.founders)} fundadores** evaluados sobre "
            f"{len(result.raw_hits)} fuentes · motor cognitivo: "
            f"`{result.provider_used}`"
        )

        # ---------- Tabla estructurada ----------
        df = pd.DataFrame(
            [
                {
                    "Score": f.founder_score,
                    "Fundador": f.name,
                    "Empresa": f.company,
                    "Rol": f.role,
                    "Justificación": f.justification,
                    "Evidencia": " · ".join(f.evidence),
                }
                for f in result.founders
            ]
        )
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Founder Score", min_value=0, max_value=100, format="%d"
                ),
            },
        )

        # ---------- Detalle + Connect ----------
        st.subheader("📇 Detalle y contacto")
        for i, founder in enumerate(result.founders):
            with st.expander(
                f"{founder.founder_score}/100 — {founder.name} · {founder.company}"
            ):
                st.markdown(f"**Rol:** {founder.role or '—'}")
                st.markdown(f"**Justificación:** {founder.justification}")
                if founder.signals:
                    st.markdown("**Señales técnicas:**")
                    for s in founder.signals:
                        st.markdown(f"- {s}")
                if founder.evidence:
                    st.markdown("**Evidencia:**")
                    for url in founder.evidence:
                        st.markdown(f"- {url}")
                if founder.contact_hint:
                    st.markdown(f"**Canal de contacto:** {founder.contact_hint}")

                msg_key = f"outreach_{i}"
                if st.button("✉️ Generar outreach personalizado", key=f"btn_{i}"):
                    with st.spinner("Connect: redactando mensaje…"):
                        try:
                            message, provider = generate_outreach(founder)
                            st.session_state[msg_key] = (message, provider)
                        except Exception as exc:
                            st.error(f"No se pudo generar el mensaje: {exc}")
                if msg_key in st.session_state:
                    message, provider = st.session_state[msg_key]
                    st.text_area(
                        f"Mensaje listo para enviar (generado con {provider})",
                        value=message,
                        height=180,
                        key=f"txt_{i}",
                    )
    elif not result.errors:
        st.info(
            "No se identificaron fundadores con evidencia suficiente. "
            "Prueba con un sector más específico."
        )

    # ---------- Fuentes crudas (transparencia) ----------
    if result.raw_hits:
        with st.expander(f"🔍 Fuentes analizadas ({len(result.raw_hits)})"):
            for hit in result.raw_hits:
                st.markdown(f"- [{hit.title or hit.url}]({hit.url}) · relevancia {hit.score:.2f}")
else:
    st.info("Introduce un sector/tecnología y pulsa **Ejecutar** para descubrir fundadores.")
